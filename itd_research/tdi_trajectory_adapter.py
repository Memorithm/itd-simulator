"""ITD-33.1 TDI adaptive-inference trajectory adapter.

TDI owns adaptive-inference semantics.  This adapter carries opaque, hashed
non-final TDI trajectory snapshots plus separately labelled ITD research
descriptors.  It deliberately does not invent unresolved TDI-9.1 observation
fields and has no TDI-9.2 final surface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.trajectory_schema import TrajectoryDescriptorKind


class TdiResearchStage(StrEnum):
    """TDI stages that are currently safe for ITD adapter development."""

    TDI_9_1_NON_FINAL = "tdi_9_1_non_final"
    TDI_9_3_NON_FINAL = "tdi_9_3_non_final"


class TdiPolicyArm(StrEnum):
    C0_FIXED_COMPUTE = "c0_fixed_compute"
    C1_STATIC_PREALLOCATION = "c1_static_preallocation"
    C2_ADAPTIVE_STOPPING = "c2_adaptive_stopping"
    C3_ADAPTIVE_VERIFY_RECOVER = "c3_adaptive_verify_recover"


class TdiAdaptiveAction(StrEnum):
    CONTINUE = "continue"
    STOP = "stop"
    VERIFY = "verify"
    BACKTRACK = "backtrack"
    RECOVER = "recover"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class TdiTrajectoryStepRef:
    """Opaque identity for one non-final TDI trajectory step."""

    trajectory_id: str
    step: int
    role: SplitRole
    stage: TdiResearchStage
    policy_arm: TdiPolicyArm
    source: SourceIdentity
    observation_schema_id: str
    payload_sha256: str
    action: TdiAdaptiveAction | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", SplitRole(self.role))
        if not self.trajectory_id.strip():
            raise ValueError("trajectory_id must not be empty.")
        if self.step < 0:
            raise ValueError("trajectory step must be non-negative.")
        if self.role is SplitRole.FINAL:
            raise ValueError("TDI-33.1 adapter cannot consume final TDI material.")
        if not self.observation_schema_id.strip():
            raise ValueError("observation_schema_id must not be empty.")
        object.__setattr__(
            self,
            "payload_sha256",
            _validate_sha256("payload_sha256", self.payload_sha256),
        )
        if self.policy_arm in {
            TdiPolicyArm.C0_FIXED_COMPUTE,
            TdiPolicyArm.C1_STATIC_PREALLOCATION,
        } and self.action in {
            TdiAdaptiveAction.VERIFY,
            TdiAdaptiveAction.BACKTRACK,
            TdiAdaptiveAction.RECOVER,
        }:
            raise ValueError("C0/C1 controls cannot report adaptive recovery actions.")
        if self.policy_arm is TdiPolicyArm.C2_ADAPTIVE_STOPPING and self.action in {
            TdiAdaptiveAction.VERIFY,
            TdiAdaptiveAction.BACKTRACK,
            TdiAdaptiveAction.RECOVER,
        }:
            raise ValueError("C2 supports only continue/stop adaptive actions.")


@dataclass(frozen=True)
class TdiStructuralDescriptorRecord:
    """One ITD research descriptor attached to an opaque TDI trajectory step."""

    step_ref: TdiTrajectoryStepRef
    descriptor: TrajectoryDescriptorKind
    value: float
    unit: str
    descriptor_semantics: str
    itd_source: SourceIdentity

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise ValueError("descriptor value must be finite.")
        if not self.unit.strip():
            raise ValueError("descriptor unit must not be empty.")
        if not self.descriptor_semantics.strip():
            raise ValueError("descriptor_semantics must not be empty.")


@dataclass(frozen=True)
class TdiTrajectoryPair:
    """Two causally ordered TDI steps eligible for transition descriptors."""

    previous: TdiTrajectoryStepRef
    current: TdiTrajectoryStepRef

    def __post_init__(self) -> None:
        if self.previous.trajectory_id != self.current.trajectory_id:
            raise ValueError("trajectory pair must use one trajectory identity.")
        if self.current.step <= self.previous.step:
            raise ValueError("trajectory pair must be strictly ordered.")
        if self.previous.source != self.current.source:
            raise ValueError("trajectory pair must use one exact TDI source identity.")
        if self.previous.observation_schema_id != self.current.observation_schema_id:
            raise ValueError("trajectory pair observation schemas must match.")
        if self.previous.stage is not self.current.stage:
            raise ValueError("trajectory pair TDI stages must match.")
