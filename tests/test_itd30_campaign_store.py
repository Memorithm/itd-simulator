from __future__ import annotations

from pathlib import Path

import pytest

from itd_research.campaign_runner import (
    CampaignCaseV1,
    CampaignPlanV1,
    CaseExecutionV1,
    FinalEvaluationAuthorizationV1,
)
from itd_research.campaign_store import (
    ArtifactEvaluator,
    ArtifactRecordV1,
    CampaignHalt,
    CampaignLedgerV1,
    CampaignLifecycleStatus,
    completed_run_from_store,
    load_campaign_ledger,
    resume_persisted_campaign,
    run_persisted_campaign,
)
from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.result_schema import CampaignIdentityV1
from itd_research.source_verification import digest_bytes, verify_source_bytes


def _source(name: str, payload: bytes) -> SourceIdentity:
    return SourceIdentity(name, "v1", digest_bytes(payload))


def _plan(*cases: CampaignCaseV1) -> CampaignPlanV1:
    return CampaignPlanV1(
        campaign=CampaignIdentityV1(
            campaign_id="itd-30.4-store",
            protocol_fingerprint="a" * 64,
            implementation=SourceIdentity("Memorithm/itd-simulator", "store-test"),
        ),
        cases=cases,
        work_unit="evaluations",
        maximum_total_work=sum(case.work_units for case in cases),
    )


class _ExactBytes(ArtifactEvaluator):
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads
        self.calls: list[str] = []

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        self.calls.append(case.case_id)
        payload = self.payloads[case.case_id]
        return CaseExecutionV1(case.case_id, digest_bytes(payload), case.work_units), payload


class _Halt(ArtifactEvaluator):
    def __init__(
        self,
        status: CampaignLifecycleStatus,
        reason: str,
        *,
        artifact: bytes | None = None,
    ) -> None:
        self.status = status
        self.reason = reason
        self.artifact = artifact

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        execution = None
        if self.artifact is not None:
            execution = CaseExecutionV1(case.case_id, digest_bytes(self.artifact), case.work_units)
        raise CampaignHalt(self.status, self.reason, execution=execution, artifact=self.artifact)


class _CrashAfterFirst(ArtifactEvaluator):
    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        if case.case_id == "c1":
            payload = b"first"
            return CaseExecutionV1(case.case_id, digest_bytes(payload), case.work_units), payload
        raise RuntimeError("evaluator crashed")


def test_source_bytes_must_match_declared_digest() -> None:
    payload = b"development-source"
    identity = _source("dev", payload)
    record = verify_source_bytes(identity, payload)
    assert record.byte_count == len(payload)
    with pytest.raises(ValueError, match="do not match declared sha256"):
        verify_source_bytes(identity, b"tampered")
    with pytest.raises(ValueError, match="no declared sha256"):
        verify_source_bytes(SourceIdentity("dev", "v1"), payload)


def test_persisted_campaign_writes_artifacts_and_completed_run(tmp_path: Path) -> None:
    dev = b"dev-bytes"
    val = b"val-bytes"
    plan = _plan(
        CampaignCaseV1("c1", SplitRole.DEVELOPMENT, _source("dev", dev), 1.0),
        CampaignCaseV1("c2", SplitRole.VALIDATION, _source("val", val), 2.0),
    )
    evaluator = _ExactBytes({"c1": b"out-1", "c2": b"out-2"})
    ledger = run_persisted_campaign(
        tmp_path,
        plan,
        evaluator,
        source_payloads={("dev", "v1"): dev, ("val", "v1"): val},
    )

    assert ledger.status is CampaignLifecycleStatus.COMPLETED
    assert evaluator.calls == ["c1", "c2"]
    run = completed_run_from_store(tmp_path)
    run.assert_replay_of(plan)
    assert (tmp_path / "artifacts" / "c1" / "output.bin").read_bytes() == b"out-1"
    assert load_campaign_ledger(tmp_path).source_verifications[0].observed_sha256 == digest_bytes(dev)


