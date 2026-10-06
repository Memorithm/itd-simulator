from __future__ import annotations

import json
from pathlib import Path

import pytest

from itd_research.campaign_runner import CampaignCaseV1, CaseExecutionV1
from itd_research.campaign_store import (
    ArtifactEvaluator,
    CampaignHalt,
    CampaignLifecycleStatus,
    completed_run_from_store,
    run_persisted_campaign,
)
from itd_research.experiment_schema import SplitRole
from itd_research.pascal_integrity import (
    PASCAL_R2_CASE_COUNT,
    pascal_r2_plan,
    pascal_r2_protocol,
    pascal_r2_source_payloads,
    pascal_r2_split_payload,
    run_pascal_r2,
)
from itd_research.source_verification import digest_bytes


def test_pascal_r2_plan_is_nonfinal_and_fingerprint_stable() -> None:
    protocol = pascal_r2_protocol()
    plan = pascal_r2_plan(protocol)

    assert len(plan.cases) == PASCAL_R2_CASE_COUNT
    assert all(case.role is not SplitRole.FINAL for case in plan.cases)
    assert plan.fingerprint() == pascal_r2_plan(protocol).fingerprint()
    with pytest.raises(ValueError, match="protected"):
        pascal_r2_split_payload(SplitRole.FINAL)


def test_pascal_r2_persistent_run_is_exact_and_replayable(tmp_path: Path) -> None:
    ledger = run_pascal_r2(tmp_path)

    assert ledger.status is CampaignLifecycleStatus.COMPLETED
    assert len(ledger.executions) == PASCAL_R2_CASE_COUNT
    assert len(ledger.source_verifications) == 2
    plan = pascal_r2_plan(pascal_r2_protocol())
    assert ledger.plan_fingerprint == plan.fingerprint()

    replay = completed_run_from_store(tmp_path)
    replay.assert_replay_of(plan)
    for artifact in ledger.artifacts:
        payload = json.loads((tmp_path / artifact.relative_path).read_text())
        assert payload["direct_mismatches"] == 0
        assert payload["canonical_mismatches"] == 0
        assert payload["direct_reference_mismatches"] == 0
        assert payload["direct_checksum"] == payload["canonical_checksum"]
        assert payload["canonical_checksum"] == payload["transformed_checksum"]


class _InconclusiveEvaluator(ArtifactEvaluator):
    def evaluate(
        self,
        case: CampaignCaseV1,
    ) -> tuple[CaseExecutionV1, bytes]:
        artifact = b'{"status":"synthetic_integrity_mismatch"}'
        execution = CaseExecutionV1(
            case_id=case.case_id,
            output_sha256=digest_bytes(artifact),
            work_units_used=1.0,
        )
        raise CampaignHalt(
            CampaignLifecycleStatus.INCONCLUSIVE,
            "synthetic integrity mismatch",
            execution=execution,
            artifact=artifact,
        )


def test_pascal_r2_preserves_inconclusive_evidence(tmp_path: Path) -> None:
    protocol = pascal_r2_protocol()
    plan = pascal_r2_plan(protocol)
    ledger = run_persisted_campaign(
        tmp_path,
        plan,
        _InconclusiveEvaluator(),
        source_payloads=pascal_r2_source_payloads(),
        protocol=protocol,
    )

    assert ledger.status is CampaignLifecycleStatus.INCONCLUSIVE
    assert len(ledger.executions) == 1
    assert len(ledger.artifacts) == 1
    artifact = tmp_path / ledger.artifacts[0].relative_path
    assert artifact.read_bytes() == b'{"status":"synthetic_integrity_mismatch"}'


def test_pascal_r2_source_bytes_fail_closed_when_tampered(tmp_path: Path) -> None:
    protocol = pascal_r2_protocol()
    plan = pascal_r2_plan(protocol)
    payloads = pascal_r2_source_payloads()
    first_key = next(iter(payloads))
    payloads[first_key] += b"tamper"

    with pytest.raises(ValueError, match="source bytes"):
        run_persisted_campaign(
            tmp_path,
            plan,
            _InconclusiveEvaluator(),
            source_payloads=payloads,
            protocol=protocol,
        )
