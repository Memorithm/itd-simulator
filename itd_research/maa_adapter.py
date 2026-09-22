"""ITD-35.2 Multi-Algebra Attention evidence adapter.

FLAT owns MAA semantics and qualification. ITD records exact route/policy/data
identities and numerical diagnostics without converting host evidence into a
softmax-replacement, performance, or runtime-routing claim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity, SplitRole


class MaaAlgebraDomain(StrEnum):
    BOOLEAN = "boolean"
    F2 = "f2"
    ZHEGALKIN = "zhegalkin"
    MAX_PLUS = "max_plus"


class MaaEvidenceDisposition(StrEnum):
    """Preserved upstream evidence classification, not an ITD verdict."""

    SMOKE = "smoke"
    EXPLORATORY = "exploratory"
    CONFIRMATORY_SUPPORTED = "confirmatory_supported"
    CONFIRMATORY_REJECTED = "confirmatory_rejected"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class MaaRouteRef:
    """Exact non-final or frozen-confirmatory MAA route identity."""

    route_id: str
    source: SourceIdentity
    role: SplitRole
    domains: tuple[MaaAlgebraDomain, ...]
    policy_sha256: str
    feature_schema_sha256: str
    dataset_sha256: str
    recomposition_policy: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", SplitRole(self.role))
        if not self.route_id.strip():
            raise ValueError("route_id must not be empty.")
        if self.source.source != "Memorithm/FLAT-ATTENTION":
            raise ValueError("MAA source must be Memorithm/FLAT-ATTENTION.")
        if not self.domains:
            raise ValueError("MAA route must declare at least one algebraic domain.")
        if len(set(self.domains)) != len(self.domains):
            raise ValueError("MAA route domains must be unique.")
        if MaaAlgebraDomain.BOOLEAN not in self.domains:
            raise ValueError("MAA route must retain the Boolean admission domain.")
        if not self.recomposition_policy.strip():
            raise ValueError("recomposition_policy must not be empty.")
        for field_name in ("policy_sha256", "feature_schema_sha256", "dataset_sha256"):
            object.__setattr__(
                self,
                field_name,
                _validate_sha256(field_name, getattr(self, field_name)),
            )


@dataclass(frozen=True)
class MaaNumericalObservation:
    """Numerical diagnostic for one exact MAA arm/case."""

    route: MaaRouteRef
    case_id: str
    arm: str
    disposition: MaaEvidenceDisposition
    selected_candidate_ids: tuple[int, ...]
    score_evaluations: int
    retained_dense_relevant: int
    output_max_abs_error: float | None
    lse_abs_error: float | None
    no_survivors: bool

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.arm.strip():
            raise ValueError("MAA case_id and arm must not be empty.")
        if self.score_evaluations < 0 or self.retained_dense_relevant < 0:
            raise ValueError("MAA counts must be non-negative.")
        if len(set(self.selected_candidate_ids)) != len(self.selected_candidate_ids):
            raise ValueError("selected candidate identifiers must be unique.")
        if any(candidate < 0 for candidate in self.selected_candidate_ids):
            raise ValueError("selected candidate identifiers must be non-negative.")
        if tuple(sorted(self.selected_candidate_ids)) != self.selected_candidate_ids:
            raise ValueError("selected candidate identifiers must preserve source order.")
        if self.no_survivors:
            if self.selected_candidate_ids or self.score_evaluations != 0:
                raise ValueError("empty MAA observations must contain no selected work.")
            if self.output_max_abs_error is not None or self.lse_abs_error is not None:
                raise ValueError("empty MAA observations cannot fabricate O/LSE errors.")
        else:
            if not self.selected_candidate_ids:
                raise ValueError("non-empty MAA observations require selected candidates.")
            if self.output_max_abs_error is None or self.lse_abs_error is None:
                raise ValueError("non-empty MAA observations require O/LSE diagnostics.")
            for name, value in (
                ("output_max_abs_error", self.output_max_abs_error),
                ("lse_abs_error", self.lse_abs_error),
            ):
                if value is None or not math.isfinite(value) or value < 0.0:
                    raise ValueError(f"{name} must be finite and non-negative.")
        if self.retained_dense_relevant > len(self.selected_candidate_ids):
            raise ValueError("retained relevant count cannot exceed selected candidates.")

    @property
    def authorizes_softmax_replacement_claim(self) -> bool:
        return False

    @property
    def authorizes_performance_claim(self) -> bool:
        return False

    @property
    def authorizes_runtime_routing(self) -> bool:
        return False
