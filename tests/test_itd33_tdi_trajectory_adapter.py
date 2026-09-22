from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.tdi_trajectory_adapter import (
    TdiAdaptiveAction,
    TdiPolicyArm,
    TdiResearchStage,
    TdiStructuralDescriptorRecord,
    TdiTrajectoryPair,
    TdiTrajectoryStepRef,
)
from itd_research.trajectory_schema import TrajectoryDescriptorKind


def _step(
    step: int,
    *,
    role: SplitRole = SplitRole.DEVELOPMENT,
    arm: TdiPolicyArm = TdiPolicyArm.C2_ADAPTIVE_STOPPING,
    action: TdiAdaptiveAction | None = TdiAdaptiveAction.CONTINUE,
) -> TdiTrajectoryStepRef:
    return TdiTrajectoryStepRef(
        trajectory_id="traj-1",
        step=step,
        role=role,
        stage=TdiResearchStage.TDI_9_1_NON_FINAL,
        policy_arm=arm,
        source=SourceIdentity("Memorithm/TDI", "tdi-test"),
        observation_schema_id="tdi-9.1-dev-observation-v1",
        payload_sha256=("a" if step == 0 else "b") * 64,
        action=action,
    )


def test_tdi_adapter_rejects_final_material() -> None:
    with pytest.raises(ValueError, match="final TDI material"):
        _step(0, role=SplitRole.FINAL)


def test_c2_rejects_recovery_action() -> None:
    with pytest.raises(ValueError, match="C2 supports only"):
        _step(0, action=TdiAdaptiveAction.RECOVER)


def test_c3_accepts_recovery_action() -> None:
    step = _step(
        0,
        arm=TdiPolicyArm.C3_ADAPTIVE_VERIFY_RECOVER,
        action=TdiAdaptiveAction.RECOVER,
    )

    assert step.action is TdiAdaptiveAction.RECOVER


def test_trajectory_pair_requires_order_and_same_schema() -> None:
    pair = TdiTrajectoryPair(previous=_step(0), current=_step(1))

    assert pair.current.step == 1


def test_structural_descriptor_remains_separately_owned() -> None:
    record = TdiStructuralDescriptorRecord(
        step_ref=_step(0),
        descriptor=TrajectoryDescriptorKind.STATE_DEFORMATION,
        value=0.25,
        unit="ratio",
        descriptor_semantics="ITD-33 normalized state deformation",
        itd_source=SourceIdentity("Memorithm/itd-simulator", "itd-test"),
    )

    assert record.step_ref.source.source == "Memorithm/TDI"
    assert record.itd_source.source == "Memorithm/itd-simulator"


@pytest.mark.parametrize("role", ["final", "unknown", None])
def test_serialized_role_cannot_bypass_final_boundary(role: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        _step(0, role=role)
