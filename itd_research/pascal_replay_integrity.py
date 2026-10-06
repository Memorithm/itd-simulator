"""Independent Pascal serialization/replay integrity campaign for ITD.

R3 is Development/Validation only. It tests exact serialization, chunking,
persistence and replay of a deterministic packed-u16 Pascal/subset-zeta table.
It is independent of TDI's cost/utility programme and does not authorize final
or model-side work.
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
    persist_campaign_ledger,
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

PASCAL_R3_VERSION = "itd-pascal-r3-serialization-replay-v1"
PASCAL_R3_GATE_COUNT = 10
PASCAL_R3_DENSITY = 17
PASCAL_R3_CASE_COUNT = 32

_BYTE_ORDERS = ("little", "big")
_CHUNK_WIDTHS = (1, 3, 7, 31)
_REPLAY_COUNTS = (1, 2)
_FINAL_SENTINEL = SourceIdentity(
    source="itd-pascal-protected-final",
    revision="not-opened-no-authorization",
    sha256=None,
)


@dataclass(frozen=True)
class PascalR3CaseSpec:
    """Frozen non-final geometry for one serialization/replay case."""

    case_id: str
    role: SplitRole
    variable_count: int
    byte_order: str
    chunk_width: int
    replay_count: int


def _canonical_json(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _gate_terms(variable_count: int) -> tuple[tuple[int, ...], ...]:
    """Return the independent R3 ANF bank fixed before R3 execution."""

    domain_size = 1 << variable_count
    banks: list[tuple[int, ...]] = []
    for gate in range(PASCAL_R3_GATE_COUNT):
        terms = tuple(
            1 + ((29 * gate + 43 * index) % (domain_size - 1))
            for index in range(PASCAL_R3_DENSITY)
        )
        if len(set(terms)) != PASCAL_R3_DENSITY:
            raise ValueError("Pascal R3 generator produced duplicate ANF terms.")
        banks.append(terms)
    return tuple(banks)


def _constant_word() -> int:
    word = 0
    for gate in range(PASCAL_R3_GATE_COUNT):
        if gate % 4 == 2:
            word |= 1 << gate
    return word


def _canonical_table(variable_count: int) -> tuple[int, ...]:
    domain_size = 1 << variable_count
    table = [0] * domain_size
    table[0] = _constant_word()
    for gate, terms in enumerate(_gate_terms(variable_count)):
        lane = 1 << gate
        for term in terms:
            table[term] ^= lane
    for bit in range(variable_count):
        selector = 1 << bit
        for mask in range(domain_size):
            if mask & selector:
                table[mask] ^= table[mask ^ selector]
    return tuple(table)


def _words_to_bytes(words: tuple[int, ...] | list[int], byte_order: str) -> bytes:
    if byte_order not in _BYTE_ORDERS:
        raise ValueError(f"unknown R3 byte order: {byte_order}")
    return b"".join(word.to_bytes(2, byteorder=byte_order, signed=False) for word in words)


def _bytes_to_words(payload: bytes, byte_order: str) -> tuple[int, ...]:
    if len(payload) % 2:
        raise ValueError("packed-u16 payload must contain an even number of bytes.")
    if byte_order not in _BYTE_ORDERS:
        raise ValueError(f"unknown R3 byte order: {byte_order}")
    return tuple(
        int.from_bytes(payload[offset : offset + 2], byteorder=byte_order, signed=False)
        for offset in range(0, len(payload), 2)
    )


def pascal_r3_split_payload(role: SplitRole) -> bytes:
    """Return exact canonical little-endian source bytes for a non-final split."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R3 final source is protected and not authorized.")
    variable_count = 8 if resolved is SplitRole.DEVELOPMENT else 10
    return _words_to_bytes(_canonical_table(variable_count), "little")


def _split_source(role: SplitRole) -> SourceIdentity:
    payload = pascal_r3_split_payload(role)
    return SourceIdentity(
        source=f"generated:itd-pascal-r3:{SplitRole(role).value}",
        revision=PASCAL_R3_VERSION,
        sha256=digest_bytes(payload),
    )


