"""ITD-36.x shadow-policy contracts.

Shadow decisions are observations only.  They do not actuate ElasticXxx or any
other runtime and therefore cannot be mistaken for an approved control policy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class AdaptiveAction(StrEnum):
    KEEP = "keep"
    CHANGE_PRECISION = "change_precision"
    CHANGE_REPRESENTATION = "change_representation"
    CHANGE_MODEL = "change_model"
    CHANGE_COMPUTE_BUDGET = "change_compute_budget"
    VERIFY = "verify"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class ShadowDecision:
    """One non-actuating adaptive decision candidate."""

    decision_id: str
    action: AdaptiveAction
    predicted_quality_delta: float
    predicted_cost_delta: float
    invariant_risk: float
    evidence_fingerprint: str

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("decision_id must not be empty.")
        for name, value in (
            ("predicted_quality_delta", self.predicted_quality_delta),
            ("predicted_cost_delta", self.predicted_cost_delta),
            ("invariant_risk", self.invariant_risk),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if self.invariant_risk < 0.0:
            raise ValueError("invariant_risk must be non-negative.")
        digest = self.evidence_fingerprint.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("evidence_fingerprint must be a SHA-256 hex digest.")
        object.__setattr__(self, "evidence_fingerprint", digest)

    @property
    def actuates(self) -> bool:
        """Shadow-mode decisions never actuate a runtime."""

        return False


class QualityDirection(StrEnum):
    """Declared optimization direction for one task quality quantity."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


@dataclass(frozen=True)
class ShadowRealization:
    """Observed outcome for one decision that was never physically actuated."""

    decision: ShadowDecision
    baseline_quality: float
    realized_quality: float
    baseline_cost: float
    realized_cost: float
    invariant_violated: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("baseline_quality", self.baseline_quality),
            ("realized_quality", self.realized_quality),
            ("baseline_cost", self.baseline_cost),
            ("realized_cost", self.realized_cost),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if self.baseline_cost < 0.0 or self.realized_cost < 0.0:
            raise ValueError("shadow costs must be non-negative.")

    @property
    def observed_quality_delta(self) -> float:
        return self.realized_quality - self.baseline_quality

    @property
    def observed_cost_delta(self) -> float:
        return self.realized_cost - self.baseline_cost

    @property
    def quality_prediction_error(self) -> float:
        return abs(self.decision.predicted_quality_delta - self.observed_quality_delta)

    @property
    def cost_prediction_error(self) -> float:
        return abs(self.decision.predicted_cost_delta - self.observed_cost_delta)

    @property
    def actuates(self) -> bool:
        return False


@dataclass(frozen=True)
class ShadowUtilityContract:
    """Explicit scalarization used only when a regret quantity is required."""

    quality_direction: QualityDirection
    quality_weight: float
    cost_weight: float
    invariant_penalty: float

    def __post_init__(self) -> None:
        for name, value in (
            ("quality_weight", self.quality_weight),
            ("cost_weight", self.cost_weight),
            ("invariant_penalty", self.invariant_penalty),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if self.quality_weight == self.cost_weight == self.invariant_penalty == 0.0:
            raise ValueError("shadow utility must contain at least one positive weight.")

    def score(self, *, quality: float, cost: float, invariant_violated: bool) -> float:
        if not math.isfinite(quality):
            raise ValueError("quality must be finite.")
        if not math.isfinite(cost) or cost < 0.0:
            raise ValueError("cost must be finite and non-negative.")
        signed_quality = (
            quality
            if self.quality_direction is QualityDirection.HIGHER_IS_BETTER
            else -quality
        )
        penalty = self.invariant_penalty if invariant_violated else 0.0
        return (
            self.quality_weight * signed_quality
            - self.cost_weight * cost
            - penalty
        )


@dataclass(frozen=True)
class ShadowRegretEvaluation:
    """Regret against an explicitly supplied oracle/comparator outcome."""

    realization: ShadowRealization
    oracle_quality: float
    oracle_cost: float
    oracle_invariant_violated: bool
    utility: ShadowUtilityContract

    def __post_init__(self) -> None:
        if not math.isfinite(self.oracle_quality):
            raise ValueError("oracle_quality must be finite.")
        if not math.isfinite(self.oracle_cost) or self.oracle_cost < 0.0:
            raise ValueError("oracle_cost must be finite and non-negative.")

    @property
    def chosen_utility(self) -> float:
        return self.utility.score(
            quality=self.realization.realized_quality,
            cost=self.realization.realized_cost,
            invariant_violated=self.realization.invariant_violated,
        )

    @property
    def oracle_utility(self) -> float:
        return self.utility.score(
            quality=self.oracle_quality,
            cost=self.oracle_cost,
            invariant_violated=self.oracle_invariant_violated,
        )

    @property
    def regret(self) -> float:
        return max(0.0, self.oracle_utility - self.chosen_utility)

    @property
    def actuates(self) -> bool:
        return False
