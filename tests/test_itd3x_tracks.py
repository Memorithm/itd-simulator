from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.itd3x_tracks import (
    AIComparisonArm,
    AIComparisonLadder,
    EvidenceBinding,
    MechanisticGate,
    PerturbationResponse,
    SearchAuthorization,
)


def test_ai_ladder_requires_established_control() -> None:
    with pytest.raises(ValueError, match="established control"):
        AIComparisonLadder((AIComparisonArm.RAW_MODEL, AIComparisonArm.ITD_ONLY))


def test_attention_gate_rejects_posthoc_holdout_metric() -> None:
    gate = MechanisticGate(
        deterministic_reference=True,
        invariant_tests_pass=True,
        preregistered_tradeoff_observed=True,
        holdout_metric_posthoc=True,
        failure_modes_documented=True,
    )
    assert gate.allows_model_scale is False


def test_perturbation_response_keeps_source_identity() -> None:
    response = PerturbationResponse(
        perturbation_id="noise-1",
        amplitude=0.1,
        structural_delta=0.2,
        task_error_delta=0.3,
        uncertainty_delta=0.4,
        source=SourceIdentity("Memorithm/NoiseLab", "abc"),
    )
    assert response.source.source == "Memorithm/NoiseLab"


def test_search_forbids_final_split() -> None:
    auth = SearchAuthorization(
        role=SplitRole.FINAL,
        search_space_frozen=True,
        compute_budget_frozen=True,
    )
    with pytest.raises(ValueError, match="final split"):
        auth.assert_allowed()


def test_evidence_binding_requires_sha256() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        EvidenceBinding(
            producer="SciRust-Verify",
            source=SourceIdentity("Memorithm/SciRust-Verify", "abc"),
            protocol_fingerprint="bad",
            campaign_fingerprint="a" * 64,
        )
