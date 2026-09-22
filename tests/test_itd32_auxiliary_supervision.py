from __future__ import annotations

from dataclasses import replace

import pytest

from itd_research.auxiliary_supervision import (
    AuxiliaryTargetClass,
    AuxiliaryTargetRef,
    AuxiliaryTrainingArm,
    LearningCurvePoint,
    MetricDirection,
    assert_matched_training_budget,
    sample_count_to_threshold,
    sample_efficiency_ratio,
)
from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.neural_operator_adapter import OperatorModelRef


def _model() -> OperatorModelRef:
    return OperatorModelRef(
        model_id="fno",
        family="fno",
        source=SourceIdentity("Memorithm/NeuralOperator", "model-test"),
    )


def _arm(
    arm_id: str,
    target: AuxiliaryTargetRef | None,
    *,
    work: float = 100.0,
) -> AuxiliaryTrainingArm:
    return AuxiliaryTrainingArm(
        arm_id=arm_id,
        role=SplitRole.DEVELOPMENT,
        model=_model(),
        auxiliary_target=target,
        auxiliary_loss_weight=0.0 if target is None else 0.1,
        parameter_budget=1000,
        training_work=work,
        training_work_unit="optimizer_steps",
        seed=7,
    )


def _target(target_class: AuxiliaryTargetClass) -> AuxiliaryTargetRef:
    return AuxiliaryTargetRef(
        target_id=target_class.value,
        target_class=target_class,
        source=SourceIdentity("Memorithm/itd-simulator", "itd-test"),
        schema_sha256="a" * 64,
        unit="normalized",
    )


def test_auxiliary_comparison_requires_matched_budget() -> None:
    baseline = _arm("baseline", None)
    candidate = _arm("itd-aux", _target(AuxiliaryTargetClass.ITD_DERIVED))

    assert_matched_training_budget(baseline, candidate)


def test_auxiliary_comparison_rejects_training_work_mismatch() -> None:
    baseline = _arm("baseline", None)
    candidate = _arm(
        "itd-aux",
        _target(AuxiliaryTargetClass.ITD_DERIVED),
        work=101.0,
    )

    with pytest.raises(ValueError, match="equal training work"):
        assert_matched_training_budget(baseline, candidate)


def test_auxiliary_fitting_rejects_final_data() -> None:
    with pytest.raises(ValueError, match="final data"):
        AuxiliaryTrainingArm(
            arm_id="bad",
            role=SplitRole.FINAL,
            model=_model(),
            auxiliary_target=None,
            auxiliary_loss_weight=0.0,
            parameter_budget=1000,
            training_work=100.0,
            training_work_unit="optimizer_steps",
            seed=7,
        )


def test_sample_count_to_threshold_uses_first_preregistered_crossing() -> None:
    points = (
        LearningCurvePoint(16, 0.40),
        LearningCurvePoint(32, 0.20),
        LearningCurvePoint(64, 0.10),
    )

    count = sample_count_to_threshold(
        points,
        threshold=0.20,
        direction=MetricDirection.LOWER_IS_BETTER,
    )

    assert count == 32


def test_sample_efficiency_ratio_reports_baseline_over_candidate_samples() -> None:
    baseline = (
        LearningCurvePoint(16, 0.50),
        LearningCurvePoint(32, 0.30),
        LearningCurvePoint(64, 0.15),
    )
    candidate = (
        LearningCurvePoint(16, 0.35),
        LearningCurvePoint(32, 0.15),
        LearningCurvePoint(64, 0.10),
    )

    ratio = sample_efficiency_ratio(
        baseline,
        candidate,
        threshold=0.20,
        direction=MetricDirection.LOWER_IS_BETTER,
    )

    assert ratio == pytest.approx(2.0)


def test_sample_efficiency_returns_none_if_threshold_is_not_reached() -> None:
    baseline = (LearningCurvePoint(16, 0.50),)
    candidate = (LearningCurvePoint(16, 0.10),)

    assert (
        sample_efficiency_ratio(
            baseline,
            candidate,
            threshold=0.20,
            direction=MetricDirection.LOWER_IS_BETTER,
        )
        is None
    )


@pytest.mark.parametrize("role", ["final", "unknown", None])
def test_serialized_role_cannot_bypass_final_boundary(role: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        replace(_arm("baseline", None), role=role)
