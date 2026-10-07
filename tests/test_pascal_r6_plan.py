"""R6 prospective plan/source preflight; these tests do not run campaigns."""

from __future__ import annotations

from pathlib import Path

import pytest

from itd_research.experiment_schema import SplitRole
from itd_research.pascal_r6_plan import (
    PASCAL_R6_CASES_PER_SPLIT,
    PASCAL_R6_PREFIXES,
    pascal_r6_case_ids,
    pascal_r6_plan,
    pascal_r6_protocol,
    pascal_r6_shape,
    pascal_r6_source_payload,
    pascal_r6_source_payloads,
)
from itd_research.source_verification import digest_bytes, verify_source_bytes


def test_r6_declared_design_is_frozen() -> None:
    assert PASCAL_R6_PREFIXES == (2, 4)
    assert PASCAL_R6_CASES_PER_SPLIT == 6
    assert pascal_r6_shape(SplitRole.DEVELOPMENT) == (7, 128)
    assert pascal_r6_shape(SplitRole.VALIDATION) == (9, 512)
    assert pascal_r6_case_ids(SplitRole.DEVELOPMENT) == tuple(
        f"dev-n7-r6-ledger-case-{i:02d}" for i in range(6)
    )
    assert pascal_r6_case_ids(SplitRole.VALIDATION) == tuple(
        f"val-n9-r6-ledger-case-{i:02d}" for i in range(6)
    )


@pytest.mark.parametrize(
    "function",
    (pascal_r6_shape, pascal_r6_case_ids, pascal_r6_source_payload,
     pascal_r6_source_payloads, pascal_r6_plan),
)
def test_r6_final_is_not_constructible(function: object) -> None:
    with pytest.raises(ValueError):
        function(SplitRole.FINAL)  # type: ignore[operator]


def test_r6_protocol_is_bound_to_exact_preregistration_bytes() -> None:
    protocol = pascal_r6_protocol()
    rev = protocol.implementation.revision
    root = Path(__file__).resolve().parents[1]
    prereg = root / "docs/itd3x/ITD_PASCAL_R6_LEDGER_SEMANTICS_PREREGISTRATION.md"
    erratum = root / "docs/itd3x/ITD_PASCAL_R6_LEDGER_SEMANTICS_ERRATUM.md"
    assert f"protocol={digest_bytes(prereg.read_bytes())}" in rev
    assert f"erratum={digest_bytes(erratum.read_bytes())}" in rev
    assert protocol.split(SplitRole.FINAL).source.sha256 is None
    assert protocol.implementation.sha256 is not None


@pytest.mark.parametrize("role", [SplitRole.DEVELOPMENT, SplitRole.VALIDATION])
def test_r6_plans_have_stable_disjoint_identities(role: SplitRole) -> None:
    protocol = pascal_r6_protocol()
    plan = pascal_r6_plan(role, protocol)
    assert plan.fingerprint() == pascal_r6_plan(role, protocol).fingerprint()
    assert len(plan.cases) == 6
    assert tuple(case.case_id for case in plan.cases) == pascal_r6_case_ids(role)
    assert all(case.input_source == protocol.split(role).source for case in plan.cases)
    assert all(case.work_units == 1.0 for case in plan.cases)
    assert plan.fingerprint() != pascal_r6_plan(
        SplitRole.VALIDATION if role is SplitRole.DEVELOPMENT
        else SplitRole.DEVELOPMENT,
        protocol,
    ).fingerprint()


@pytest.mark.parametrize("role", [SplitRole.DEVELOPMENT, SplitRole.VALIDATION])
def test_r6_source_exact_oracle_and_tampering_rejected(role: SplitRole) -> None:
    n, domain_size = pascal_r6_shape(role)
    payload = pascal_r6_source_payload(role)
    assert len(payload) == 2 * domain_size
    identity = pascal_r6_protocol().split(role).source
    record = verify_source_bytes(identity, payload)
    assert record.observed_sha256 == digest_bytes(payload)
    assert len(pascal_r6_source_payloads(role)) == 1
    with pytest.raises(ValueError, match="do not match"):
        verify_source_bytes(identity, payload[:-1] + bytes([payload[-1] ^ 1]))

    # Independent Boolean ANF oracle, no use of the subset-zeta loop.
    for mask in range(domain_size):
        packed = 0
        for gate in range(12):
            bit = int(gate % 2 == 0)
            for term_index in range(16):
                term = 1 + ((31 * gate + 17 * term_index) % (domain_size - 1))
                if term & mask == term:
                    bit ^= 1
            packed |= bit << gate
        observed = int.from_bytes(payload[2 * mask:2 * mask + 2], "little")
        assert observed == packed, (n, mask)
