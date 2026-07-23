"""Explicit 3D vorticity-equation budget with closure check (research).

The incompressible vorticity equation is

    d omega/d t = -(u.grad) omega + (omega.grad) u + nu laplacian(omega) + curl(f).

This module evaluates each right-hand-side term (advection, stretching+tilting,
viscous diffusion, forcing curl) spectrally at a snapshot, estimates the Eulerian
temporal change from two consecutive snapshots, and reports the closure residual

    residual = d omega/d t - RHS,

globally (RMS, relative to the Eulerian change) and locally (Linf). Vector terms
are summarised by magnitude and by orientation change. Quantifying this closure is
one of the principal scientific reasons for the 3D solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.grids import SpectralGrid3D
from itd_research.spectral3d.operators import curl, gradient_scalar

FloatArray: TypeAlias = NDArray[np.float64]
Vector: TypeAlias = tuple[FloatArray, FloatArray, FloatArray]


def _rms_vector(vector: Vector) -> float:
    return float(np.sqrt(np.mean(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)))


def _advection(u: Vector, omega: Vector, grid: SpectralGrid3D) -> Vector:
    """``-(u.grad) omega`` component-wise."""
    result = []
    for component in omega:
        gx, gy, gz = gradient_scalar(component, grid)
        result.append(-(u[0] * gx + u[1] * gy + u[2] * gz))
    return (result[0], result[1], result[2])


def _stretching(u: Vector, omega: Vector, grid: SpectralGrid3D) -> Vector:
    """``(omega.grad) u`` component-wise (stretching + tilting)."""
    result = []
    for component in u:
        gx, gy, gz = gradient_scalar(component, grid)
        result.append(omega[0] * gx + omega[1] * gy + omega[2] * gz)
    return (result[0], result[1], result[2])


def _diffusion(omega: Vector, grid: SpectralGrid3D, viscosity: float) -> Vector:
    """``nu laplacian(omega)`` component-wise (spectral Laplacian)."""
    from itd_research.spectral3d.operators import _irfft, _rfft

    factor = -viscosity * grid.k_squared
    return (
        _irfft(factor * _rfft(omega[0]), grid),
        _irfft(factor * _rfft(omega[1]), grid),
        _irfft(factor * _rfft(omega[2]), grid),
    )


@dataclass(frozen=True)
class VorticityBudget:
    """RMS of each vorticity-budget term and the closure residual."""

    eulerian_rms: float
    advection_rms: float
    stretching_rms: float
    diffusion_rms: float
    forcing_curl_rms: float
    residual_rms: float
    residual_linf: float

    @property
    def closure_fraction(self) -> float:
        """rms(residual) / rms(Eulerian change): closure quality (small is good)."""
        if self.eulerian_rms <= 0.0:
            return 0.0
        return self.residual_rms / self.eulerian_rms

    def as_dict(self) -> dict[str, float]:
        return {
            "eulerian_rms": self.eulerian_rms,
            "advection_rms": self.advection_rms,
            "stretching_rms": self.stretching_rms,
            "diffusion_rms": self.diffusion_rms,
            "forcing_curl_rms": self.forcing_curl_rms,
            "residual_rms": self.residual_rms,
            "residual_linf": self.residual_linf,
            "closure_fraction": self.closure_fraction,
        }


def vorticity_budget(
    velocity_before: Vector,
    velocity_after: Vector,
    delta_time: float,
    grid: SpectralGrid3D,
    viscosity: float,
    forcing_curl: Vector | None = None,
) -> VorticityBudget:
    """Evaluate the vorticity budget and its closure residual between two snapshots."""
    dt = float(delta_time)
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("delta_time must be finite and strictly positive.")
    omega0 = curl(velocity_before[0], velocity_before[1], velocity_before[2], grid)
    omega1 = curl(velocity_after[0], velocity_after[1], velocity_after[2], grid)
    eulerian = tuple((omega1[i] - omega0[i]) / dt for i in range(3))

    advection = _advection(velocity_before, omega0, grid)
    stretching = _stretching(velocity_before, omega0, grid)
    diffusion = _diffusion(omega0, grid, viscosity)
    curl_force: Vector = forcing_curl if forcing_curl is not None else (
        np.zeros(omega0[0].shape), np.zeros(omega0[0].shape), np.zeros(omega0[0].shape)
    )

    residual = tuple(
        eulerian[i] - (advection[i] + stretching[i] + diffusion[i] + curl_force[i])
        for i in range(3)
    )
    residual_field = np.sqrt(residual[0] ** 2 + residual[1] ** 2 + residual[2] ** 2)
    return VorticityBudget(
        eulerian_rms=_rms_vector(eulerian),
        advection_rms=_rms_vector(advection),
        stretching_rms=_rms_vector(stretching),
        diffusion_rms=_rms_vector(diffusion),
        forcing_curl_rms=_rms_vector(curl_force),
        residual_rms=_rms_vector(residual),
        residual_linf=float(np.max(residual_field)),
    )
