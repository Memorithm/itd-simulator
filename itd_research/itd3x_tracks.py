"""Bootstrap contracts for the remaining ITD-3X research tracks.

The contracts in this module deliberately encode scientific boundaries before
large experiment implementations exist.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity, SplitRole


class AIComparisonArm(StrEnum):
    ESTABLISHED_CONTROL = "established_control"
    RAW_MODEL = "raw_model"
    ITD_ONLY = "itd_only"
    ESTABLISHED_PLUS_ITD = "established_plus_itd"
    RAW_PLUS_ITD = "raw_plus_itd"
    LEARNED_CONTROL = "learned_control"
    LEARNED_PLUS_ITD_AUX = "learned_plus_itd_aux"


@dataclass(frozen=True)
class AIComparisonLadder:
    """ITD-32.x set of declared comparison arms."""

    arms: tuple[AIComparisonArm, ...]

    def __post_init__(self) -> None:
        if len(self.arms) < 2:
            raise ValueError("comparison ladder requires at least two arms.")
        if len(set(self.arms)) != len(self.arms):
            raise ValueError("comparison ladder arms must be unique.")
        if AIComparisonArm.ESTABLISHED_CONTROL not in self.arms:
            raise ValueError("comparison ladder requires an established control.")


@dataclass(frozen=True)
class MechanisticGate:
    """ITD-35.x gate before expensive model-scale evaluation."""

    deterministic_reference: bool
    invariant_tests_pass: bool
    preregistered_tradeoff_observed: bool
    holdout_metric_posthoc: bool
    failure_modes_documented: bool

    @property
    def allows_model_scale(self) -> bool:
        return (
            self.deterministic_reference
            and self.invariant_tests_pass
            and self.preregistered_tradeoff_observed
            and not self.holdout_metric_posthoc
            and self.failure_modes_documented
        )


@dataclass(frozen=True)
class PerturbationResponse:
    """ITD-37.x measured response to one controlled intervention."""

    perturbation_id: str
    amplitude: float
    structural_delta: float
    task_error_delta: float
    uncertainty_delta: float
    source: SourceIdentity

    def __post_init__(self) -> None:
        if not self.perturbation_id.strip():
            raise ValueError("perturbation_id must not be empty.")
        for name, value in (
            ("amplitude", self.amplitude),
            ("structural_delta", self.structural_delta),
            ("task_error_delta", self.task_error_delta),
            ("uncertainty_delta", self.uncertainty_delta),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")


@dataclass(frozen=True)
class SearchAuthorization:
    """ITD-38.x leakage guard for bounded search."""

    role: SplitRole
    search_space_frozen: bool
    compute_budget_frozen: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", SplitRole(self.role))
        for name, value in (
            ("search_space_frozen", self.search_space_frozen),
            ("compute_budget_frozen", self.compute_budget_frozen),
        ):
            if type(value) is not bool:
                raise ValueError(f"{name} must be a bool.")

    def assert_allowed(self) -> None:
        if self.role is SplitRole.FINAL:
            raise ValueError("search on the final split is forbidden.")
        if not self.search_space_frozen:
            raise ValueError("search space must be frozen before bounded search.")
        if not self.compute_budget_frozen:
            raise ValueError("compute budget must be frozen before bounded search.")


@dataclass(frozen=True)
class EvidenceBinding:
    """ITD-39.x identity binding for an external evidence bundle."""

    producer: str
    source: SourceIdentity
    protocol_fingerprint: str
    campaign_fingerprint: str

    def __post_init__(self) -> None:
        if not self.producer.strip():
            raise ValueError("evidence producer must not be empty.")
        for field_name, digest in (
            ("protocol_fingerprint", self.protocol_fingerprint),
            ("campaign_fingerprint", self.campaign_fingerprint),
        ):
            lowered = digest.lower()
            if len(lowered) != 64 or any(char not in "0123456789abcdef" for char in lowered):
                raise ValueError(f"{field_name} must be a SHA-256 hex digest.")
            object.__setattr__(self, field_name, lowered)
