from __future__ import annotations

from dataclasses import replace

import pytest

from itd_research.campaign_runner import (
    CampaignCaseV1,
    CampaignPlanV1,
    CampaignRunV1,
    CaseExecutionV1,
    run_bounded_campaign,
)
from itd_research.experiment_schema import (
    ComputeBudget,
    ExperimentProtocolV1,
    HypothesisContract,
    MetricContract,
    MetricDirection,
    MetricRole,
    SourceIdentity,
    SplitIdentity,
    SplitRole,
    UncertaintyContract,
)
from itd_research.itd3x_tracks import SearchAuthorization
from itd_research.result_schema import (
    CampaignIdentityV1,
    ExperimentResultV1,
    MetricObservationV1,
    StudyClass,
    StudyOutcome,
)


def _protocol() -> ExperimentProtocolV1:
    return ExperimentProtocolV1(
        experiment_id="integrity-fixture",
        hypothesis=HypothesisContract("H1", "Bindings remain exact.", "Mutation controls."),
        implementation=SourceIdentity("code", "fixture-v1"),
        splits=tuple(SplitIdentity(role, SourceIdentity("fixture", role.value)) for role in SplitRole),
        metrics=(MetricContract("error", MetricRole.PRIMARY, MetricDirection.LOWER_IS_BETTER, "ratio"),),
        compute_budget=ComputeBudget("evaluations", 3.0),
        uncertainty=UncertaintyContract("declared-fixture-method", 0.95, True),
    )


def _plan() -> CampaignPlanV1:
    protocol = _protocol()
    campaign = CampaignIdentityV1.from_protocol("c1", protocol, implementation=protocol.implementation)
    return CampaignPlanV1(
        campaign,
        (CampaignCaseV1("case1", SplitRole.DEVELOPMENT, protocol.split(SplitRole.DEVELOPMENT).source, 2.0),),
        "evaluations",
        3.0,
    )


def _result() -> ExperimentResultV1:
    return ExperimentResultV1(
        "integrity-fixture", _protocol().fingerprint(), _plan().campaign.fingerprint(),
        StudyClass.EXPLORATORY, StudyOutcome.INCONCLUSIVE,
        (MetricObservationV1("error", 0.5, "ratio"),),
    )


