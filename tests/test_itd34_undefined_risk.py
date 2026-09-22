from __future__ import annotations

import json
import math
from dataclasses import asdict

import numpy as np
import pytest

from itd_research.uq import (
    SelectiveRiskPoint,
    calibration_summary,
    risk_coverage_curve,
    selective_risk_point,
    trapezoidal_risk_coverage_area,
)


def test_absent_denominators_are_not_zero_risks() -> None:
    point = selective_risk_point((1.0,), (0.8,), (False,), threshold=0.0)
    assert point.coverage == 0.0
    assert point.selective_risk is None
    assert point.false_confidence is None
    assert json.loads(json.dumps(asdict(point), allow_nan=False))["selective_risk"] is None


def test_measured_zero_is_still_distinct_from_absence() -> None:
    point = selective_risk_point((0.0, 1.0), (0.0, 1.0), (False, True), threshold=0.5)
    assert point.coverage == 0.5
    assert point.selective_risk == 0.0
    assert point.false_confidence == 0.0


@pytest.mark.parametrize("flag", ["False", "True", "", None, 1, 0, float("nan")])
def test_flags_are_not_coerced_by_truthiness(flag: object) -> None:
    with pytest.raises((ValueError, TypeError), match="bool"):
        calibration_summary((1.0,), (flag,))
    with pytest.raises((ValueError, TypeError), match="bool"):
        selective_risk_point((0.0,), (0.1,), (flag,), threshold=1.0)


def test_numpy_arrays_and_numpy_boolean_flags_are_supported() -> None:
    point = selective_risk_point(
        np.array([0.0, 1.0]), np.array([0.1, 0.9]), np.array([False, True]), threshold=0.5,
    )
    assert point.selective_risk == pytest.approx(0.1)
    summary = calibration_summary(np.array([0.0, 1.0]), np.array([False, True]))
    assert summary.brier_score == 0.0


def test_finite_mean_does_not_overflow_intermediate_sum() -> None:
    point = selective_risk_point((0.0, 0.0), (1e308, 1e308), (False, True), threshold=0.5)
    assert point.selective_risk == pytest.approx(1e308)
    assert math.isfinite(point.selective_risk)


def test_area_rejects_undefined_risk_without_inventing_origin() -> None:
    points = risk_coverage_curve((1.0, 2.0), (0.8, 0.4), (False, True), thresholds=(0.0, 1.0, 2.0))
    with pytest.raises(ValueError, match="undefined"):
        trapezoidal_risk_coverage_area(points)
    assert trapezoidal_risk_coverage_area(points[1:]) == pytest.approx(0.35)


def test_finite_area_does_not_overflow_adding_two_risks() -> None:
    points = (
        SelectiveRiskPoint(0.0, 0.5, 1e308, None),
        SelectiveRiskPoint(1.0, 1.0, 1e308, None),
    )
    assert trapezoidal_risk_coverage_area(points) == pytest.approx(5e307)


@pytest.mark.parametrize("coverage,risk", [(0.0, 0.0), (0.5, None)])
def test_direct_points_require_consistent_coverage_and_risk(coverage: float, risk: float | None) -> None:
    with pytest.raises(ValueError, match="risk"):
        SelectiveRiskPoint(0.0, coverage, risk, None)


@pytest.mark.parametrize("count", [True, 1.5, 0, -1])
def test_bin_count_is_a_positive_integer(count: object) -> None:
    with pytest.raises((ValueError, TypeError), match="bin_count"):
        calibration_summary((0.5,), (True,), bin_count=count)
