from __future__ import annotations

import pytest

from itd_research.experiment_schema import SplitRole
from itd_research.pascal_resume_integrity import (
    PASCAL_R4_CASES_PER_SPLIT,
    PASCAL_R4_PREFIXES,
    PascalR4Evaluator,
    pascal_r4_case_ids,
    pascal_r4_plan,
    pascal_r4_protocol,
    pascal_r4_shape,
    pascal_r4_source_payload,
    pascal_r4_source_payloads,
)


def test_r4_geometry_is_nonfinal() -> None:
    assert PASCAL_R4_PREFIXES == (1, 4, 7)
    assert PASCAL_R4_CASES_PER_SPLIT == 8
    assert pascal_r4_shape(SplitRole.DEVELOPMENT) == (7, 128)
    assert pascal_r4_shape(SplitRole.VALIDATION) == (9, 512)
    assert len(set(pascal_r4_case_ids(SplitRole.DEVELOPMENT))) == 8
    assert len(set(pascal_r4_case_ids(SplitRole.VALIDATION))) == 8
    with pytest.raises(ValueError, match="protected"):
        pascal_r4_source_payload(SplitRole.FINAL)

def test_r4_protocol_and_plans_are_frozen_nonfinal() -> None:
    protocol = pascal_r4_protocol()
    assert protocol.split(SplitRole.FINAL).source.sha256 is None

    for role in (SplitRole.DEVELOPMENT, SplitRole.VALIDATION):
        first = pascal_r4_plan(role, protocol)
        second = pascal_r4_plan(role, protocol)
        assert first.fingerprint() == second.fingerprint()
        assert tuple(case.case_id for case in first.cases) == pascal_r4_case_ids(role)
        assert all(case.role is role for case in first.cases)
        assert len(first.cases) == PASCAL_R4_CASES_PER_SPLIT


def test_r4_evaluator_is_deterministic_without_final_access() -> None:
    protocol = pascal_r4_protocol()
    role = SplitRole.DEVELOPMENT
    plan = pascal_r4_plan(role, protocol)
    payloads = pascal_r4_source_payloads(role)
    case = plan.cases[0]

    first = PascalR4Evaluator(payloads, plan.fingerprint())
    second = PascalR4Evaluator(payloads, plan.fingerprint())
    first_execution, first_artifact = first.evaluate(case)
    second_execution, second_artifact = second.evaluate(case)

    assert first_execution == second_execution
    assert first_artifact == second_artifact
    assert first.calls == {case.case_id: 1}
    assert second.calls == {case.case_id: 1}
