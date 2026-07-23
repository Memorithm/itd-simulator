"""Near-OOD abstention campaign (research, Mission 5, H31).

Mission 4's OOD cases were extremely different from the training family (astronomically
large distances, trivial separation). This module tests **subtle** domain shifts --
untrained circulation, viscosity, vortex spacing, and resolution on the same merger
family -- where the near-OOD flows are often still predictable. The goal is useful risk
reduction (abstain on the genuinely unreliable) without abstaining on nearly everything.
Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.ood_near.campaign import (
    NearOODResult,
    run_near_ood_campaign,
)

__all__ = ["NearOODResult", "run_near_ood_campaign"]
