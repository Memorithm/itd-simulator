"""Deterministic initial conditions for the 3D spectral solver (research).

Every field is analytic or seeded-deterministic and divergence-free (projected
where needed). Random fields use an explicit ``numpy`` generator seed and a fixed
construction order, so a given seed reproduces the field bit-for-bit.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.grids import SpectralGrid3D
from itd_research.spectral3d.operators import _irfft, project_solenoidal

FloatArray: TypeAlias = NDArray[np.float64]


def abc_flow_velocity(
    grid: SpectralGrid3D, a: float = 1.0, b: float = 1.0, c: float = 1.0
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Arnold-Beltrami-Childress flow (``curl u = u`` for the standard form)."""
    xx, yy, zz = grid.mesh()
    u = a * np.sin(zz) + c * np.cos(yy)
    v = b * np.sin(xx) + a * np.cos(zz)
    w = c * np.sin(yy) + b * np.cos(xx)
    return u.astype(np.float64), v.astype(np.float64), w.astype(np.float64)


def taylor_green_velocity(
    grid: SpectralGrid3D, amplitude: float = 1.0, wavenumber: int = 1
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Classic 3D Taylor-Green vortex initial condition (divergence-free, w=0)."""
    xx, yy, zz = grid.mesh()
    k = float(wavenumber)
    v0 = float(amplitude)
    u = v0 * np.sin(k * xx) * np.cos(k * yy) * np.cos(k * zz)
    v = -v0 * np.cos(k * xx) * np.sin(k * yy) * np.cos(k * zz)
    w = np.zeros_like(u)
    return u.astype(np.float64), v.astype(np.float64), w.astype(np.float64)


def corotating_tubes(
    grid: SpectralGrid3D,
    circulation: float = 1.0,
    core: float = 0.5,
    separation: float = 1.6,
    same_sign: bool = True,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Two straight vortex tubes along z (co-rotating by default), z-invariant.

    Built as a superposition of two Lamb-Oseen swirls in the (x, y) plane centred
    in the box, then projected to remove any residual divergence from periodicity.
    """
    xx, yy, _ = grid.mesh()
    centre = 0.5 * grid.length
    sign = 1.0 if same_sign else -1.0

    def swirl(cx: float, strength: float) -> tuple[FloatArray, FloatArray]:
        dx = xx - cx
        dy = yy - centre
        r2 = dx**2 + dy**2
        with np.errstate(divide="ignore", invalid="ignore"):
            factor = -np.expm1(-r2 / core**2) / r2
        factor = np.where(r2 > 0.0, factor, 1.0 / core**2)
        magnitude = (strength / (2.0 * np.pi)) * factor
        return -magnitude * dy, magnitude * dx

    ua, va = swirl(centre - 0.5 * separation, circulation)
    ub, vb = swirl(centre + 0.5 * separation, sign * circulation)
    u = (ua + ub).astype(np.float64)
    v = (va + vb).astype(np.float64)
    w = np.zeros_like(u)
    return project_solenoidal(u, v, w, grid)


def isotropic_seed(
    grid: SpectralGrid3D, seed: int, peak_wavenumber: float = 4.0, energy: float = 0.5
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Seeded divergence-free isotropic field with a peaked energy spectrum.

    The spectral amplitude follows ``k^2 exp(-(k/k0)^2)`` with deterministic
    random phases from ``numpy.random.default_rng(seed)``; the field is projected
    solenoidal and rescaled to the requested mean kinetic energy. Fully
    deterministic for a given seed.
    """
    generator = np.random.default_rng(int(seed))
    shape = grid.spectral_shape
    k_magnitude = np.sqrt(grid.k_squared)
    with np.errstate(divide="ignore", invalid="ignore"):
        amplitude = np.where(
            k_magnitude > 0.0,
            k_magnitude * np.exp(-((k_magnitude / float(peak_wavenumber)) ** 2)),
            0.0,
        )
    fields: list[FloatArray] = []
    for _ in range(3):
        phase = generator.uniform(0.0, 2.0 * np.pi, size=shape)
        spectrum = (amplitude * np.exp(1j * phase)).astype(np.complex128)
        fields.append(_irfft(spectrum, grid))
    u, v, w = project_solenoidal(fields[0], fields[1], fields[2], grid)
    current = float(np.mean(u**2 + v**2 + w**2))
    if current > 0.0:
        scale = float(np.sqrt(2.0 * float(energy) / current))
        u, v, w = u * scale, v * scale, w * scale
    return u, v, w
