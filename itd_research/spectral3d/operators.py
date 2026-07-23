"""Spectral differential operators and the incompressible projection (research).

All operators act on real physical-space fields of shape ``(N, N, N)`` and return
real fields, transforming internally with ``rfftn``/``irfftn``. Derivative sign
convention: ``d/dx <-> i*kx`` (and y, z). The projection removes the compressible
part of a vector field so its divergence is zero to round-off.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.grids import SpectralGrid3D

FloatArray: TypeAlias = NDArray[np.float64]
ComplexArray: TypeAlias = NDArray[np.complex128]


def _rfft(field: FloatArray) -> ComplexArray:
    return np.fft.rfftn(np.asarray(field, dtype=np.float64), axes=(0, 1, 2))


def _irfft(field_hat: ComplexArray, grid: SpectralGrid3D) -> FloatArray:
    real = np.fft.irfftn(field_hat, s=(grid.nodes, grid.nodes, grid.nodes), axes=(0, 1, 2))
    return np.ascontiguousarray(real, dtype=np.float64)


def gradient_scalar(
    field: FloatArray, grid: SpectralGrid3D
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Spectral gradient ``(df/dx, df/dy, df/dz)`` of a scalar field."""
    field_hat = _rfft(field)
    fx = _irfft(1j * grid.kx * field_hat, grid)
    fy = _irfft(1j * grid.ky * field_hat, grid)
    fz = _irfft(1j * grid.kz * field_hat, grid)
    return fx, fy, fz


def divergence(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D
) -> FloatArray:
    """Spectral divergence ``du/dx + dv/dy + dw/dz``."""
    div_hat = 1j * (grid.kx * _rfft(u) + grid.ky * _rfft(v) + grid.kz * _rfft(w))
    return _irfft(div_hat, grid)


def curl(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Spectral curl ``(dw/dy - dv/dz, du/dz - dw/dx, dv/dx - du/dy)``."""
    u_hat, v_hat, w_hat = _rfft(u), _rfft(v), _rfft(w)
    cx = _irfft(1j * (grid.ky * w_hat - grid.kz * v_hat), grid)
    cy = _irfft(1j * (grid.kz * u_hat - grid.kx * w_hat), grid)
    cz = _irfft(1j * (grid.kx * v_hat - grid.ky * u_hat), grid)
    return cx, cy, cz


def vorticity(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Vorticity ``omega = curl u`` (alias of :func:`curl`)."""
    return curl(u, v, w, grid)


def laplacian_vector(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Spectral vector Laplacian ``(lap u, lap v, lap w)``."""
    factor = -grid.k_squared
    return (
        _irfft(factor * _rfft(u), grid),
        _irfft(factor * _rfft(v), grid),
        _irfft(factor * _rfft(w), grid),
    )


def _project_hat(
    u_hat: ComplexArray, v_hat: ComplexArray, w_hat: ComplexArray, grid: SpectralGrid3D
) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
    k_dot_u = grid.kx * u_hat + grid.ky * v_hat + grid.kz * w_hat
    factor = k_dot_u * grid.inv_k_squared
    return (
        u_hat - grid.kx * factor,
        v_hat - grid.ky * factor,
        w_hat - grid.kz * factor,
    )


def project_solenoidal(
    u: FloatArray, v: FloatArray, w: FloatArray, grid: SpectralGrid3D
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Return the divergence-free (solenoidal) part of a vector field.

    Uses the Fourier-space Leray projection ``u_perp = u - k (k.u)/|k|^2`` for
    ``k != 0``; the mean mode ``k = 0`` is preserved unchanged.
    """
    up_hat, vp_hat, wp_hat = _project_hat(_rfft(u), _rfft(v), _rfft(w), grid)
    return _irfft(up_hat, grid), _irfft(vp_hat, grid), _irfft(wp_hat, grid)