def pascal_r3_protocol() -> ExperimentProtocolV1:
    """Build the prospective R3 protocol without opening final bytes."""

    implementation_bytes = Path(__file__).read_bytes()
    implementation = SourceIdentity(
        source="itd_research/pascal_replay_integrity.py",
        revision=PASCAL_R3_VERSION,
        sha256=digest_bytes(implementation_bytes),
    )
    return ExperimentProtocolV1(
        experiment_id="itd-pascal-r3-serialization-replay",
        hypothesis=HypothesisContract(
            hypothesis_id="ITD-PASCAL-R3-H1",
            statement=(
                "Packed-u16 Pascal source bytes survive the preregistered "
                "serialization, chunking and replay transformations exactly."
            ),
            comparison=(
                "Each reconstructed payload is compared word-for-word with the "
                "verified canonical split bytes and replayed from its persisted "
                "serialized artifact."
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
                name="mismatch_count",
                role=MetricRole.PRIMARY,
                direction=MetricDirection.LOWER_IS_BETTER,
                unit="count",
            ),
            MetricContract(
                name="replay_digest_matches",
                role=MetricRole.DIAGNOSTIC,
                direction=MetricDirection.DESCRIPTIVE,
                unit="boolean",
            ),
        ),
        compute_budget=ComputeBudget(
            unit="serialization_replay_case",
            maximum=PASCAL_R3_CASE_COUNT,
        ),
        uncertainty=UncertaintyContract(
            method="exact_exhaustive_byte_and_word_comparison_no_sampling_interval",
            confidence_level=0.95,
            paired=True,
        ),
    )


def _case_specs() -> tuple[PascalR3CaseSpec, ...]:
    specs: list[PascalR3CaseSpec] = []
    for role, variable_count in (
        (SplitRole.DEVELOPMENT, 8),
        (SplitRole.VALIDATION, 10),
    ):
        prefix = "dev" if role is SplitRole.DEVELOPMENT else "val"
        for byte_order in _BYTE_ORDERS:
            for chunk_width in _CHUNK_WIDTHS:
                for replay_count in _REPLAY_COUNTS:
                    specs.append(
                        PascalR3CaseSpec(
                            case_id=(
                                f"{prefix}-n{variable_count}-bo{byte_order}"
                                f"-c{chunk_width}-r{replay_count}"
                            ),
                            role=role,
                            variable_count=variable_count,
                            byte_order=byte_order,
                            chunk_width=chunk_width,
                            replay_count=replay_count,
                        )
                    )
    return tuple(specs)


def pascal_r3_plan(protocol: ExperimentProtocolV1 | None = None) -> CampaignPlanV1:
    """Create the bounded 32-case non-final R3 plan."""

    frozen_protocol = pascal_r3_protocol() if protocol is None else protocol
    campaign = CampaignIdentityV1.from_protocol(
        "itd-pascal-r3-serialization-replay-campaign",
        frozen_protocol,
        implementation=frozen_protocol.implementation,
    )
    cases = tuple(
        CampaignCaseV1(
            case_id=spec.case_id,
            role=spec.role,
            input_source=frozen_protocol.split(spec.role).source,
            work_units=1.0,
        )
        for spec in _case_specs()
    )
    return CampaignPlanV1(
        campaign=campaign,
        cases=cases,
        work_unit="serialization_replay_case",
        maximum_total_work=float(PASCAL_R3_CASE_COUNT),
    )


def pascal_r3_source_payloads() -> dict[tuple[str, str], bytes]:
    """Return only Development and Validation source bytes."""

    payloads: dict[tuple[str, str], bytes] = {}
    for role in (SplitRole.DEVELOPMENT, SplitRole.VALIDATION):
        identity = _split_source(role)
        payloads[(identity.source, identity.revision)] = pascal_r3_split_payload(role)
    return payloads


def _chunk_roundtrip(serialized: bytes, chunk_width: int) -> bytes:
    if chunk_width <= 0:
        raise ValueError("chunk_width must be positive.")
    chunk_bytes = chunk_width * 2
    chunks = tuple(
        serialized[offset : offset + chunk_bytes]
        for offset in range(0, len(serialized), chunk_bytes)
    )
    return b"".join(chunks)


