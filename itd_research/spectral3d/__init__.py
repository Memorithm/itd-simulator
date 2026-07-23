"""Deterministic pseudo-spectral 3D incompressible Navier-Stokes (research).

A NumPy-only, deterministic, periodic-box spectral solver in the
velocity-pressure projection formulation, built so the research layer can run a
genuine 3D CFD solver in-environment and study vortex stretching, tilting,
merger, and cascades, and feed the ITD-3D candidates.

Part of the isolated ``itd_research`` namespace: it never modifies the certified
V29.18 core, is never imported by ``itd_v29_core``, imports no plotting library at
import time, and performs no network access. It is explicitly experimental and is
**not** a certified revision.

Fourier conventions, projection, dealiasing, and integrator are documented in
``docs/research/ITD_SPECTRAL3D_PREDICTIVE_VALIDATION_SPEC.md`` and enforced by
tests in ``tests/test_spectral3d.py``.
"""

from __future__ import annotations

from itd_research.spectral3d.grids import SpectralGrid3D, spectral_grid_3d
from itd_research.spectral3d.initial_conditions import (
    abc_flow_velocity,
    corotating_tubes,
    isotropic_seed,
    taylor_green_velocity,
)
from itd_research.spectral3d.invariants import (
    dissipation_rate,
    kinetic_energy,
    mean_enstrophy,
    mean_helicity,
)
from itd_research.spectral3d.operators import (
    curl,
    divergence,
    gradient_scalar,
    laplacian_vector,
    project_solenoidal,
    vorticity,
)
from itd_research.spectral3d.simulation import (
    SimulationResult3D,
    simulate,
)
from itd_research.spectral3d.vorticity_budget import (
    VorticityBudget,
    vorticity_budget,
)

__all__ = (
    "SpectralGrid3D",
    "spectral_grid_3d",
    "divergence",
    "curl",
    "vorticity",
    "gradient_scalar",
    "laplacian_vector",
    "project_solenoidal",
    "kinetic_energy",
    "mean_enstrophy",
    "mean_helicity",
    "dissipation_rate",
    "abc_flow_velocity",
    "taylor_green_velocity",
    "corotating_tubes",
    "isotropic_seed",
    "simulate",
    "SimulationResult3D",
    "vorticity_budget",
    "VorticityBudget",
)
