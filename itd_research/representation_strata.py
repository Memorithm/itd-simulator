"""ITD-31.x representation-strata measurement contracts.

These contracts operationalize representation observations without claiming that
representation space is a mathematical metric, manifold, or stratified space.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class RepresentationKind(StrEnum):
    DENSE = "dense"
    UNIFORM_QUANTIZED = "uniform_quantized"
    STRUCTURED_SPARSE = "structured_sparse"
    LOW_RANK = "low_rank"
    MIXED = "mixed"


@dataclass(frozen=True)
class RepresentationObservation:
    """Measured state of one representation under one frozen task/protocol."""

    representation_id: str
    kind: RepresentationKind
    stored_payload_bits: int
    metadata_bits: int
    peak_working_bytes: int
    task_error: float
    reconstruction_error: float

    def __post_init__(self) -> None:
        if not self.representation_id.strip():
            raise ValueError("representation_id must not be empty.")
        for name, value in (
            ("stored_payload_bits", self.stored_payload_bits),
            ("metadata_bits", self.metadata_bits),
            ("peak_working_bytes", self.peak_working_bytes),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative.")
        for name, value in (
            ("task_error", self.task_error),
            ("reconstruction_error", self.reconstruction_error),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")

    @property
    def total_stored_bits(self) -> int:
        return self.stored_payload_bits + self.metadata_bits


@dataclass(frozen=True)
class RepresentationTransition:
    """Observed directed transition between two representation states."""

    source_id: str
    target_id: str
    fidelity_loss: float
    transition_cost: float
    storage_delta_bits: int

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.target_id.strip():
            raise ValueError("transition endpoints must not be empty.")
        if self.source_id == self.target_id:
            raise ValueError("transition endpoints must differ.")
        for name, value in (
            ("fidelity_loss", self.fidelity_loss),
            ("transition_cost", self.transition_cost),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")

    def scalarized_cost(self, *, alpha: float, beta: float, gamma: float) -> float:
        """Return one explicitly chosen scalarization for a frozen experiment."""

        for name, weight in (("alpha", alpha), ("beta", beta), ("gamma", gamma)):
            if not math.isfinite(weight) or weight < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        return (
            alpha * self.fidelity_loss
            + beta * self.transition_cost
            + gamma * abs(float(self.storage_delta_bits))
        )
