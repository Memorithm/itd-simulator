"""Deterministic **synthetic** 2D velocity fields for comparison (research).

These fields stand in for CFD solver output that this environment cannot produce
(no OpenFOAM/VTK). They are analytic or exactly superposed constructions, so they
are reproducible to round-off and carry no measurement noise. They are used for
code verification and qualitative diagnostic comparison **only**; a synthetic
field is never presented as external empirical validation. Where a field mimics a
canonical flow (cylinder wake, mixing-layer roll-up) that correspondence is
approximate and labelled as such.

Convention matches the field-data model: arrays are ``(ny, nx)`` (axis 0 = y,
axis 1 = x); coordinates are explicit strictly increasing 1D arrays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class Grid2D:
    """A structured 2D grid with explicit coordinates and mesh."""

    x: FloatArray
    y: FloatArray
    xx: FloatArray
    yy: FloatArray
    boundary_mode: str

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.size, self.x.size)

    @property
    def spacing(self) -> tuple[float, float]:
        return (float(self.x[1] - self.x[0]), float(self.y[1] - self.y[0]))


def finite_grid_2d(
    nx: int, ny: int, x_bounds: tuple[float, float], y_bounds: tuple[float, float]
) -> Grid2D:
    """Endpoint-included uniform rectangular grid."""
    if nx < 3 or ny < 3:
        raise ValueError("a finite grid needs at least three nodes per axis.")
    x: FloatArray = np.linspace(x_bounds[0], x_bounds[1], nx, dtype=np.float64)
    y: FloatArray = np.linspace(y_bounds[0], y_bounds[1], ny, dtype=np.float64)
    xx: FloatArray
    yy: FloatArray
    yy, xx = np.meshgrid(y, x, indexing="ij")
    return Grid2D(x, y, xx, yy, "finite")


def periodic_grid_2d(n: int, period: float) -> Grid2D:
    """Endpoint-excluded uniform square periodic grid of the given period."""
    if n < 3:
        raise ValueError("a periodic grid needs at least three nodes per axis.")
    if not np.isfinite(period) or period <= 0.0:
        raise ValueError("period must be finite and strictly positive.")
    spacing = float(period) / float(n)
    coordinates: FloatArray = np.arange(n, dtype=np.float64) * spacing
    xx: FloatArray
    yy: FloatArray
    yy, xx = np.meshgrid(coordinates, coordinates, indexing="ij")
    return Grid2D(coordinates, coordinates, xx, yy, "periodic")


def _lamb_oseen_velocity(
    xx: FloatArray,
    yy: FloatArray,
    circulation: float,
    core_radius: float,
    center: tuple[float, float],
) -> tuple[FloatArray, FloatArray]:
    """Cartesian velocity of one Lamb-Oseen vortex (regular at the core)."""
    core = float(core_radius)
    if not np.isfinite(core) or core <= 0.0:
        raise ValueError("core_radius must be finite and strictly positive.")
    dx = xx - center[0]
    dy = yy - center[1]
    r_squared = dx**2 + dy**2
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = -np.expm1(-r_squared / core**2) / r_squared
    factor = np.where(r_squared > 0.0, factor, 1.0 / core**2)
    swirl = (float(circulation) / (2.0 * np.pi)) * factor
    return (-swirl * dy).astype(np.float64), (swirl * dx).astype(np.float64)


def lamb_oseen_vortex(
    grid: Grid2D,
    circulation: float = 1.0,
    core_radius: float = 0.5,
    center: tuple[float, float] = (0.0, 0.0),
) -> tuple[FloatArray, FloatArray]:
    """A single Lamb-Oseen vortex (rotation-dominated core, Q > 0 inside)."""
    return _lamb_oseen_velocity(grid.xx, grid.yy, circulation, core_radius, center)


def vortex_pair(
    grid: Grid2D,
    circulation: float = 1.0,
    core_radius: float = 0.4,
    separation: float = 1.5,
) -> tuple[FloatArray, FloatArray]:
    """Two counter-rotating Lamb-Oseen vortices separated along x."""
    ua, va = _lamb_oseen_velocity(
        grid.xx, grid.yy, circulation, core_radius, (-0.5 * separation, 0.0)
    )
    ub, vb = _lamb_oseen_velocity(
        grid.xx, grid.yy, -circulation, core_radius, (0.5 * separation, 0.0)
    )
    return (ua + ub).astype(np.float64), (va + vb).astype(np.float64)


def shear_layer(
    grid: Grid2D, u_infinity: float = 1.0, thickness: float = 0.5
) -> tuple[FloatArray, FloatArray]:
    """Parallel hyperbolic-tangent shear layer ``u = U tanh(y/delta)``, ``v = 0``.

    A pure shear flow: the vorticity is large but the flow is not rotation
    -dominated, so Q, swirling strength, and Okubo-Weiss stay non-vortical. This
    is the base state whose instability produces Kelvin-Helmholtz roll-up.
    """
    delta = float(thickness)
    if delta <= 0.0:
        raise ValueError("thickness must be strictly positive.")
    u = float(u_infinity) * np.tanh(grid.yy / delta)
    v = np.zeros_like(u)
    return u.astype(np.float64), v.astype(np.float64)


def stuart_vortices(
    grid: Grid2D, concentration: float = 4.0, amplitude: float = 1.0
) -> tuple[FloatArray, FloatArray]:
    """Stuart's exact steady 2D mixing-layer roll-up (a row of cat's-eye vortices).

    Streamfunction ``psi = A ln(C cosh y + sqrt(C^2-1) cos x)`` gives a
    divergence-free field that interpolates between a pure shear layer
    (``C = 1``) and concentrated vortices (``C`` large). It is an exact steady
    solution of the 2D Euler equations. The grid is expected periodic in ``x``
    with period ``2 pi`` and finite in ``y``; place a core at ``x = pi``.
    """
    c = float(concentration)
    if c < 1.0:
        raise ValueError("concentration C must be >= 1 (C=1 is the pure shear layer).")
    b = float(np.sqrt(c**2 - 1.0))
    denom = c * np.cosh(grid.yy) + b * np.cos(grid.xx)
    # u = d psi / d y, v = -d psi / d x  (streamfunction form -> divergence-free)
    u = float(amplitude) * (c * np.sinh(grid.yy)) / denom
    v = float(amplitude) * (b * np.sin(grid.xx)) / denom
    return u.astype(np.float64), v.astype(np.float64)


def taylor_green_2d(
    grid: Grid2D, amplitude: float = 1.0, wavenumber: float = 1.0
) -> tuple[FloatArray, FloatArray]:
    """Periodic Taylor-Green cellular flow ``u = A cos(kx) sin(ky)``.

    ``v = -A sin(kx) cos(ky)``. A checkerboard of counter-rotating cells; each
    cell interior is rotation-dominated and the cell edges are strain-dominated.
    """
    a = float(amplitude)
    k = float(wavenumber)
    u = a * np.cos(k * grid.xx) * np.sin(k * grid.yy)
    v = -a * np.sin(k * grid.xx) * np.cos(k * grid.yy)
    return u.astype(np.float64), v.astype(np.float64)


def karman_street(
    grid: Grid2D,
    circulation: float = 1.0,
    core_radius: float = 0.3,
    row_spacing: float = 1.2,
    vortex_spacing: float = 2.0,
    rows: int = 3,
) -> tuple[FloatArray, FloatArray]:
    """A staggered array of alternating-sign vortices (a cylinder-wake analogue).

    Two rows of Lamb-Oseen vortices of opposite sign, staggered by half a spacing,
    approximate the classical von Karman vortex street shed by a bluff body. This
    is a **synthetic** stand-in for a solved cylinder wake, not a solver result.
    """
    u: FloatArray = np.zeros(grid.shape, dtype=np.float64)
    v: FloatArray = np.zeros(grid.shape, dtype=np.float64)
    half = 0.5 * float(row_spacing)
    x0 = float(grid.x[0] + grid.x[-1]) * 0.5
    for k in range(-rows, rows + 1):
        # top row: negative sign at integer positions; bottom row: positive, offset.
        top_center = (x0 + k * vortex_spacing, half)
        bottom_center = (x0 + (k + 0.5) * vortex_spacing, -half)
        ut, vt = _lamb_oseen_velocity(grid.xx, grid.yy, -circulation, core_radius, top_center)
        ub, vb = _lamb_oseen_velocity(grid.xx, grid.yy, circulation, core_radius, bottom_center)
        u = u + ut + ub
        v = v + vt + vb
    return u, v
