"""ITD-39.0 SciRust ITD parity qualification contracts.

SciRust already contains the independent pure-Rust scirust-itd crate. This
module therefore qualifies that existing implementation instead of creating a
second Rust port. It keeps hand-derived analytical evidence distinct from
Python-generated regression snapshots.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity


class OracleEvidenceClass(StrEnum):
    """Authority class of an oracle used for cross-language qualification."""

    HAND_DERIVED_ANALYTICAL = "hand_derived_analytical"
    PYTHON_REGRESSION_SNAPSHOT = "python_regression_snapshot"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class ScirustItdImplementationRef:
    """Exact identity of the existing SciRust Rust implementation."""

    source: SourceIdentity
    crate_name: str = "scirust-itd"
    crate_version: str = "0.1.0"
    test_command: str = "cargo test -p scirust-itd"
    scenario_command: str = "cargo run -p scirust-itd --example itd_scenarios"

    def __post_init__(self) -> None:
        if self.source.source != "Memorithm/scirust":
            raise ValueError("Rust ITD implementation source must be Memorithm/scirust.")
        if self.crate_name != "scirust-itd":
            raise ValueError("ITD-39.0 qualifies only the existing scirust-itd crate.")
        if not self.crate_version.strip():
            raise ValueError("crate_version must not be empty.")
        if not self.test_command.strip() or not self.scenario_command.strip():
            raise ValueError("SciRust qualification commands must not be empty.")

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source.as_dict(),
            "crate_name": self.crate_name,
            "crate_version": self.crate_version,
            "test_command": self.test_command,
            "scenario_command": self.scenario_command,
        }


@dataclass(frozen=True)
class OracleFixtureRef:
    """Exact identity of one analytical or regression fixture set."""

    fixture_id: str
    evidence_class: OracleEvidenceClass
    source: SourceIdentity
    path: str
    sha256: str

    def __post_init__(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id must not be empty.")
        if not self.path.strip():
            raise ValueError("fixture path must not be empty.")
        object.__setattr__(self, "sha256", _validate_sha256("sha256", self.sha256))

    def as_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "evidence_class": self.evidence_class.value,
            "source": self.source.as_dict(),
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ScirustItdParityContract:
    """Frozen implementation + oracle identities for one parity campaign."""

    implementation: ScirustItdImplementationRef
    model_baseline: str
    fixtures: tuple[OracleFixtureRef, ...]
    contract_version: str = "itd-scirust-parity-v1"

    def __post_init__(self) -> None:
        if self.contract_version != "itd-scirust-parity-v1":
            raise ValueError("unsupported SciRust parity contract version.")
        if self.model_baseline != "ITD V29.18":
            raise ValueError("ITD-39.0 parity baseline must remain ITD V29.18.")
        if not self.fixtures:
            raise ValueError("parity contract requires at least one oracle fixture.")
        identifiers = tuple(item.fixture_id for item in self.fixtures)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("oracle fixture identifiers must be unique.")
        classes = {item.evidence_class for item in self.fixtures}
        required = {
            OracleEvidenceClass.HAND_DERIVED_ANALYTICAL,
            OracleEvidenceClass.PYTHON_REGRESSION_SNAPSHOT,
        }
        if not required.issubset(classes):
            raise ValueError(
                "parity contract requires both analytical and regression evidence."
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "implementation": self.implementation.as_dict(),
            "model_baseline": self.model_baseline,
            "fixtures": [item.as_dict() for item in self.fixtures],
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
class NumericParityObservation:
    """One cross-language or analytical numeric comparison."""

    observation_id: str
    evidence_class: OracleEvidenceClass
    expected: float
    observed: float
    absolute_tolerance: float
    relative_tolerance: float

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must not be empty.")
        for name, value in (
            ("expected", self.expected),
            ("observed", self.observed),
            ("absolute_tolerance", self.absolute_tolerance),
            ("relative_tolerance", self.relative_tolerance),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if self.absolute_tolerance < 0.0 or self.relative_tolerance < 0.0:
            raise ValueError("parity tolerances must be non-negative.")

    @property
    def absolute_error(self) -> float:
        return abs(self.observed - self.expected)

    @property
    def within_tolerance(self) -> bool:
        allowed = self.absolute_tolerance + self.relative_tolerance * max(
            abs(self.expected),
            abs(self.observed),
        )
        return self.absolute_error <= allowed


@dataclass(frozen=True)
class ScirustItdParityReport:
    """Observed qualification report preserving evidence-class distinctions."""

    contract_fingerprint: str
    observations: tuple[NumericParityObservation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "contract_fingerprint",
            _validate_sha256("contract_fingerprint", self.contract_fingerprint),
        )
        if not self.observations:
            raise ValueError("parity report requires observations.")
        identifiers = tuple(item.observation_id for item in self.observations)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("parity observation identifiers must be unique.")

    @property
    def failed_observation_ids(self) -> tuple[str, ...]:
        return tuple(
            item.observation_id
            for item in self.observations
            if not item.within_tolerance
        )

    @property
    def all_within_tolerance(self) -> bool:
        return not self.failed_observation_ids

    @property
    def authorizes_physical_validity_claim(self) -> bool:
        """Numerical parity cannot establish physical validity or universality."""

        return False

    @property
    def authorizes_v30_promotion(self) -> bool:
        """Parity with V29.18 cannot promote a V30 research mechanism."""

        return False

    def assert_matches_contract(self, contract: ScirustItdParityContract) -> None:
        if self.contract_fingerprint != contract.fingerprint():
            raise ValueError("parity report does not match SciRust parity contract.")
