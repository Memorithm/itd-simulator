"""Tests for the competent-baseline cross-code transfer (Mission 6, H37-H42).

These cover the mechanical properties of the normalization + transfer machinery on tiny
synthetic runs -- determinism, leakage-safety of the normalizers, and that selection
never inspects the holdout. They deliberately do NOT assert a scientific verdict (that is
established by the full campaign and reported honestly, including a likely negative H38).
"""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.cross_code.normalization import (
    METHODS,
    normalize_run,
    normalize_runs,
)
from itd_research.cross_code.transfer import (
    _COMPETENT_METHODS,
    DirectionResult,
    evaluate_direction,
    run_competent_campaign,
    select_competent_method,
    transfer_auc,
)
from itd_research.hard_prediction.flows import ALL_FEATURES, HardRun


def _make_run(seed: int, n_frames: int = 12, event_frame: int = 8, scale: float = 1.0) -> HardRun:
    """A deterministic synthetic run whose features rise toward the event frame."""
    rng = np.random.default_rng(seed)
    times = tuple(float(i) for i in range(n_frames))
    features: dict[str, np.ndarray] = {}
    ramp = np.linspace(0.0, 1.0, n_frames)
    for k, name in enumerate(ALL_FEATURES):
        noise = rng.normal(0.0, 0.05, size=n_frames)
        features[name] = np.asarray(scale * (0.5 + 0.5 * k + ramp + noise), dtype=np.float64)
    return HardRun(seed, "synthetic", times, event_frame, features)


def test_normalize_run_zscore_is_zero_mean_unit_std() -> None:
    run = _make_run(1)
    out = normalize_run(run, "per_run_zscore")
    for values in out.features.values():
        assert abs(float(np.mean(values))) < 1e-9
        assert abs(float(np.std(values)) - 1.0) < 1e-9


def test_normalize_run_minmax_in_unit_interval() -> None:
    out = normalize_run(_make_run(2), "per_run_minmax")
    for values in out.features.values():
        assert float(np.min(values)) >= -1e-12
        assert float(np.max(values)) <= 1.0 + 1e-12


def test_normalize_run_rank_is_permutation_of_plotting_positions() -> None:
    out = normalize_run(_make_run(3), "per_run_rank")
    for values in out.features.values():
        n = values.size
        expected = np.sort((np.arange(n) + 0.5) / n)
        assert np.allclose(np.sort(values), expected)


def test_normalize_run_raw_is_identity() -> None:
    run = _make_run(4)
    out = normalize_run(run, "raw")
    for name in run.features:
        assert np.array_equal(out.features[name], run.features[name])


def test_normalize_run_preserves_run_metadata() -> None:
    run = _make_run(5, event_frame=7)
    out = normalize_run(run, "per_run_zscore")
    assert out.seed == run.seed
    assert out.family == run.family
    assert out.times == run.times
    assert out.event_frame == run.event_frame


def test_normalize_run_rejects_unknown_method() -> None:
    with pytest.raises(ValueError, match="unknown normalization"):
        normalize_run(_make_run(6), "not_a_method")


def test_normalize_run_constant_channel_is_finite() -> None:
    run = _make_run(7)
    constant = {name: np.full(run.times.__len__(), 3.0) for name in run.features}
    flat = HardRun(run.seed, run.family, run.times, run.event_frame, constant)
    for method in METHODS:
        out = normalize_run(flat, method)
        for values in out.features.values():
            assert np.all(np.isfinite(values))


def test_normalize_runs_is_deterministic() -> None:
    runs = [_make_run(s) for s in (10, 11)]
    a = normalize_runs(runs, "per_run_zscore")
    b = normalize_runs(runs, "per_run_zscore")
    for ra, rb in zip(a, b, strict=True):
        for name in ra.features:
            assert np.array_equal(ra.features[name], rb.features[name])


def test_transfer_auc_is_finite_or_nan() -> None:
    train = [_make_run(s, scale=1.0) for s in (10, 11, 12)]
    test = [_make_run(s, scale=2.0) for s in (90, 91, 92)]
    auc = transfer_auc(train, test, ("intensity", "localization"), "per_run_zscore")
    assert np.isnan(auc) or 0.0 <= auc <= 1.0


def test_select_competent_method_excludes_raw_and_is_deterministic() -> None:
    spec_train = [_make_run(s, scale=1.0) for s in (10, 11)]
    fd_train = [_make_run(s, scale=3.0) for s in (10, 11)]
    spec_devtest = [_make_run(s, scale=1.0) for s in (13, 14)]
    fd_devtest = [_make_run(s, scale=3.0) for s in (13, 14)]
    first, table = select_competent_method(spec_train, fd_train, spec_devtest, fd_devtest)
    again, _ = select_competent_method(spec_train, fd_train, spec_devtest, fd_devtest)
    assert first == again
    assert first in _COMPETENT_METHODS
    assert "raw" not in table  # raw is the reference, never a competent candidate


def test_evaluate_direction_reports_raw_and_competent_separately() -> None:
    train = [_make_run(s, scale=1.0) for s in (10, 11, 12)]
    test = [_make_run(s, scale=2.5) for s in (90, 91, 92)]
    result = evaluate_direction(train, test, "spectral_to_fd", "per_run_zscore", bootstrap=50)
    assert isinstance(result, DirectionResult)
    assert result.direction == "spectral_to_fd"
    assert result.normalization == "per_run_zscore"
    # added-value verdict is one of the evaluation's discrete verdicts (never forced positive)
    assert result.added_value_verdict in {
        "supported within tested scope", "not supported", "inconclusive",
    }


def test_quick_campaign_runs_and_selects_a_competent_method() -> None:
    result = run_competent_campaign(quick=True)
    assert result.competent_method_selected in _COMPETENT_METHODS
    assert {d.direction for d in result.holdout_directions} == {"spectral_to_fd", "fd_to_spectral"}
    # The selection table only scores the genuinely-normalized candidates.
    assert set(result.dev_established_auc_by_method) == set(_COMPETENT_METHODS)
