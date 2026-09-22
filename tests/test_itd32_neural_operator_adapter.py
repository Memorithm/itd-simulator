from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.itd3x_tracks import AIComparisonArm
from itd_research.neural_operator_adapter import (
    OperatorEvaluationCase,
    OperatorModelRef,
    OperatorPredictionRecord,
    OperatorSampleRef,
    OperatorTaskKind,
)


def _sample(role: SplitRole) -> OperatorSampleRef:
    return OperatorSampleRef(
        sample_id="burgers-001",
        task=OperatorTaskKind.BURGERS_1D,
        role=role,
        source=SourceIdentity("Memorithm/NeuralOperator", "dataset-v1"),
        input_sha256="a" * 64,
        target_sha256="b" * 64,
        resolution=(128,),
        distribution="in_distribution",
    )


def _case(role: SplitRole = SplitRole.DEVELOPMENT) -> OperatorEvaluationCase:
    return OperatorEvaluationCase(
        case_id="case-1",
        sample=_sample(role),
        arm=AIComparisonArm.RAW_MODEL,
        model=OperatorModelRef(
            model_id="fno-reference",
            family="fno",
            source=SourceIdentity("Memorithm/NeuralOperator", "model-v1"),
            checkpoint_sha256="c" * 64,
        ),
        representation_id="raw-field",
    )


def test_neural_operator_development_case_allows_selection() -> None:
    case = _case()

    case.assert_selection_allowed()
    assert case.sample.resolution == (128,)


def test_neural_operator_final_case_rejects_selection() -> None:
    case = _case(SplitRole.FINAL)

    with pytest.raises(ValueError, match="final NeuralOperator"):
        case.assert_selection_allowed()


def test_prediction_record_binds_exact_case_and_units() -> None:
    case = _case()
    record = OperatorPredictionRecord(
        case_id=case.case_id,
        prediction_sha256="d" * 64,
        relative_l2_error=0.1,
        physics_residual=0.02,
        inference_cost=3.5,
        inference_cost_unit="milliseconds",
    )

    record.assert_matches_case(case)
    assert record.physics_residual == pytest.approx(0.02)


def test_prediction_record_rejects_negative_error() -> None:
    with pytest.raises(ValueError, match="relative_l2_error"):
        OperatorPredictionRecord(
            case_id="case-1",
            prediction_sha256="d" * 64,
            relative_l2_error=-0.1,
            physics_residual=None,
            inference_cost=1.0,
            inference_cost_unit="milliseconds",
        )


@pytest.mark.parametrize("role", ["final", "unknown", None])
def test_serialized_role_cannot_bypass_final_boundary(role: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        _sample(role).assert_selection_allowed()
