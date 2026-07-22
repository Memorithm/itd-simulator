"""Deterministic analytical and manufactured velocity fields (post-V29 research).

Each field here has a hand-derived analytical vorticity (recorded in
``docs/research/ANALYTICAL_ORACLES.md``) so that the V29.18 numerical operators
can be checked against an independent reference. Fields are pure functions of the
sampled coordinates and explicit parameters; they hold no global state and never
import plotting libraries.

Grid conventions follow ``docs/numerical_methods.md``:

* ``finite`` grids are endpoint-included uniform grids (both endpoints present),
  matched to the V29.18 second-order edge derivatives and trapezoidal means.
* ``periodic`` grids are endpoint-excluded uniform grids with period
  ``spacing * node_count``.

Arrays use ``meshgrid(..., indexing="xy")`` so axis 0 is y and axis 1 is x, in
agreement with the V29.18 core.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class Grid:
    """A validated 2D Cartesian sampling grid.

    ``spacing`` is the uniform node spacing (dx == dy). ``boundary_mode`` is the
    V29.18 boundary convention the grid was built for (``"finite"`` or
    ``"periodic"``).
    """

    x: FloatArray
    y: FloatArray
    spacing: float
    boundary_mode: str
    node_count: int

    @property
    def shape(self) -> tuple[int, int]:
        return (self.node_count, self.node_count)


def finite_grid(node_count: int, lower: float, upper: float) -> Grid:
    """Endpoint-included uniform square grid on ``[lower, upper]**2``."""
    if node_count < 3:
        raise ValueError("A finite grid needs at least three nodes per axis.")
    if not (np.isfinite(lower) and np.isfinite(upper)) or upper <= lower:
        raise ValueError("Require finite bounds with upper > lower.")
    coordinates = np.linspace(lower, upper, node_count, dtype=np.float64)
    x, y = np.meshgrid(coordinates, coordinates, indexing="xy")
    spacing = float(coordinates[1] - coordinates[0])
    return Grid(x, y, spacing, "finite", node_count)


def periodic_grid(node_count: int, period: float, origin: float = 0.0) -> Grid:
    """Endpoint-excluded uniform square grid with the given ``period``."""
    if node_count < 3:
        raise ValueError("A periodic grid needs at least three nodes per axis.")
    if not np.isfinite(period) or period <= 0.0:
        raise ValueError("period must be finite and strictly positive.")
    if not np.isfinite(origin):
        raise ValueError("origin must be finite.")
    spacing = float(period) / float(node_count)
    coordinates = origin + np.arange(node_count, dtype=np.float64) * spacing
    x, y = np.meshgrid(coordinates, coordinates, indexing="xy")
    return Grid(x, y, spacing, "periodic", node_count)


def _as_pair(vx: FloatArray, vy: FloatArray) -> tuple[FloatArray, FloatArray]:
    return np.asarray(vx, dtype=np.float64), np.asarray(vy, dtype=np.float64)


# --------------------------------------------------------------------------- #
# Velocity fields (all pure, deterministic, float64).                         #
# --------------------------------------------------------------------------- #


def zero_field(x: FloatArray, y: FloatArray) -> tuple[FloatArray, FloatArray]:
    """The identically zero velocity field. Analytical vorticity is 0."""
    return _as_pair(np.zeros_like(x), np.zeros_like(y))


def solid_body_rotation(
    x: FloatArray, y: FloatArray, rotation_rate: float
) -> tuple[FloatArray, FloatArray]:
    """Rigid rotation ``vx = -Omega*y``, ``vy = Omega*x``.

    Analytical vorticity is the uniform value ``2*Omega``.
    """
    omega = float(rotation_rate)
    return _as_pair(-omega * y, omega * x)


def uniform_shear(
    x: FloatArray, y: FloatArray, shear_rate: float
) -> tuple[FloatArray, FloatArray]:
    """Uniform shear ``vx = gamma*y``, ``vy = 0``.

    Analytical vorticity is the uniform value ``-gamma``.
    """
    gamma = float(shear_rate)
    return _as_pair(gamma * y, np.zeros_like(y))


def taylor_green(
    x: FloatArray,
    y: FloatArray,
    amplitude: float,
    wavenumber: float,
) -> tuple[FloatArray, FloatArray]:
    """Taylor-Green field ``vx = U sin(kx)cos(ky)``, ``vy = -U cos(kx)sin(ky)``.

    Analytical vorticity is ``2*U*k*sin(kx)*sin(ky)``.
    """
    amp = float(amplitude)
    k = float(wavenumber)
    vx = amp * np.sin(k * x) * np.cos(k * y)
    vy = -amp * np.cos(k * x) * np.sin(k * y)
    return _as_pair(vx, vy)


def taylor_green_vorticity(
    x: FloatArray,
    y: FloatArray,
    amplitude: float,
    wavenumber: float,
) -> FloatArray:
    """Analytical Taylor-Green vorticity ``2*U*k*sin(kx)*sin(ky)``."""
    amp = float(amplitude)
    k = float(wavenumber)
    return np.asarray(2.0 * amp * k * np.sin(k * x) * np.sin(k * y), dtype=np.float64)


def lamb_oseen(
    x: FloatArray,
    y: FloatArray,
    circulation: float,
    core_radius: float,
    center_x: float = 0.0,
    center_y: float = 0.0,
) -> tuple[FloatArray, FloatArray]:
    """Lamb-Oseen vortex velocity with a regular limit at the core centre.

    Azimuthal velocity ``u_theta = (Gamma / (2*pi*r)) * (1 - exp(-r^2/rc^2))``.
    The Cartesian components use ``u_theta / r``, whose ``r -> 0`` limit is
    ``Gamma / (2*pi*rc^2)`` (evaluated directly instead of dividing by zero).
    """
    gamma = float(circulation)
    core = float(core_radius)
    if not np.isfinite(core) or core <= 0.0:
        raise ValueError("core_radius must be finite and strictly positive.")
    dx = x - float(center_x)
    dy = y - float(center_y)
    r2 = dx * dx + dy * dy
    with np.errstate(divide="ignore", invalid="ignore"):
        radial = -np.expm1(-r2 / core**2) / r2
    radial = np.where(r2 > 0.0, radial, 1.0 / core**2)
    factor = gamma / (2.0 * np.pi)
    return _as_pair(-factor * radial * dy, factor * radial * dx)


def lamb_oseen_vorticity(
    x: FloatArray,
    y: FloatArray,
    circulation: float,
    core_radius: float,
    center_x: float = 0.0,
    center_y: float = 0.0,
) -> FloatArray:
    """Analytical Lamb-Oseen vorticity ``(Gamma/(pi*rc^2)) exp(-r^2/rc^2)``."""
    gamma = float(circulation)
    core = float(core_radius)
    if not np.isfinite(core) or core <= 0.0:
        raise ValueError("core_radius must be finite and strictly positive.")
    dx = x - float(center_x)
    dy = y - float(center_y)
    r2 = dx * dx + dy * dy
    peak = gamma / (np.pi * core**2)
    return np.asarray(peak * np.exp(-r2 / core**2), dtype=np.float64)


def counter_rotating_pair(
    x: FloatArray,
    y: FloatArray,
    circulation: float,
    core_radius: float,
    separation: float,
) -> tuple[FloatArray, FloatArray]:
    """Two opposite-sign Lamb-Oseen vortices separated along x by ``separation``.

    The left vortex carries ``+circulation`` and the right ``-circulation`` so
    the total circulation is zero and the vorticity field is sign-balanced.
    """
    half = 0.5 * float(separation)
    vx1, vy1 = lamb_oseen(x, y, +circulation, core_radius, center_x=-half)
    vx2, vy2 = lamb_oseen(x, y, -circulation, core_radius, center_x=+half)
    return _as_pair(vx1 + vx2, vy1 + vy2)


def counter_rotating_pair_vorticity(
    x: FloatArray,
    y: FloatArray,
    circulation: float,
    core_radius: float,
    separation: float,
) -> FloatArray:
    """Analytical vorticity of the counter-rotating pair."""
    half = 0.5 * float(separation)
    w1 = lamb_oseen_vorticity(x, y, +circulation, core_radius, center_x=-half)
    w2 = lamb_oseen_vorticity(x, y, -circulation, core_radius, center_x=+half)
    return np.asarray(w1 + w2, dtype=np.float64)


# --------------------------------------------------------------------------- #
# Closed-form continuum reference values (hand-derived).                       #
# --------------------------------------------------------------------------- #


def taylor_green_mean_square_vorticity(amplitude: float, wavenumber: float) -> float:
    """Continuum ``<omega^2> = U^2 k^2`` (period-averaged sin^2 factors = 1/2)."""
    return float(amplitude) ** 2 * float(wavenumber) ** 2


def taylor_green_localization() -> float:
    """Exact localization ``<omega^4>/<omega^2>^2 - 1 = 9/4 - 1 = 5/4``.

    With ``omega = 2Uk sin(kx)sin(ky)`` the period-averaged ``sin^4 = 3/8`` and
    ``sin^2 = 1/2`` are reproduced exactly by an endpoint-excluded periodic grid
    of at least five nodes per axis, so the amplitude/wavenumber and the uniform
    finite-difference scaling cancel and the value is exact at every resolution.
    """
    return 1.25


def taylor_green_heterogeneity_continuum() -> float:
    """Continuum heterogeneity ``(pi^2/8) * sqrt(1 - 64/pi^4)``.

    Derived from ``<|omega|> = (8/pi^2) U k`` and ``<omega^2> = U^2 k^2``; the
    discrete grid converges to this value at second order.
    """
    return float((np.pi**2 / 8.0) * np.sqrt(1.0 - 64.0 / np.pi**4))


def lamb_oseen_peak_vorticity(circulation: float, core_radius: float) -> float:
    """Analytical peak (centre) vorticity ``Gamma / (pi * rc^2)``."""
    return float(circulation) / (np.pi * float(core_radius) ** 2)


def lamb_oseen_total_circulation(circulation: float) -> float:
    """Total circulation of an untruncated Lamb-Oseen vortex is ``Gamma``."""
    return float(circulation)
