"""Independent ITD Pascal R4 interruption/resume integrity campaign.

R4 is Development/Validation only. It compares uninterrupted campaigns with
prospectively interrupted/resumed executions of the same frozen plan. It does
not import TDI cost/utility conclusions and has no protected/final execution
path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from itd_research.campaign_runner import CampaignCaseV1, CampaignPlanV1, CaseExecutionV1
from itd_research.campaign_store import (
    ArtifactEvaluator,
    CampaignLedgerV1,
    CampaignLifecycleStatus,
    load_campaign_ledger,
    load_campaign_plan,
    resume_persisted_campaign,
    run_persisted_campaign,
    verify_persisted_artifacts,
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
from itd_research.result_schema import CampaignIdentityV1
from itd_research.source_verification import digest_bytes

PASCAL_R4_VERSION = "itd-pascal-r4-interruption-resume-v1"
PASCAL_R4_PREFIXES = (1, 4, 7)
PASCAL_R4_CASES_PER_SPLIT = 8
_GATE_COUNT = 8
_DENSITY = 11
_FINAL_SENTINEL = SourceIdentity(
    source="itd-pascal-protected-final",
    revision="not-opened-no-authorization",
    sha256=None,
)


@dataclass(frozen=True)
class PascalR4Comparison:
    """One exact matched control versus interruption/resume comparison."""

    role: SplitRole
    prefix: int
    clean: bool
    comparison_sha256: str


class PreregisteredR4Interruption(RuntimeError):
    """Deliberate interruption after a frozen persisted prefix."""


def _canonical_json(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _write_canonical_json(path: Path, payload: dict[str, object]) -> bytes:
    encoded = _canonical_json(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(encoded)
    temporary.replace(path)
    return encoded


def pascal_r4_shape(role: SplitRole) -> tuple[int, int]:
    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R4 final source is protected and not authorized.")
    return (7, 128) if resolved is SplitRole.DEVELOPMENT else (9, 512)


def pascal_r4_case_ids(role: SplitRole) -> tuple[str, ...]:
    resolved = SplitRole(role)
    n, _ = pascal_r4_shape(resolved)
    prefix = "dev" if resolved is SplitRole.DEVELOPMENT else "val"
    return tuple(f"{prefix}-n{n}-case-{index:02d}" for index in range(PASCAL_R4_CASES_PER_SPLIT))


def pascal_r4_source_payload(role: SplitRole) -> bytes:
    """Return exact little-endian packed-u16 non-final source bytes."""

    n, domain_size = pascal_r4_shape(role)
    table = [0] * domain_size
    constants = 0
    for gate in range(_GATE_COUNT):
        if gate % 3 == 1:
            constants |= 1 << gate
        terms = tuple(
            1 + ((17 * gate + 31 * index) % (domain_size - 1))
            for index in range(_DENSITY)
        )
        if len(set(terms)) != _DENSITY:
            raise ValueError("Pascal R4 generator produced duplicate terms.")
        lane = 1 << gate
        for term in terms:
            table[term] ^= lane
    table[0] = constants
    for bit in range(n):
        selector = 1 << bit
        for mask in range(domain_size):
            if mask & selector:
                table[mask] ^= table[mask ^ selector]
    return b"".join(word.to_bytes(2, "little", signed=False) for word in table)


def _split_source(role: SplitRole) -> SourceIdentity:
    resolved = SplitRole(role)
    payload = pascal_r4_source_payload(resolved)
    return SourceIdentity(
        source=f"generated:itd-pascal-r4:{resolved.value}",
        revision=PASCAL_R4_VERSION,
        sha256=digest_bytes(payload),
    )


def pascal_r4_protocol() -> ExperimentProtocolV1:
    """Build the prospective R4 protocol without materializing final bytes."""

    implementation = SourceIdentity(
        source="itd_research/pascal_resume_integrity.py",
        revision=PASCAL_R4_VERSION,
        sha256=digest_bytes(Path(__file__).read_bytes()),
    )
    return ExperimentProtocolV1(
        experiment_id="itd-pascal-r4-interruption-resume",
        hypothesis=HypothesisContract(
            hypothesis_id="ITD-PASCAL-R4-H1",
            statement=(
                "An interrupted non-final Pascal campaign resumes from its exact "
                "persisted prefix without changing identities, artifact bytes, or outcome."
            ),
            comparison=(
                "Each interrupted/resumed arm is compared exactly with an uninterrupted "
                "control executing the identical frozen plan and source bytes."
            ),
        ),
        implementation=implementation,
        splits=(
            SplitIdentity(SplitRole.DEVELOPMENT, _split_source(SplitRole.DEVELOPMENT)),
            SplitIdentity(SplitRole.VALIDATION, _split_source(SplitRole.VALIDATION)),
            SplitIdentity(SplitRole.FINAL, _FINAL_SENTINEL),
        ),
        metrics=(
            MetricContract(
                name="matched_artifact_equality",
                role=MetricRole.PRIMARY,
                direction=MetricDirection.DESCRIPTIVE,
                unit="boolean",
            ),
            MetricContract(
                name="duplicate_or_skipped_cases",
                role=MetricRole.DIAGNOSTIC,
                direction=MetricDirection.DESCRIPTIVE,
                unit="count",
            ),
        ),
        compute_budget=ComputeBudget(
            unit="resume_integrity_case",
            maximum=float(PASCAL_R4_CASES_PER_SPLIT),
        ),
        uncertainty=UncertaintyContract(
            method="exact_paired_persistence_comparison_no_sampling_interval",
            confidence_level=0.95,
            paired=True,
        ),
    )


def pascal_r4_plan(
    role: SplitRole,
    protocol: ExperimentProtocolV1 | None = None,
) -> CampaignPlanV1:
    """Return the same frozen plan for control and all resumed arms of one split."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R4 final plan is protected and not authorized.")
    frozen_protocol = pascal_r4_protocol() if protocol is None else protocol
    campaign = CampaignIdentityV1.from_protocol(
        f"itd-pascal-r4-{resolved.value}-campaign",
        frozen_protocol,
        implementation=frozen_protocol.implementation,
    )
    source = frozen_protocol.split(resolved).source
    cases = tuple(
        CampaignCaseV1(
            case_id=case_id,
            role=resolved,
            input_source=source,
            work_units=1.0,
        )
        for case_id in pascal_r4_case_ids(resolved)
    )
    plan = CampaignPlanV1(
        campaign=campaign,
        cases=cases,
        work_unit="resume_integrity_case",
        maximum_total_work=float(PASCAL_R4_CASES_PER_SPLIT),
    )
    plan.assert_matches_protocol(frozen_protocol)
    return plan


