"""ITD-35.1 adapter for FLAT-ATTENTION deterministic reference semantics.

This boundary binds exact inputs/outputs of FLAT's scalar Rust forward_reference
oracle. It intentionally carries no device routing, latency, throughput or
GPU-performance verdict.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from itd_research.experiment_schema import SourceIdentity


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class FlatReferenceCase:
    """Exact input identity for FLAT's scalar forward_reference oracle."""

    case_id: str
    source: SourceIdentity
    batch: int
    heads: int
    seq_len: int
    head_dim: int
    causal: bool
    softmax_scale: float | None
    q_sha256: str
    k_sha256: str
    v_sha256: str
    reference_symbol: str = "forward_reference"

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        if self.source.source != "Memorithm/FLAT-ATTENTION":
            raise ValueError("FLAT reference source must be Memorithm/FLAT-ATTENTION.")
        for name, value in (
            ("batch", self.batch),
            ("heads", self.heads),
            ("seq_len", self.seq_len),
            ("head_dim", self.head_dim),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive.")
        if self.softmax_scale is not None and (
            not math.isfinite(self.softmax_scale) or self.softmax_scale <= 0.0
        ):
            raise ValueError("softmax_scale must be finite and positive when supplied.")
        if self.reference_symbol != "forward_reference":
            raise ValueError("ITD-35.1 supports only FLAT forward_reference semantics.")
        for field_name in ("q_sha256", "k_sha256", "v_sha256"):
            object.__setattr__(
                self,
                field_name,
                _validate_sha256(field_name, getattr(self, field_name)),
            )

    @property
    def tensor_elements(self) -> int:
        return self.batch * self.heads * self.seq_len * self.head_dim

    @property
    def lse_elements(self) -> int:
        return self.batch * self.heads * self.seq_len


@dataclass(frozen=True)
class FlatReferenceResult:
    """Exact output/LSE identity from the FLAT scalar reference oracle."""

    case_id: str
    output_sha256: str
    lse_sha256: str
    execution_semantics: str = "scalar_rust_online_softmax_reference"

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        if self.execution_semantics != "scalar_rust_online_softmax_reference":
            raise ValueError("unsupported FLAT reference execution semantics.")
        object.__setattr__(
            self,
            "output_sha256",
            _validate_sha256("output_sha256", self.output_sha256),
        )
        object.__setattr__(
            self,
            "lse_sha256",
            _validate_sha256("lse_sha256", self.lse_sha256),
        )

    @property
    def authorizes_performance_claim(self) -> bool:
        """Reference-oracle evidence cannot establish hardware performance."""

        return False

    @property
    def authorizes_runtime_routing(self) -> bool:
        """Reference-oracle evidence cannot select a production kernel."""

        return False

    def assert_matches_case(self, case: FlatReferenceCase) -> None:
        if self.case_id != case.case_id:
            raise ValueError("FLAT reference result does not match case identity.")
