"""ITD-33.x trajectory descriptor contracts.

Research-only descriptors over ordered inference/state trajectories.  They are
not ITD V29.18 components and must not be interpreted as stopping policies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class TrajectoryDescriptorKind(StrEnum):
    STATE_DEFORMATION = "state_deformation"
    CONCENTRATION = "concentration"
    HETEROGENEITY = "heterogeneity"
    DIRECTIONAL_MIXING = "directional_mixing"
    MULTISCALE_CHANGE = "multiscale_change"
    RETRIEVAL_CONFLICT = "retrieval_conflict"
    VERIFIER_DISAGREEMENT = "verifier_disagreement"
    MEMORY_CHURN = "memory_churn"
    COLLAPSE_EXPANSION = "collapse_expansion"


@dataclass(frozen=True)
class TrajectoryPoint:
    """One ordered research observation from a causal inference trajectory."""

    step: int
    descriptor: TrajectoryDescriptorKind
    value: float
    unit: str
    source_semantics: str

    def __post_init__(self) -> None:
        if self.step < 0:
            raise ValueError("trajectory step must be non-negative.")
        if not math.isfinite(self.value):
            raise ValueError("trajectory descriptor value must be finite.")
        if not self.unit.strip():
            raise ValueError("trajectory descriptor unit must not be empty.")
        if not self.source_semantics.strip():
            raise ValueError("source_semantics must identify the descriptor meaning.")


@dataclass(frozen=True)
class TrajectorySeries:
    """A single-descriptor ordered trajectory with no policy semantics."""

    trajectory_id: str
    points: tuple[TrajectoryPoint, ...]

    def __post_init__(self) -> None:
        if not self.trajectory_id.strip():
            raise ValueError("trajectory_id must not be empty.")
        if not self.points:
            raise ValueError("trajectory series must contain points.")

        descriptors = {point.descriptor for point in self.points}
        units = {point.unit for point in self.points}
        semantics = {point.source_semantics for point in self.points}
        steps = tuple(point.step for point in self.points)

        if len(descriptors) != 1:
            raise ValueError("one trajectory series must contain one descriptor kind.")
        if len(units) != 1:
            raise ValueError("one trajectory series must use one declared unit.")
        if len(semantics) != 1:
            raise ValueError("one trajectory series must use one source semantics.")
        if any(right <= left for left, right in zip(steps, steps[1:], strict=False)):
            raise ValueError("trajectory steps must be strictly increasing.")

    @property
    def descriptor(self) -> TrajectoryDescriptorKind:
        return self.points[0].descriptor