def pascal_r4_source_payloads(role: SplitRole) -> dict[tuple[str, str], bytes]:
    resolved = SplitRole(role)
    source = _split_source(resolved)
    return {(source.source, source.revision): pascal_r4_source_payload(resolved)}


def _case_artifact(
    case: CampaignCaseV1,
    source: bytes,
    plan_fingerprint: str,
) -> bytes:
    case_ids = pascal_r4_case_ids(case.role)
    try:
        index = case_ids.index(case.case_id)
    except ValueError as error:
        raise ValueError("Pascal R4 case is not part of the frozen plan.") from error

    sample_width = 32
    start = (29 * index) % len(source)
    doubled = source + source
    sample = doubled[start : start + sample_width]
    return _canonical_json(
        {
            "version": PASCAL_R4_VERSION,
            "case_id": case.case_id,
            "role": case.role.value,
            "plan_fingerprint": plan_fingerprint,
            "source_sha256": digest_bytes(source),
            "source_byte_count": len(source),
            "sample_sha256": digest_bytes(sample),
            "case_payload_sha256": digest_bytes(source + case.case_id.encode("ascii")),
        }
    )


class PascalR4Evaluator(ArtifactEvaluator):
    """Deterministic evaluator with exact per-case execution counts."""

    def __init__(
        self,
        source_payloads: dict[tuple[str, str], bytes],
        plan_fingerprint: str,
    ) -> None:
        self._source_payloads = dict(source_payloads)
        self._plan_fingerprint = plan_fingerprint
        self.calls: dict[str, int] = {}

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        key = (case.input_source.source, case.input_source.revision)
        source = self._source_payloads.get(key)
        if source is None:
            raise ValueError("Pascal R4 verified source payload is unavailable.")
        if digest_bytes(source) != case.input_source.sha256:
            raise ValueError("Pascal R4 source bytes drifted after verification.")
        if case.case_id not in pascal_r4_case_ids(case.role):
            raise ValueError("Pascal R4 case is not part of the frozen plan.")

        self.calls[case.case_id] = self.calls.get(case.case_id, 0) + 1
        artifact = _case_artifact(case, source, self._plan_fingerprint)
        return (
            CaseExecutionV1(
                case_id=case.case_id,
                output_sha256=digest_bytes(artifact),
                work_units_used=1.0,
            ),
            artifact,
        )