def _artifact_for_spec(
    spec: PascalR3CaseSpec,
    canonical_source: bytes,
    plan_fingerprint: str,
) -> bytes:
    canonical_words = _bytes_to_words(canonical_source, "little")
    if len(canonical_words) != 1 << spec.variable_count:
        raise ValueError("R3 verified source bytes do not match frozen domain size.")

    serialized = _words_to_bytes(canonical_words, spec.byte_order)
    transported = _chunk_roundtrip(serialized, spec.chunk_width)
    reconstructed_words = _bytes_to_words(transported, spec.byte_order)
    reconstructed_canonical = _words_to_bytes(reconstructed_words, "little")
    mismatch_count = sum(
        observed != expected
        for observed, expected in zip(reconstructed_words, canonical_words, strict=True)
    )

    replay_digests: list[str] = []
    for _ in range(spec.replay_count):
        replay_words = _bytes_to_words(transported, spec.byte_order)
        replay_canonical = _words_to_bytes(replay_words, "little")
        replay_digests.append(digest_bytes(replay_canonical))

    canonical_digest = digest_bytes(canonical_source)
    reconstructed_digest = digest_bytes(reconstructed_canonical)
    replay_digest_matches = all(item == reconstructed_digest for item in replay_digests)
    outcome = "negative" if mismatch_count else "pass"

    return _canonical_json(
        {
            "version": PASCAL_R3_VERSION,
            "case_id": spec.case_id,
            "role": spec.role.value,
            "variable_count": spec.variable_count,
            "byte_order": spec.byte_order,
            "chunk_width": spec.chunk_width,
            "replay_count": spec.replay_count,
            "plan_fingerprint": plan_fingerprint,
            "canonical_payload_sha256": canonical_digest,
            "serialized_source_sha256": digest_bytes(transported),
            "reconstructed_payload_sha256": reconstructed_digest,
            "replay_artifact_sha256": replay_digests,
            "replay_digest_matches": replay_digest_matches,
            "mismatch_count": mismatch_count,
            "integrity_outcome": outcome,
            "serialized_hex": transported.hex(),
        }
    )


class PascalR3Evaluator(ArtifactEvaluator):
    """Exact evaluator bound to verified source bytes and the frozen plan."""

    def __init__(
        self,
        source_payloads: dict[tuple[str, str], bytes],
        plan_fingerprint: str,
    ) -> None:
        self._source_payloads = dict(source_payloads)
        self._plan_fingerprint = plan_fingerprint
        self._specs = {spec.case_id: spec for spec in _case_specs()}

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        spec = self._specs.get(case.case_id)
        if spec is None or spec.role is not case.role:
            raise ValueError("Pascal R3 case is not part of the frozen plan.")
        key = (case.input_source.source, case.input_source.revision)
        source = self._source_payloads.get(key)
        if source is None:
            raise ValueError("Pascal R3 verified source payload is unavailable.")
        if digest_bytes(source) != case.input_source.sha256:
            raise ValueError("Pascal R3 source bytes drifted after verification.")

        artifact = _artifact_for_spec(spec, source, self._plan_fingerprint)
        execution = CaseExecutionV1(
            case_id=case.case_id,
            output_sha256=digest_bytes(artifact),
            work_units_used=1.0,
        )
        return execution, artifact


def run_pascal_r3(
    root: Path,
    *,
    source_payloads: dict[tuple[str, str], bytes] | None = None,
) -> CampaignLedgerV1:
    """Execute R3 while persisting pre-execution provenance failures."""

    protocol = pascal_r3_protocol()
    plan = pascal_r3_plan(protocol)
    payloads = pascal_r3_source_payloads() if source_payloads is None else source_payloads
    evaluator = PascalR3Evaluator(payloads, plan.fingerprint())
    try:
        return run_persisted_campaign(
            root,
            plan,
            evaluator,
            source_payloads=payloads,
            protocol=protocol,
        )
    except ValueError as error:
        ledger_path = root / "ledger.json"
        plan_path = root / "plan.json"
        if plan_path.exists() and not ledger_path.exists():
            ledger = CampaignLedgerV1(
                plan_fingerprint=plan.fingerprint(),
                status=CampaignLifecycleStatus.INCONCLUSIVE,
                reason=f"pre-execution provenance failure: {error}",
                executions=(),
                artifacts=(),
                source_verifications=(),
            )
            persist_campaign_ledger(root, ledger)
            return ledger
        raise


def replay_pascal_r3_artifact(root: Path, case_id: str) -> tuple[str, ...]:
    """Replay one completed R3 case from persisted serialized bytes only."""

    ledger = load_campaign_ledger(root)
    verify_persisted_artifacts(root, ledger)
    record = next((item for item in ledger.artifacts if item.case_id == case_id), None)
    if record is None:
        raise ValueError(f"unknown persisted R3 case: {case_id}")

    payload = json.loads((root / record.relative_path).read_text(encoding="utf-8"))
    if payload["plan_fingerprint"] != ledger.plan_fingerprint:
        raise ValueError("persisted R3 artifact plan fingerprint does not match ledger.")

    serialized = bytes.fromhex(str(payload["serialized_hex"]))
    byte_order = str(payload["byte_order"])
    replay_count = int(payload["replay_count"])
    digests: list[str] = []
    for _ in range(replay_count):
        words = _bytes_to_words(serialized, byte_order)
        canonical = _words_to_bytes(words, "little")
        digests.append(digest_bytes(canonical))
    return tuple(digests)
