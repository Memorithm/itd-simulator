from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity
from itd_research.hub_orchestration import (
    HubArtifactRef,
    HubCampaignSubmission,
    HubRunRecord,
    HubRunState,
)


def _submission() -> HubCampaignSubmission:
    return HubCampaignSubmission(
        source=SourceIdentity("Memorithm/scirust-hub", "hub-test"),
        component_id="component-uuid",
        capability="itd.campaign",
        campaign_plan_fingerprint="a" * 64,
        params_sha256="b" * 64,
        maximum_parallelism=4,
        maximum_attempts=2,
        timeout_seconds=300.0,
    )


def test_hub_submission_binds_campaign_and_resource_limits() -> None:
    submission = _submission()

    assert submission.maximum_parallelism == 4
    assert submission.maximum_attempts == 2


def test_successful_hub_run_requires_immutable_artifact() -> None:
    with pytest.raises(ValueError, match="at least one artifact"):
        HubRunRecord(
            submission=_submission(),
            run_id="run-1",
            state=HubRunState.SUCCEEDED,
            attempt_count=1,
            provenance_sha256="c" * 64,
            artifacts=(),
        )


def test_hub_run_preserves_nonclaim_and_nonsandbox_boundaries() -> None:
    run = HubRunRecord(
        submission=_submission(),
        run_id="run-1",
        state=HubRunState.SUCCEEDED,
        attempt_count=1,
        provenance_sha256="c" * 64,
        artifacts=(
            HubArtifactRef(
                artifact_id="artifact-1",
                content_sha256="d" * 64,
            ),
        ),
    )

    assert run.authorizes_scientific_conclusion is False
    assert run.claims_os_sandbox is False


def test_hub_run_rejects_attempt_overrun() -> None:
    with pytest.raises(ValueError, match="maximum_attempts"):
        HubRunRecord(
            submission=_submission(),
            run_id="run-1",
            state=HubRunState.FAILED,
            attempt_count=3,
            provenance_sha256="c" * 64,
            artifacts=(),
        )


def test_hub_artifact_ids_must_be_unique() -> None:
    artifact = HubArtifactRef(
        artifact_id="same",
        content_sha256="d" * 64,
    )

    with pytest.raises(ValueError, match="artifact identifiers"):
        HubRunRecord(
            submission=_submission(),
            run_id="run-1",
            state=HubRunState.SUCCEEDED,
            attempt_count=1,
            provenance_sha256="c" * 64,
            artifacts=(artifact, artifact),
        )