class InterruptAfterPrefix(ArtifactEvaluator):
    """Raise before the first case after the frozen completed prefix."""

    def __init__(self, evaluator: PascalR4Evaluator, prefix: int) -> None:
        if prefix not in PASCAL_R4_PREFIXES:
            raise ValueError("Pascal R4 interruption prefix is not preregistered.")
        self._evaluator = evaluator
        self._prefix = prefix
        self._observed = 0

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        if self._observed == self._prefix:
            raise PreregisteredR4Interruption(
                f"preregistered interruption after persisted prefix {self._prefix}"
            )
        execution = self._evaluator.evaluate(case)
        self._observed += 1
        return execution


def _artifact_bytes(root: Path, ledger: CampaignLedgerV1) -> dict[str, bytes]:
    return {
        record.case_id: (root / record.relative_path).read_bytes()
        for record in ledger.artifacts
    }


def _ledger_bytes(root: Path) -> bytes:
    return (root / "ledger.json").read_bytes()


def _run_interrupted_prefix(
    root: Path,
    plan: CampaignPlanV1,
    protocol: ExperimentProtocolV1,
    payloads: dict[tuple[str, str], bytes],
    prefix: int,
) -> tuple[PascalR4Evaluator, CampaignLedgerV1, dict[str, bytes], bytes]:
    evaluator = PascalR4Evaluator(payloads, plan.fingerprint())
    try:
        run_persisted_campaign(
            root,
            plan,
            InterruptAfterPrefix(evaluator, prefix),
            source_payloads=payloads,
            protocol=protocol,
        )
    except PreregisteredR4Interruption:
        pass
    else:
        raise AssertionError("Pascal R4 preregistered interruption did not occur.")

    ledger = load_campaign_ledger(root)
    ledger.assert_prefix_of(plan)
    verify_persisted_artifacts(root, ledger)
    if ledger.status is not CampaignLifecycleStatus.INTERRUPTED:
        raise AssertionError("Pascal R4 prefix ledger is not interrupted.")
    if len(ledger.executions) != prefix:
        raise AssertionError("Pascal R4 interrupted ledger has the wrong prefix length.")
    expected_prefix = pascal_r4_case_ids(plan.cases[0].role)[:prefix]
    observed_prefix = tuple(item.case_id for item in ledger.executions)
    if observed_prefix != expected_prefix:
        raise AssertionError("Pascal R4 interrupted ledger changed frozen case order.")
    return evaluator, ledger, _artifact_bytes(root, ledger), _ledger_bytes(root)


def _compare_completed_arm(
    *,
    role: SplitRole,
    prefix: int,
    plan: CampaignPlanV1,
    control_root: Path,
    arm_root: Path,
    prefix_artifacts: dict[str, bytes],
    pre_resume_ledger: bytes,
    evaluator: PascalR4Evaluator,
) -> PascalR4Comparison:
    control_plan = load_campaign_plan(control_root)
    arm_plan = load_campaign_plan(arm_root)
    control = load_campaign_ledger(control_root)
    resumed = load_campaign_ledger(arm_root)
    verify_persisted_artifacts(control_root, control)
    verify_persisted_artifacts(arm_root, resumed)
    control.completed_run(control_plan)
    resumed.completed_run(arm_plan)

    control_ids = tuple(item.case_id for item in control.executions)
    resumed_ids = tuple(item.case_id for item in resumed.executions)
    control_outputs = tuple(item.output_sha256 for item in control.executions)
    resumed_outputs = tuple(item.output_sha256 for item in resumed.executions)
    control_artifacts = _artifact_bytes(control_root, control)
    resumed_artifacts = _artifact_bytes(arm_root, resumed)
    prefix_unchanged = all(
        resumed_artifacts[case_id] == payload for case_id, payload in prefix_artifacts.items()
    )
    exact_once = all(
        evaluator.calls.get(case_id, 0) == 1 for case_id in pascal_r4_case_ids(role)
    )
    source_equal = (
        tuple(item.as_dict() for item in control.source_verifications)
        == tuple(item.as_dict() for item in resumed.source_verifications)
    )

    pre_digest = digest_bytes(pre_resume_ledger)
    post_digest = digest_bytes(_ledger_bytes(arm_root))
    event_core: dict[str, object] = {
        "version": PASCAL_R4_VERSION,
        "role": role.value,
        "prefix": prefix,
        "plan_fingerprint": plan.fingerprint(),
        "pre_resume_ledger_sha256": pre_digest,
        "post_resume_ledger_sha256": post_digest,
    }
    resume_event_id = digest_bytes(_canonical_json(event_core))

    checks: dict[str, bool] = {
        "plan_fingerprint_equal": control.plan_fingerprint == resumed.plan_fingerprint == plan.fingerprint(),
        "protocol_fingerprint_equal": (
            control_plan.campaign.protocol_fingerprint
            == arm_plan.campaign.protocol_fingerprint
            == plan.campaign.protocol_fingerprint
        ),
        "ordered_case_ids_equal": control_ids == resumed_ids == pascal_r4_case_ids(role),
        "per_case_output_sha256_equal": control_outputs == resumed_outputs,
        "artifact_bytes_equal": control_artifacts == resumed_artifacts,
        "source_verification_equal": source_equal,
        "completed_after_resume": resumed.status is CampaignLifecycleStatus.COMPLETED,
        "no_duplicate_or_skipped_execution": exact_once,
        "persisted_prefix_artifacts_unchanged": prefix_unchanged,
    }
    comparison_payload: dict[str, object] = {
        **event_core,
        "resume_event_id": resume_event_id,
        "checks": checks,
        "control_ledger_sha256": digest_bytes(_ledger_bytes(control_root)),
        "resumed_ledger_sha256": post_digest,
        "control_case_output_sha256": list(control_outputs),
        "resumed_case_output_sha256": list(resumed_outputs),
        "evaluator_call_counts": dict(sorted(evaluator.calls.items())),
        "outcome": "pass" if all(checks.values()) else "negative",
    }
    encoded = _write_canonical_json(arm_root / "comparison.json", comparison_payload)
    return PascalR4Comparison(
        role=role,
        prefix=prefix,
        clean=all(checks.values()),
        comparison_sha256=digest_bytes(encoded),
    )


