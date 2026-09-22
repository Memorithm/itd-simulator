from __future__ import annotations

import pytest

from itd_research.adaptive_shadow import (
    AdaptiveAction,
    QualityDirection,
    ShadowDecision,
    ShadowRealization,
    ShadowRegretEvaluation,
    ShadowUtilityContract,
)


def _decision() -> ShadowDecision:
    return ShadowDecision(
        decision_id="shadow-1",
        action=AdaptiveAction.CHANGE_PRECISION,
        predicted_quality_delta=-0.02,
        predicted_cost_delta=-4.0,
        invariant_risk=0.0,
        evidence_fingerprint="a" * 64,
    )


def test_shadow_realization_measures_prediction_error_without_actuation() -> None:
    realization = ShadowRealization(
        decision=_decision(),
        baseline_quality=0.90,
        realized_quality=0.87,
        baseline_cost=10.0,
        realized_cost=5.0,
        invariant_violated=False,
    )

    assert realization.observed_quality_delta == pytest.approx(-0.03)
    assert realization.observed_cost_delta == pytest.approx(-5.0)
    assert realization.quality_prediction_error == pytest.approx(0.01)
    assert realization.cost_prediction_error == pytest.approx(1.0)
    assert realization.actuates is False


def test_shadow_regret_requires_explicit_scalarization() -> None:
    realization = ShadowRealization(
        decision=_decision(),
        baseline_quality=0.90,
        realized_quality=0.87,
        baseline_cost=10.0,
        realized_cost=5.0,
        invariant_violated=False,
    )
    utility = ShadowUtilityContract(
        quality_direction=QualityDirection.HIGHER_IS_BETTER,
        quality_weight=10.0,
        cost_weight=0.1,
        invariant_penalty=100.0,
    )
    evaluation = ShadowRegretEvaluation(
        realization=realization,
        oracle_quality=0.89,
        oracle_cost=4.0,
        oracle_invariant_violated=False,
        utility=utility,
    )

    assert evaluation.regret == pytest.approx(
        evaluation.oracle_utility - evaluation.chosen_utility
    )
    assert evaluation.actuates is False


def test_invariant_violation_is_explicitly_penalized() -> None:
    utility = ShadowUtilityContract(
        quality_direction=QualityDirection.HIGHER_IS_BETTER,
        quality_weight=1.0,
        cost_weight=0.0,
        invariant_penalty=10.0,
    )

    safe = utility.score(quality=1.0, cost=0.0, invariant_violated=False)
    unsafe = utility.score(quality=1.0, cost=0.0, invariant_violated=True)

    assert safe - unsafe == pytest.approx(10.0)


def test_zero_weight_shadow_utility_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one positive"):
        ShadowUtilityContract(
            quality_direction=QualityDirection.LOWER_IS_BETTER,
            quality_weight=0.0,
            cost_weight=0.0,
            invariant_penalty=0.0,
        )
