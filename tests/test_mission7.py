"""Tests for the Mission 7 external-evidence pipeline (H49-H54).

Offline and deterministic: they use the synthetic fixture and tiny hand-built frames, never
the network. They check ingestion safety (the failure modes the preregistration lists),
physical validation, ITD-independence of the event, and campaign determinism. They assert
NO scientific verdict on real data -- that is reported honestly from the manual JHTDB run.
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path

import numpy as np
import pytest

from itd_research.mission7.analysis import (
    compute_trajectories,
    external_prediction,
    label_enstrophy_event,
    rank_complementarity,
)
from itd_research.mission7.campaign import run_external_campaign, run_fixture_campaign
from itd_research.mission7.fixtures import write_synthetic_sequence
from itd_research.mission7.ingestion import IngestionLimits, load_field_sequence
from itd_research.mission7.physics import validate_isotropic_dns


def _write_frame(path: Path, n: int, seed: int, time: float) -> None:
    rng = np.random.default_rng(seed)
    coords = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    u, v, w = (rng.normal(size=(n, n, n)) for _ in range(3))
    np.savez(path, x=coords, y=coords, z=coords, u=u, v=v, w=w, time=np.array([time]))


def test_load_sequence_returns_ordered_frames_with_provenance(tmp_path: Path) -> None:
    for i in range(4):
        _write_frame(tmp_path / f"frame_{i:02d}.npz", 8, seed=i, time=0.1 * i)
    frames, prov = load_field_sequence(tmp_path, source_id="unit")
    assert prov.n_frames == 4
    assert prov.grid_shape == (8, 8, 8)
    assert [fr.time for fr in frames] == pytest.approx([0.0, 0.1, 0.2, 0.3])
    assert len(prov.frame_sha256) == 4 and all(len(h) == 64 for h in prov.frame_sha256)


def test_ingestion_rejects_non_finite(tmp_path: Path) -> None:
    coords = np.linspace(0.0, 1.0, 6, endpoint=False)
    bad = np.zeros((6, 6, 6))
    bad[0, 0, 0] = np.inf
    np.savez(tmp_path / "frame_00.npz", x=coords, y=coords, z=coords, u=bad, v=bad, w=bad, time=np.array([0.0]))
    with pytest.raises(ValueError, match="non-finite"):
        load_field_sequence(tmp_path, source_id="unit")


def test_ingestion_rejects_duplicate_frames(tmp_path: Path) -> None:
    _write_frame(tmp_path / "frame_00.npz", 6, seed=1, time=0.0)
    # A byte-identical copy under a new name is a genuine duplicate (same checksum).
    shutil.copy(tmp_path / "frame_00.npz", tmp_path / "frame_01.npz")
    with pytest.raises(ValueError):
        load_field_sequence(tmp_path, source_id="unit")


def test_ingestion_rejects_non_monotone_coordinates(tmp_path: Path) -> None:
    coords = np.array([0.0, 0.2, 0.1, 0.3, 0.4, 0.5])  # not increasing
    f = np.zeros((6, 6, 6))
    np.savez(tmp_path / "frame_00.npz", x=coords, y=coords, z=coords, u=f, v=f, w=f, time=np.array([0.0]))
    with pytest.raises(ValueError, match="increasing"):
        load_field_sequence(tmp_path, source_id="unit")


def test_ingestion_enforces_frame_limit(tmp_path: Path) -> None:
    for i in range(3):
        _write_frame(tmp_path / f"frame_{i:02d}.npz", 6, seed=i, time=0.1 * i)
    with pytest.raises(ValueError, match="too many frames"):
        load_field_sequence(tmp_path, source_id="unit", limits=IngestionLimits(max_frames=2))


def test_ingestion_enforces_grid_cell_limit(tmp_path: Path) -> None:
    _write_frame(tmp_path / "frame_00.npz", 8, seed=1, time=0.0)
    with pytest.raises(ValueError, match="max_grid_cells"):
        load_field_sequence(tmp_path, source_id="unit", limits=IngestionLimits(max_grid_cells=10))


def test_physics_flags_solenoidal_field(tmp_path: Path) -> None:
    # A Taylor-Green field is divergence-free; validation should mark it solenoidal.
    write_synthetic_sequence(tmp_path, nodes=12, n_frames=4)
    frames, _ = load_field_sequence(tmp_path, source_id="fixture")
    phys = validate_isotropic_dns(frames)
    assert phys.solenoidal_ok
    assert phys.divergence_relative < 0.30


def test_event_label_uses_only_enstrophy_and_dev_threshold(tmp_path: Path) -> None:
    write_synthetic_sequence(tmp_path, nodes=12, n_frames=12)
    frames, _ = load_field_sequence(tmp_path, source_id="fixture")
    traj = compute_trajectories(frames)
    labels, threshold = label_enstrophy_event(traj, dev_frames=8)
    # The event is defined purely from established enstrophy exceeding a dev threshold.
    enst = np.asarray(traj.established["enstrophy"])
    assert np.array_equal(labels, (enst > threshold).astype(np.int64))


def test_complementarity_reports_all_itd_channels(tmp_path: Path) -> None:
    write_synthetic_sequence(tmp_path, nodes=12, n_frames=10)
    frames, _ = load_field_sequence(tmp_path, source_id="fixture")
    comp = rank_complementarity(compute_trajectories(frames))
    assert comp.reference == "enstrophy"
    assert len(comp.correlations) == 8  # all ITD channels scored


def test_prediction_is_deterministic_and_honest_about_power(tmp_path: Path) -> None:
    write_synthetic_sequence(tmp_path, nodes=12, n_frames=12)
    frames, _ = load_field_sequence(tmp_path, source_id="fixture")
    traj = compute_trajectories(frames)
    a = external_prediction(traj).as_dict()
    b = external_prediction(traj).as_dict()
    # NaN != NaN, so compare NaN-aware: same keys, equal values or both NaN.
    assert a.keys() == b.keys()
    for key in a:
        av, bv = a[key], b[key]
        if isinstance(av, float) and math.isnan(av):
            assert isinstance(bv, float) and math.isnan(bv)
        else:
            assert av == bv
    a = external_prediction(traj)
    # A short external sequence must never be reported as strong evidence.
    assert a.verdict in {"inconclusive", "not supported", "supported within tested scope"}
    if a.n_holdout < 8:
        assert a.verdict == "inconclusive"


def test_fixture_campaign_is_labelled_synthetic() -> None:
    result = run_fixture_campaign()
    assert result.is_synthetic_fixture
    assert "NOT external evidence" in str(result.as_dict()["evidence_class"])


def test_external_campaign_on_fixture_dir(tmp_path: Path) -> None:
    write_synthetic_sequence(tmp_path, nodes=12, n_frames=10)
    result = run_external_campaign(tmp_path, source_id="fixture_dir")
    assert result.provenance.n_frames == 10
    assert result.physics.verdict in {
        "supported within tested scope", "partially supported", "not supported",
    }