def run_pascal_r4_split(root: Path, role: SplitRole) -> tuple[PascalR4Comparison, ...]:
    """Execute one frozen non-final split: control plus all interruption arms."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R4 final execution is protected and not authorized.")
    protocol = pascal_r4_protocol()
    plan = pascal_r4_plan(resolved, protocol)
    payloads = pascal_r4_source_payloads(resolved)

    control_root = root / resolved.value / "control"
    control_evaluator = PascalR4Evaluator(payloads, plan.fingerprint())
    control = run_persisted_campaign(
        control_root,
        plan,
        control_evaluator,
        source_payloads=payloads,
        protocol=protocol,
    )
    if control.status is not CampaignLifecycleStatus.COMPLETED:
        raise AssertionError("Pascal R4 matched control did not complete.")
    if any(control_evaluator.calls.get(case_id, 0) != 1 for case_id in pascal_r4_case_ids(resolved)):
        raise AssertionError("Pascal R4 control duplicated or skipped a case.")

    comparisons: list[PascalR4Comparison] = []
    for prefix in PASCAL_R4_PREFIXES:
        arm_root = root / resolved.value / f"resume-{prefix}"
        evaluator, _, prefix_artifacts, pre_resume_ledger = _run_interrupted_prefix(
            arm_root,
            plan,
            protocol,
            payloads,
            prefix,
        )
        resumed = resume_persisted_campaign(
            arm_root,
            evaluator,
            source_payloads=payloads,
            protocol=protocol,
        )
        if resumed.status is not CampaignLifecycleStatus.COMPLETED:
            raise AssertionError("Pascal R4 resumed arm did not complete.")
        comparisons.append(
            _compare_completed_arm(
                role=resolved,
                prefix=prefix,
                plan=plan,
                control_root=control_root,
                arm_root=arm_root,
                prefix_artifacts=prefix_artifacts,
                pre_resume_ledger=pre_resume_ledger,
                evaluator=evaluator,
            )
        )

    summary_payload: dict[str, object] = {
        "version": PASCAL_R4_VERSION,
        "role": resolved.value,
        "protocol_fingerprint": plan.campaign.protocol_fingerprint,
        "plan_fingerprint": plan.fingerprint(),
        "source_sha256": protocol.split(resolved).source.sha256,
        "comparisons": [
            {
                "prefix": item.prefix,
                "clean": item.clean,
                "comparison_sha256": item.comparison_sha256,
            }
            for item in comparisons
        ],
        "outcome": "pass" if all(item.clean for item in comparisons) else "negative",
    }
    _write_canonical_json(root / resolved.value / "summary.json", summary_payload)
    return tuple(comparisons)


def _record_probe_error(
    root: Path,
    probe: str,
    prefix: int,
    error: Exception,
    evaluator: PascalR4Evaluator,
) -> str:
    ledger = load_campaign_ledger(root)
    payload: dict[str, object] = {
        "version": PASCAL_R4_VERSION,
        "probe": probe,
        "outcome": "integrity_error",
        "error_type": type(error).__name__,
        "error": str(error),
        "ledger_status": ledger.status.value,
        "persisted_prefix_length": len(ledger.executions),
        "evaluator_call_counts": dict(sorted(evaluator.calls.items())),
        "additional_case_executions_after_probe": max(0, sum(evaluator.calls.values()) - prefix),
    }
    encoded = _write_canonical_json(root / "integrity-error.json", payload)
    return digest_bytes(encoded)


def run_pascal_r4_probes(root: Path) -> dict[str, str]:
    """Execute preregistered fail-closed provenance probes on Development only."""

    protocol = pascal_r4_protocol()
    role = SplitRole.DEVELOPMENT
    plan = pascal_r4_plan(role, protocol)
    payloads = pascal_r4_source_payloads(role)
    prefix = 1
    outcomes: dict[str, str] = {}

    source_root = root / "source-drift"
    evaluator, _, _, _ = _run_interrupted_prefix(
        source_root, plan, protocol, payloads, prefix
    )
    drifted = dict(payloads)
    key = next(iter(drifted))
    changed = bytearray(drifted[key])
    changed[0] ^= 1
    drifted[key] = bytes(changed)
    try:
        resume_persisted_campaign(
            source_root,
            evaluator,
            source_payloads=drifted,
            protocol=protocol,
        )
    except ValueError as error:
        outcomes["source_drift"] = _record_probe_error(
            source_root, "source_drift", prefix, error, evaluator
        )
    else:
        raise AssertionError("Pascal R4 source-drift probe did not fail closed.")

    artifact_root = root / "artifact-drift"
    evaluator, ledger, _, _ = _run_interrupted_prefix(
        artifact_root, plan, protocol, payloads, prefix
    )
    artifact_path = artifact_root / ledger.artifacts[0].relative_path
    artifact_path.write_bytes(artifact_path.read_bytes() + b"\x00")
    try:
        resume_persisted_campaign(
            artifact_root,
            evaluator,
            source_payloads=payloads,
            protocol=protocol,
        )
    except ValueError as error:
        outcomes["artifact_drift"] = _record_probe_error(
            artifact_root, "artifact_drift", prefix, error, evaluator
        )
    else:
        raise AssertionError("Pascal R4 artifact-drift probe did not fail closed.")

    plan_root = root / "plan-drift"
    evaluator, _, _, _ = _run_interrupted_prefix(
        plan_root, plan, protocol, payloads, prefix
    )
    plan_path = plan_root / "plan.json"
    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_payload["maximum_total_work"] = float(PASCAL_R4_CASES_PER_SPLIT + 1)
    plan_path.write_text(
        json.dumps(plan_payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    try:
        resume_persisted_campaign(
            plan_root,
            evaluator,
            source_payloads=payloads,
            protocol=protocol,
        )
    except ValueError as error:
        outcomes["plan_drift"] = _record_probe_error(
            plan_root, "plan_drift", prefix, error, evaluator
        )
    else:
        raise AssertionError("Pascal R4 plan-drift probe did not fail closed.")

    _write_canonical_json(
        root / "summary.json",
        {
            "version": PASCAL_R4_VERSION,
            "role": role.value,
            "probe_record_sha256": dict(sorted(outcomes.items())),
            "outcome": "pass" if len(outcomes) == 3 else "inconclusive",
        },
    )
    return outcomes


def run_pascal_r4(root: Path) -> dict[str, object]:
    """Execute the complete preregistered non-final R4 campaign exactly once."""

    if root.exists() and any(root.iterdir()):
        raise ValueError("Pascal R4 evidence root already exists; refusing a fresh rerun.")
    root.mkdir(parents=True, exist_ok=True)

    development = run_pascal_r4_split(root, SplitRole.DEVELOPMENT)
    validation = run_pascal_r4_split(root, SplitRole.VALIDATION)
    probes = run_pascal_r4_probes(root / "probes")

    payload: dict[str, object] = {
        "version": PASCAL_R4_VERSION,
        "development": [
            {
                "prefix": item.prefix,
                "clean": item.clean,
                "comparison_sha256": item.comparison_sha256,
            }
            for item in development
        ],
        "validation": [
            {
                "prefix": item.prefix,
                "clean": item.clean,
                "comparison_sha256": item.comparison_sha256,
            }
            for item in validation
        ],
        "probe_record_sha256": dict(sorted(probes.items())),
        "outcome": (
            "pass"
            if all(item.clean for item in development + validation) and len(probes) == 3
            else "negative"
        ),
    }
    encoded = _write_canonical_json(root / "r4-summary.json", payload)
    return {
        **payload,
        "r4_summary_sha256": digest_bytes(encoded),
    }
