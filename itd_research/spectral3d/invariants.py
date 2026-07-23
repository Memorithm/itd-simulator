"""Global invariants and diagnostics for 3D spectral fields (research)."""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.grids import SpectralGrid3D
from itd_research.spectral3d.operators import curl

FloatArray: TypeAlias = NDArray[np.float64]


def kinetic_energy(u: FloatArray, v: FloatArray, w: FloatArray) -> float:
    """Mean kinetic energy ``<|u|^2>/2``."""
    return 0.5 * float(np.mean(u**2 + v**2 + w**2))


def mean_enstrophy(u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D) -> float:
    """Mean enstrophy ``<|omega|^2>/2``."""
    ox, oy, oz = curl(u, v, w, grid)
    return 0.5 * float(np.mean(ox**2 + oy**2 + oz**2))


def mean_helicity(u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D) -> float:
    """Mean helicity ``<u . omega>``."""
    ox, oy, oz = curl(u, v, w, grid)
    return float(np.mean(u * ox + v * oy + w * oz))


def dissipation_rate(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D, viscosity: float
) -> float:
    """Viscous dissipation rate ``nu * <|omega|^2>`` (homogeneous incompressible)."""
    return float(viscosity) * 2.0 * mean_enstrophy(u, v, w, grid)
