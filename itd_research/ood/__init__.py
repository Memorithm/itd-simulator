"""Out-of-distribution detection and abstention for ITD prediction (research, H23).

Transparent distance-based OOD scoring (Mahalanobis, PCA residual, nearest training
sample) fitted on the in-distribution feature set, plus a selective-prediction layer
that abstains when the OOD score is high. The product should prefer abstention over
unjustified extrapolation. Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.ood.abstention import (
    SelectiveResult,
    risk_coverage_curve,
    selective_evaluation,
)
from itd_research.ood.reference import OODReference, fit_reference

__all__ = [
    "OODReference",
    "SelectiveResult",
    "fit_reference",
    "risk_coverage_curve",
    "selective_evaluation",
]
