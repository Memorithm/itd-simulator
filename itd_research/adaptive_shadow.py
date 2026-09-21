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
