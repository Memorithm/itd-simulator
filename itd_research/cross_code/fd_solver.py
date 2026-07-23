"""Independent finite-difference projection solver for 3D incompressible flow (research).

A second, numerically distinct 3D Navier-Stokes code. The genuine numerical difference
from `spectral3d` is the discretization of the **nonlinear advection and viscous
terms**: here they use 2nd-order central finite differences in physical space with an
explicit fractional-step (Chorin) time advance, versus `spectral3d`'s pseudo-spectral
rotational form with RK4. The Leray pressure projection is done spectrally (exact,
divergence-free, and free of the odd-even null mode a collocated finite-difference
Poisson solve would suffer). So the codes differ in truncation error, dispersion, and
time integration while sharing the mathematical projection; comparing Taylor-Green
through both separates solver from physics (Mission 5, H29).

Axis convention matches `spectral3d`: arrays are ``(x, y, z)`` (`indexing='ij'`), a
periodic box of side ``2*pi`` with spacing ``h = 2*pi/N``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d import SpectralGrid3D, project_solenoidal, spectral_grid_3d

FloatArray: TypeAlias = NDArray[np.float64]


def _ddx(f: FloatArray, h: float, axis: int) -> FloatArray:
    return (np.roll(f, -1, axis=axis) - np.roll(f, 1, axis=axis)) / (2.0 * h)


def _laplacian(f: FloatArray, h: float) -> FloatArray:
    acc = -6.0 * f
    for axis in (0, 1, 2):
        acc = acc + np.roll(f, -1, axis=axis) + np.roll(f, 1, axis=axis)
    return acc / (h * h)


def _divergence(u: FloatArray, v: FloatArray, w: FloatArray, h: float) -> FloatArray:
    return _ddx(u, h, 0) + _ddx(v, h, 1) + _ddx(w, h, 2)


def _advection(u: FloatArray, v: FloatArray, w: FloatArray, h: float) -> tuple[FloatArray, FloatArray, FloatArray]:
    def adv(field: FloatArray) -> FloatArray:
        return u * _ddx(field, h, 0) + v * _ddx(field, h, 1) + w * _ddx(field, h, 2)

    return adv(u), adv(v), adv(w)


def max_divergence(u: FloatArray, v: FloatArray, w: FloatArray, length: float = 2.0 * np.pi) -> float:
    h = length / u.shape[0]
    return float(np.max(np.abs(_divergence(u, v, w, h))))


def taylor_green_fd(grid: SpectralGrid3D) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Taylor-Green initial field on the FD grid (same physics as spectral3d's)."""
    xx, yy, zz = grid.mesh()
    u = np.cos(xx) * np.sin(yy) * np.sin(zz)
    v = -np.sin(xx) * np.cos(yy) * np.sin(zz)
    w = np.zeros_like(u)
    return np.ascontiguousarray(u), np.ascontiguousarray(v), np.ascontiguousarray(w)


@dataclass(frozen=True)
class FDSimulationResult:
    """Recorded velocity snapshots from the finite-difference solver."""

    grid: SpectralGrid3D
    times: tuple[float, ...]
    velocity: tuple[tuple[FloatArray, FloatArray, FloatArray], ...]


def simulate_fd(
    velocity0: tuple[FloatArray, FloatArray, FloatArray],
    grid: SpectralGrid3D,
    viscosity: float,
    delta_time: float,
    steps: int,
    record_every: int,
    length: float = 2.0 * np.pi,
) -> FDSimulationResult:
    """Integrate incompressible flow with the explicit FD fractional-step method."""
    h = length / grid.nodes
    u, v, w = (np.ascontiguousarray(c, dtype=np.float64) for c in velocity0)
    u, v, w = project_solenoidal(u, v, w, grid)  # start divergence-free
    dt = float(delta_time)
    if dt <= 0.0 or steps < 1 or record_every < 1:
        raise ValueError("delta_time>0, steps>=1, record_every>=1 required.")

    times = [0.0]
    snapshots = [(u.copy(), v.copy(), w.copy())]
    for step in range(1, steps + 1):
        au, av, aw = _advection(u, v, w, h)
        u_star = u + dt * (-au + viscosity * _laplacian(u, h))
        v_star = v + dt * (-av + viscosity * _laplacian(v, h))
        w_star = w + dt * (-aw + viscosity * _laplacian(w, h))
        u, v, w = project_solenoidal(u_star, v_star, w_star, grid)
        if not np.all(np.isfinite(u)):
            raise FloatingPointError("FD simulation went non-finite; reduce delta_time.")
        if step % record_every == 0 or step == steps:
            times.append(step * dt)
            snapshots.append((u.copy(), v.copy(), w.copy()))
    return FDSimulationResult(grid, tuple(times), tuple(snapshots))


def make_grid(nodes: int) -> SpectralGrid3D:
    """Reuse the spectral grid (coordinates + rfft wavenumbers) for the FD solver."""
    return spectral_grid_3d(nodes)
