"""Tests for the event-conditioned profile registry and stability (Mission 5, H34)."""

from __future__ import annotations

from itd_research.profiles.registry import REGISTRY, get_profile, select_profile
from itd_research.profiles.stability import profile_stability


def test_registry_profiles_declare_domains() -> None:
    assert set(REGISTRY) == {"merger_2d", "taylorgreen_breakdown_3d"}
    merger = get_profile("merger_2d")
    assert merger.event_type == "merger"
    assert "localization" in merger.required_channels
    # magnitude channels are a declared failure mode, not required
    assert "intensity" not in merger.required_channels


def test_select_profile_refuses_out_of_domain() -> None:
    profile, reason = select_profile("merger", reynolds=200.0, resolution=80, noise=0.02)
    assert profile is not None and profile.profile_id == "merger_2d"
    # Reynolds outside the declared range -> refuse, with a reason (never silent).
    none_profile, reason2 = select_profile("merger", reynolds=1e6, resolution=80, noise=0.02)
    assert none_profile is None and "Reynolds" in reason2
    unknown, reason3 = select_profile("nonexistent_event", reynolds=200.0, resolution=80, noise=0.0)
    assert unknown is None and "no profile" in reason3


def test_profile_stability_detects_reshuffle() -> None:
    channels = ["intensity", "heterogeneity", "localization", "roughness", "sign_mixing",
                "temporal_deformation", "structure_score", "enstrophy", "palinstrophy",
                "vorticity_rms", "vorticity_flatness", "q_positive_fraction", "swirl_mean"]
    same = {c: float(i) for i, c in enumerate(channels)}
    stable = profile_stability(same, same)
    assert stable.rank_correlation > 0.99
    assert stable.verdict == "supported within tested scope"
    reversed_imp = {c: float(len(channels) - i) for i, c in enumerate(channels)}
    unstable = profile_stability(same, reversed_imp)
    assert unstable.rank_correlation < -0.5
    assert unstable.verdict == "not supported"
