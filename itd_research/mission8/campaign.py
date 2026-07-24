"""Orchestrate the Mission 8 structural/topological campaign on ingested sequences.

Given a directory of external ``frame_*.npz`` sequences (real JHTDB data in a manual run,
or the offline synthetic fixture in CI), this loads each sequence, computes its baseline +
structural trajectories and ITD-independent topology events, then runs the saturation
screen and (if unsaturated) the primary H61/H62 test on preregistered dev/holdout splits.
No network access occurs here -- the caller supplies already-downloaded directories.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from itd_research.mission8.baselines import (
    BASELINE_COMPETENT_COMBINED,
    compute_baseline_trajectory,
)
from itd_research.mission8.degradation import degrade_noise
from itd_research.mission8.descriptive import (
    evaluate_channel_stability,
    evaluate_lead_time,
    evaluate_topology_response_consistency,
)
from itd_research.mission8.event_labels import label_structural_events
from itd_research.mission8.fixtures import write_synthetic_sequence
from itd_research.mission8.ingestion import load_sequence_as_tuples
from itd_research.mission8.ood import run_structural_ood_analysis
from itd_research.mission8.prediction import (
    PrimaryTestResult,
    Sequence,
    make_sequence,
    run_primary_test,
)
from itd_research.mission8.profiles import benchmark_profile, get_profile
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    compute_structural_trajectory,
)


def build_sequence(directory: str | Path, *, sequence_id: str, min_cells: int = 8, horizon: int = 2) -> Sequence:
    """Ingest one external sequence directory and compute everything needed for prediction."""
    frames, _provenance = load_sequence_as_tuples(directory, source_id=sequence_id)
    baseline = compute_baseline_trajectory(frames, min_cells=min_cells)
    structural = compute_structural_trajectory(frames)
    events, _disagreement = label_structural_events(frames, source_id=sequence_id, min_cells=min_cells)
    return make_sequence(sequence_id, baseline, structural, events, horizon=horizon)


@dataclass(frozen=True)
class Mission8CampaignResult:
    """Full campaign outcome: per-sequence event counts plus the primary test result."""

    dev_ids: list[str]
    holdout_ids: list[str]
    dev_event_counts: dict[str, int]
    holdout_event_counts: dict[str, int]
    primary_test: PrimaryTestResult
    is_synthetic_fixture: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "dev_ids": self.dev_ids,
            "holdout_ids": self.holdout_ids,
            "dev_event_counts": self.dev_event_counts,
            "holdout_event_counts": self.holdout_event_counts,
            "primary_test": self.primary_test.as_dict(),
            "is_synthetic_fixture": self.is_synthetic_fixture,
            "evidence_class": "synthetic-code-verification (NOT external evidence)"
            if self.is_synthetic_fixture else "external-DNS",
        }


def run_structural_campaign(
    dev_dirs: list[tuple[str, str]], holdout_dirs: list[tuple[str, str]],
    *, is_synthetic_fixture: bool = False, min_cells: int = 8, horizon: int = 2,
    established_names: tuple[str, ...] = BASELINE_COMPETENT_COMBINED,
    itd_names: tuple[str, ...] = ITD_3D_NONREDUNDANT, bootstrap: int = 2000,
) -> Mission8CampaignResult:
    """Run the full campaign given (sequence_id, directory) pairs for dev and holdout."""
    dev_sequences = [build_sequence(d, sequence_id=sid, min_cells=min_cells, horizon=horizon) for sid, d in dev_dirs]
    holdout_sequences = [
        build_sequence(d, sequence_id=sid, min_cells=min_cells, horizon=horizon) for sid, d in holdout_dirs
    ]
    primary = run_primary_test(
        dev_sequences, holdout_sequences, established_names, itd_names=itd_names, bootstrap=bootstrap,
    )
    return Mission8CampaignResult(
        dev_ids=[s.sequence_id for s in dev_sequences],
        holdout_ids=[s.sequence_id for s in holdout_sequences],
        dev_event_counts={s.sequence_id: len(s.events) for s in dev_sequences},
        holdout_event_counts={s.sequence_id: len(s.events) for s in holdout_sequences},
        primary_test=primary,
        is_synthetic_fixture=is_synthetic_fixture,
    )


def run_fixture_campaign(*, nodes: int = 24, n_frames: int = 16) -> Mission8CampaignResult:
    """Offline CI path: synthesise two tiny dev + two tiny holdout sequences (no network).

    Each of the 4 sequences uses a distinct seed so they are not byte-identical realisations.
    """
    with tempfile.TemporaryDirectory(prefix="itd-m8-fixture-") as tmp:
        base = Path(tmp)
        dev_dirs = []
        holdout_dirs = []
        for i in range(2):
            d = base / f"dev_{i}"
            write_synthetic_sequence(d, nodes=nodes, n_frames=n_frames, seed=i)
            dev_dirs.append((f"synthetic_dev_{i}", str(d)))
        for i in range(2):
            d = base / f"holdout_{i}"
            write_synthetic_sequence(d, nodes=nodes, n_frames=n_frames, seed=2 + i)
            holdout_dirs.append((f"synthetic_holdout_{i}", str(d)))
        return run_structural_campaign(dev_dirs, holdout_dirs, is_synthetic_fixture=True, bootstrap=200)


def run_full_fixture_validation(*, nodes: int = 24, n_frames: int = 16) -> dict[str, object]:
    """Bounded, deterministic, offline exercise of the FULL Mission 8 module set (CI).

    Synthetic fixtures only -- CODE-VERIFICATION, never presented as external evidence.
    Runs the primary campaign (saturation screen + H61/H62) plus the descriptive H64/H70/
    H71 checks, the H73 structural-OOD detector, and one profile-benchmark call, so every
    Mission 8 module stays numerically exercised without any network access.
    """
    primary = run_fixture_campaign(nodes=nodes, n_frames=n_frames)

    with tempfile.TemporaryDirectory(prefix="itd-m8-fixture-full-") as tmp:
        base = Path(tmp)
        dirs = []
        for i in range(4):
            d = base / f"seq_{i}"
            write_synthetic_sequence(d, nodes=nodes, n_frames=n_frames, seed=i)
            dirs.append((f"synthetic_{i}", str(d)))
        sequences = [build_sequence(d, sequence_id=sid, min_cells=8, horizon=2) for sid, d in dirs]
        frames_holdout, _ = load_sequence_as_tuples(dirs[2][1], source_id=dirs[2][0])

    swe = [(s.sequence_id, s.structural, [e.event_frame for e in s.events]) for s in sequences]
    h64 = evaluate_topology_response_consistency(swe, min_events=1)
    h70_established = evaluate_lead_time(
        sequences, feature_set="established_only", established_names=BASELINE_COMPETENT_COMBINED, itd_names=(),
    )
    h70_itd_only = evaluate_lead_time(
        sequences, feature_set="itd_only", established_names=(), itd_names=ITD_3D_NONREDUNDANT,
    )
    h71 = evaluate_channel_stability(sequences)

    noisy_frames = degrade_noise(frames_holdout, 0.05, seed=7)
    categories = {
        "holdout_same_source": ("held-out synthetic fixture sequence", sequences[2].structural),
        "measurement_noise": ("noise-degraded synthetic fixture sequence", compute_structural_trajectory(noisy_frames)),
    }
    dev_trajectories = [s.structural for s in sequences[:2]]
    ood = run_structural_ood_analysis(dev_trajectories, categories, far_category="measurement_noise")

    profile = get_profile("external_vortex_merger")
    bench = benchmark_profile(frames_holdout, profile, repeats=2, min_cells=8)

    return {
        "primary": primary.as_dict(),
        "h64_topology_response": h64.as_dict(),
        "h70_lead_time_established": h70_established.as_dict(),
        "h70_lead_time_itd_only": h70_itd_only.as_dict(),
        "h71_channel_stability": h71.as_dict(),
        "h73_structural_ood": ood.as_dict(),
        "profile_benchmark": bench.as_dict(),
        "evidence_class": "synthetic-code-verification (NOT external evidence)",
    }
