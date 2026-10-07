"""Independent ITD Pascal R5 cold-process relocation/replay integrity support.

R5 is Development/Validation only.  This module freezes source, plan, relocation
and replay semantics without importing any TDI cost/utility conclusion.  It has
no protected/final execution path.
"""

from __future__ import annotations

import json
import shutil
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

PASCAL_R5_VERSION = "itd-pascal-r5-cold-relocation-v1"
PASCAL_R5_PREFIXES = (2, 5)
PASCAL_R5_CASES_PER_SPLIT = 6
PASCAL_R5_DESTINATIONS = {
    2: "relocated-after-02",
    5: "relocated-after-05",
}
_GATE_COUNT = 6
_DENSITY = 7
_SOURCE_FILENAME = "source.bin"
_FINAL_SENTINEL = SourceIdentity(
    source="itd-pascal-protected-final",
    revision="not-opened-no-authorization",
    sha256=None,
)


@dataclass(frozen=True)
class PascalR5Comparison:
    """Exact comparison of one relocated arm against its split-matched control."""

    role: SplitRole
    prefix: int
    clean: bool
    comparison_sha256: str


class PreregisteredR5Interruption(RuntimeError):
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


def pascal_r5_shape(role: SplitRole) -> tuple[int, int]:
    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R5 final source is protected and not authorized.")
    return (6, 64) if resolved is SplitRole.DEVELOPMENT else (11, 2048)


def pascal_r5_case_ids(role: SplitRole) -> tuple[str, ...]:
    resolved = SplitRole(role)
    n, _ = pascal_r5_shape(resolved)
    prefix = "dev" if resolved is SplitRole.DEVELOPMENT else "val"
    return tuple(
        f"{prefix}-n{n}-relocation-case-{index:02d}"
        for index in range(PASCAL_R5_CASES_PER_SPLIT)
    )


def pascal_r5_source_payload(role: SplitRole) -> bytes:
    """Return exact little-endian packed-u16 non-final source bytes."""

    n, domain_size = pascal_r5_shape(role)
    table = [0] * domain_size
    constants = 0
    for gate in range(_GATE_COUNT):
        if gate % 2 == 0:
            constants |= 1 << gate
        terms = tuple(
            1 + ((23 * gate + 29 * index) % (domain_size - 1))
            for index in range(_DENSITY)
        )
        if len(set(terms)) != _DENSITY:
            raise ValueError("Pascal R5 generator produced duplicate terms.")
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
    payload = pascal_r5_source_payload(resolved)
    return SourceIdentity(
        source=f"generated:itd-pascal-r5:{resolved.value}",
        revision=PASCAL_R5_VERSION,
        sha256=digest_bytes(payload),
    )