def test_missing_source_bytes_fail_before_evaluation(tmp_path: Path) -> None:
    payload = b"dev-bytes"
    plan = _plan(CampaignCaseV1("c1", SplitRole.DEVELOPMENT, _source("dev", payload), 1.0))
    evaluator = _ExactBytes({"c1": b"out"})
    with pytest.raises(ValueError, match="missing source bytes"):
        run_persisted_campaign(tmp_path, plan, evaluator, source_payloads={})
    assert evaluator.calls == []
    assert not (tmp_path / "ledger.json").exists()


def test_blocked_campaign_is_terminal_and_not_resumable(tmp_path: Path) -> None:
    payload = b"dev-bytes"
    plan = _plan(
        CampaignCaseV1("c1", SplitRole.DEVELOPMENT, _source("dev", payload), 1.0),
        CampaignCaseV1("c2", SplitRole.VALIDATION, _source("val", b"val-bytes"), 1.0),
    )
    ledger = run_persisted_campaign(
        tmp_path,
        plan,
        _Halt(CampaignLifecycleStatus.BLOCKED, "external source unreadable"),
        source_payloads={("dev", "v1"): payload, ("val", "v1"): b"val-bytes"},
    )
    assert ledger.status is CampaignLifecycleStatus.BLOCKED
    assert ledger.executions == ()
    with pytest.raises(ValueError, match="only an interrupted campaign"):
        resume_persisted_campaign(
            tmp_path,
            _ExactBytes({"c1": b"out", "c2": b"out"}),
            source_payloads={("dev", "v1"): payload, ("val", "v1"): b"val-bytes"},
        )

    evaluator = _ExactBytes({"c1": b"out", "c2": b"out"})
    with pytest.raises(ValueError, match="already contains a ledger"):
        run_persisted_campaign(
            tmp_path,
            plan,
            evaluator,
            source_payloads={("dev", "v1"): payload, ("val", "v1"): b"val-bytes"},
        )
    assert evaluator.calls == []


def test_inconclusive_prefix_is_recorded_without_becoming_success(tmp_path: Path) -> None:
    payload = b"dev-bytes"
    plan = _plan(
        CampaignCaseV1("c1", SplitRole.DEVELOPMENT, _source("dev", payload), 1.0),
        CampaignCaseV1("c2", SplitRole.VALIDATION, _source("val", b"val-bytes"), 1.0),
    )
    ledger = run_persisted_campaign(
        tmp_path,
        plan,
        _Halt(
            CampaignLifecycleStatus.INCONCLUSIVE,
            "metric variance exceeds protocol bound",
            artifact=b"partial",
        ),
        source_payloads={("dev", "v1"): payload, ("val", "v1"): b"val-bytes"},
    )
    assert ledger.status is CampaignLifecycleStatus.INCONCLUSIVE
    assert tuple(item.case_id for item in ledger.executions) == ("c1",)
    with pytest.raises(ValueError, match="only a completed ledger"):
        ledger.completed_run(plan)


def test_persistence_rejects_case_ids_that_are_not_safe_path_components(tmp_path: Path) -> None:
    payload = b"dev-bytes"
    plan = _plan(
        CampaignCaseV1("../../outside", SplitRole.DEVELOPMENT, _source("dev", payload), 1.0)
    )
    evaluator = _ExactBytes({"../../outside": b"out"})
    with pytest.raises(ValueError, match="case_id used for persistence"):
        run_persisted_campaign(
            tmp_path,
            plan,
            evaluator,
            source_payloads={("dev", "v1"): payload},
        )
    assert not (tmp_path.parent / "outside").exists()


def test_ledger_rejects_artifact_digest_not_bound_to_execution() -> None:
    execution = CaseExecutionV1("c1", digest_bytes(b"execution"), 1.0)
    artifact = ArtifactRecordV1(
        case_id="c1",
        relative_path="artifacts/c1/output.bin",
        output_sha256=digest_bytes(b"different"),
        byte_count=len(b"different"),
    )
    with pytest.raises(ValueError, match="artifact digest must match"):
        CampaignLedgerV1(
            plan_fingerprint="a" * 64,
            status=CampaignLifecycleStatus.COMPLETED,
            reason="invalid binding",
            executions=(execution,),
            artifacts=(artifact,),
        )


def test_halt_execution_requires_exact_artifact_bytes() -> None:
    execution = CaseExecutionV1("c1", digest_bytes(b"output"), 1.0)
    with pytest.raises(ValueError, match="supplied together"):
        CampaignHalt(CampaignLifecycleStatus.BLOCKED, "blocked", execution=execution)


