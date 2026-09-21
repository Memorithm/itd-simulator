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
        for name, integer_value in (
            ("stored_payload_bits", self.stored_payload_bits),
            ("metadata_bits", self.metadata_bits),
            ("peak_working_bytes", self.peak_working_bytes),
        ):
            if integer_value < 0:
                raise ValueError(f"{name} must be non-negative.")
        for name, float_value in (
            ("task_error", self.task_error),
            ("reconstruction_error", self.reconstruction_error),
        ):
            if not math.isfinite(float_value) or float_value < 0.0:
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


@dataclass(frozen=True)
class RepresentationResourceAccounting:
    """Exact storage and declared transition-resource accounting."""

    stored_payload_bits: int
    metadata_bits: int
    peak_working_bytes: int
    encode_cost: float
    decode_cost: float
    cost_unit: str

    def __post_init__(self) -> None:
        for name, value in (
            ("stored_payload_bits", self.stored_payload_bits),
            ("metadata_bits", self.metadata_bits),
            ("peak_working_bytes", self.peak_working_bytes),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative.")
        for name, value in (
            ("encode_cost", self.encode_cost),
            ("decode_cost", self.decode_cost),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if not self.cost_unit.strip():
            raise ValueError("cost_unit must not be empty.")

    @property
    def total_stored_bits(self) -> int:
        return self.stored_payload_bits + self.metadata_bits

    @property
    def total_transition_cost(self) -> float:
        return self.encode_cost + self.decode_cost


@dataclass(frozen=True)
class RepresentationObservationV2:
    """ITD-31.1 observation with explicit exact resource accounting."""

    representation_id: str
    kind: RepresentationKind
    accounting: RepresentationResourceAccounting
    task_error: float
    reconstruction_error: float

    def __post_init__(self) -> None:
        if not self.representation_id.strip():
            raise ValueError("representation_id must not be empty.")
        for name, value in (
            ("task_error", self.task_error),
            ("reconstruction_error", self.reconstruction_error),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")


@dataclass(frozen=True)
class RepresentationTransitionV2:
    """Directed transition with explicit cost unit and working-memory accounting."""

    source_id: str
    target_id: str
    fidelity_loss: float
    transition_cost: float
    cost_unit: str
    peak_working_bytes: int
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
        if not self.cost_unit.strip():
            raise ValueError("cost_unit must not be empty.")
        if self.peak_working_bytes < 0:
            raise ValueError("peak_working_bytes must be non-negative.")

    def scalarized_cost(
        self,
        *,
        alpha: float,
        beta: float,
        gamma: float,
        delta: float,
    ) -> float:
        """Scalarize only after the experiment freezes all four weights."""

        for name, weight in (
            ("alpha", alpha),
            ("beta", beta),
            ("gamma", gamma),
            ("delta", delta),
        ):
            if not math.isfinite(weight) or weight < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        return (
            alpha * self.fidelity_loss
            + beta * self.transition_cost
            + gamma * abs(float(self.storage_delta_bits))
            + delta * float(self.peak_working_bytes)
        )
