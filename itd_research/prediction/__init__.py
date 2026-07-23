"""Falsifiable vortex-transition prediction study (research, H7).

Tests whether the ITD signature predicts an *impending* vortex merger earlier or
more reliably than established scalar diagnostics, under a leakage-safe
leave-one-run-out protocol with ITD-independent event labels. Experimental research
code; it does not modify or re-certify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.prediction.ensemble import (
    MergerRun,
    RunConfig,
    default_ensemble,
    quick_ensemble,
    simulate_merger_run,
)
from itd_research.prediction.evaluation import (
    FEATURE_SETS,
    PredictionMetrics,
    classify_h7,
    evaluate_all,
)
from itd_research.prediction.events import count_vortex_cores, detect_merger_frame

__all__ = [
    "FEATURE_SETS",
    "MergerRun",
    "PredictionMetrics",
    "RunConfig",
    "classify_h7",
    "count_vortex_cores",
    "default_ensemble",
    "detect_merger_frame",
    "evaluate_all",
    "quick_ensemble",
    "simulate_merger_run",
]
