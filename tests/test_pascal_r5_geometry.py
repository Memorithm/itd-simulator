from __future__ import annotations

from pathlib import Path

import pytest

from itd_research.experiment_schema import SplitRole
from itd_research.pascal_relocation_integrity import (
    PASCAL_R5_CASES_PER_SPLIT,
    PASCAL_R5_DESTINATIONS,
    PASCAL_R5_PREFIXES,
    PascalR5Evaluator,
    pascal_r5_case_ids,
    pascal_r5_plan,
    pascal_r5_protocol,
    pascal_r5_shape,
    pascal_r5_source_payload,
    pascal_r5_source_payloads,
)


def test_r5_geometry_is_frozen_nonfinal() -> None:
    assert PASCAL_R5_PREFIXES == (2, 5)
    assert PASCAL_R5_CASES_PER_SPLIT == 6
    assert PASCAL_R5_DESTINATIONS == {
        2: "relocated-after-02",
        5: "relocated-after-05",
    }
    assert pascal_r5_shape(SplitRole.DEVELOPMENT) == (6, 64)
    assert pascal_r5_shape(SplitRole.VALIDATION) == (11, 2048)
    assert len(set(pascal_r5_case_ids(SplitRole.DEVELOPMENT))) == 6
    assert len(set(pascal_r5_case_ids(SplitRole.VALIDATION))) == 6
    with pytest.raises(ValueError, match="protected"):
        pascal_r5_source_payload(SplitRole.FINAL)


def test_r5_protocol_plans_and_sources_are_stable_and_distinct() -> None:
    protocol = pascal_r5_protocol()
    assert protocol.split(SplitRole.FINAL).source.sha256 is None

    dev_source = protocol.split(SplitRole.DEVELOPMENT).source
    val_source = protocol.split(SplitRole.VALIDATION).source
    assert dev_source.sha256 is not None
    assert val_source.sha256 is not None
    assert dev_source.sha256 != val_source.sha256

    for role in (SplitRole.DEVELOPMENT, SplitRole.VALIDATION):
        first = pascal_r5_plan(role, protocol)
        second = pascal_r5_plan(role, protocol)
        assert first.fingerprint() == second.fingerprint()
        assert tuple(case.case_id for case in first.cases) == pascal_r5_case_ids(role)
        assert len(first.cases) == PASCAL_R5_CASES_PER_SPLIT
        assert all(case.role is role for case in first.cases)


def test_r5_artifacts_are_deterministic_and_root_independent(tmp_path: Path) -> None:
    protocol = pascal_r5_protocol()
    role = SplitRole.DEVELOPMENT
    plan = pascal_r5_plan(role, protocol)
    payloads = pascal_r5_source_payloads(role)
    case = plan.cases[0]

    left = PascalR5Evaluator(payloads, plan.fingerprint())
    right = PascalR5Evaluator(payloads, plan.fingerprint())
    left_execution, left_artifact = left.evaluate(case)
    right_execution, right_artifact = right.evaluate(case)

    assert left_execution == right_execution
    assert left_artifact == right_artifact
    assert str(tmp_path).encode("utf-8") not in left_artifact
    assert left.calls == {case.case_id: 1}
    assert right.calls == {case.case_id: 1}