from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.forge_search_adapter import (
    ForgeCandidateEvidence,
    ForgeObjectiveObservation,
    ForgeSearchContractV1,
    ForgeSearchResultV1,
    ObjectiveDirection,
)


def _contract(role: SplitRole = SplitRole.DEVELOPMENT) -> ForgeSearchContractV1:
    return ForgeSearchContractV1(
        search_id="forge-1",
        source=SourceIdentity("Memorithm/Forge", "forge-test"),
        role=role,
        domain="descriptor_search",
        candidate_schema="itd-descriptor-candidate-v1",
        search_space_sha256="a" * 64,
        objective_schema_sha256="b" * 64,
        maximum_candidates=16,
        compute_budget=100.0,
        compute_unit="evaluations",
        base_seed=7,
    )


def test_forge_search_rejects_final_split() -> None:
    with pytest.raises(ValueError, match="final ITD data"):
        _contract(SplitRole.FINAL)


def test_forge_measurement_requires_verification() -> None:
    objective = ForgeObjectiveObservation(
        name="error",
        value=0.1,
        unit="fraction",
        direction=ObjectiveDirection.MINIMIZE,
    )

    with pytest.raises(ValueError, match="verification_passed"):
        ForgeCandidateEvidence(
            candidate_id="candidate-1",
            candidate_sha256="c" * 64,
            verification_passed=False,
            objectives=(objective,),
        )


def test_forge_search_result_binds_contract_and_budget() -> None:
    contract = _contract()
    result = ForgeSearchResultV1(
        contract_fingerprint=contract.fingerprint(),
        candidates_evaluated=8,
        pareto_candidate_ids=("candidate-a", "candidate-b"),
        pareto_front_sha256="d" * 64,
    )

    result.assert_matches_contract(contract)
    assert result.authorizes_confirmatory_claim is False


def test_forge_result_rejects_candidate_count_overrun() -> None:
    contract = _contract()
    result = ForgeSearchResultV1(
        contract_fingerprint=contract.fingerprint(),
        candidates_evaluated=17,
        pareto_candidate_ids=(),
        pareto_front_sha256="d" * 64,
    )

    with pytest.raises(ValueError, match="maximum_candidates"):
        result.assert_matches_contract(contract)
