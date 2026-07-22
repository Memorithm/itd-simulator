"""Deterministic analytical and manufactured 3D velocity fields (research).

These fields validate the 3D operators and velocity-gradient diagnostics against
independent references. Linear fields have an exact, spatially constant
velocity-gradient tensor, which the second-order operators must recover to
round-off; nonlinear fields (Burgers vortex, Taylor-Green) are used for
convergence and qualitative diagnostic comparison.

Convention matches :mod:`itd_research.diagnostics_3d.operators`: 3D fields have
shape ``(nz, ny, nx)`` with 1D coordinates ``x`` (axis 2), ``y`` (axis 1),
``z`` (axis 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class Grid3D:
    """A validated structured 3D grid with explicit coordinates and mesh."""

    x: FloatArray
    y: FloatArray
    z: FloatArray
    xx: FloatArray
    yy: FloatArray
    zz: FloatArray
    boundary_mode: str

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.z.size, self.y.size, self.x.size)


def finite_grid_3d(nodes: int, lower: float, upper: float) -> Grid3D:
    """Endpoint-included uniform cubic grid on ``[lower, upper]**3``."""
    if nodes < 3:
        raise ValueError("A finite grid needs at least three nodes per axis.")
    if not (np.isfinite(lower) and np.isfinite(upper)) or upper <= lower:
        raise ValueError("Require finite bounds with upper > lower.")
    coordinates: FloatArray = np.linspace(lower, upper, nodes, dtype=np.float64)
    zz: FloatArray
    yy: FloatArray
    xx: FloatArray
    zz, yy, xx = np.meshgrid(coordinates, coordinates, coordinates, indexing="ij")
    return Grid3D(coordinates, coordinates, coordinates, xx, yy, zz, "finite")


def periodic_grid_3d(nodes: int, period: float) -> Grid3D:
    """Endpoint-excluded uniform cubic grid with the given ``period``."""
    if nodes < 3:
        raise ValueError("A periodic grid needs at least three nodes per axis.")
    if not np.isfinite(period) or period <= 0.0:
        raise ValueError("period must be finite and strictly positive.")
    spacing = float(period) / float(nodes)
    coordinates: FloatArray = np.arange(nodes, dtype=np.float64) * spacing
    zz: FloatArray
    yy: FloatArray
    xx: FloatArray
    zz, yy, xx = np.meshgrid(coordinates, coordinates, coordinates, indexing="ij")
    return Grid3D(coordinates, coordinates, coordinates, xx, yy, zz, "periodic")


def linear_velocity(
    gradient: FloatArray, grid: Grid3D
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Velocity field ``u_i = sum_j J[i, j] * x_j`` for a constant gradient ``J``.

    The velocity-gradient tensor of this field is exactly ``gradient`` everywhere,
    so second-order finite differences recover it to round-off.
    """
    matrix = np.asarray(gradient, dtype=np.float64)
    if matrix.shape != (3, 3):
        raise ValueError("gradient must be a 3x3 matrix.")
    coordinates = np.stack((grid.xx, grid.yy, grid.zz), axis=0)  # (3, nz, ny, nx)
    velocity = np.einsum("ij,jzyx->izyx", matrix, coordinates)
    return (
        np.ascontiguousarray(velocity[0]),
        np.ascontiguousarray(velocity[1]),
        np.ascontiguousarray(velocity[2]),
    )


# --------------------------------------------------------------------------- #
# Canonical constant velocity-gradient tensors (exact oracle inputs).         #
# --------------------------------------------------------------------------- #


