"""Tests for shift-aware detection and calibrated abstention (Mission 6, H43-H45).

Mechanical properties only -- monotone discount, band logic, utility accounting, and the
severity localizer -- on tiny synthetic inputs. The scientific verdicts come from the
full campaign and are reported honestly (H43 may be only partially supported).
"""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.ood_shift.detector import (
    fit_shift_reference,
    monotone_separation,
)
from itd_research.ood_shift.policy import (
    ABSTAIN,
    ACCEPT,
    REDUCE,
    binary_policy,
    confidence_discount,
    degradation_policy,
    evaluate_policy,
    no_abstention_policy,
    three_state_policy,
)

_NAMES = tuple(f"f{i}" for i in range(4))


def _reference(seed: int = 0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=(40, len(_NAMES)))
    return fit_shift_reference(x, _NAMES)


def test_confidence_discount_is_monotone_and_bounded() -> None:
    sev = np.linspace(0.0, 5.0, 50)
    c = confidence_discount(sev, s_low=1.0, s_high=3.0)
    assert np.all(c >= 0.0) and np.all(c <= 1.0)
    assert np.all(np.diff(c) <= 1e-12)  # non-increasing
    assert c[0] == 1.0 and c[-1] == 0.0


def test_confidence_discount_degenerate_band_is_hard_step() -> None:
    sev = np.array([0.5, 1.0, 1.5])
    c = confidence_discount(sev, s_low=1.0, s_high=1.0)
    assert list(c) == [1.0, 1.0, 0.0]


def test_three_state_bands_assign_expected_states() -> None:
    sev = np.array([0.1, 2.0, 9.0])
    decision = three_state_policy(sev, s_low=1.0, s_high=3.0)
    assert decision.states == [ACCEPT, REDUCE, ABSTAIN]
    assert decision.confidence[0] == 1.0
    assert 0.0 < decision.confidence[1] < 1.0
    assert decision.confidence[2] == 0.0


def test_binary_policy_predicts_below_threshold() -> None:
    decision = binary_policy(np.array([0.2, 0.8, 1.5]), threshold=1.0)
    assert decision.states == [ACCEPT, ACCEPT, ABSTAIN]


def test_no_abstention_predicts_everything() -> None:
    decision = no_abstention_policy(5)
    assert decision.states == [ACCEPT] * 5
    assert np.all(decision.confidence == 1.0)


def test_utility_penalizes_confident_errors_more_than_hedged() -> None:
    error = np.array([1.0, 1.0])  # both wrong
    confident = evaluate_policy("confident", no_abstention_policy(2), error)
    # A degradation policy that hedges both to low confidence should be less penalized.
    hedged = degradation_policy(np.array([10.0, 10.0]), s_low=0.0, s_high=1.0)
    hedged_out = evaluate_policy("hedged", hedged, error)
    assert hedged_out.utility > confident.utility


def test_utility_unnecessary_abstention_counts_predictable_abstained() -> None:
    # Two predictable frames (error 0), one abstained by a low threshold.
    error = np.array([0.0, 0.0])
    decision = binary_policy(np.array([0.1, 5.0]), threshold=1.0)  # abstain the 2nd
    outcome = evaluate_policy("x", decision, error)
    assert outcome.unnecessary_abstention_rate == pytest.approx(0.5)


def test_monotone_separation_perfect_and_chance() -> None:
    scores = np.array([0.0, 1.0, 2.0, 3.0])
    levels = np.array([0, 1, 2, 3])
    assert monotone_separation(scores, levels) == pytest.approx(1.0)
    # Reversed scores order every cross-level pair wrongly.
    assert monotone_separation(scores[::-1], levels) == pytest.approx(0.0)


def test_severity_rises_with_shift() -> None:
    ref = _reference()
    baseline = ref.severity(np.zeros((1, len(_NAMES))))
    shifted = ref.severity(np.full((1, len(_NAMES)), 6.0))
    assert shifted[0] > baseline[0]


def test_attribution_points_to_the_shifted_channel() -> None:
    ref = _reference()
    x = np.zeros((1, len(_NAMES)))
    x[0, 2] = 20.0  # channel 2 is by far the most anomalous
    assert ref.dominant_feature(x)[0] == "f2"


def test_fit_shift_reference_rejects_mismatched_names() -> None:
    with pytest.raises(ValueError, match="feature_names length"):
        fit_shift_reference(np.zeros((5, 3)), _NAMES)
