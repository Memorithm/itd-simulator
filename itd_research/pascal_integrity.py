"""Independent Pascal/ANF representation-integrity campaign for ITD Research Lab.

This Development/Validation-only slice checks whether a packed ``u16`` bank of
Boolean ANF gates preserves exact semantics under deterministic gate-lane and
term-order re-encodings. It is deliberately independent of TDI's Pascal cost
study and does not authorize final evaluation or model-side promotion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from itd_research.campaign_runner import CampaignCaseV1, CampaignPlanV1, CaseExecutionV1
from itd_research.campaign_store import (
    ArtifactEvaluator,
    CampaignHalt,
    CampaignLedgerV1,
    CampaignLifecycleStatus,
    run_persisted_campaign,
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

PASCAL_R2_VERSION = "itd-pascal-r2-order-integrity-v1"
PASCAL_R2_GATE_COUNT = 12
PASCAL_R2_DENSITY = 24
PASCAL_R2_CASE_COUNT = 12

_GATE_PERMUTATIONS = ("identity", "reverse", "rotate5")
_TERM_ORDERS = ("forward", "reverse")
_FINAL_SENTINEL = SourceIdentity(
    source="itd-pascal-protected-final",
    revision="not-opened-no-authorization",
    sha256=None,
)


@dataclass(frozen=True)
class PascalR2CaseSpec:
    """Frozen non-final geometry for one integrity case."""

    case_id: str
    role: SplitRole
    variable_count: int
    gate_permutation: str
    term_order: str


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def pascal_r2_split_payload(role: SplitRole) -> bytes:
    """Return exact generated source bytes for Development or Validation only."""

    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R2 final source is protected and not authorized.")
    variable_count = 9 if resolved is SplitRole.DEVELOPMENT else 11
    return _canonical_bytes(
        {
            "version": PASCAL_R2_VERSION,
            "role": resolved.value,
            "variable_count": variable_count,
            "gate_count": PASCAL_R2_GATE_COUNT,
            "density": PASCAL_R2_DENSITY,
            "generator": "affine-mask-v1",
        }
    )


def _split_source(role: SplitRole) -> SourceIdentity:
    payload = pascal_r2_split_payload(role)
    return SourceIdentity(
        source=f"generated:itd-pascal-r2:{SplitRole(role).value}",
        revision=PASCAL_R2_VERSION,
        sha256=digest_bytes(payload),
    )


def pascal_r2_protocol() -> ExperimentProtocolV1:
    """Build the prospective integrity protocol without opening final bytes."""

    implementation_bytes = Path(__file__).read_bytes()
    implementation = SourceIdentity(
        source="itd_research/pascal_integrity.py",
        revision=PASCAL_R2_VERSION,
        sha256=digest_bytes(implementation_bytes),
    )
    return ExperimentProtocolV1(
        experiment_id="itd-pascal-r2-order-integrity",
        hypothesis=HypothesisContract(
            hypothesis_id="ITD-PASCAL-R2-H1",
            statement=(
                "Packed-u16 Pascal materialization is exactly invariant to the "
                "preregistered gate-lane and ANF-term order re-encodings."
            ),
            comparison=(
                "Each transformed representation is mapped back to canonical lanes "
                "and compared exhaustively with both a canonical subset-zeta table "
                "and an independent direct-ANF oracle."
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
                name="evaluated_assignments",
                role=MetricRole.DIAGNOSTIC,
                direction=MetricDirection.DESCRIPTIVE,
                unit="assignments",
            ),
        ),
        compute_budget=ComputeBudget(
            unit="integrity_case",
            maximum=PASCAL_R2_CASE_COUNT,
        ),
        uncertainty=UncertaintyContract(
            method="exact_exhaustive_enumeration_no_sampling_interval",
            confidence_level=0.95,
            paired=True,
        ),
    )


def _case_specs() -> tuple[PascalR2CaseSpec, ...]:
    specs: list[PascalR2CaseSpec] = []
    for role, variable_count in (
        (SplitRole.DEVELOPMENT, 9),
        (SplitRole.VALIDATION, 11),
    ):
        prefix = "dev" if role is SplitRole.DEVELOPMENT else "val"
        for gate_permutation in _GATE_PERMUTATIONS:
            for term_order in _TERM_ORDERS:
                specs.append(
                    PascalR2CaseSpec(
                        case_id=(
                            f"{prefix}-n{variable_count}-g{gate_permutation}"
                            f"-t{term_order}"
                        ),
                        role=role,
                        variable_count=variable_count,
                        gate_permutation=gate_permutation,
                        term_order=term_order,
                    )
                )
    return tuple(specs)


def pascal_r2_plan(protocol: ExperimentProtocolV1 | None = None) -> CampaignPlanV1:
    """Create a bounded plan containing no final cases."""

    frozen_protocol = pascal_r2_protocol() if protocol is None else protocol
    campaign = CampaignIdentityV1.from_protocol(
        "itd-pascal-r2-order-integrity-campaign",
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
        work_unit="integrity_case",
        maximum_total_work=float(PASCAL_R2_CASE_COUNT),
    )


def pascal_r2_source_payloads() -> dict[tuple[str, str], bytes]:
    """Return only the two non-final source payloads used by the campaign."""

    payloads: dict[tuple[str, str], bytes] = {}
    for role in (SplitRole.DEVELOPMENT, SplitRole.VALIDATION):
        identity = _split_source(role)
        payloads[(identity.source, identity.revision)] = pascal_r2_split_payload(role)
    return payloads


def _gate_terms(variable_count: int) -> tuple[tuple[int, ...], ...]:
    domain_size = 1 << variable_count
    banks: list[tuple[int, ...]] = []
    for gate in range(PASCAL_R2_GATE_COUNT):
        terms = tuple(
            1 + ((37 * gate + 53 * index) % (domain_size - 1))
            for index in range(PASCAL_R2_DENSITY)
        )
        if len(set(terms)) != PASCAL_R2_DENSITY:
            raise ValueError("Pascal R2 generator produced duplicate ANF terms.")
        banks.append(terms)
    return tuple(banks)


def _constant_word() -> int:
    word = 0
    for gate in range(PASCAL_R2_GATE_COUNT):
        if gate % 3 == 1:
            word |= 1 << gate
    return word


def _permutation(name: str) -> tuple[int, ...]:
    if name == "identity":
        return tuple(range(PASCAL_R2_GATE_COUNT))
    if name == "reverse":
        return tuple(reversed(range(PASCAL_R2_GATE_COUNT)))
    if name == "rotate5":
        return tuple(
            (gate + 5) % PASCAL_R2_GATE_COUNT
            for gate in range(PASCAL_R2_GATE_COUNT)
        )
    raise ValueError(f"unknown gate permutation: {name}")


def _direct_word(
    assignment: int,
    gate_terms: tuple[tuple[int, ...], ...],
) -> int:
    result = 0
    constants = _constant_word()
    for gate, terms in enumerate(gate_terms):
        value = bool(constants & (1 << gate))
        for term in terms:
            if assignment & term == term:
                value = not value
        if value:
            result |= 1 << gate
    return result


def _materialize(
    variable_count: int,
    gate_permutation: str,
    term_order: str,
) -> list[int]:
    domain_size = 1 << variable_count
    permutation = _permutation(gate_permutation)
    table = [0] * domain_size
    constants = _constant_word()
    for canonical_gate, physical_gate in enumerate(permutation):
        if constants & (1 << canonical_gate):
            table[0] |= 1 << physical_gate
        terms = list(_gate_terms(variable_count)[canonical_gate])
        if term_order == "reverse":
            terms.reverse()
        elif term_order != "forward":
            raise ValueError(f"unknown term order: {term_order}")
        lane = 1 << physical_gate
        for term in terms:
            table[term] ^= lane

    for bit in range(variable_count):
        selector = 1 << bit
        for mask in range(domain_size):
            if mask & selector:
                table[mask] ^= table[mask ^ selector]
    return table


def _restore_word(word: int, gate_permutation: str) -> int:
    restored = 0
    for canonical_gate, physical_gate in enumerate(_permutation(gate_permutation)):
        if word & (1 << physical_gate):
            restored |= 1 << canonical_gate
    return restored


def _table_digest(table: list[int]) -> str:
    payload = b"".join(word.to_bytes(2, byteorder="little") for word in table)
    return digest_bytes(payload)


def _evaluate_spec(spec: PascalR2CaseSpec) -> bytes:
    canonical = _materialize(spec.variable_count, "identity", "forward")
    transformed_physical = _materialize(
        spec.variable_count,
        spec.gate_permutation,
        spec.term_order,
    )
    transformed = [
        _restore_word(word, spec.gate_permutation) for word in transformed_physical
    ]
    gate_terms = _gate_terms(spec.variable_count)
    direct = [
        _direct_word(assignment, gate_terms)
        for assignment in range(1 << spec.variable_count)
    ]
    direct_mismatches = sum(
        observed != expected
        for observed, expected in zip(transformed, direct, strict=True)
    )
    canonical_mismatches = sum(
        observed != expected
        for observed, expected in zip(transformed, canonical, strict=True)
    )
    direct_reference_mismatches = sum(
        observed != expected
        for observed, expected in zip(canonical, direct, strict=True)
    )
    return _canonical_bytes(
        {
            "version": PASCAL_R2_VERSION,
            "case_id": spec.case_id,
            "role": spec.role.value,
            "variable_count": spec.variable_count,
            "domain_size": 1 << spec.variable_count,
            "gate_count": PASCAL_R2_GATE_COUNT,
            "density": PASCAL_R2_DENSITY,
            "gate_permutation": spec.gate_permutation,
            "term_order": spec.term_order,
            "direct_mismatches": direct_mismatches,
            "canonical_mismatches": canonical_mismatches,
            "direct_reference_mismatches": direct_reference_mismatches,
            "direct_checksum": _table_digest(direct),
            "canonical_checksum": _table_digest(canonical),
            "transformed_checksum": _table_digest(transformed),
        }
    )


class PascalR2Evaluator(ArtifactEvaluator):
    """Exact evaluator that persists mismatch evidence before halting."""

    def evaluate(self, case: CampaignCaseV1) -> tuple[CaseExecutionV1, bytes]:
        specs = {spec.case_id: spec for spec in _case_specs()}
        spec = specs.get(case.case_id)
        if spec is None or spec.role is not case.role:
            raise ValueError("Pascal R2 case is not part of the frozen plan.")
        artifact = _evaluate_spec(spec)
        payload = json.loads(artifact.decode("utf-8"))
        execution = CaseExecutionV1(
            case_id=case.case_id,
            output_sha256=digest_bytes(artifact),
            work_units_used=1.0,
        )
        mismatch_count = (
            int(payload["direct_mismatches"])
            + int(payload["canonical_mismatches"])
            + int(payload["direct_reference_mismatches"])
        )
        if mismatch_count != 0:
            raise CampaignHalt(
                CampaignLifecycleStatus.INCONCLUSIVE,
                "Pascal R2 representation-integrity mismatch",
                execution=execution,
                artifact=artifact,
            )
        return execution, artifact


def run_pascal_r2(root: Path) -> CampaignLedgerV1:
    """Execute the frozen Development/Validation integrity campaign."""

    protocol = pascal_r2_protocol()
    plan = pascal_r2_plan(protocol)
    return run_persisted_campaign(
        root,
        plan,
        PascalR2Evaluator(),
        source_payloads=pascal_r2_source_payloads(),
        protocol=protocol,
    )
