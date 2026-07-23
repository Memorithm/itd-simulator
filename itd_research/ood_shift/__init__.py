"""Shift-aware OOD detection and calibrated abstention (research, Mission 6, H43-H45).

Mission 5's near-OOD study used one global Mahalanobis radius and one hard threshold, and
over-abstained on ~85% of still-predictable shifted frames. This package adds a per-axis
severity view that localizes *which* channel shifts (H43), a transparent monotone
confidence discount, and a three-state accept / accept-with-reduced-confidence / abstain
policy scored by a false-confidence-vs-unnecessary-abstention utility (H44/H45). The goal
is to reduce confidence intelligently under domain shift without rejecting usable data.
Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.ood_shift.campaign import ShiftCampaignResult, run_shift_campaign
from itd_research.ood_shift.detector import (
    ShiftReference,
    fit_shift_reference,
    monotone_separation,
)
from itd_research.ood_shift.policy import (
    PolicyDecision,
    PolicyOutcome,
    binary_policy,
    confidence_discount,
    degradation_policy,
    evaluate_policy,
    no_abstention_policy,
    three_state_policy,
)

__all__ = [
    "PolicyDecision",
    "PolicyOutcome",
    "ShiftCampaignResult",
    "ShiftReference",
    "binary_policy",
    "confidence_discount",
    "degradation_policy",
    "evaluate_policy",
    "fit_shift_reference",
    "monotone_separation",
    "no_abstention_policy",
    "run_shift_campaign",
    "three_state_policy",
]
