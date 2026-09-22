"""ITD-34.x uncertainty and selective-prediction primitives.

These utilities are generic research measurements.  They do not assign
probabilistic meaning to ITD descriptors and do not replace task-specific UQ
baselines.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SelectiveRiskPoint:
    threshold: float
    coverage: float
    selective_risk: float
    false_confidence: float

    def __post_init__(self) -> None:
        for name, value in (
            ("threshold", self.threshold),
            ("coverage", self.coverage),
            ("selective_risk", self.selective_risk),
            ("false_confidence", self.false_confidence),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("coverage must be in [0, 1].")
        if self.selective_risk < 0.0:
            raise ValueError("selective_risk must be non-negative.")
        if not 0.0 <= self.false_confidence <= 1.0:
            raise ValueError("false_confidence must be in [0, 1].")


def selective_risk_point(
    scores: Sequence[float],
    errors: Sequence[float],
    is_ood: Sequence[bool],
    *,
    threshold: float,
) -> SelectiveRiskPoint:
    """Evaluate one deterministic abstention threshold.

    Samples with score <= threshold are covered.  Error magnitudes must be
    finite and non-negative.  False confidence is the covered fraction among
    OOD samples, or zero when no OOD samples are present.
    """

    if not math.isfinite(threshold):
        raise ValueError("threshold must be finite.")
    if not (len(scores) == len(errors) == len(is_ood)):
        raise ValueError("scores, errors and is_ood must have equal length.")
    if not scores:
        raise ValueError("at least one sample is required.")

    normalized_scores = tuple(float(value) for value in scores)
    normalized_errors = tuple(float(value) for value in errors)

    if any(not math.isfinite(value) for value in normalized_scores):
        raise ValueError("scores must be finite.")
    if any(not math.isfinite(value) or value < 0.0 for value in normalized_errors):
        raise ValueError("errors must be finite and non-negative.")

    covered = tuple(score <= threshold for score in normalized_scores)
    covered_count = sum(covered)
    coverage = covered_count / len(covered)

    if covered_count:
        selective_risk = (
            sum(error for error, keep in zip(normalized_errors, covered, strict=True) if keep)
            / covered_count
        )
    else:
        selective_risk = 0.0

    ood_flags = tuple(bool(value) for value in is_ood)
    ood_count = sum(ood_flags)
    if ood_count:
        false_confidence = (
            sum(
                keep
                for keep, ood in zip(covered, ood_flags, strict=True)
                if ood
            )
            / ood_count
        )
    else:
        false_confidence = 0.0

    return SelectiveRiskPoint(
        threshold=threshold,
        coverage=coverage,
        selective_risk=selective_risk,
        false_confidence=false_confidence,
    )


@dataclass(frozen=True)
class CalibrationBin:
    """One populated equal-width confidence bin."""

    lower: float
    upper: float
    count: int
    mean_confidence: float
    accuracy: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.lower < self.upper <= 1.0:
            raise ValueError("calibration bin bounds must satisfy 0 <= lower < upper <= 1.")
        if self.count <= 0:
            raise ValueError("calibration bin count must be positive.")
        for name, value in (
            ("mean_confidence", self.mean_confidence),
            ("accuracy", self.accuracy),
        ):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1].")

    @property
    def absolute_gap(self) -> float:
        return abs(self.mean_confidence - self.accuracy)


@dataclass(frozen=True)
class CalibrationSummary:
    """Deterministic calibration summary for confidence/correctness pairs."""

    expected_calibration_error: float
    brier_score: float
    bins: tuple[CalibrationBin, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("expected_calibration_error", self.expected_calibration_error),
            ("brier_score", self.brier_score),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")


def calibration_summary(
    confidence: Sequence[float],
    correct: Sequence[bool],
    *,
    bin_count: int = 10,
) -> CalibrationSummary:
    """Compute equal-width ECE and Brier score without fitting thresholds."""

    if len(confidence) != len(correct):
        raise ValueError("confidence and correct must have equal length.")
    if not confidence:
        raise ValueError("at least one calibration sample is required.")
    if bin_count < 1:
        raise ValueError("bin_count must be positive.")

    values = tuple(float(value) for value in confidence)
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("confidence values must be finite and in [0, 1].")
    outcomes = tuple(bool(value) for value in correct)

    bucket_confidence: list[list[float]] = [[] for _ in range(bin_count)]
    bucket_correct: list[list[bool]] = [[] for _ in range(bin_count)]
    for value, outcome in zip(values, outcomes, strict=True):
        index = min(int(value * bin_count), bin_count - 1)
        bucket_confidence[index].append(value)
        bucket_correct[index].append(outcome)

    bins: list[CalibrationBin] = []
    weighted_gap = 0.0
    sample_count = len(values)
    for index in range(bin_count):
        if not bucket_confidence[index]:
            continue
        lower = index / bin_count
        upper = (index + 1) / bin_count
        mean_confidence = sum(bucket_confidence[index]) / len(bucket_confidence[index])
        accuracy = (
            sum(1 for value in bucket_correct[index] if value)
            / len(bucket_correct[index])
        )
        calibration_bin = CalibrationBin(
            lower=lower,
            upper=upper,
            count=len(bucket_confidence[index]),
            mean_confidence=mean_confidence,
            accuracy=accuracy,
        )
        bins.append(calibration_bin)
        weighted_gap += calibration_bin.count / sample_count * calibration_bin.absolute_gap

    brier = sum(
        (value - (1.0 if outcome else 0.0)) ** 2
        for value, outcome in zip(values, outcomes, strict=True)
    ) / sample_count
    return CalibrationSummary(
        expected_calibration_error=weighted_gap,
        brier_score=brier,
        bins=tuple(bins),
    )


def risk_coverage_curve(
    scores: Sequence[float],
    errors: Sequence[float],
    is_ood: Sequence[bool],
    *,
    thresholds: Sequence[float],
) -> tuple[SelectiveRiskPoint, ...]:
    """Evaluate a preregistered strictly increasing threshold sequence."""

    resolved = tuple(float(value) for value in thresholds)
    if not resolved:
        raise ValueError("at least one threshold is required.")
    if any(not math.isfinite(value) for value in resolved):
        raise ValueError("thresholds must be finite.")
    if any(right <= left for left, right in zip(resolved, resolved[1:], strict=False)):
        raise ValueError("thresholds must be strictly increasing.")

    return tuple(
        selective_risk_point(
            scores,
            errors,
            is_ood,
            threshold=threshold,
        )
        for threshold in resolved
    )


def trapezoidal_risk_coverage_area(
    points: Sequence[SelectiveRiskPoint],
) -> float:
    """Integrate risk over the covered coverage interval of supplied points."""

    resolved = tuple(points)
    if not resolved:
        raise ValueError("at least one risk-coverage point is required.")
    coverages = tuple(point.coverage for point in resolved)
    if any(right < left for left, right in zip(coverages, coverages[1:], strict=False)):
        raise ValueError("risk-coverage points must have non-decreasing coverage.")

    area = 0.0
    for left, right in zip(resolved, resolved[1:], strict=False):
        width = right.coverage - left.coverage
        area += width * 0.5 * (left.selective_risk + right.selective_risk)
    return area