@pytest.mark.parametrize("role", ["final", "FINAL", "unknown", None, 0])
def test_selection_never_accepts_final_or_unknown_serialized_role(role: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        _protocol().assert_selection_allowed(role)
    with pytest.raises((ValueError, TypeError)):
        SearchAuthorization(role, True, True).assert_allowed()


@pytest.mark.parametrize("role", ["development", "validation"])
def test_allowed_serialized_roles_are_normalized(role: str) -> None:
    _protocol().assert_selection_allowed(role)
    auth = SearchAuthorization(role, True, True)
    auth.assert_allowed()
    assert auth.role is SplitRole(role)
    assert SplitIdentity(role, SourceIdentity("data", "v1")).role is SplitRole(role)


@pytest.mark.parametrize("flag", ["false", "true", 1, 0, None])
def test_search_requires_actual_boolean_control_flags(flag: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        SearchAuthorization(SplitRole.DEVELOPMENT, flag, True).assert_allowed()
    with pytest.raises((ValueError, TypeError)):
        SearchAuthorization(SplitRole.DEVELOPMENT, True, flag).assert_allowed()


def test_final_string_is_blocked_before_evaluator_side_effect() -> None:
    plan = _plan()
    final_case = CampaignCaseV1("final", "final", SourceIdentity("fixture", "final"), 1.0)
    called = []

    def evaluator(case: CampaignCaseV1) -> CaseExecutionV1:
        called.append(case.case_id)
        return CaseExecutionV1(case.case_id, "a" * 64, 1.0)

    with pytest.raises(ValueError, match="authorization"):
        run_bounded_campaign(replace(plan, cases=(final_case,)), evaluator)
    assert called == []


def test_serialized_blocked_result_cannot_include_metrics() -> None:
    with pytest.raises(ValueError, match="blocked"):
        replace(_result(), outcome="blocked")
    result = replace(_result(), outcome="blocked", observations=(), study_class="exploratory")
    assert result.outcome is StudyOutcome.BLOCKED
    assert result.study_class is StudyClass.EXPLORATORY
    assert result.as_dict()["outcome"] == "blocked"


@pytest.mark.parametrize("field,value", [("outcome", "unknown"), ("study_class", "unknown")])
def test_result_rejects_unknown_classification(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        replace(_result(), **{field: value})


def test_diagnostic_string_cannot_become_an_objective() -> None:
    with pytest.raises(ValueError, match="diagnostic"):
        MetricContract("posthoc", "diagnostic", "higher_is_better", "ratio")


def test_recorded_run_rechecks_each_budget() -> None:
    plan = _plan()
    run = CampaignRunV1(plan.fingerprint(), (CaseExecutionV1("case1", "a" * 64, 2.1),))
    with pytest.raises(ValueError, match="budget"):
        run.assert_replay_of(plan)


def test_valid_recorded_run_and_live_run_agree() -> None:
    plan = _plan()
    run = run_bounded_campaign(
        plan, lambda case: CaseExecutionV1(case.case_id, "a" * 64, 1.0), protocol=_protocol(),
    )
    recorded = CampaignRunV1(plan.fingerprint(), run.executions)
    recorded.assert_replay_of(plan)
    assert recorded.fingerprint() == run.fingerprint()


@pytest.mark.parametrize("change", ["protocol", "source", "unit", "budget", "implementation"])
def test_protocol_binding_fails_before_evaluation(change: str) -> None:
    plan, protocol = _plan(), _protocol()
    if change == "protocol":
        plan = replace(plan, campaign=replace(plan.campaign, protocol_fingerprint="b" * 64))
    elif change == "source":
        plan = replace(plan, cases=(replace(plan.cases[0], input_source=SourceIdentity("wrong", "source")),))
    elif change == "unit":
        plan = replace(plan, work_unit="seconds")
    elif change == "budget":
        plan = replace(plan, maximum_total_work=4.0)
    elif change == "implementation":
        plan = replace(plan, campaign=replace(plan.campaign, implementation=SourceIdentity("code", "v2")))
    called = []

    def evaluator(case: CampaignCaseV1) -> CaseExecutionV1:
        called.append(case.case_id)
        return CaseExecutionV1(case.case_id, "a" * 64, 1.0)

    with pytest.raises(ValueError):
        run_bounded_campaign(plan, evaluator, protocol=protocol)
    assert called == []


def test_result_checks_actual_campaign_and_protocol() -> None:
    campaign = _plan().campaign
    campaign.assert_matches_protocol(_protocol())
    _result().assert_matches_campaign(campaign)
    with pytest.raises(ValueError, match="campaign"):
        _result().assert_matches_campaign(replace(campaign, campaign_id="other"))
    bad_campaign = replace(campaign, protocol_fingerprint="c" * 64)
    result = replace(_result(), campaign_fingerprint=bad_campaign.fingerprint())
    with pytest.raises(ValueError, match="protocol"):
        result.assert_matches_campaign(bad_campaign)


def test_collections_are_copied_before_they_are_fingerprinted() -> None:
    plan, protocol = _plan(), _protocol()
    cases, observations, adapters = list(plan.cases), list(_result().observations), []
    splits, metrics, limitations = list(protocol.splits), list(protocol.metrics), ["fixture"]
    plan_copy = replace(plan, cases=cases)
    result = replace(_result(), observations=observations, limitations=limitations)
    campaign = replace(plan.campaign, adapters=adapters)
    protocol_copy = replace(protocol, splits=splits, metrics=metrics)
    executions = [CaseExecutionV1("case1", "a" * 64, 1.0)]
    run = CampaignRunV1(plan.fingerprint(), executions)
    before = (plan_copy.fingerprint(), result.as_dict(), campaign.fingerprint(), protocol_copy.fingerprint(), run.fingerprint())
    for collection in (cases, observations, splits, metrics, limitations, executions):
        collection.clear()
    adapters.append(None)
    after = (plan_copy.fingerprint(), result.as_dict(), campaign.fingerprint(), protocol_copy.fingerprint(), run.fingerprint())
    assert after == before
    run.assert_replay_of(plan)