def test_exception_persists_interrupted_ledger_then_reraises(tmp_path: Path) -> None:
    payload = b"dev-bytes"
    plan = _plan(
        CampaignCaseV1("c1", SplitRole.DEVELOPMENT, _source("dev", payload), 1.0),
        CampaignCaseV1("c2", SplitRole.VALIDATION, _source("val", b"val-bytes"), 1.0),
    )
    with pytest.raises(RuntimeError, match="evaluator crashed"):
        run_persisted_campaign(
            tmp_path,
            plan,
            _CrashAfterFirst(),
            source_payloads={("dev", "v1"): payload, ("val", "v1"): b"val-bytes"},
        )
    ledger = load_campaign_ledger(tmp_path)
    assert ledger.status is CampaignLifecycleStatus.INTERRUPTED
    assert tuple(item.case_id for item in ledger.executions) == ("c1",)


def test_interrupted_campaign_can_resume_remaining_cases(tmp_path: Path) -> None:
    dev = b"dev-bytes"
    val = b"val-bytes"
    plan = _plan(
        CampaignCaseV1("c1", SplitRole.DEVELOPMENT, _source("dev", dev), 1.0),
        CampaignCaseV1("c2", SplitRole.VALIDATION, _source("val", val), 1.0),
    )
    with pytest.raises(RuntimeError, match="evaluator crashed"):
        run_persisted_campaign(
            tmp_path,
            plan,
            _CrashAfterFirst(),
            source_payloads={("dev", "v1"): dev, ("val", "v1"): val},
        )
    resumed = resume_persisted_campaign(
        tmp_path,
        _ExactBytes({"c2": b"second"}),
        source_payloads={("dev", "v1"): dev, ("val", "v1"): val},
    )
    assert resumed.status is CampaignLifecycleStatus.COMPLETED
    assert tuple(item.case_id for item in resumed.executions) == ("c1", "c2")
    completed_run_from_store(tmp_path).assert_replay_of(plan)
    assert (tmp_path / "artifacts" / "c1" / "output.bin").read_bytes() == b"first"
    assert (tmp_path / "artifacts" / "c2" / "output.bin").read_bytes() == b"second"


def test_final_authorization_digest_is_not_enough_without_bytes(tmp_path: Path) -> None:
    payload = b"final-source"
    plan = _plan(CampaignCaseV1("final", SplitRole.FINAL, _source("final", payload), 1.0))
    authorization = FinalEvaluationAuthorizationV1(
        protocol_fingerprint="a" * 64,
        final_source=_source("final", payload),
        authorization_sha256=digest_bytes(b"permit"),
    )
    with pytest.raises(ValueError, match="artifact bytes"):
        run_persisted_campaign(
            tmp_path,
            plan,
            _ExactBytes({"final": b"out"}),
            source_payloads={("final", "v1"): payload},
            final_authorization=authorization,
        )


def test_final_authorization_bytes_must_match_declared_digest(tmp_path: Path) -> None:
    payload = b"final-source"
    permit = b"permit"
    plan = _plan(CampaignCaseV1("final", SplitRole.FINAL, _source("final", payload), 1.0))
    authorization = FinalEvaluationAuthorizationV1(
        protocol_fingerprint="a" * 64,
        final_source=_source("final", payload),
        authorization_sha256=digest_bytes(permit),
    )
    with pytest.raises(ValueError, match="authorization artifact bytes"):
        run_persisted_campaign(
            tmp_path,
            plan,
            _ExactBytes({"final": b"out"}),
            source_payloads={("final", "v1"): payload},
            final_authorization=authorization,
            authorization_payload=b"other",
        )
    ledger = run_persisted_campaign(
        tmp_path,
        plan,
        _ExactBytes({"final": b"out"}),
        source_payloads={("final", "v1"): payload},
        final_authorization=authorization,
        authorization_payload=permit,
    )
    assert ledger.status is CampaignLifecycleStatus.COMPLETED
    assert ledger.authorization_verification is not None
    assert ledger.authorization_verification.observed_sha256 == digest_bytes(permit)
