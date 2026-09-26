"""ITD-30.4 persistent campaign artifacts and incomplete-run lifecycle.

A completed CampaignRunV1 remains the replay contract. This module stores
plans, per-case artifacts and a ledger that can represent interrupted,
blocked and inconclusive campaigns without converting exceptions into
successes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from itd_research.campaign_runner import (
    CampaignCaseV1,
    CampaignPlanV1,
    CampaignRunV1,
    CaseExecutionV1,
    FinalEvaluationAuthorizationV1,
    _assert_case_execution,
)
from itd_research.experiment_schema import (
    ExperimentProtocolV1,
    SourceIdentity,
    SplitRole,
)
from itd_research.result_schema import AdapterIdentityV1, CampaignIdentityV1
from itd_research.source_verification import (
    AuthorizationVerificationV1,
    SourceVerificationV1,
    digest_bytes,
    verify_authorization_bytes,
    verify_source_bytes,
)

LEDGER_VERSION = "itd-campaign-ledger-v1"
PLAN_FILENAME = "plan.json"
LEDGER_FILENAME = "ledger.json"
ARTIFACT_DIRNAME = "artifacts"
OUTPUT_FILENAME = "output.bin"
AUTHORIZATION_FILENAME = "authorization.bin"
SAFE_CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _artifact_relative_path(case_id: str) -> str:
    """Return the canonical artifact path for one safe case identifier."""

    if SAFE_CASE_ID.fullmatch(case_id) is None or case_id in {".", ".."}:
        raise ValueError(
            "case_id used for persistence must be 1-128 ASCII letters, digits, '.', '_' or '-' "
            "and must start with a letter or digit."
        )
    return f"{ARTIFACT_DIRNAME}/{case_id}/{OUTPUT_FILENAME}"


class CampaignLifecycleStatus(StrEnum):
    """Durable status of one persisted campaign directory."""

    INTERRUPTED = "interrupted"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"
    COMPLETED = "completed"


class CampaignHalt(Exception):
    """Evaluator-declared terminal status that is recorded, not converted."""

    def __init__(
        self,
        status: CampaignLifecycleStatus,
        reason: str,
        execution: CaseExecutionV1 | None = None,
        artifact: bytes | None = None,
    ) -> None:
        if status is CampaignLifecycleStatus.COMPLETED:
            raise ValueError("CampaignHalt cannot declare a completed campaign.")
        if not reason.strip():
            raise ValueError("CampaignHalt reason must not be empty.")
        if (execution is None) != (artifact is None):
            raise ValueError("CampaignHalt execution and artifact bytes must be supplied together.")
        self.status = CampaignLifecycleStatus(status)
        self.reason = reason
        self.execution = execution
        self.artifact = artifact
        super().__init__(reason)


@dataclass(frozen=True)
class ArtifactRecordV1:
    """One persisted case artifact bound to its output digest."""

    case_id: str
    relative_path: str
    output_sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        expected = _artifact_relative_path(self.case_id)
        if self.relative_path != expected:
            raise ValueError("artifact path must follow artifacts/<case_id>/output.bin.")
        if self.byte_count < 0:
            raise ValueError("byte_count must be non-negative.")
        digest = self.output_sha256.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("output_sha256 must be a SHA-256 hex digest.")
        object.__setattr__(self, "output_sha256", digest)

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "relative_path": self.relative_path,
            "output_sha256": self.output_sha256,
            "byte_count": self.byte_count,
        }


@dataclass(frozen=True)
class CampaignLedgerV1:
    """Durable record for complete or incomplete campaign execution."""

    plan_fingerprint: str
    status: CampaignLifecycleStatus
    reason: str
    executions: tuple[CaseExecutionV1, ...]
    artifacts: tuple[ArtifactRecordV1, ...]
    source_verifications: tuple[SourceVerificationV1, ...] = ()
    authorization_verification: AuthorizationVerificationV1 | None = None
    ledger_version: str = LEDGER_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", CampaignLifecycleStatus(self.status))
        object.__setattr__(self, "executions", tuple(self.executions))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "source_verifications", tuple(self.source_verifications))
        if self.ledger_version != LEDGER_VERSION:
            raise ValueError("unsupported campaign ledger version.")
        digest = self.plan_fingerprint.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("plan_fingerprint must be a SHA-256 hex digest.")
        object.__setattr__(self, "plan_fingerprint", digest)
        if not self.reason.strip():
            raise ValueError("ledger reason must not be empty.")

        execution_ids = tuple(item.case_id for item in self.executions)
        if len(set(execution_ids)) != len(execution_ids):
            raise ValueError("ledger execution identifiers must be unique.")
        artifact_ids = tuple(item.case_id for item in self.artifacts)
        if len(set(artifact_ids)) != len(artifact_ids):
            raise ValueError("ledger artifact identifiers must be unique.")
        if set(artifact_ids) != set(execution_ids):
            raise ValueError("every execution must have exactly one artifact record.")
        execution_digests = {item.case_id: item.output_sha256 for item in self.executions}
        for artifact in self.artifacts:
            if artifact.output_sha256 != execution_digests[artifact.case_id]:
                raise ValueError("artifact digest must match its execution output_sha256.")
        if self.status is CampaignLifecycleStatus.COMPLETED and not self.executions:
            raise ValueError("completed ledger must contain every planned execution.")

    def as_dict(self) -> dict[str, object]:
        authorization: dict[str, object] | None
        if self.authorization_verification is None:
            authorization = None
        else:
            authorization = self.authorization_verification.as_dict()
        return {
            "ledger_version": self.ledger_version,
            "plan_fingerprint": self.plan_fingerprint,
            "status": self.status.value,
            "reason": self.reason,
            "executions": [item.as_dict() for item in self.executions],
            "artifacts": [item.as_dict() for item in self.artifacts],
            "source_verifications": [item.as_dict() for item in self.source_verifications],
            "authorization_verification": authorization,
        }

    def assert_prefix_of(self, plan: CampaignPlanV1) -> None:
        if self.plan_fingerprint != plan.fingerprint():
            raise ValueError("ledger does not match plan fingerprint.")
        planned = tuple(case.case_id for case in plan.cases)
        observed = tuple(item.case_id for item in self.executions)
        if planned[: len(observed)] != observed:
            raise ValueError("ledger executions are not a prefix of the plan.")
        for case, execution in zip(plan.cases, self.executions, strict=False):
            _assert_case_execution(case, execution)
        if self.status is CampaignLifecycleStatus.COMPLETED and observed != planned:
            raise ValueError("completed ledger must cover the entire plan.")
        if self.status is not CampaignLifecycleStatus.COMPLETED and observed == planned:
            raise ValueError("a full execution cannot use an incomplete lifecycle status.")

    def completed_run(self, plan: CampaignPlanV1) -> CampaignRunV1:
        if self.status is not CampaignLifecycleStatus.COMPLETED:
            raise ValueError("only a completed ledger can produce a campaign run.")
        self.assert_verification_evidence(plan)
        run = CampaignRunV1(
            plan_fingerprint=self.plan_fingerprint,
            executions=self.executions,
        )
        run.assert_replay_of(plan)
        return run

    def assert_verification_evidence(self, plan: CampaignPlanV1) -> None:
        """Require complete, valid source and final-authorization evidence."""

        expected_sources = {
            (case.input_source.source, case.input_source.revision, case.input_source.sha256):
            case.input_source
            for case in plan.cases
        }
        observed_sources: dict[tuple[str, str, str | None], SourceVerificationV1] = {}
        for record in self.source_verifications:
            record.assert_matches_declared_identity()
            key = (record.identity.source, record.identity.revision, record.identity.sha256)
            if key in observed_sources:
                raise ValueError("source verification identities must be unique.")
            observed_sources[key] = record
        if set(observed_sources) != set(expected_sources):
            raise ValueError("source verification evidence must exactly cover plan sources.")

        if any(case.role is SplitRole.FINAL for case in plan.cases):
            if self.authorization_verification is None:
                raise ValueError("final campaign replay requires authorization verification evidence.")
            self.authorization_verification.assert_matches_declared_authorization()
            if (
                self.authorization_verification.protocol_fingerprint
                != plan.campaign.protocol_fingerprint
            ):
                raise ValueError("authorization verification protocol does not match campaign.")
            for case in plan.cases:
                if (
                    case.role is SplitRole.FINAL
                    and self.authorization_verification.final_source != case.input_source
                ):
                    raise ValueError("authorization verification source does not match final case.")


def _source_from_dict(payload: dict[str, object]) -> SourceIdentity:
    sha256 = payload["sha256"]
    return SourceIdentity(
        source=str(payload["source"]),
        revision=str(payload["revision"]),
        sha256=None if sha256 is None else str(sha256),
    )


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


def persist_campaign_plan(root: Path, plan: CampaignPlanV1) -> Path:
    """Write the immutable plan next to later ledger and artifact files."""

    destination = root / PLAN_FILENAME
    if destination.exists():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing != plan.as_dict():
            raise ValueError("campaign directory already contains a different plan.")
        return destination
    _write_json_atomic(destination, plan.as_dict())
    return destination


def persist_campaign_ledger(root: Path, ledger: CampaignLedgerV1) -> Path:
    destination = root / LEDGER_FILENAME
    _write_json_atomic(destination, ledger.as_dict())
    return destination


def load_campaign_plan(root: Path) -> CampaignPlanV1:
    payload = json.loads((root / PLAN_FILENAME).read_text(encoding="utf-8"))
    campaign_payload = payload["campaign"]
    adapters = tuple(
        AdapterIdentityV1(
            ecosystem=str(item["ecosystem"]),
            interface=str(item["interface"]),
            source=_source_from_dict(item["source"]),
        )
        for item in campaign_payload["adapters"]
    )
    campaign = CampaignIdentityV1(
        campaign_id=str(campaign_payload["campaign_id"]),
        protocol_fingerprint=str(campaign_payload["protocol_fingerprint"]),
        implementation=_source_from_dict(campaign_payload["implementation"]),
        adapters=adapters,
    )
    cases = tuple(
        CampaignCaseV1(
            case_id=str(item["case_id"]),
            role=SplitRole(str(item["role"])),
            input_source=_source_from_dict(item["input_source"]),
            work_units=float(item["work_units"]),
        )
        for item in payload["cases"]
    )
    return CampaignPlanV1(
        campaign=campaign,
        cases=cases,
        work_unit=str(payload["work_unit"]),
        maximum_total_work=float(payload["maximum_total_work"]),
        plan_version=str(payload["plan_version"]),
    )


def load_campaign_ledger(root: Path) -> CampaignLedgerV1:
    payload = json.loads((root / LEDGER_FILENAME).read_text(encoding="utf-8"))
    executions = tuple(
        CaseExecutionV1(
            case_id=str(item["case_id"]),
            output_sha256=str(item["output_sha256"]),
            work_units_used=float(item["work_units_used"]),
        )
        for item in payload["executions"]
    )
    artifacts = tuple(
        ArtifactRecordV1(
            case_id=str(item["case_id"]),
            relative_path=str(item["relative_path"]),
            output_sha256=str(item["output_sha256"]),
            byte_count=int(item["byte_count"]),
        )
        for item in payload["artifacts"]
    )
    source_verifications = tuple(
        SourceVerificationV1(
            identity=_source_from_dict(item["identity"]),
            observed_sha256=str(item["observed_sha256"]),
            byte_count=int(item["byte_count"]),
            method=str(item["method"]),
            verification_version=str(item["verification_version"]),
        )
        for item in payload["source_verifications"]
    )
    authorization_payload = payload["authorization_verification"]
    if authorization_payload is None:
        authorization = None
    else:
        authorization = AuthorizationVerificationV1(
            protocol_fingerprint=str(authorization_payload["protocol_fingerprint"]),
            final_source=_source_from_dict(authorization_payload["final_source"]),
            authorization_sha256=str(authorization_payload["authorization_sha256"]),
            observed_sha256=str(authorization_payload["observed_sha256"]),
            byte_count=int(authorization_payload["byte_count"]),
            method=str(authorization_payload["method"]),
            verification_version=str(authorization_payload["verification_version"]),
        )
    return CampaignLedgerV1(
        plan_fingerprint=str(payload["plan_fingerprint"]),
        status=CampaignLifecycleStatus(str(payload["status"])),
        reason=str(payload["reason"]),
        executions=executions,
        artifacts=artifacts,
        source_verifications=source_verifications,
        authorization_verification=authorization,
        ledger_version=str(payload["ledger_version"]),
    )


def persist_case_artifact(root: Path, execution: CaseExecutionV1, payload: bytes) -> ArtifactRecordV1:
    digest = digest_bytes(payload)
    if digest != execution.output_sha256:
        raise ValueError("artifact bytes do not match execution output_sha256.")
    relative = _artifact_relative_path(execution.case_id)
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)
    return ArtifactRecordV1(
        case_id=execution.case_id,
        relative_path=relative,
        output_sha256=digest,
        byte_count=len(payload),
    )


def verify_persisted_artifacts(root: Path, ledger: CampaignLedgerV1) -> None:
    for record in ledger.artifacts:
        path = root / record.relative_path
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing campaign artifact: {record.relative_path}")
        payload = path.read_bytes()
        if len(payload) != record.byte_count:
            raise ValueError(f"artifact size mismatch: {record.relative_path}")
        if digest_bytes(payload) != record.output_sha256:
            raise ValueError(f"artifact digest mismatch: {record.relative_path}")


def persist_authorization_artifact(
    root: Path,
    payload: bytes,
    verification: AuthorizationVerificationV1,
) -> Path:
    """Persist the exact authorization bytes bound by the ledger record."""

    verification.assert_matches_declared_authorization()
    if digest_bytes(payload) != verification.observed_sha256:
        raise ValueError("authorization payload does not match verification evidence.")
    destination = root / AUTHORIZATION_FILENAME
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ValueError("authorization artifact path must be a regular file.")
        if destination.read_bytes() != payload:
            raise ValueError("campaign directory contains a different authorization artifact.")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)
    return destination


def verify_persisted_authorization(root: Path, ledger: CampaignLedgerV1) -> None:
    """Re-hash durable authorization bytes instead of trusting ledger digests."""

    record = ledger.authorization_verification
    if record is None:
        return
    path = root / AUTHORIZATION_FILENAME
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing persisted authorization artifact.")
    payload = path.read_bytes()
    if len(payload) != record.byte_count:
        raise ValueError("persisted authorization artifact size mismatch.")
    if digest_bytes(payload) != record.observed_sha256:
        raise ValueError("persisted authorization artifact digest mismatch.")
    record.assert_matches_declared_authorization()


def verify_plan_sources(
    plan: CampaignPlanV1,
    payloads: dict[tuple[str, str], bytes],
) -> tuple[SourceVerificationV1, ...]:
    """Verify every case source that declared a digest, using supplied bytes."""

    records: list[SourceVerificationV1] = []
    seen: set[tuple[str, str, str | None]] = set()
    for case in plan.cases:
        identity = case.input_source
        key = (identity.source, identity.revision, identity.sha256)
        if key in seen:
            continue
        seen.add(key)
        if identity.sha256 is None:
            raise ValueError("persisted campaigns require declared source digests.")
        payload = payloads.get((identity.source, identity.revision))
        if payload is None:
            raise ValueError(f"missing source bytes for {identity.source}@{identity.revision}.")
        records.append(verify_source_bytes(identity, payload))
    return tuple(records)


class ArtifactEvaluator:
    """Evaluator that also returns the exact artifact bytes for persistence."""

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        raise NotImplementedError


def _invoke_evaluator(
    evaluator: ArtifactEvaluator,
    case: CampaignCaseV1,
) -> tuple[CaseExecutionV1, bytes]:
    return evaluator.evaluate(case)


def run_persisted_campaign(
    root: Path,
    plan: CampaignPlanV1,
    evaluator: ArtifactEvaluator,
    *,
    source_payloads: dict[tuple[str, str], bytes],
    protocol: ExperimentProtocolV1 | None = None,
    final_authorization: FinalEvaluationAuthorizationV1 | None = None,
    authorization_payload: bytes | None = None,
) -> CampaignLedgerV1:
    """Execute a campaign into a directory, including incomplete outcomes.

    Source identities are verified from actual bytes before any case runs.
    Authorization artifact bytes are verified when a final authorization is
    supplied. Evaluator exceptions stay visible after the interrupted ledger
    is written.
    """

    if (root / LEDGER_FILENAME).exists():
        raise ValueError("campaign directory already contains a ledger; use resume for interrupted runs.")
    persist_campaign_plan(root, plan)
    source_verifications = verify_plan_sources(plan, source_payloads)
    authorization_verification: AuthorizationVerificationV1 | None = None
    if final_authorization is not None:
        if authorization_payload is None:
            raise ValueError("final authorization requires artifact bytes, not only its digest.")
        authorization_verification = verify_authorization_bytes(
            final_authorization,
            authorization_payload,
        )
        persist_authorization_artifact(root, authorization_payload, authorization_verification)

    if protocol is not None:
        plan.assert_matches_protocol(protocol)
    plan.assert_final_authorized(final_authorization)

    executions: list[CaseExecutionV1] = []
    artifacts: list[ArtifactRecordV1] = []
    total_work = 0.0

    def _persist(status: CampaignLifecycleStatus, reason: str) -> CampaignLedgerV1:
        ledger = CampaignLedgerV1(
            plan_fingerprint=plan.fingerprint(),
            status=status,
            reason=reason,
            executions=tuple(executions),
            artifacts=tuple(artifacts),
            source_verifications=source_verifications,
            authorization_verification=authorization_verification,
        )
        ledger.assert_prefix_of(plan)
        persist_campaign_ledger(root, ledger)
        verify_persisted_artifacts(root, ledger)
        return ledger

    for case in plan.cases:
        try:
            execution, payload = _invoke_evaluator(evaluator, case)
            _assert_case_execution(case, execution)
            total_work += execution.work_units_used
            if total_work > plan.maximum_total_work:
                raise ValueError("campaign evaluator exceeded maximum_total_work.")
            artifacts.append(persist_case_artifact(root, execution, payload))
            executions.append(execution)
        except CampaignHalt as halt:
            if halt.execution is not None:
                _assert_case_execution(case, halt.execution)
                assert halt.artifact is not None
                artifacts.append(persist_case_artifact(root, halt.execution, halt.artifact))
                executions.append(halt.execution)
            return _persist(halt.status, halt.reason)
        except Exception as error:
            _persist(CampaignLifecycleStatus.INTERRUPTED, f"{type(error).__name__}: {error}")
            raise

    ledger = _persist(CampaignLifecycleStatus.COMPLETED, "all planned cases executed")
    CampaignRunV1(
        plan_fingerprint=plan.fingerprint(),
        executions=tuple(executions),
    ).assert_replay_of(plan)
    return ledger


def resume_persisted_campaign(
    root: Path,
    evaluator: ArtifactEvaluator,
    *,
    source_payloads: dict[tuple[str, str], bytes],
    protocol: ExperimentProtocolV1 | None = None,
    final_authorization: FinalEvaluationAuthorizationV1 | None = None,
    authorization_payload: bytes | None = None,
) -> CampaignLedgerV1:
    """Continue only an interrupted campaign from the next planned case."""

    plan = load_campaign_plan(root)
    existing = load_campaign_ledger(root)
    existing.assert_prefix_of(plan)
    verify_persisted_artifacts(root, existing)
    if existing.status is not CampaignLifecycleStatus.INTERRUPTED:
        raise ValueError("only an interrupted campaign can be resumed.")

    start = len(existing.executions)
    remaining = plan.cases[start:]
    if not remaining:
        raise ValueError("interrupted ledger already covers the plan.")

    source_verifications = verify_plan_sources(plan, source_payloads)
    authorization_verification: AuthorizationVerificationV1 | None = None
    if final_authorization is not None:
        if authorization_payload is None:
            raise ValueError("final authorization requires artifact bytes, not only its digest.")
        authorization_verification = verify_authorization_bytes(
            final_authorization,
            authorization_payload,
        )
        persist_authorization_artifact(root, authorization_payload, authorization_verification)
    if protocol is not None:
        plan.assert_matches_protocol(protocol)
    plan.assert_final_authorized(final_authorization)

    executions = list(existing.executions)
    artifacts = list(existing.artifacts)
    total_work = sum(item.work_units_used for item in executions)

    def _persist(status: CampaignLifecycleStatus, reason: str) -> CampaignLedgerV1:
        ledger = CampaignLedgerV1(
            plan_fingerprint=plan.fingerprint(),
            status=status,
            reason=reason,
            executions=tuple(executions),
            artifacts=tuple(artifacts),
            source_verifications=source_verifications,
            authorization_verification=authorization_verification,
        )
        ledger.assert_prefix_of(plan)
        persist_campaign_ledger(root, ledger)
        verify_persisted_artifacts(root, ledger)
        return ledger

    for case in remaining:
        try:
            execution, payload = _invoke_evaluator(evaluator, case)
            _assert_case_execution(case, execution)
            total_work += execution.work_units_used
            if total_work > plan.maximum_total_work:
                raise ValueError("campaign evaluator exceeded maximum_total_work.")
            artifacts.append(persist_case_artifact(root, execution, payload))
            executions.append(execution)
        except CampaignHalt as halt:
            if halt.execution is not None:
                _assert_case_execution(case, halt.execution)
                assert halt.artifact is not None
                artifacts.append(persist_case_artifact(root, halt.execution, halt.artifact))
                executions.append(halt.execution)
            return _persist(halt.status, halt.reason)
        except Exception as error:
            _persist(CampaignLifecycleStatus.INTERRUPTED, f"{type(error).__name__}: {error}")
            raise

    ledger = _persist(CampaignLifecycleStatus.COMPLETED, "resumed interrupted campaign completed")
    CampaignRunV1(
        plan_fingerprint=plan.fingerprint(),
        executions=tuple(executions),
    ).assert_replay_of(plan)
    return ledger


def completed_run_from_store(root: Path) -> CampaignRunV1:
    plan = load_campaign_plan(root)
    ledger = load_campaign_ledger(root)
    verify_persisted_artifacts(root, ledger)
    verify_persisted_authorization(root, ledger)
    return ledger.completed_run(plan)
