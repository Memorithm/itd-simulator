"""Spectral grid and wavenumber operators for a periodic 3D box (research).

Real fields on an ``N x N x N`` periodic box of side ``L`` are transformed with
NumPy's real FFT (``rfftn``/``irfftn``) over axes ``(0, 1, 2) = (x, y, z)``, so the
spectral arrays have shape ``(N, N, N//2 + 1)``. Conventions (authoritative):

* ``norm=None`` (NumPy default: forward unnormalised, inverse divides by N^3).
* ``kx = ky = 2*pi*fftfreq(N, L/N)``; ``kz = 2*pi*rfftfreq(N, L/N)``.
* derivative ``d/dx <-> i*kx`` and likewise for y, z.
* even-N Nyquist modes are zeroed by the derivative operators and by the 2/3
  dealias mask, keeping real-field reconstruction exact.
* mean mode ``k = 0`` is handled explicitly by the inverse Laplacian/projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
ComplexArray: TypeAlias = NDArray[np.complex128]


@dataclass(frozen=True)
class SpectralGrid3D:
    """Wavenumber operators and masks for a cubic periodic box."""

    nodes: int
    length: float
    kx: FloatArray
    ky: FloatArray
    kz: FloatArray
    k_squared: FloatArray
    inv_k_squared: FloatArray
    dealias: FloatArray
    nyquist_mask: FloatArray

    @property
    def spectral_shape(self) -> tuple[int, int, int]:
        return (self.nodes, self.nodes, self.nodes // 2 + 1)

    @property
    def coordinates(self) -> FloatArray:
        spacing = self.length / self.nodes
        return np.arange(self.nodes, dtype=np.float64) * spacing

    def mesh(self) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Physical coordinate mesh ``(xx, yy, zz)`` with ``indexing='ij'``."""
        coordinates = self.coordinates
        xx: FloatArray
        yy: FloatArray
        zz: FloatArray
        xx, yy, zz = np.meshgrid(coordinates, coordinates, coordinates, indexing="ij")
        return xx, yy, zz


def spectral_grid_3d(nodes: int, length: float = 2.0 * np.pi) -> SpectralGrid3D:
    """Build the spectral operators for an ``nodes^3`` box of side ``length``."""
    if nodes < 8 or nodes % 2 != 0:
        raise ValueError("nodes must be an even integer >= 8.")
    if not np.isfinite(length) or length <= 0.0:
        raise ValueError("length must be finite and strictly positive.")
    spacing = length / nodes
    kx_1d = 2.0 * np.pi * np.fft.fftfreq(nodes, d=spacing)
    kz_1d = 2.0 * np.pi * np.fft.rfftfreq(nodes, d=spacing)
    kx_full: FloatArray
    ky_full: FloatArray
    kz_full: FloatArray
    kx_full, ky_full, kz_full = np.meshgrid(kx_1d, kx_1d, kz_1d, indexing="ij")
    # True |k|^2 (from full wavenumbers) for the Laplacian and projection denominator.
    k_squared = kx_full**2 + ky_full**2 + kz_full**2
    safe = k_squared.copy()
    safe[0, 0, 0] = 1.0
    inv_k_squared = 1.0 / safe
    inv_k_squared[0, 0, 0] = 0.0

    # First-derivative wavenumbers: zero the even-N Nyquist plane on each axis so
    # d/dx keeps real-field reconstruction exact (the Nyquist mode of a real field
    # is real and its odd derivative is unrepresentable).
    nyquist_value = 2.0 * np.pi * (nodes // 2) / length
    not_nyquist = 1.0 - (np.abs(kx_full) >= nyquist_value).astype(np.float64)
    not_nyquist *= 1.0 - (np.abs(ky_full) >= nyquist_value).astype(np.float64)
    not_nyquist *= 1.0 - (np.abs(kz_full) >= nyquist_value).astype(np.float64)
    kx = kx_full * not_nyquist
    ky = ky_full * not_nyquist
    kz = kz_full * not_nyquist

    cutoff = (2.0 / 3.0) * nyquist_value
    dealias = (
        (np.abs(kx_full) < cutoff)
        & (np.abs(ky_full) < cutoff)
        & (np.abs(kz_full) < cutoff)
    ).astype(np.float64)
    return SpectralGrid3D(
        nodes=nodes,
        length=float(length),
        kx=kx,
        ky=ky,
        kz=kz,
        k_squared=k_squared,
        inv_k_squared=inv_k_squared,
        dealias=dealias,
        nyquist_mask=not_nyquist,
    )
