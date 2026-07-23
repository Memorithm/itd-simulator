"""Same-physics cross-code validation (research, Mission 5, H29).

Provides a second, INDEPENDENT 3D incompressible Navier-Stokes solver -- a
finite-difference fractional-step (projection) method whose spatial discretization is
genuinely different from the pseudo-spectral `spectral3d`. Running the *same* physics
(Taylor-Green) through both codes separates solver effects from physics/event/
dimensionality (the Mission 4 confound). This is cross-CODE (two in-repo numerical
methods), NOT cross-institution. Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.cross_code.comparison import (
    CrossCodeComparison,
    compare_taylorgreen,
    simulate_taylorgreen_fd_raw,
)
from itd_research.cross_code.fd_solver import (
    FDSimulationResult,
    max_divergence,
    simulate_fd,
    taylor_green_fd,
)
from itd_research.cross_code.normalization import METHODS, normalize_run, normalize_runs
from itd_research.cross_code.transfer import (
    CampaignResult,
    DirectionResult,
    evaluate_direction,
    run_competent_campaign,
    select_competent_method,
    transfer_auc,
)

__all__ = [
    "METHODS",
    "CampaignResult",
    "CrossCodeComparison",
    "DirectionResult",
    "FDSimulationResult",
    "compare_taylorgreen",
    "evaluate_direction",
    "max_divergence",
    "normalize_run",
    "normalize_runs",
    "run_competent_campaign",
    "select_competent_method",
    "simulate_fd",
    "simulate_taylorgreen_fd_raw",
    "taylor_green_fd",
    "transfer_auc",
]
