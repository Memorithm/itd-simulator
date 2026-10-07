"""ITD Pascal R6 frozen non-final geometry and source/plan identities.

This module creates no campaign runs. Scientific-ledger replay remains a separate,
prospectively frozen experiment and must not reuse R5 result identities.
"""

from __future__ import annotations

from pathlib import Path

from itd_research.campaign_runner import CampaignCaseV1, CampaignPlanV1
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

PASCAL_R6_VERSION = "itd-pascal-r6-ledger-semantics-v1"
PASCAL_R6_CASES_PER_SPLIT = 6
PASCAL_R6_PREFIXES = (2, 4)
_R6_GATES = 12
_R6_TERMS_PER_GATE = 16
_ROOT = Path(__file__).resolve().parents[1]
_PREREG = _ROOT / "docs/itd3x/ITD_PASCAL_R6_LEDGER_SEMANTICS_PREREGISTRATION.md"
_ERRATUM = _ROOT / "docs/itd3x/ITD_PASCAL_R6_LEDGER_SEMANTICS_ERRATUM.md"


def pascal_r6_shape(role: SplitRole) -> tuple[int, int]:
    """Return the two frozen synthetic domains; never resolve a final source."""
    resolved = SplitRole(role)
    if resolved is SplitRole.DEVELOPMENT:
        return 7, 128
    if resolved is SplitRole.VALIDATION:
        return 9, 512
    raise ValueError("R6 source geometry is restricted to Development/Validation")


def pascal_r6_case_ids(role: SplitRole) -> tuple[str, ...]:
    n, _ = pascal_r6_shape(role)
    prefix = "dev" if SplitRole(role) is SplitRole.DEVELOPMENT else "val"
    return tuple(
        f"{prefix}-n{n}-r6-ledger-case-{index:02d}"
        for index in range(PASCAL_R6_CASES_PER_SPLIT)
    )


def pascal_r6_source_payload(role: SplitRole) -> bytes:
    """Deterministic little-endian packed-u16 subset-zeta source bytes."""
    n, domain_size = pascal_r6_shape(role)
    anf = [0] * domain_size
    for gate in range(_R6_GATES):
        lane = 1 << gate
        if gate % 2 == 0:
            anf[0] ^= lane
        terms = tuple(
            1 + ((31 * gate + 17 * term_index) % (domain_size - 1))
            for term_index in range(_R6_TERMS_PER_GATE)
        )
        if len(set(terms)) != _R6_TERMS_PER_GATE:
            raise ValueError("R6 affine ANF generator generated duplicate terms")
        for term in terms:
            anf[term] ^= lane
    for bit in range(n):
        selector = 1 << bit
        for mask in range(domain_size):
            if mask & selector:
                anf[mask] ^= anf[mask ^ selector]
    if any(not (0 <= word < (1 << _R6_GATES)) for word in anf):
        raise ValueError("R6 zeta materialization exceeds packed gate width")
    return b"".join(word.to_bytes(2, "little") for word in anf)


def _source_identity(role: SplitRole) -> SourceIdentity:
    resolved = SplitRole(role)
    return SourceIdentity(
        source=f"generated:itd-pascal-r6:{resolved.value}",
        revision=PASCAL_R6_VERSION,
        sha256=digest_bytes(pascal_r6_source_payload(resolved)),
    )


def pascal_r6_protocol() -> ExperimentProtocolV1:
    """Bind prospective R6 protocol+erratum bytes and implementation bytes."""
    prereg_digest = digest_bytes(_PREREG.read_bytes())
    erratum_digest = digest_bytes(_ERRATUM.read_bytes())
    implementation = SourceIdentity(
        source="itd_research/pascal_r6_plan.py",
        revision=f"{PASCAL_R6_VERSION}:protocol={prereg_digest}:erratum={erratum_digest}",
        sha256=digest_bytes(Path(__file__).read_bytes()),
    )
    return ExperimentProtocolV1(
        experiment_id="itd-pascal-r6-scientific-ledger-relocation",
        hypothesis=HypothesisContract(
            hypothesis_id="ITD-PASCAL-R6-H1",
            statement="Persisted synthetic scientific ledgers remain identical after cold relocation",
            comparison="Exact canonical projection versus uninterrupted matched control",
        ),
        implementation=implementation,
        splits=(
            SplitIdentity(SplitRole.DEVELOPMENT, _source_identity(SplitRole.DEVELOPMENT)),
            SplitIdentity(SplitRole.VALIDATION, _source_identity(SplitRole.VALIDATION)),
            SplitIdentity(
                SplitRole.FINAL,
                SourceIdentity(
                    source="itd-pascal-protected-final",
                    revision="unavailable-no-authorization",
                    sha256=None,
                ),
            ),
        ),
        metrics=(
            MetricContract(
                name="exact_scientific_ledger_equality",
                role=MetricRole.PRIMARY,
                direction=MetricDirection.DESCRIPTIVE,
                unit="boolean",
            ),
            MetricContract(
                name="full_raw_ledger_equality",
                role=MetricRole.SECONDARY,
                direction=MetricDirection.DESCRIPTIVE,
                unit="boolean",
            ),
            MetricContract(
                name="missing_or_duplicate_cases",
                role=MetricRole.DIAGNOSTIC,
                direction=MetricDirection.DESCRIPTIVE,
                unit="count",
            ),
        ),
        compute_budget=ComputeBudget(
            unit="r6_ledger_integrity_case",
            maximum=float(PASCAL_R6_CASES_PER_SPLIT),
        ),
        uncertainty=UncertaintyContract(
            method="exact_paired_comparison_without_sampling_interval",
            confidence_level=0.95,
            paired=True,
        ),
    )


def pascal_r6_plan(
    role: SplitRole, protocol: ExperimentProtocolV1 | None = None
) -> CampaignPlanV1:
    """Six immutable case identities per non-final split, no execution."""
    resolved = SplitRole(role)
    pascal_r6_shape(resolved)
    frozen = pascal_r6_protocol() if protocol is None else protocol
    campaign = CampaignIdentityV1.from_protocol(
        f"itd-pascal-r6-{resolved.value}-campaign",
        frozen,
        implementation=frozen.implementation,
    )
    source = frozen.split(resolved).source
    plan = CampaignPlanV1(
        campaign=campaign,
        cases=tuple(
            CampaignCaseV1(case_id=case_id, role=resolved,
                           input_source=source, work_units=1.0)
            for case_id in pascal_r6_case_ids(resolved)
        ),
        work_unit="r6_ledger_integrity_case",
        maximum_total_work=float(PASCAL_R6_CASES_PER_SPLIT),
    )
    plan.assert_matches_protocol(frozen)
    return plan


def pascal_r6_source_payloads(role: SplitRole) -> dict[tuple[str, str], bytes]:
    """Return only explicitly requested non-final verified source bytes."""
    identity = _source_identity(role)
    return {(identity.source, identity.revision): pascal_r6_source_payload(role)}
