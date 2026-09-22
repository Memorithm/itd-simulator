"""ITD-32.2 auxiliary-supervision experiment contracts.

The programme distinguishes ITD-derived auxiliary targets from established
domain auxiliaries and matched random controls so generic multi-task
regularization is not misreported as ITD-specific value.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.neural_operator_adapter import OperatorModelRef


class AuxiliaryTargetClass(StrEnum):
    ITD_DERIVED = "itd_derived"
    ESTABLISHED_DOMAIN = "established_domain"
    MATCHED_RANDOM_CONTROL = "matched_random_control"


class MetricDirection(StrEnum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class AuxiliaryTargetRef:
    """Exact identity of one auxiliary target schema."""

    target_id: str
    target_class: AuxiliaryTargetClass
    source: SourceIdentity
    schema_sha256: str
    unit: str

    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError("target_id must not be empty.")
        object.__setattr__(
            self,
            "schema_sha256",
            _validate_sha256("schema_sha256", self.schema_sha256),
        )
        if not self.unit.strip():
            raise ValueError("auxiliary target unit must not be empty.")


@dataclass(frozen=True)
class AuxiliaryTrainingArm:
    """Matched-budget training arm for Development/Validation research."""

    arm_id: str
    role: SplitRole
    model: OperatorModelRef
    auxiliary_target: AuxiliaryTargetRef | None
    auxiliary_loss_weight: float
    parameter_budget: int
    training_work: float
    training_work_unit: str
    seed: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", SplitRole(self.role))
        if not self.arm_id.strip():
            raise ValueError("arm_id must not be empty.")
        if self.role is SplitRole.FINAL:
            raise ValueError("auxiliary-supervision fitting cannot use final data.")
        if self.auxiliary_target is None and self.auxiliary_loss_weight != 0.0:
            raise ValueError("no-auxiliary arms must use zero auxiliary_loss_weight.")
        if self.auxiliary_target is not None and (
            not math.isfinite(self.auxiliary_loss_weight)
            or self.auxiliary_loss_weight <= 0.0
        ):
            raise ValueError(
                "auxiliary arms require a finite positive auxiliary_loss_weight."
            )
        if self.parameter_budget <= 0:
            raise ValueError("parameter_budget must be positive.")
        if not math.isfinite(self.training_work) or self.training_work <= 0.0:
            raise ValueError("training_work must be finite and positive.")
        if not self.training_work_unit.strip():
            raise ValueError("training_work_unit must not be empty.")
        if self.seed < 0:
            raise ValueError("seed must be non-negative.")


def assert_matched_training_budget(
    baseline: AuxiliaryTrainingArm,
    candidate: AuxiliaryTrainingArm,
) -> None:
    """Require matched model/resource budgets before attributing auxiliary value."""

    if baseline.model.family != candidate.model.family:
        raise ValueError("matched auxiliary arms must use one model family.")
    if baseline.parameter_budget != candidate.parameter_budget:
        raise ValueError("matched auxiliary arms must use equal parameter budgets.")
    if baseline.training_work_unit != candidate.training_work_unit:
        raise ValueError("matched auxiliary arms must use one training-work unit.")
    if baseline.training_work != candidate.training_work:
        raise ValueError("matched auxiliary arms must use equal training work.")
    if baseline.seed != candidate.seed:
        raise ValueError("matched auxiliary arms must use the same seed.")


@dataclass(frozen=True)
class LearningCurvePoint:
    """One frozen sample-count measurement for sample-efficiency analysis."""

    sample_count: int
    primary_metric: float

    def __post_init__(self) -> None:
        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive.")
        if not math.isfinite(self.primary_metric):
            raise ValueError("primary_metric must be finite.")


def sample_count_to_threshold(
    points: tuple[LearningCurvePoint, ...],
    *,
    threshold: float,
    direction: MetricDirection,
) -> int | None:
    """Return the first sample count meeting a preregistered primary threshold."""

    if not points:
        raise ValueError("learning curve must contain at least one point.")
    if not math.isfinite(threshold):
        raise ValueError("threshold must be finite.")
    counts = tuple(point.sample_count for point in points)
    if any(right <= left for left, right in zip(counts, counts[1:], strict=False)):
        raise ValueError("learning-curve sample counts must be strictly increasing.")

    for point in points:
        if direction is MetricDirection.LOWER_IS_BETTER:
            if point.primary_metric <= threshold:
                return point.sample_count
        elif point.primary_metric >= threshold:
            return point.sample_count
    return None


def sample_efficiency_ratio(
    baseline_points: tuple[LearningCurvePoint, ...],
    candidate_points: tuple[LearningCurvePoint, ...],
    *,
    threshold: float,
    direction: MetricDirection,
) -> float | None:
    """Return baseline/candidate samples-to-threshold when both reach it."""

    baseline_count = sample_count_to_threshold(
        baseline_points,
        threshold=threshold,
        direction=direction,
    )
    candidate_count = sample_count_to_threshold(
        candidate_points,
        threshold=threshold,
        direction=direction,
    )
    if baseline_count is None or candidate_count is None:
        return None
    return baseline_count / candidate_count
