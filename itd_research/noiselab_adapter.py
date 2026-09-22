"""ITD-37.0 NoiseLab perturbation adapter contracts.

The adapter preserves raw and perturbed observation identities and follows the
"characterize before filtering" rule.  It transports controlled perturbation
provenance but does not establish causal direction by itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from itd_research.experiment_schema import SourceIdentity, SplitRole


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class NoiseInterventionRef:
    """Exact provenance for one controlled non-final NoiseLab intervention."""

    intervention_id: str
    role: SplitRole
    source: SourceIdentity
    family: str
    seed: int
    intervention_site: str
    parameters_sha256: str
    raw_observation_sha256: str
    perturbed_observation_sha256: str
    filtered_observation_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.intervention_id.strip():
            raise ValueError("intervention_id must not be empty.")
        if self.role is SplitRole.FINAL:
            raise ValueError("ITD-37.0 adapter cannot consume final perturbation material.")
        if self.source.source != "Memorithm/NoiseLab":
            raise ValueError("noise intervention source must be Memorithm/NoiseLab.")
        if not self.family.strip():
            raise ValueError("noise family must not be empty.")
        if self.seed < 0:
            raise ValueError("seed must be non-negative.")
        if not self.intervention_site.strip():
            raise ValueError("intervention_site must not be empty.")
        for field_name in (
            "parameters_sha256",
            "raw_observation_sha256",
            "perturbed_observation_sha256",
        ):
            object.__setattr__(
                self,
                field_name,
                _validate_sha256(field_name, getattr(self, field_name)),
            )
        if self.filtered_observation_sha256 is not None:
            object.__setattr__(
                self,
                "filtered_observation_sha256",
                _validate_sha256(
                    "filtered_observation_sha256",
                    self.filtered_observation_sha256,
                ),
            )

    @property
    def raw_observation_preserved(self) -> bool:
        return True

    @property
    def authorizes_causal_claim(self) -> bool:
        return False


@dataclass(frozen=True)
class PerturbationResponseRecord:
    """Measured response attached to one exact NoiseLab intervention."""

    intervention: NoiseInterventionRef
    amplitude: float
    structural_delta: float
    task_error_delta: float
    uncertainty_delta: float
    response_unit: str

    def __post_init__(self) -> None:
        for name, value in (
            ("amplitude", self.amplitude),
            ("structural_delta", self.structural_delta),
            ("task_error_delta", self.task_error_delta),
            ("uncertainty_delta", self.uncertainty_delta),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if not self.response_unit.strip():
            raise ValueError("response_unit must not be empty.")

    @property
    def authorizes_causal_claim(self) -> bool:
        return False
