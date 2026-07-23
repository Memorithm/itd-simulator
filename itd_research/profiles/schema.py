"""Event-profile schema (research, Mission 5).

A profile declares the channels and the valid operating domain for one (flow family,
event type). ``applies_to`` returns whether an observation's Reynolds number,
resolution, and noise level fall inside the declared ranges; the product must never
silently apply a profile outside its domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventProfile:
    """A declared, domain-bounded event-conditioned ITD profile."""

    profile_id: str
    flow_family: str
    event_type: str
    dimensionality: str
    required_channels: tuple[str, ...]
    optional_channels: tuple[str, ...]
    established_diagnostics: tuple[str, ...]
    normalization: str
    calibration_source: str
    valid_reynolds_range: tuple[float, float]
    valid_resolution_range: tuple[int, int]
    valid_noise_range: tuple[float, float]
    prediction_horizon: str
    ood_reference: str
    thresholds: dict[str, float]
    uncertainty: str
    known_failure_modes: tuple[str, ...] = field(default_factory=tuple)

    def applies_to(self, *, reynolds: float, resolution: int, noise: float) -> tuple[bool, str]:
        """Whether the profile is valid for these conditions; reason if not."""
        if not self.valid_reynolds_range[0] <= reynolds <= self.valid_reynolds_range[1]:
            return False, f"Reynolds {reynolds} outside {self.valid_reynolds_range}"
        if not self.valid_resolution_range[0] <= resolution <= self.valid_resolution_range[1]:
            return False, f"resolution {resolution} outside {self.valid_resolution_range}"
        if not self.valid_noise_range[0] <= noise <= self.valid_noise_range[1]:
            return False, f"noise {noise} outside {self.valid_noise_range}"
        return True, "in declared domain"

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "flow_family": self.flow_family,
            "event_type": self.event_type,
            "dimensionality": self.dimensionality,
            "required_channels": list(self.required_channels),
            "optional_channels": list(self.optional_channels),
            "established_diagnostics": list(self.established_diagnostics),
            "normalization": self.normalization,
            "calibration_source": self.calibration_source,
            "valid_reynolds_range": list(self.valid_reynolds_range),
            "valid_resolution_range": list(self.valid_resolution_range),
            "valid_noise_range": list(self.valid_noise_range),
            "prediction_horizon": self.prediction_horizon,
            "ood_reference": self.ood_reference,
            "thresholds": self.thresholds,
            "uncertainty": self.uncertainty,
            "known_failure_modes": list(self.known_failure_modes),
        }