def rigid_rotation_gradient(rate: float) -> FloatArray:
    """Rigid rotation about z: ``u = -Omega y``, ``v = Omega x``, ``w = 0``."""
    omega = float(rate)
    return np.array(
        [[0.0, -omega, 0.0], [omega, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64
    )


def pure_strain_gradient(rate: float) -> FloatArray:
    """Incompressible planar strain ``u = a x``, ``v = -a y``, ``w = 0``."""
    a = float(rate)
    return np.array(
        [[a, 0.0, 0.0], [0.0, -a, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64
    )


def simple_shear_gradient(rate: float) -> FloatArray:
    """Simple shear ``u = gamma y``, ``v = 0``, ``w = 0`` (non-vortical swirl)."""
    gamma = float(rate)
    return np.array(
        [[0.0, gamma, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64
    )


def rotation_plus_strain_gradient(rate: float, strain: float) -> FloatArray:
    """Superposed rigid rotation about z and planar strain."""
    return rigid_rotation_gradient(rate) + pure_strain_gradient(strain)


def axisymmetric_stretch_rotation_gradient(rate: float, axial_strain: float) -> FloatArray:
    """Rotation about z with incompressible axial stretching along z."""
    a = float(axial_strain)
    return rigid_rotation_gradient(rate) + np.array(
        [[-0.5 * a, 0.0, 0.0], [0.0, -0.5 * a, 0.0], [0.0, 0.0, a]], dtype=np.float64
    )


# --------------------------------------------------------------------------- #
# Nonlinear analytical fields.                                                 #
# --------------------------------------------------------------------------- #


def _radial_factor(r_squared: FloatArray, core: float) -> FloatArray:
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = -np.expm1(-r_squared / core**2) / r_squared
    return np.where(r_squared > 0.0, factor, 1.0 / core**2)


def burgers_vortex(
    grid: Grid3D,
    circulation: float,
    core_radius: float,
    axial_strain: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Burgers vortex: azimuthal swirl with axisymmetric strain and axial stretch.

    ``vx = -(a/2) x - (Gamma/2pi) g(r^2) y``,
    ``vy = -(a/2) y + (Gamma/2pi) g(r^2) x``, ``vz = a z``, with
    ``g(r^2) = (1 - exp(-r^2/rc^2)) / r^2`` (regular at the axis). The axial
    vorticity is ``(Gamma/(pi rc^2)) exp(-r^2/rc^2)``.
    """
    core = float(core_radius)
    if not np.isfinite(core) or core <= 0.0:
        raise ValueError("core_radius must be finite and strictly positive.")
    a = float(axial_strain)
    gamma = float(circulation)
    r_squared = grid.xx**2 + grid.yy**2
    swirl = (gamma / (2.0 * np.pi)) * _radial_factor(r_squared, core)
    vx = -0.5 * a * grid.xx - swirl * grid.yy
    vy = -0.5 * a * grid.yy + swirl * grid.xx
    vz = a * grid.zz
    return vx.astype(np.float64), vy.astype(np.float64), vz.astype(np.float64)


def burgers_vortex_axial_vorticity(
    grid: Grid3D, circulation: float, core_radius: float
) -> FloatArray:
    """Analytical axial vorticity of the Burgers vortex."""
    core = float(core_radius)
    r_squared = grid.xx**2 + grid.yy**2
    peak = float(circulation) / (np.pi * core**2)
    return np.asarray(peak * np.exp(-r_squared / core**2), dtype=np.float64)


def taylor_green_3d(
    grid: Grid3D, amplitude: float, wavenumber: float
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Standard Taylor-Green initial field (incompressible, w = 0).

    ``u = V sin(kx) cos(ky) cos(kz)``, ``v = -V cos(kx) sin(ky) cos(kz)``,
    ``w = 0``. Only the initial condition is represented; no time evolution is
    implied without a Navier-Stokes solver.
    """
    v0 = float(amplitude)
    k = float(wavenumber)
    kx, ky, kz = k * grid.xx, k * grid.yy, k * grid.zz
    u = v0 * np.sin(kx) * np.cos(ky) * np.cos(kz)
    v = -v0 * np.cos(kx) * np.sin(ky) * np.cos(kz)
    w = np.zeros_like(u)
    return u.astype(np.float64), v.astype(np.float64), w.astype(np.float64)


def abc_flow(
    grid: Grid3D, a: float = 1.0, b: float = 1.0, c: float = 1.0
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Arnold-Beltrami-Childress flow, a Beltrami flow with ``curl u = u``.

    ``u = a sin z + c cos y``, ``v = b sin x + a cos z``, ``w = c sin y + b cos x``
    on a periodic domain. Because the vorticity equals the velocity, the
    normalized helicity is 1 everywhere -- a clean helicity oracle.
    """
    u = a * np.sin(grid.zz) + c * np.cos(grid.yy)
    v = b * np.sin(grid.xx) + a * np.cos(grid.zz)
    w = c * np.sin(grid.yy) + b * np.cos(grid.xx)
    return u.astype(np.float64), v.astype(np.float64), w.astype(np.float64)


def vortex_tube(
    grid: Grid3D, circulation: float, core_radius: float, axis: str = "z"
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """A straight Gaussian vorticity tube aligned with the given axis.

    Built as a Lamb-Oseen swirl in the plane orthogonal to ``axis``, invariant
    along ``axis``. Used to test orientation-sensitive diagnostics.
    """
    if axis not in ("x", "y", "z"):
        raise ValueError("axis must be 'x', 'y', or 'z'.")
    core = float(core_radius)
    if not np.isfinite(core) or core <= 0.0:
        raise ValueError("core_radius must be finite and strictly positive.")
    gamma = float(circulation)
    if axis == "z":
        p, q = grid.xx, grid.yy
    elif axis == "y":
        p, q = grid.zz, grid.xx
    else:
        p, q = grid.yy, grid.zz
    r_squared = p**2 + q**2
    swirl = (gamma / (2.0 * np.pi)) * _radial_factor(r_squared, core)
    a = -swirl * q
    b = swirl * p
    zero = np.zeros_like(a)
    if axis == "z":
        return a.astype(np.float64), b.astype(np.float64), zero
    if axis == "y":
        return b.astype(np.float64), zero, a.astype(np.float64)
    return zero, a.astype(np.float64), b.astype(np.float64)
