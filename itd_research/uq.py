"""ITD-34.x uncertainty and selective-prediction primitives.

These utilities are generic research measurements.  They do not assign
probabilistic meaning to ITD descriptors and do not replace task-specific UQ
baselines.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


def _boolean_flags(values: Sequence[bool], name: str) -> tuple[bool, ...]:
    """Accept actual Python/NumPy booleans, never truthy strings or numbers."""
    if any(not isinstance(value, (bool, np.bool_)) for value in values):
        raise ValueError(f"{name} must contain only boolean flags.")
    return tuple(bool(value) for value in values)


def _nonnegative_mean(values: Sequence[float]) -> float:
    """Avoid overflow of a finite non-negative mean's intermediate sum."""
    scale = max(values)
    if scale == 0.0:
        return 0.0
    return scale * (math.fsum(value / scale for value in values) / len(values))


@dataclass(frozen=True)
class SelectiveRiskPoint:
    """Conditional ratios use None when their denominator is absent."""

    threshold: float
    coverage: float
    selective_risk: float | None
    false_confidence: float | None

    def __post_init__(self) -> None:
        for name, value in (("threshold", self.threshold), ("coverage", self.coverage)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("coverage must be in [0, 1].")
        if self.coverage == 0.0:
            if self.selective_risk is not None:
                raise ValueError("selective_risk must be undefined at zero coverage.")
        elif self.selective_risk is None:
            raise ValueError("selective_risk is required at positive coverage.")
        if self.selective_risk is not None and (
            not math.isfinite(self.selective_risk) or self.selective_risk < 0.0
        ):
            raise ValueError("selective_risk must be finite and non-negative when defined.")
        if self.false_confidence is not None and (
            not math.isfinite(self.false_confidence)
            or not 0.0 <= self.false_confidence <= 1.0
        ):
            raise ValueError("false_confidence must be finite and in [0, 1] when defined.")


def selective_risk_point(
    scores: Sequence[float],
    errors: Sequence[float],
    is_ood: Sequence[bool],
    *,
    threshold: float,
) -> SelectiveRiskPoint:
    """Evaluate one deterministic abstention threshold without fitting it.

    Samples with score <= threshold are covered. Errors must be finite and
    non-negative. Risk is the mean error among covered samples, or None when
    coverage is zero. False confidence is the fraction of OOD samples covered,
    or None when no OOD sample exists. Neither absence is a measured zero.
    """

    if not math.isfinite(threshold):
        raise ValueError("threshold must be finite.")
    if not (len(scores) == len(errors) == len(is_ood)):
        raise ValueError("scores, errors and is_ood must have equal length.")
    if len(scores) == 0:
        raise ValueError("at least one sample is required.")

    normalized_scores = tuple(float(value) for value in scores)
    normalized_errors = tuple(float(value) for value in errors)
    ood_flags = _boolean_flags(is_ood, "is_ood")
    if any(not math.isfinite(value) for value in normalized_scores):
        raise ValueError("scores must be finite.")
    if any(not math.isfinite(value) or value < 0.0 for value in normalized_errors):
        raise ValueError("errors must be finite and non-negative.")

    covered = tuple(score <= threshold for score in normalized_scores)
    covered_errors = tuple(
        error for error, keep in zip(normalized_errors, covered, strict=True) if keep
    )
    ood_count = sum(ood_flags)
    covered_ood = sum(keep and ood for keep, ood in zip(covered, ood_flags, strict=True))
    return SelectiveRiskPoint(
        threshold=threshold,
        coverage=len(covered_errors) / len(covered),
        selective_risk=_nonnegative_mean(covered_errors) if covered_errors else None,
        false_confidence=covered_ood / ood_count if ood_count else None,
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
    if len(confidence) == 0:
        raise ValueError("at least one calibration sample is required.")
    if type(bin_count) is not int or bin_count < 1:
        raise ValueError("bin_count must be a positive integer.")

    values = tuple(float(value) for value in confidence)
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("confidence values must be finite and in [0, 1].")
    outcomes = _boolean_flags(correct, "correct")

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
        mean_confidence = _nonnegative_mean(bucket_confidence[index])
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

    brier = math.fsum(
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
    """Integrate only the supplied interval, rejecting undefined risk points.

    Zero-coverage points do not define an interpolation endpoint. Callers must
    explicitly choose a measured interval; this function never invents an origin.
    """

    resolved = tuple(points)
    if not resolved:
        raise ValueError("at least one risk-coverage point is required.")
    if any(point.selective_risk is None for point in resolved):
        raise ValueError("cannot integrate undefined selective risk.")
    coverages = tuple(point.coverage for point in resolved)
    if any(right < left for left, right in zip(coverages, coverages[1:], strict=False)):
        raise ValueError("risk-coverage points must have non-decreasing coverage.")

    areas = []
    for left, right in zip(resolved, resolved[1:], strict=False):
        if left.selective_risk is None or right.selective_risk is None:
            raise ValueError("cannot integrate undefined selective risk.")
        width = right.coverage - left.coverage
        areas.append(width * (0.5 * left.selective_risk + 0.5 * right.selective_risk))
    return math.fsum(areas)
