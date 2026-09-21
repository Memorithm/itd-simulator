"""ITD-34.x uncertainty and selective-prediction primitives.

These utilities are generic research measurements.  They do not assign
probabilistic meaning to ITD descriptors and do not replace task-specific UQ
baselines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from collections.abc import Sequence


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
