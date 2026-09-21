from __future__ import annotations

import pytest

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
from itd_research.result_schema import (
    AdapterIdentityV1,
    CampaignIdentityV1,
    ExperimentResultV1,
    MetricObservationV1,
    StudyClass,
    StudyOutcome,
)


def _protocol() -> ExperimentProtocolV1:
    return ExperimentProtocolV1(
        experiment_id="itd-30.1-contract-smoke",
        hypothesis=HypothesisContract(
            "H30.1",
            "The result layer preserves protocol identity.",
            "Bound result versus deliberately mismatched result.",
        ),
        implementation=SourceIdentity("Memorithm/itd-simulator", "test"),
        splits=(
            SplitIdentity(SplitRole.DEVELOPMENT, SourceIdentity("dataset-dev", "v1")),
            SplitIdentity(SplitRole.VALIDATION, SourceIdentity("dataset-val", "v1")),
            SplitIdentity(SplitRole.FINAL, SourceIdentity("dataset-final", "v1")),
        ),
        metrics=(
            MetricContract(
                "error",
                MetricRole.PRIMARY,
                MetricDirection.LOWER_IS_BETTER,
                "fraction",
            ),
        ),
        compute_budget=ComputeBudget("evaluations", 16),
        uncertainty=UncertaintyContract("paired-bootstrap", 0.95, True),
    )


def test_campaign_and_result_bind_to_protocol() -> None:
    protocol = _protocol()
    adapter = AdapterIdentityV1(
        "SciRust",
        "reference-oracle",
        SourceIdentity("Memorithm/scirust", "deadbeef"),
    )
    campaign = CampaignIdentityV1.from_protocol(
        "campaign-1",
        protocol,
        implementation=SourceIdentity("Memorithm/itd-simulator", "cafebabe"),
        adapters=(adapter,),
    )
    result = ExperimentResultV1(
        experiment_id=protocol.experiment_id,
        protocol_fingerprint=protocol.fingerprint(),
        campaign_fingerprint=campaign.fingerprint(),
        study_class=StudyClass.EXPLORATORY,
        outcome=StudyOutcome.NEGATIVE,
        observations=(MetricObservationV1("error", 0.25, "fraction"),),
    )

    result.assert_matches_protocol(protocol)
    assert len(campaign.fingerprint()) == 64


def test_result_rejects_undeclared_metrics() -> None:
    protocol = _protocol()
    campaign = CampaignIdentityV1.from_protocol(
        "campaign-1",
        protocol,
        implementation=SourceIdentity("Memorithm/itd-simulator", "cafebabe"),
    )
    result = ExperimentResultV1(
        experiment_id=protocol.experiment_id,
        protocol_fingerprint=protocol.fingerprint(),
        campaign_fingerprint=campaign.fingerprint(),
        study_class=StudyClass.EXPLORATORY,
        outcome=StudyOutcome.INCONCLUSIVE,
        observations=(MetricObservationV1("posthoc_metric", 1.0, "unit"),),
    )

    with pytest.raises(ValueError, match="undeclared metric"):
        result.assert_matches_protocol(protocol)


def test_blocked_result_cannot_smuggle_metric_values() -> None:
    protocol = _protocol()
    campaign = CampaignIdentityV1.from_protocol(
        "campaign-1",
        protocol,
        implementation=SourceIdentity("Memorithm/itd-simulator", "cafebabe"),
    )

    with pytest.raises(ValueError, match="blocked"):
        ExperimentResultV1(
            experiment_id=protocol.experiment_id,
            protocol_fingerprint=protocol.fingerprint(),
            campaign_fingerprint=campaign.fingerprint(),
            study_class=StudyClass.CONFIRMATORY,
            outcome=StudyOutcome.BLOCKED,
            observations=(MetricObservationV1("error", 0.0, "fraction"),),
        )
