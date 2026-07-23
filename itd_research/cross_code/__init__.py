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

__all__ = [
    "CrossCodeComparison",
    "FDSimulationResult",
    "compare_taylorgreen",
    "max_divergence",
    "simulate_fd",
    "simulate_taylorgreen_fd_raw",
    "taylor_green_fd",
]
