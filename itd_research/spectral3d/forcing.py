"""Deterministic forcing options for the 3D spectral solver (research).

A forcing is a callable ``(u_hat, v_hat, w_hat, grid) -> (fx_hat, fy_hat, fz_hat)``
in spectral space. All options are deterministic (no random noise). Energy
injection is reported by the solver, not hidden.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.grids import SpectralGrid3D

ComplexArray: TypeAlias = NDArray[np.complex128]
Forcing: TypeAlias = Callable[
    [ComplexArray, ComplexArray, ComplexArray, SpectralGrid3D],
    tuple[ComplexArray, ComplexArray, ComplexArray],
]


def no_forcing(
    u_hat: ComplexArray, v_hat: ComplexArray, w_hat: ComplexArray, grid: SpectralGrid3D
) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
    """Zero forcing."""
    zero = np.zeros_like(u_hat)
    return zero, zero.copy(), zero.copy()


def linear_forcing(rate: float) -> Forcing:
    """Linear forcing ``f = rate * u`` restricted to low wavenumbers.

    Injects energy proportional to the resolved kinetic energy at the largest
    scales (``|k| <= 2``); deterministic and reported.
    """

    def forcing(
        u_hat: ComplexArray, v_hat: ComplexArray, w_hat: ComplexArray, grid: SpectralGrid3D
    ) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
        low = (grid.k_squared <= 4.0 + 1e-9).astype(np.float64)
        factor = float(rate) * low
        return factor * u_hat, factor * v_hat, factor * w_hat

    return forcing
