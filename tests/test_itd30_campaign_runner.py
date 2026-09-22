from __future__ import annotations

import pytest

from itd_research.campaign_runner import (
    CampaignCaseV1,
    CampaignPlanV1,
    CaseExecutionV1,
    FinalEvaluationAuthorizationV1,
    run_bounded_campaign,
)
from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.result_schema import CampaignIdentityV1


def _campaign() -> CampaignIdentityV1:
    return CampaignIdentityV1(
        campaign_id="itd-30.3-smoke",
        protocol_fingerprint="a" * 64,
        implementation=SourceIdentity("Memorithm/itd-simulator", "runner-test"),
    )


def test_bounded_campaign_preserves_declared_order() -> None:
    source = SourceIdentity("fixture", "v1")
    plan = CampaignPlanV1(
        campaign=_campaign(),
        cases=(
            CampaignCaseV1("c1", SplitRole.DEVELOPMENT, source, 2.0),
            CampaignCaseV1("c2", SplitRole.VALIDATION, source, 3.0),
        ),
        work_unit="evaluations",
        maximum_total_work=5.0,
    )

    def evaluator(case: CampaignCaseV1) -> CaseExecutionV1:
        return CaseExecutionV1(case.case_id, ("1" if case.case_id == "c1" else "2") * 64, case.work_units)

    run = run_bounded_campaign(plan, evaluator)

    assert tuple(item.case_id for item in run.executions) == ("c1", "c2")
    run.assert_replay_of(plan)
    assert len(run.fingerprint()) == 64


def test_campaign_rejects_final_without_authorization() -> None:
    final_source = SourceIdentity("final-fixture", "v1")
    plan = CampaignPlanV1(
        campaign=_campaign(),
        cases=(CampaignCaseV1("final", SplitRole.FINAL, final_source, 1.0),),
        work_unit="evaluations",
        maximum_total_work=1.0,
    )

    with pytest.raises(ValueError, match="explicit authorization"):
        run_bounded_campaign(
            plan,
            lambda case: CaseExecutionV1(case.case_id, "f" * 64, 1.0),
        )


def test_campaign_accepts_exact_final_authorization() -> None:
    final_source = SourceIdentity("final-fixture", "v1")
    campaign = _campaign()
    plan = CampaignPlanV1(
        campaign=campaign,
        cases=(CampaignCaseV1("final", SplitRole.FINAL, final_source, 1.0),),
        work_unit="evaluations",
        maximum_total_work=1.0,
    )
    authorization = FinalEvaluationAuthorizationV1(
        protocol_fingerprint=campaign.protocol_fingerprint,
        final_source=final_source,
        authorization_sha256="e" * 64,
    )

    run = run_bounded_campaign(
        plan,
        lambda case: CaseExecutionV1(case.case_id, "f" * 64, 1.0),
        final_authorization=authorization,
    )

    assert run.executions[0].case_id == "final"


def test_campaign_rejects_case_budget_overrun() -> None:
    source = SourceIdentity("fixture", "v1")
    plan = CampaignPlanV1(
        campaign=_campaign(),
        cases=(CampaignCaseV1("c1", SplitRole.DEVELOPMENT, source, 1.0),),
        work_unit="evaluations",
        maximum_total_work=1.0,
    )

    with pytest.raises(ValueError, match="work budget"):
        run_bounded_campaign(
            plan,
            lambda case: CaseExecutionV1(case.case_id, "a" * 64, 2.0),
        )


def test_campaign_rejects_mismatched_case_identity() -> None:
    source = SourceIdentity("fixture", "v1")
    plan = CampaignPlanV1(
        campaign=_campaign(),
        cases=(CampaignCaseV1("c1", SplitRole.DEVELOPMENT, source, 1.0),),
        work_unit="evaluations",
        maximum_total_work=1.0,
    )

    with pytest.raises(ValueError, match="mismatched case_id"):
        run_bounded_campaign(
            plan,
            lambda _case: CaseExecutionV1("other", "a" * 64, 1.0),
        )
