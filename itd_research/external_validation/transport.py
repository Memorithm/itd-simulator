"""Transport versus deformation for time-resolved fields (research).

Eulerian temporal change (``partial s / partial t``) responds strongly to mere
translation of a pattern: a frozen vortex advected past a fixed grid produces a
large Eulerian signal even though nothing about its structure changed. This
module separates translation from genuine deformation by forming the advective
(transport) term and the transport-compensated residual:

    D s / D t  ~=  partial s / partial t  +  u . grad s

The residual is an **advective estimate** of the material derivative on a fixed
grid: forward difference in time, second-order centred differences in space. It
is called the material derivative only in that discrete sense. For a field that
is purely advected by ``u``, the residual is small (limited by time discretisation)
while the raw Eulerian change is large -- this is how the module demonstrates that
transport compensation removes false temporal responses (hypothesis H3).

:func:`translate_periodic` performs an exact spectral translation of a periodic
band-limited field, so a controlled pure-translation test can be constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.operators import (
    partial_derivative,
    validate_axis_coordinates,
    validate_boundary_mode,
)

FloatArray: TypeAlias = NDArray[np.float64]


def _rms(values: FloatArray) -> float:
    return float(np.sqrt(np.mean(np.asarray(values, dtype=np.float64) ** 2)))


@dataclass(frozen=True)
class TransportDecomposition:
    """Eulerian change, advective transport, and the compensated residual."""

    eulerian_change: FloatArray
    advective_term: FloatArray
    material_residual: FloatArray
    eulerian_rms: float
    advective_rms: float
    residual_rms: float

    @property
    def residual_fraction(self) -> float:
        """rms(residual) / rms(Eulerian change): the uncompensated fraction."""
        if self.eulerian_rms <= 0.0:
            return 0.0
        return self.residual_rms / self.eulerian_rms

    def as_dict(self) -> dict[str, float]:
        return {
            "eulerian_rms": self.eulerian_rms,
            "advective_rms": self.advective_rms,
            "residual_rms": self.residual_rms,
            "residual_fraction": self.residual_fraction,
        }


def transport_decomposition(
    scalar_before: FloatArray,
    scalar_after: FloatArray,
    u: FloatArray,
    v: FloatArray,
    x: object,
    y: object,
    delta_time: float,
    boundary_mode: str = "finite",
) -> TransportDecomposition:
    """Decompose the Eulerian change of a scalar into transport plus residual.

    ``scalar_before``/``scalar_after`` are the field at ``t`` and ``t + dt``;
    ``u``/``v`` are the advecting velocity (evaluated at ``t``). The advective
    term uses the field at ``t``. The residual ``partial s/partial t + u.grad s``
    is small when the change is pure advection by ``u``.
    """
    dt = float(delta_time)
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("delta_time must be finite and strictly positive.")
    boundary_mode = validate_boundary_mode(boundary_mode)
    s0 = np.asarray(scalar_before, dtype=np.float64)
    s1 = np.asarray(scalar_after, dtype=np.float64)
    u_field = np.asarray(u, dtype=np.float64)
    v_field = np.asarray(v, dtype=np.float64)
    if not (s0.shape == s1.shape == u_field.shape == v_field.shape):
        raise ValueError("all fields must share a shape.")
    x_coords = validate_axis_coordinates(x, "x")
    y_coords = validate_axis_coordinates(y, "y")
    if s0.shape != (y_coords.size, x_coords.size):
        raise ValueError("field shape does not match the (y, x) coordinates.")

    eulerian: FloatArray = (s1 - s0) / dt
    ds_dx = partial_derivative(s0, x_coords, axis=1, boundary_mode=boundary_mode)
    ds_dy = partial_derivative(s0, y_coords, axis=0, boundary_mode=boundary_mode)
    advective: FloatArray = u_field * ds_dx + v_field * ds_dy
    residual: FloatArray = eulerian + advective
    return TransportDecomposition(
        eulerian_change=eulerian,
        advective_term=advective,
        material_residual=residual,
        eulerian_rms=_rms(eulerian),
        advective_rms=_rms(advective),
        residual_rms=_rms(residual),
    )


def transport_decomposition_3d(
    scalar_before: FloatArray,
    scalar_after: FloatArray,
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: object,
    y: object,
    z: object,
    delta_time: float,
    boundary_mode: str = "finite",
) -> TransportDecomposition:
    """3D analogue of :func:`transport_decomposition`.

    ``Ds/Dt ~= partial s/partial t + u.grad s`` for a 3D scalar. On real
    turbulence the advective term captures the (large) transport of the scalar by
    the flow, and the residual is the material change -- for vorticity magnitude
    that residual is the deformation (vortex stretching), not translation.
    """
    dt = float(delta_time)
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("delta_time must be finite and strictly positive.")
    boundary_mode = validate_boundary_mode(boundary_mode)
    s0 = np.asarray(scalar_before, dtype=np.float64)
    s1 = np.asarray(scalar_after, dtype=np.float64)
    u_field = np.asarray(u, dtype=np.float64)
    v_field = np.asarray(v, dtype=np.float64)
    w_field = np.asarray(w, dtype=np.float64)
    if not (s0.shape == s1.shape == u_field.shape == v_field.shape == w_field.shape):
        raise ValueError("all fields must share a shape.")
    x_coords = validate_axis_coordinates(x, "x")
    y_coords = validate_axis_coordinates(y, "y")
    z_coords = validate_axis_coordinates(z, "z")
    if s0.shape != (z_coords.size, y_coords.size, x_coords.size):
        raise ValueError("field shape does not match the (z, y, x) coordinates.")

    eulerian: FloatArray = (s1 - s0) / dt
    ds_dx = partial_derivative(s0, x_coords, axis=2, boundary_mode=boundary_mode)
    ds_dy = partial_derivative(s0, y_coords, axis=1, boundary_mode=boundary_mode)
    ds_dz = partial_derivative(s0, z_coords, axis=0, boundary_mode=boundary_mode)
    advective: FloatArray = u_field * ds_dx + v_field * ds_dy + w_field * ds_dz
    residual: FloatArray = eulerian + advective
    return TransportDecomposition(
        eulerian_change=eulerian,
        advective_term=advective,
        material_residual=residual,
        eulerian_rms=_rms(eulerian),
        advective_rms=_rms(advective),
        residual_rms=_rms(residual),
    )


def translate_periodic(
    field: FloatArray, shift_x: float = 0.0, shift_y: float = 0.0
) -> FloatArray:
    """Exactly translate a periodic, band-limited field by a shift in cells.

    Positive ``shift_x`` moves content toward increasing ``x``. The translation
    is performed with a Fourier phase ramp, so it is exact for fields that are
    periodic on the grid (no interpolation error). Used to build controlled
    pure-translation tests for :func:`transport_decomposition`.
    """
    array = np.asarray(field, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError("field must be 2D.")
    ny, nx = array.shape
    freq_x = np.fft.fftfreq(nx)
    freq_y = np.fft.fftfreq(ny)
    phase = np.exp(
        -2.0j * np.pi * (freq_x[None, :] * float(shift_x) + freq_y[:, None] * float(shift_y))
    )
    shifted = np.fft.ifft2(np.fft.fft2(array) * phase)
    return np.asarray(shifted.real, dtype=np.float64)