def pascal_r5_protocol() -> ExperimentProtocolV1:
    """Build the prospective R5 protocol without materializing final bytes."""

    implementation = SourceIdentity(
        source="itd_research/pascal_relocation_integrity.py",
        revision=PASCAL_R5_VERSION,
        sha256=digest_bytes(Path(__file__).read_bytes()),
    )
    return ExperimentProtocolV1(
        experiment_id="itd-pascal-r5-cold-relocation",
        hypothesis=HypothesisContract(
            hypothesis_id="ITD-PASCAL-R5-H1",
            statement=(
                "A persisted non-final Pascal campaign can be relocated and "
                "resumed without changing scientific identities or persisted evidence."
            ),
            comparison=(
                "Each cold-relocated arm is compared exactly with an uninterrupted "
                "split-matched control using the same frozen plan and source bytes."
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
                name="relocated_artifact_equality",
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
            unit="relocation_integrity_case",
            maximum=float(PASCAL_R5_CASES_PER_SPLIT),
        ),
        uncertainty=UncertaintyContract(
            method="exact_paired_relocation_comparison_no_sampling_interval",
            confidence_level=0.95,
            paired=True,
        ),
    )


def pascal_r5_plan(
    role: SplitRole,
    protocol: ExperimentProtocolV1 | None = None,
) -> CampaignPlanV1:
    """Return the frozen six-case plan for one non-final split."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R5 final plan is protected and not authorized.")
    frozen_protocol = pascal_r5_protocol() if protocol is None else protocol
    campaign = CampaignIdentityV1.from_protocol(
        f"itd-pascal-r5-{resolved.value}-campaign",
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
        for case_id in pascal_r5_case_ids(resolved)
    )
    plan = CampaignPlanV1(
        campaign=campaign,
        cases=cases,
        work_unit="relocation_integrity_case",
        maximum_total_work=float(PASCAL_R5_CASES_PER_SPLIT),
    )
    plan.assert_matches_protocol(frozen_protocol)
    return plan


def pascal_r5_source_payloads(role: SplitRole) -> dict[tuple[str, str], bytes]:
    resolved = SplitRole(role)
    source = _split_source(resolved)
    return {(source.source, source.revision): pascal_r5_source_payload(resolved)}


def _case_artifact(
    case: CampaignCaseV1,
    source: bytes,
    plan_fingerprint: str,
) -> bytes:
    case_ids = pascal_r5_case_ids(case.role)
    try:
        index = case_ids.index(case.case_id)
    except ValueError as error:
        raise ValueError("Pascal R5 case is not part of the frozen plan.") from error

    sample_width = 40
    start = (37 * index + 5) % len(source)
    doubled = source + source
    sample = doubled[start : start + sample_width]
    return _canonical_json(
        {
            "version": PASCAL_R5_VERSION,
            "case_id": case.case_id,
            "role": case.role.value,
            "plan_fingerprint": plan_fingerprint,
            "source_sha256": digest_bytes(source),
            "source_byte_count": len(source),
            "sample_sha256": digest_bytes(sample),
            "case_payload_sha256": digest_bytes(
                source + b"\x00" + case.case_id.encode("ascii")
            ),
        }
    )


class PascalR5Evaluator(ArtifactEvaluator):
    """Deterministic evaluator whose artifacts contain no storage-root identity."""

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
            raise ValueError("Pascal R5 verified source payload is unavailable.")
        if digest_bytes(source) != case.input_source.sha256:
            raise ValueError("Pascal R5 source bytes drifted after verification.")
        if case.case_id not in pascal_r5_case_ids(case.role):
            raise ValueError("Pascal R5 case is not part of the frozen plan.")

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


class InterruptAfterR5Prefix(ArtifactEvaluator):
    """Raise before the first case after one preregistered relocation boundary."""

    def __init__(self, evaluator: PascalR5Evaluator, prefix: int) -> None:
        if prefix not in PASCAL_R5_PREFIXES:
            raise ValueError("Pascal R5 interruption prefix is not preregistered.")
        self._evaluator = evaluator
        self._prefix = prefix
        self._observed = 0

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        if self._observed == self._prefix:
            raise PreregisteredR5Interruption(
                f"preregistered relocation boundary after persisted prefix {self._prefix}"
            )
        execution = self._evaluator.evaluate(case)
        self._observed += 1
        return execution


def _persist_source(root: Path, payload: bytes) -> Path:
    destination = root / _SOURCE_FILENAME
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ValueError("Pascal R5 source path must be a regular file.")
        if destination.read_bytes() != payload:
            raise ValueError("Pascal R5 persisted source bytes differ.")
        return destination
    root.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination


def _payloads_from_persisted_source(
    root: Path,
    role: SplitRole,
    protocol: ExperimentProtocolV1,
) -> dict[tuple[str, str], bytes]:
    source_path = root / _SOURCE_FILENAME
    if source_path.is_symlink() or not source_path.is_file():
        raise ValueError("Pascal R5 persisted source bytes are missing.")
    payload = source_path.read_bytes()
    identity = protocol.split(role).source
    if identity.sha256 is None or digest_bytes(payload) != identity.sha256:
        raise ValueError("Pascal R5 persisted source digest mismatch.")
    return {(identity.source, identity.revision): payload}


def run_pascal_r5_control(root: Path, role: SplitRole) -> CampaignLedgerV1:
    """Execute one uninterrupted non-final matched control."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R5 final execution is protected and not authorized.")
    protocol = pascal_r5_protocol()
    plan = pascal_r5_plan(resolved, protocol)
    payloads = pascal_r5_source_payloads(resolved)
    _persist_source(root, next(iter(payloads.values())))
    evaluator = PascalR5Evaluator(payloads, plan.fingerprint())
    ledger = run_persisted_campaign(
        root,
        plan,
        evaluator,
        source_payloads=payloads,
        protocol=protocol,
    )
    if ledger.status is not CampaignLifecycleStatus.COMPLETED:
        raise AssertionError("Pascal R5 control did not complete.")
    return ledger


