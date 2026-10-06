from __future__ import annotations

import json
from pathlib import Path

import pytest

from itd_research.campaign_store import CampaignLifecycleStatus
from itd_research.experiment_schema import SplitRole
from itd_research.pascal_replay_integrity import (
    PASCAL_R3_CASE_COUNT,
    pascal_r3_plan,
    pascal_r3_protocol,
    pascal_r3_source_payloads,
    pascal_r3_split_payload,
    replay_pascal_r3_artifact,
    run_pascal_r3,
)
from itd_research.source_verification import digest_bytes


def test_pascal_r3_plan_is_nonfinal_and_fingerprint_stable() -> None:
    protocol = pascal_r3_protocol()
    plan = pascal_r3_plan(protocol)

    assert len(plan.cases) == PASCAL_R3_CASE_COUNT
    assert all(case.role is not SplitRole.FINAL for case in plan.cases)
    assert plan.fingerprint() == pascal_r3_plan(protocol).fingerprint()
    assert sum(case.role is SplitRole.DEVELOPMENT for case in plan.cases) == 16
    assert sum(case.role is SplitRole.VALIDATION for case in plan.cases) == 16
    with pytest.raises(ValueError, match="protected"):
        pascal_r3_split_payload(SplitRole.FINAL)


def test_pascal_r3_sources_are_exact_packed_u16_bytes() -> None:
    development = pascal_r3_split_payload(SplitRole.DEVELOPMENT)
    validation = pascal_r3_split_payload(SplitRole.VALIDATION)

    assert len(development) == 2 * 256
    assert len(validation) == 2 * 1024
    sources = pascal_r3_source_payloads()
    assert len(sources) == 2
    assert {digest_bytes(payload) for payload in sources.values()} == {
        digest_bytes(development),
        digest_bytes(validation),
    }


def test_pascal_r3_persistent_run_is_exact_and_replayable(tmp_path: Path) -> None:
    ledger = run_pascal_r3(tmp_path)

    assert ledger.status is CampaignLifecycleStatus.COMPLETED
    assert len(ledger.executions) == PASCAL_R3_CASE_COUNT
    assert len(ledger.artifacts) == PASCAL_R3_CASE_COUNT
    assert len(ledger.source_verifications) == 2

    plan = pascal_r3_plan(pascal_r3_protocol())
    assert ledger.plan_fingerprint == plan.fingerprint()

    outcomes: list[str] = []
    for artifact in ledger.artifacts:
        payload = json.loads((tmp_path / artifact.relative_path).read_text())
        outcomes.append(str(payload["integrity_outcome"]))
        assert payload["plan_fingerprint"] == ledger.plan_fingerprint
        assert payload["mismatch_count"] == 0
        assert payload["replay_digest_matches"] is True
        assert payload["canonical_payload_sha256"] == payload["reconstructed_payload_sha256"]
        replay = replay_pascal_r3_artifact(tmp_path, artifact.case_id)
        assert list(replay) == payload["replay_artifact_sha256"]

    assert outcomes == ["pass"] * PASCAL_R3_CASE_COUNT


def test_pascal_r3_source_drift_persists_inconclusive_ledger(tmp_path: Path) -> None:
    payloads = pascal_r3_source_payloads()
    first_key = next(iter(payloads))
    payloads[first_key] += b"tamper"

    ledger = run_pascal_r3(tmp_path, source_payloads=payloads)

    assert ledger.status is CampaignLifecycleStatus.INCONCLUSIVE
    assert ledger.executions == ()
    assert ledger.artifacts == ()
    assert "source bytes" in ledger.reason
    assert (tmp_path / "plan.json").is_file()
    assert (tmp_path / "ledger.json").is_file()


def test_pascal_r3_replay_fails_closed_on_artifact_tamper(tmp_path: Path) -> None:
    ledger = run_pascal_r3(tmp_path)
    record = ledger.artifacts[0]
    path = tmp_path / record.relative_path
    path.write_bytes(path.read_bytes() + b"tamper")

    with pytest.raises(ValueError, match="artifact"):
        replay_pascal_r3_artifact(tmp_path, record.case_id)
