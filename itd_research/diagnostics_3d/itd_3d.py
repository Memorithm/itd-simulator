"""Experimental 3D ITD candidate channels (research).

This is an **experimental** 3D formulation, not a certified revision. It keeps
magnitude-based analogues of the 2D signature *and* adds explicit orientation,
helicity, and vortex-stretching channels, because the 2D scalar-vorticity
signature does not generalise to a vector vorticity field by magnitude alone.
See ``docs/research/ITD_3D_CANDIDATE_SPEC.md``.

It is built on :mod:`itd_research.diagnostics_3d.operators` and imports no
certified V29.18 code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.operators import (
    validate_axis_coordinates,
    validate_boundary_mode,
    velocity_gradient_3d,
    vorticity_3d_from_gradient,
)
from itd_research.diagnostics_3d.velocity_gradient import strain_rate_tensor

FloatArray: TypeAlias = NDArray[np.float64]

_ZERO = 1.0e-12


def spatial_mean_3d(
    field: FloatArray,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    boundary_mode: str,
) -> float:
    """Boundary-consistent 3D spatial mean of a scalar field.

    ``finite`` uses trapezoidal quadrature over the box divided by its volume;
    ``periodic`` uses the arithmetic mean.
    """
    boundary_mode = validate_boundary_mode(boundary_mode)
    array = np.asarray(field, dtype=np.float64)
    if boundary_mode == "periodic":
        return float(np.mean(array, dtype=np.float64))
    integral = np.trapezoid(
        np.trapezoid(np.trapezoid(array, x=x, axis=2), x=y, axis=1), x=z, axis=0
    )
    volume = (
        float(x[-1] - x[0]) * float(y[-1] - y[0]) * float(z[-1] - z[0])
    )
    if volume <= 0.0:
        raise ValueError("domain volume must be strictly positive.")
    return float(integral / volume)


@dataclass(frozen=True)
class ITD3DResult:
    """Experimental 3D ITD channels for a single velocity snapshot."""

    intensity: float
    heterogeneity: float
    localization: float
    roughness: float
    orientation_dispersion: float
    helicity_mean: float
    normalized_helicity: float
    stretching_rate: float
    vorticity_rms: float

    def as_dict(self) -> dict[str, float]:
        return {
            "intensity": self.intensity,
            "heterogeneity": self.heterogeneity,
            "localization": self.localization,
            "roughness": self.roughness,
            "orientation_dispersion": self.orientation_dispersion,
            "helicity_mean": self.helicity_mean,
            "normalized_helicity": self.normalized_helicity,
            "stretching_rate": self.stretching_rate,
            "vorticity_rms": self.vorticity_rms,
        }


def _zero_result() -> ITD3DResult:
    return ITD3DResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def evaluate_itd3d(
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: object,
    y: object,
    z: object,
    boundary_mode: str = "finite",
    *,
    curvature: FloatArray | None = None,
    characteristic_length: float = 0.5,
    structural_length: float = 0.5,
) -> ITD3DResult:
    """Evaluate the experimental 3D ITD channels for one velocity snapshot."""
    boundary_mode = validate_boundary_mode(boundary_mode)
    x_coords = validate_axis_coordinates(x, "x")
    y_coords = validate_axis_coordinates(y, "y")
    z_coords = validate_axis_coordinates(z, "z")
    length = float(characteristic_length)
    if not np.isfinite(length) or length < 0.0:
        raise ValueError("characteristic_length must be finite and non-negative.")
    structural_length = float(structural_length)
    if not np.isfinite(structural_length) or structural_length < 0.0:
        raise ValueError("structural_length must be finite and non-negative.")

    u_field = np.asarray(u, dtype=np.float64)
    v_field = np.asarray(v, dtype=np.float64)
    w_field = np.asarray(w, dtype=np.float64)

    gradient = velocity_gradient_3d(
        u_field, v_field, w_field, x_coords, y_coords, z_coords, boundary_mode
    )
    omega = vorticity_3d_from_gradient(gradient)  # (nz, ny, nx, 3)
    magnitude = np.sqrt(np.sum(omega**2, axis=-1))

    def mean(field: FloatArray) -> float:
        return spatial_mean_3d(field, x_coords, y_coords, z_coords, boundary_mode)

    mean_square = mean(magnitude**2)
    rms = float(np.sqrt(max(mean_square, 0.0)))
    if rms < _ZERO:
        return _zero_result()

    if curvature is None:
        weight: FloatArray = np.ones_like(magnitude)
    else:
        curvature_array = np.asarray(curvature, dtype=np.float64)
        if curvature_array.shape != magnitude.shape:
            raise ValueError("curvature must match the field shape.")
        if not np.all(np.isfinite(curvature_array)):
            raise ValueError("curvature contains a non-finite value.")
        weight = np.exp(length**2 * curvature_array)
        if not np.all(np.isfinite(weight)):
            raise ValueError("curvature weight exceeds the finite numeric range.")

    intensity = mean(magnitude**2 * weight)

    mean_magnitude = mean(magnitude)
    variance = mean((magnitude - mean_magnitude) ** 2)
    heterogeneity = float(np.sqrt(max(variance, 0.0)) / max(mean_magnitude, _ZERO))

    localization = float(mean(magnitude**4) / max(mean_square**2, _ZERO) - 1.0)

    vorticity_gradient = velocity_gradient_3d(
        omega[..., 0], omega[..., 1], omega[..., 2],
        x_coords, y_coords, z_coords, boundary_mode,
    )
    gradient_norm = np.sqrt(np.sum(vorticity_gradient**2, axis=(-1, -2)))
    roughness = float(structural_length * mean(gradient_norm) / max(rms, _ZERO))

    mean_vector = np.array(
        [mean(omega[..., 0]), mean(omega[..., 1]), mean(omega[..., 2])],
        dtype=np.float64,
    )
    orientation_dispersion = float(
        np.clip(
            1.0 - float(np.linalg.norm(mean_vector)) / max(mean_magnitude, _ZERO),
            0.0,
            1.0,
        )
    )

    velocity = np.stack((u_field, v_field, w_field), axis=-1)
    helicity_density = np.sum(velocity * omega, axis=-1)
    helicity_mean = mean(helicity_density)

    speed = np.sqrt(np.sum(velocity**2, axis=-1))
    valid = (magnitude > _ZERO) & (speed > _ZERO)
    if bool(np.any(valid)):
        normalized_helicity = float(
            np.mean(helicity_density[valid] / (speed[valid] * magnitude[valid]))
        )
    else:
        normalized_helicity = 0.0

    strain = strain_rate_tensor(gradient)
    stretch_numerator = np.einsum("...i,...ij,...j->...", omega, strain, omega)
    core = magnitude > _ZERO
    if bool(np.any(core)):
        stretching_rate = float(
            np.mean(stretch_numerator[core] / (magnitude[core] ** 2))
        )
    else:
        stretching_rate = 0.0

    return ITD3DResult(
        intensity=float(intensity),
        heterogeneity=heterogeneity,
        localization=localization,
        roughness=roughness,
        orientation_dispersion=orientation_dispersion,
        helicity_mean=float(helicity_mean),
        normalized_helicity=normalized_helicity,
        stretching_rate=stretching_rate,
        vorticity_rms=rms,
    )
