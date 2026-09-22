"""ITD-32.1 NeuralOperator research adapter contracts.

The adapter binds deterministic Burgers/Darcy samples and model outputs to ITD
comparison arms without importing NeuralOperator runtime semantics into ITD.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.itd3x_tracks import AIComparisonArm


class OperatorTaskKind(StrEnum):
    """Current NeuralOperator task families explicitly supported by the bridge."""

    BURGERS_1D = "burgers_1d"
    DARCY_2D = "darcy_2d"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class OperatorSampleRef:
    """Immutable identity for one operator-learning sample."""

    sample_id: str
    task: OperatorTaskKind
    role: SplitRole
    source: SourceIdentity
    input_sha256: str
    target_sha256: str
    resolution: tuple[int, ...]
    distribution: str

    def __post_init__(self) -> None:
        if not self.sample_id.strip():
            raise ValueError("sample_id must not be empty.")
        if not self.resolution or any(size <= 0 for size in self.resolution):
            raise ValueError("resolution must contain positive dimensions.")
        if not self.distribution.strip():
            raise ValueError("distribution must not be empty.")
        object.__setattr__(
            self,
            "input_sha256",
            _validate_sha256("input_sha256", self.input_sha256),
        )
        object.__setattr__(
            self,
            "target_sha256",
            _validate_sha256("target_sha256", self.target_sha256),
        )

    def assert_selection_allowed(self) -> None:
        if self.role is SplitRole.FINAL:
            raise ValueError("final NeuralOperator samples cannot be used for selection.")


@dataclass(frozen=True)
class OperatorModelRef:
    """Exact model/checkpoint identity used by one comparison arm."""

    model_id: str
    family: str
    source: SourceIdentity
    checkpoint_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id must not be empty.")
        if not self.family.strip():
            raise ValueError("model family must not be empty.")
        if self.checkpoint_sha256 is not None:
            object.__setattr__(
                self,
                "checkpoint_sha256",
                _validate_sha256("checkpoint_sha256", self.checkpoint_sha256),
            )


@dataclass(frozen=True)
class OperatorEvaluationCase:
    """One frozen sample/model/representation comparison case."""

    case_id: str
    sample: OperatorSampleRef
    arm: AIComparisonArm
    model: OperatorModelRef
    representation_id: str

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        if not self.representation_id.strip():
            raise ValueError("representation_id must not be empty.")

    def assert_selection_allowed(self) -> None:
        self.sample.assert_selection_allowed()


@dataclass(frozen=True)
class OperatorPredictionRecord:
    """Observed prediction metrics with exact prediction artifact identity."""

    case_id: str
    prediction_sha256: str
    relative_l2_error: float
    physics_residual: float | None
    inference_cost: float
    inference_cost_unit: str

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        object.__setattr__(
            self,
            "prediction_sha256",
            _validate_sha256("prediction_sha256", self.prediction_sha256),
        )
        if not math.isfinite(self.relative_l2_error) or self.relative_l2_error < 0.0:
            raise ValueError("relative_l2_error must be finite and non-negative.")
        if self.physics_residual is not None and (
            not math.isfinite(self.physics_residual) or self.physics_residual < 0.0
        ):
            raise ValueError("physics_residual must be finite and non-negative.")
        if not math.isfinite(self.inference_cost) or self.inference_cost < 0.0:
            raise ValueError("inference_cost must be finite and non-negative.")
        if not self.inference_cost_unit.strip():
            raise ValueError("inference_cost_unit must not be empty.")

    def assert_matches_case(self, case: OperatorEvaluationCase) -> None:
        if self.case_id != case.case_id:
            raise ValueError("prediction record does not match evaluation case.")
