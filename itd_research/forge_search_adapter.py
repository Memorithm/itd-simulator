"""ITD-38.0 bounded Forge search adapter contracts.

Forge may propose and measure bounded candidates on non-final surfaces. ITD
retains protocol, holdout and scientific-conclusion authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity, SplitRole


class ObjectiveDirection(StrEnum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class ForgeSearchContractV1:
    """Frozen bounded search domain for one non-final Forge campaign."""

    search_id: str
    source: SourceIdentity
    role: SplitRole
    domain: str
    candidate_schema: str
    search_space_sha256: str
    objective_schema_sha256: str
    maximum_candidates: int
    compute_budget: float
    compute_unit: str
    base_seed: int
    contract_version: str = "itd-forge-search-v1"

    def __post_init__(self) -> None:
        if self.contract_version != "itd-forge-search-v1":
            raise ValueError("unsupported Forge search contract version.")
        if not self.search_id.strip():
            raise ValueError("search_id must not be empty.")
        if self.source.source != "Memorithm/Forge":
            raise ValueError("Forge search source must be Memorithm/Forge.")
        if self.role is SplitRole.FINAL:
            raise ValueError("Forge search cannot run on final ITD data.")
        if not self.domain.strip():
            raise ValueError("Forge search domain must not be empty.")
        if not self.candidate_schema.strip():
            raise ValueError("candidate_schema must not be empty.")
        object.__setattr__(
            self,
            "search_space_sha256",
            _validate_sha256("search_space_sha256", self.search_space_sha256),
        )
        object.__setattr__(
            self,
            "objective_schema_sha256",
            _validate_sha256("objective_schema_sha256", self.objective_schema_sha256),
        )
        if self.maximum_candidates <= 0:
            raise ValueError("maximum_candidates must be positive.")
        if not math.isfinite(self.compute_budget) or self.compute_budget <= 0.0:
            raise ValueError("compute_budget must be finite and positive.")
        if not self.compute_unit.strip():
            raise ValueError("compute_unit must not be empty.")
        if self.base_seed < 0:
            raise ValueError("base_seed must be non-negative.")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "search_id": self.search_id,
            "source": self.source.as_dict(),
            "role": self.role.value,
            "domain": self.domain,
            "candidate_schema": self.candidate_schema,
            "search_space_sha256": self.search_space_sha256,
            "objective_schema_sha256": self.objective_schema_sha256,
            "maximum_candidates": self.maximum_candidates,
            "compute_budget": self.compute_budget,
            "compute_unit": self.compute_unit,
            "base_seed": self.base_seed,
        }

    def fingerprint(self) -> str:
        payload = json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ForgeObjectiveObservation:
    """One verified objective measurement for a candidate."""

    name: str
    value: float
    unit: str
    direction: ObjectiveDirection

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("objective name must not be empty.")
        if not math.isfinite(self.value):
            raise ValueError("objective value must be finite.")
        if not self.unit.strip():
            raise ValueError("objective unit must not be empty.")


@dataclass(frozen=True)
class ForgeCandidateEvidence:
    """Evidence for one candidate; measurement requires verification first."""

    candidate_id: str
    candidate_sha256: str
    verification_passed: bool
    objectives: tuple[ForgeObjectiveObservation, ...]

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty.")
        object.__setattr__(
            self,
            "candidate_sha256",
            _validate_sha256("candidate_sha256", self.candidate_sha256),
        )
        names = tuple(item.name for item in self.objectives)
        if len(set(names)) != len(names):
            raise ValueError("candidate objective names must be unique.")
        if self.objectives and not self.verification_passed:
            raise ValueError("Forge objectives require verification_passed=True.")


@dataclass(frozen=True)
class ForgeSearchResultV1:
    """Bound result of a Forge search without confirmatory authority."""

    contract_fingerprint: str
    candidates_evaluated: int
    pareto_candidate_ids: tuple[str, ...]
    pareto_front_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "contract_fingerprint",
            _validate_sha256("contract_fingerprint", self.contract_fingerprint),
        )
        object.__setattr__(
            self,
            "pareto_front_sha256",
            _validate_sha256("pareto_front_sha256", self.pareto_front_sha256),
        )
        if self.candidates_evaluated < 0:
            raise ValueError("candidates_evaluated must be non-negative.")
        if len(set(self.pareto_candidate_ids)) != len(self.pareto_candidate_ids):
            raise ValueError("Pareto candidate identifiers must be unique.")
        if len(self.pareto_candidate_ids) > self.candidates_evaluated:
            raise ValueError("Pareto front cannot exceed evaluated candidate count.")

    @property
    def authorizes_confirmatory_claim(self) -> bool:
        return False

    def assert_matches_contract(self, contract: ForgeSearchContractV1) -> None:
        if self.contract_fingerprint != contract.fingerprint():
            raise ValueError("Forge result does not match search contract.")
        if self.candidates_evaluated > contract.maximum_candidates:
            raise ValueError("Forge result exceeds maximum_candidates.")
