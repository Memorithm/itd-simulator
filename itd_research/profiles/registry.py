"""Registry of event-conditioned ITD profiles (research, Mission 5).

Profiles are grounded in the Mission 4/5 evidence: the merger favours structural
channels (localization/flatness), while the enstrophy-defined breakdown is caught by
magnitude channels. Domains are declared conservatively; ``select_profile`` refuses to
apply a profile outside its declared conditions.
"""

from __future__ import annotations

from itd_research.profiles.schema import EventProfile

REGISTRY: dict[str, EventProfile] = {
    "merger_2d": EventProfile(
        profile_id="merger_2d",
        flow_family="co_rotating_vortex_pair",
        event_type="merger",
        dimensionality="2D",
        # From H25: localization / vorticity_flatness / heterogeneity lead; magnitude
        # channels anti-predict the viscous merger.
        required_channels=("localization", "heterogeneity"),
        optional_channels=("roughness", "sign_mixing"),
        established_diagnostics=("q_positive_fraction", "vorticity_flatness"),
        normalization="train-source z-score",
        calibration_source="spectral_ns perturbed merger ensemble",
        valid_reynolds_range=(50.0, 5000.0),
        valid_resolution_range=(48, 256),
        valid_noise_range=(0.0, 0.10),
        prediction_horizon="<= 4 frames",
        ood_reference="merger feature Mahalanobis reference",
        thresholds={"decision": 0.5},
        uncertainty="grouped bootstrap AUC CI",
        known_failure_modes=(
            "magnitude channels (intensity/enstrophy) anti-predict; excluded",
            "does not transfer to breakdown/shedding events",
        ),
    ),
    "taylorgreen_breakdown_3d": EventProfile(
        profile_id="taylorgreen_breakdown_3d",
        flow_family="taylor_green",
        event_type="breakdown",
        dimensionality="3D (planar features)",
        # From H25/H34: the enstrophy-defined breakdown is caught by nearly all channels;
        # magnitude channels are as good as structural ones here.
        required_channels=("intensity", "heterogeneity"),
        optional_channels=("localization", "roughness", "sign_mixing"),
        established_diagnostics=("enstrophy", "palinstrophy"),
        normalization="train-source z-score",
        calibration_source="spectral3d perturbed Taylor-Green ensemble",
        valid_reynolds_range=(30.0, 2000.0),
        valid_resolution_range=(16, 64),
        valid_noise_range=(0.0, 0.10),
        prediction_horizon="<= 4 frames",
        ood_reference="taylor-green feature Mahalanobis reference",
        thresholds={"decision": 0.5},
        uncertainty="grouped bootstrap AUC CI",
        known_failure_modes=(
            "event is enstrophy-defined, so established diagnostics predict it trivially",
            "temporal_deformation is the weakest channel here",
            "does not transfer across solvers at fixed threshold (H19/H29 event-time shift)",
        ),
    ),
}


def get_profile(profile_id: str) -> EventProfile:
    """Return a profile by id (KeyError if unknown -- profiles are never guessed)."""
    return REGISTRY[profile_id]


def select_profile(event_type: str, *, reynolds: float, resolution: int, noise: float) -> tuple[EventProfile | None, str]:
    """Select the profile for an event type if the conditions are in its domain."""
    for profile in REGISTRY.values():
        if profile.event_type == event_type:
            ok, reason = profile.applies_to(reynolds=reynolds, resolution=resolution, noise=noise)
            if ok:
                return profile, "selected"
            return None, f"profile {profile.profile_id} declined: {reason}"
    return None, f"no profile for event_type {event_type!r}"
