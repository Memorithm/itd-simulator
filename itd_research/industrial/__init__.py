"""Industrial-readiness maturity assessment (research, H16).

Reports where the ITD software sits on an explicit IRL-0..9 maturity scale and what
gaps separate it from named standards -- **never** as a legal certification claim.
Scientific validation alone does not satisfy ISO 9001, ISO 26262, DO-178C,
IEC 61508, IEC 62304, or ISO/IEC 17025; this module produces a transparent,
evidence-anchored gap analysis instead. Experimental research code; it does not
modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.industrial.readiness import (
    IRL_SCALE,
    ReadinessAssessment,
    ReadinessCriterion,
    StandardGap,
    assess_readiness,
    standard_gaps,
)

__all__ = [
    "IRL_SCALE",
    "ReadinessAssessment",
    "ReadinessCriterion",
    "StandardGap",
    "assess_readiness",
    "standard_gaps",
]