def prepare_pascal_r5_relocation(
    original_root: Path,
    relocated_root: Path,
    role: SplitRole,
    prefix: int,
) -> tuple[str, str]:
    """Freeze a prefix, then copy its exact persisted bytes to the fixed new root."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R5 final execution is protected and not authorized.")
    if PASCAL_R5_DESTINATIONS.get(prefix) != relocated_root.name:
        raise ValueError("Pascal R5 relocation destination is not preregistered.")
    if original_root.resolve() == relocated_root.resolve():
        raise ValueError("Pascal R5 relocation root must differ from the original root.")
    if relocated_root.exists():
        raise ValueError("Pascal R5 relocation destination already exists.")

    protocol = pascal_r5_protocol()
    plan = pascal_r5_plan(resolved, protocol)
    payloads = pascal_r5_source_payloads(resolved)
    _persist_source(original_root, next(iter(payloads.values())))
    evaluator = PascalR5Evaluator(payloads, plan.fingerprint())
    try:
        run_persisted_campaign(
            original_root,
            plan,
            InterruptAfterR5Prefix(evaluator, prefix),
            source_payloads=payloads,
            protocol=protocol,
        )
    except PreregisteredR5Interruption:
        pass
    else:
        raise AssertionError("Pascal R5 preregistered interruption did not occur.")

    ledger = load_campaign_ledger(original_root)
    ledger.assert_prefix_of(plan)
    verify_persisted_artifacts(original_root, ledger)
    if ledger.status is not CampaignLifecycleStatus.INTERRUPTED:
        raise AssertionError("Pascal R5 relocation boundary is not interrupted.")
    if len(ledger.executions) != prefix:
        raise AssertionError("Pascal R5 relocation boundary has wrong prefix length.")

    before = _tree_fingerprint(original_root)
    shutil.copytree(original_root, relocated_root, symlinks=True)
    after = _tree_fingerprint(relocated_root)
    if before != after:
        raise AssertionError("Pascal R5 relocation changed persisted bytes.")
    return before, after


def _tree_fingerprint(root: Path) -> str:
    entries: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.is_symlink():
            raise ValueError("Pascal R5 evidence tree must not contain symlinks.")
        relative = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "sha256": digest_bytes(payload),
                "byte_count": len(payload),
            }
        )
    return digest_bytes(_canonical_json({"files": entries}))


def verify_pascal_r5_namespace(root: Path) -> None:
    """Reject undeclared files in the persisted campaign namespace before resume."""

    plan = load_campaign_plan(root)
    ledger = load_campaign_ledger(root)
    ledger.assert_prefix_of(plan)
    expected = {"plan.json", "ledger.json", _SOURCE_FILENAME}
    expected.update(record.relative_path for record in ledger.artifacts)
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    unexpected = sorted(observed - expected)
    missing = sorted(expected - observed)
    if unexpected:
        raise ValueError(f"Pascal R5 undeclared persisted artifact(s): {unexpected}")
    if missing:
        raise ValueError(f"Pascal R5 required persisted artifact(s) missing: {missing}")
    verify_persisted_artifacts(root, ledger)


def resume_pascal_r5_relocated(root: Path, role: SplitRole) -> CampaignLedgerV1:
    """Resume a relocated arm; intended to be invoked by a fresh process."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R5 final execution is protected and not authorized.")
    verify_pascal_r5_namespace(root)
    protocol = pascal_r5_protocol()
    plan = load_campaign_plan(root)
    expected_plan = pascal_r5_plan(resolved, protocol)
    if plan.fingerprint() != expected_plan.fingerprint():
        raise ValueError("Pascal R5 relocated plan fingerprint changed.")
    payloads = _payloads_from_persisted_source(root, resolved, protocol)
    evaluator = PascalR5Evaluator(payloads, plan.fingerprint())
    ledger = resume_persisted_campaign(
        root,
        evaluator,
        source_payloads=payloads,
        protocol=protocol,
    )
    if ledger.status is not CampaignLifecycleStatus.COMPLETED:
        raise AssertionError("Pascal R5 relocated arm did not complete.")
    return ledger


def _main() -> int:
    """Fresh-process resume entry point used by the R5 execution harness."""

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("resume", choices=("resume",))
    parser.add_argument("--root", required=True)
    parser.add_argument("--role", required=True, choices=("development", "validation"))
    args = parser.parse_args()
    role = SplitRole(args.role)
    ledger = resume_pascal_r5_relocated(Path(args.root), role)
    print(digest_bytes(_canonical_json(ledger.as_dict())))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())