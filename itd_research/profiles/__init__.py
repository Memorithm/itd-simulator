"""Event-conditioned ITD profile registry and stability (research, Mission 5, H34).

The evidence shows different events favour different channels. A profile declares, for
one (flow family, event type), the channels/diagnostics/normalization/valid domain and
known failure modes -- and refuses to apply outside its declared domain. Stability is
tested by comparing per-channel importance across two independent sources of the same
event. Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.profiles.registry import REGISTRY, get_profile, select_profile
from itd_research.profiles.schema import EventProfile
from itd_research.profiles.stability import (
    ProfileStability,
    channel_importance,
    profile_stability,
)

__all__ = [
    "REGISTRY",
    "EventProfile",
    "ProfileStability",
    "channel_importance",
    "get_profile",
    "profile_stability",
    "select_profile",
]
