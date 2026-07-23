"""Tests for the cylinder Re=3900 integration contract (Mission 6, H46).

Offline, no-network checks only: the workflow status is honestly blocked, and the
manifest schema validator accepts complete manifests and flags missing provenance keys.
No dataset is downloaded and no scientific result is asserted.
"""

from __future__ import annotations

import pytest

from itd_research.external_validation.cylinder_re3900 import (
    EVIDENCE_LEVELS,
    WORKFLOW_STAGES,
    manifest_schema,
    validate_manifest,
    workflow_status,
)


def test_workflow_status_is_honestly_blocked() -> None:
    status = workflow_status()
    assert status.blocked_stage == "download"
    assert status.reached_level is None  # nothing ingested offline
    assert status.blocked_reasons  # reasons are recorded, not hidden
    assert status.stages == WORKFLOW_STAGES
    assert status.evidence_levels == EVIDENCE_LEVELS


def test_evidence_ladder_starts_at_ingestion() -> None:
    assert EVIDENCE_LEVELS[0] == "ingestion_verified"
    assert EVIDENCE_LEVELS[-1] == "locked_external_holdout"


def test_validate_manifest_accepts_complete_payload() -> None:
    payload = {key: "x" for key in manifest_schema("source_manifest")}
    result = validate_manifest("source_manifest", payload)
    assert result.valid
    assert result.missing == ()


def test_validate_manifest_flags_missing_keys() -> None:
    result = validate_manifest("source_manifest", {"dataset_id": "x"})
    assert not result.valid
    assert "sha256" in result.missing
    assert "verified_redistribution" in result.missing


def test_unknown_manifest_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown manifest"):
        manifest_schema("not_a_manifest")
