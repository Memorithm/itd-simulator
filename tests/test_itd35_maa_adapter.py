from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.maa_adapter import (
    MaaAlgebraDomain,
    MaaEvidenceDisposition,
    MaaNumericalObservation,
    MaaRouteRef,
)


def _route() -> MaaRouteRef:
    return MaaRouteRef(
        route_id="maa-route-1",
        source=SourceIdentity("Memorithm/FLAT-ATTENTION", "maa-test"),
        role=SplitRole.DEVELOPMENT,
        domains=(
            MaaAlgebraDomain.BOOLEAN,
            MaaAlgebraDomain.F2,
            MaaAlgebraDomain.ZHEGALKIN,
        ),
        policy_sha256="a" * 64,
        feature_schema_sha256="b" * 64,
        dataset_sha256="c" * 64,
        recomposition_policy="strict_conjunction",
    )


def test_maa_route_requires_boolean_admission() -> None:
    with pytest.raises(ValueError, match="Boolean admission"):
        MaaRouteRef(
            route_id="bad",
            source=SourceIdentity("Memorithm/FLAT-ATTENTION", "maa-test"),
            role=SplitRole.DEVELOPMENT,
            domains=(MaaAlgebraDomain.F2,),
            policy_sha256="a" * 64,
            feature_schema_sha256="b" * 64,
            dataset_sha256="c" * 64,
            recomposition_policy="f2_only",
        )


def test_empty_maa_observation_cannot_fabricate_output() -> None:
    observation = MaaNumericalObservation(
        route=_route(),
        case_id="empty_selection",
        arm="boolean_f2_zhegalkin",
        disposition=MaaEvidenceDisposition.SMOKE,
        selected_candidate_ids=(),
        score_evaluations=0,
        retained_dense_relevant=0,
        output_max_abs_error=None,
        lse_abs_error=None,
        no_survivors=True,
    )

    assert observation.authorizes_softmax_replacement_claim is False
    assert observation.authorizes_performance_claim is False
    assert observation.authorizes_runtime_routing is False


def test_nonempty_maa_observation_requires_both_o_and_lse_diagnostics() -> None:
    with pytest.raises(ValueError, match="O/LSE diagnostics"):
        MaaNumericalObservation(
            route=_route(),
            case_id="case-1",
            arm="combined",
            disposition=MaaEvidenceDisposition.EXPLORATORY,
            selected_candidate_ids=(0, 2, 4),
            score_evaluations=3,
            retained_dense_relevant=1,
            output_max_abs_error=0.1,
            lse_abs_error=None,
            no_survivors=False,
        )


def test_maa_observation_preserves_upstream_negative_classification() -> None:
    observation = MaaNumericalObservation(
        route=_route(),
        case_id="holdout",
        arm="strict_conjunction",
        disposition=MaaEvidenceDisposition.CONFIRMATORY_REJECTED,
        selected_candidate_ids=(0, 2),
        score_evaluations=2,
        retained_dense_relevant=1,
        output_max_abs_error=0.2,
        lse_abs_error=0.3,
        no_survivors=False,
    )

    assert observation.disposition is MaaEvidenceDisposition.CONFIRMATORY_REJECTED


def test_maa_selected_ids_must_preserve_source_order() -> None:
    with pytest.raises(ValueError, match="source order"):
        MaaNumericalObservation(
            route=_route(),
            case_id="case-1",
            arm="combined",
            disposition=MaaEvidenceDisposition.SMOKE,
            selected_candidate_ids=(2, 0),
            score_evaluations=2,
            retained_dense_relevant=1,
            output_max_abs_error=0.1,
            lse_abs_error=0.2,
            no_survivors=False,
        )
