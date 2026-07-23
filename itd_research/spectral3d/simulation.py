"""RK4 time integration of the incompressible 3D Navier-Stokes equations (research).

Velocity-pressure projection formulation, rotational form of the nonlinear term,
2/3-dealiased, integrated with classical RK4 in spectral space:

    du_hat/dt = P[ dealias( u x omega ) ] - nu |k|^2 u_hat + f_hat,

where ``P`` is the Leray projection (pressure elimination). Divergence and an
advective CFL number are monitored; snapshots are stored in physical space.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.forcing import Forcing, no_forcing
from itd_research.spectral3d.grids import SpectralGrid3D
from itd_research.spectral3d.operators import _irfft, _project_hat, _rfft, divergence

FloatArray: TypeAlias = NDArray[np.float64]
ComplexArray: TypeAlias = NDArray[np.complex128]

Triple: TypeAlias = tuple[ComplexArray, ComplexArray, ComplexArray]


def _rhs(state: Triple, grid: SpectralGrid3D, viscosity: float, forcing: Forcing) -> Triple:
    u_hat, v_hat, w_hat = state
    u = _irfft(u_hat, grid)
    v = _irfft(v_hat, grid)
    w = _irfft(w_hat, grid)
    ox = _irfft(1j * (grid.ky * w_hat - grid.kz * v_hat), grid)
    oy = _irfft(1j * (grid.kz * u_hat - grid.kx * w_hat), grid)
    oz = _irfft(1j * (grid.kx * v_hat - grid.ky * u_hat), grid)
    # Lamb vector u x omega (rotational form); gradient part removed by projection.
    lx = v * oz - w * oy
    ly = w * ox - u * oz
    lz = u * oy - v * ox
    lx_hat = _rfft(lx) * grid.dealias
    ly_hat = _rfft(ly) * grid.dealias
    lz_hat = _rfft(lz) * grid.dealias
    lx_hat, ly_hat, lz_hat = _project_hat(lx_hat, ly_hat, lz_hat, grid)
    fx_hat, fy_hat, fz_hat = forcing(u_hat, v_hat, w_hat, grid)
    viscous = viscosity * grid.k_squared
    return (
        lx_hat - viscous * u_hat + fx_hat,
        ly_hat - viscous * v_hat + fy_hat,
        lz_hat - viscous * w_hat + fz_hat,
    )


@dataclass(frozen=True)
class SimulationResult3D:
    """Recorded physical-space velocity snapshots and per-snapshot diagnostics."""

    grid: SpectralGrid3D
    times: tuple[float, ...]
    velocity: tuple[tuple[FloatArray, FloatArray, FloatArray], ...]
    energy: tuple[float, ...]
    enstrophy: tuple[float, ...]
    helicity: tuple[float, ...]
    divergence_linf: tuple[float, ...]

    def snapshot(self, index: int) -> tuple[FloatArray, FloatArray, FloatArray]:
        return self.velocity[index]


def _diagnostics(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D
) -> tuple[float, float, float, float]:
    u_hat, v_hat, w_hat = _rfft(u), _rfft(v), _rfft(w)
    ox = _irfft(1j * (grid.ky * w_hat - grid.kz * v_hat), grid)
    oy = _irfft(1j * (grid.kz * u_hat - grid.kx * w_hat), grid)
    oz = _irfft(1j * (grid.kx * v_hat - grid.ky * u_hat), grid)
    energy = 0.5 * float(np.mean(u**2 + v**2 + w**2))
    enstrophy = 0.5 * float(np.mean(ox**2 + oy**2 + oz**2))
    helicity = float(np.mean(u * ox + v * oy + w * oz))
    divergence_linf = float(np.max(np.abs(divergence(u, v, w, grid))))
    return energy, enstrophy, helicity, divergence_linf


def cfl_number(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D, delta_time: float
) -> float:
    """Advective CFL number ``max|u| * dt / dx`` (dx = L/N)."""
    spacing = grid.length / grid.nodes
    peak = float(np.max(np.sqrt(u**2 + v**2 + w**2)))
    return peak * float(delta_time) / spacing


def simulate(
    velocity0: tuple[FloatArray, FloatArray, FloatArray],
    grid: SpectralGrid3D,
    viscosity: float,
    delta_time: float,
    steps: int,
    record_every: int = 1,
    forcing: Forcing = no_forcing,
    cfl_limit: float = 2.0,
) -> SimulationResult3D:
    """Integrate the 3D velocity field with RK4, recording physical snapshots."""
    u0, v0, w0 = (np.asarray(c, dtype=np.float64) for c in velocity0)
    if not (u0.shape == v0.shape == w0.shape == (grid.nodes, grid.nodes, grid.nodes)):
        raise ValueError("velocity components must be N x N x N matching the grid.")
    dt = float(delta_time)
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("delta_time must be finite and strictly positive.")
    if steps < 1 or record_every < 1:
        raise ValueError("steps and record_every must be positive integers.")
    if not np.isfinite(viscosity) or viscosity < 0.0:
        raise ValueError("viscosity must be finite and non-negative.")
    initial_cfl = cfl_number(u0, v0, w0, grid, dt)
    if initial_cfl > cfl_limit:
        raise ValueError(f"initial CFL {initial_cfl:.2f} exceeds limit {cfl_limit}.")

    def physical(spectral: Triple) -> tuple[FloatArray, FloatArray, FloatArray]:
        return _irfft(spectral[0], grid), _irfft(spectral[1], grid), _irfft(spectral[2], grid)

    def combine(base: Triple, increment: Triple, factor: float) -> Triple:
        return (
            base[0] + factor * increment[0],
            base[1] + factor * increment[1],
            base[2] + factor * increment[2],
        )

    # Project the initial field to guarantee it starts divergence-free.
    state: Triple = _project_hat(_rfft(u0), _rfft(v0), _rfft(w0), grid)
    times = [0.0]
    fu, fv, fw = physical(state)
    e0, z0, h0, d0 = _diagnostics(fu, fv, fw, grid)
    velocities: list[tuple[FloatArray, FloatArray, FloatArray]] = [(fu, fv, fw)]
    energy, enstrophy, helicity, divergence_linf = [e0], [z0], [h0], [d0]

    for step in range(1, steps + 1):
        k1 = _rhs(state, grid, viscosity, forcing)
        k2 = _rhs(combine(state, k1, 0.5 * dt), grid, viscosity, forcing)
        k3 = _rhs(combine(state, k2, 0.5 * dt), grid, viscosity, forcing)
        k4 = _rhs(combine(state, k3, dt), grid, viscosity, forcing)
        state = (
            state[0] + (dt / 6.0) * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]),
            state[1] + (dt / 6.0) * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]),
            state[2] + (dt / 6.0) * (k1[2] + 2.0 * k2[2] + 2.0 * k3[2] + k4[2]),
        )
        if step % record_every == 0 or step == steps:
            fields = physical(state)
            if not all(np.all(np.isfinite(f)) for f in fields):
                raise FloatingPointError("simulation went non-finite; reduce dt or add viscosity.")
            e, z, h, d = _diagnostics(fields[0], fields[1], fields[2], grid)
            velocities.append(fields)
            times.append(step * dt)
            energy.append(e)
            enstrophy.append(z)
            helicity.append(h)
            divergence_linf.append(d)

    return SimulationResult3D(
        grid=grid,
        times=tuple(times),
        velocity=tuple(velocities),
        energy=tuple(energy),
        enstrophy=tuple(enstrophy),
        helicity=tuple(helicity),
        divergence_linf=tuple(divergence_linf),
    )
