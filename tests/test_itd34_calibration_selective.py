from __future__ import annotations

import pytest

from itd_research.uq import (
    calibration_summary,
    risk_coverage_curve,
    trapezoidal_risk_coverage_area,
)


def test_calibration_summary_computes_ece_and_brier() -> None:
    summary = calibration_summary(
        confidence=(0.9, 0.8, 0.2, 0.1),
        correct=(True, True, False, False),
        bin_count=2,
    )

    assert summary.expected_calibration_error == pytest.approx(0.15)
    assert summary.brier_score == pytest.approx(0.025)
    assert len(summary.bins) == 2


def test_calibration_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence values"):
        calibration_summary(
            confidence=(1.2,),
            correct=(True,),
        )


def test_risk_coverage_curve_is_monotone_in_coverage() -> None:
    points = risk_coverage_curve(
        scores=(0.1, 0.2, 1.0, 2.0),
        errors=(0.0, 0.2, 1.0, 2.0),
        is_ood=(False, False, True, True),
        thresholds=(0.1, 0.5, 1.5, 3.0),
    )

    coverage = tuple(point.coverage for point in points)
    assert coverage == tuple(sorted(coverage))
    assert points[0].coverage == pytest.approx(0.25)
    assert points[-1].coverage == pytest.approx(1.0)


def test_trapezoidal_risk_coverage_area_uses_supplied_interval() -> None:
    points = risk_coverage_curve(
        scores=(0.1, 0.2, 1.0, 2.0),
        errors=(0.0, 0.2, 1.0, 2.0),
        is_ood=(False, False, True, True),
        thresholds=(0.1, 0.5, 1.5, 3.0),
    )

    area = trapezoidal_risk_coverage_area(points)

    assert area >= 0.0


def test_risk_coverage_requires_strictly_increasing_thresholds() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        risk_coverage_curve(
            scores=(0.1,),
            errors=(0.0,),
            is_ood=(False,),
            thresholds=(0.5, 0.5),
        )
