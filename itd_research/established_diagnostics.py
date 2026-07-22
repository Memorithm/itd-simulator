"""Established fluid-dynamics diagnostics for comparison with ITD (research).

These are standard, precisely defined quantities used to contextualise the
ITD signature. They are computed with the same V29.18 spatial operators
(boundary-consistent gradients and means) so that comparisons are made on equal
numerical footing. None of them is asserted to be superior or inferior to ITD;
the point is to show where ITD conveys the same information and where the
five-component vector adds information a single scalar cannot.

Dimensions assume velocity ``[L/T]`` and coordinates ``[L]``:

* kinetic energy density mean ``<(vx^2+vy^2)/2>``            -> ``L^2 T^-2``
* enstrophy ``<omega^2>/2``                                  -> ``T^-2``
* palinstrophy ``<|grad omega|^2>/2``                        -> ``L^-2 T^-2``
* domain circulation ``<omega> * area``                      -> ``L^2 T^-1``
* vorticity RMS ``sqrt(<omega^2>)``                          -> ``T^-1``
* vorticity absolute mean ``<|omega|>``                      -> ``T^-1``
* vorticity flatness ``<omega^4>/<omega^2>^2``               -> dimensionless
* excess kurtosis ``flatness - 3``                           -> dimensionless
* ITD localization ``flatness - 1`` (cross-reference)        -> dimensionless
* mean gradient norm ``<|grad omega|>``                      -> ``L^-1 T^-1``
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_v29_core.constants import ZERO_THRESHOLD
from itd_v29_core.spatial_geometry import (
    RectilinearGeometry,
    normalize_spatial_geometry,
)
from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    scalar_gradient_with_boundary,
    spatial_mean,
    validate_boundary_mode,
)

FloatArray: TypeAlias = NDArray[np.float64]


def _finite_2d(field: object, name: str) -> FloatArray:
    array = np.asarray(field, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a 2D array.")
    if min(array.shape) < 3:
        raise ValueError(f"{name} must have at least three points per direction.")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains a non-finite value.")
    return array


def _domain_area(spacing: object, shape: tuple[int, int]) -> float:
    """Physical area of the sampled domain for the circulation integral."""
    geometry = normalize_spatial_geometry(spacing)
    if isinstance(geometry, RectilinearGeometry):
        return float(geometry.domain_area)
    ny, nx = shape
    return float((nx - 1) * geometry.dx * (ny - 1) * geometry.dy)


def kinetic_energy_density(
    vx: FloatArray,
    vy: FloatArray,
    spacing: object,
    boundary_mode: str = "finite",
) -> float:
    """Spatially averaged kinetic energy density ``<(vx^2 + vy^2)/2>``."""
    boundary_mode = validate_boundary_mode(boundary_mode)
    vx_array = _finite_2d(vx, "vx")
    vy_array = _finite_2d(vy, "vy")
    if vx_array.shape != vy_array.shape:
        raise ValueError("vx and vy must share a shape.")
    density = 0.5 * (vx_array**2 + vy_array**2)
    return float(spatial_mean(density, spacing, boundary_mode))


def vorticity_diagnostics(
    omega: FloatArray,
    spacing: object,
    boundary_mode: str = "finite",
) -> dict[str, float]:
    """Return the vorticity-based scalar diagnostics for a vorticity field."""
    boundary_mode = validate_boundary_mode(boundary_mode)
    field = _finite_2d(omega, "omega")

    mean_square = float(spatial_mean(field**2, spacing, boundary_mode))
    mean_fourth = float(spatial_mean(field**4, spacing, boundary_mode))
    mean_vorticity = float(spatial_mean(field, spacing, boundary_mode))
    mean_absolute = float(spatial_mean(np.abs(field), spacing, boundary_mode))
    rms = float(np.sqrt(max(mean_square, 0.0)))

    gradient_y, gradient_x = scalar_gradient_with_boundary(
        field, spacing, boundary_mode
    )
    gradient_norm = np.sqrt(gradient_x**2 + gradient_y**2)
    mean_gradient_norm = float(spatial_mean(gradient_norm, spacing, boundary_mode))
    mean_gradient_square = float(
        spatial_mean(gradient_x**2 + gradient_y**2, spacing, boundary_mode)
    )

    if mean_square > ZERO_THRESHOLD:
        flatness = mean_fourth / mean_square**2
    else:
        flatness = 0.0

    area = _domain_area(spacing, field.shape)

    return {
        "enstrophy": 0.5 * mean_square,
        "mean_square_vorticity": mean_square,
        "vorticity_rms": rms,
        "vorticity_abs_mean": mean_absolute,
        "vorticity_mean": mean_vorticity,
        "vorticity_flatness": flatness,
        "vorticity_excess_kurtosis": (flatness - 3.0) if flatness != 0.0 else 0.0,
        "itd_localization_reference": (flatness - 1.0) if flatness != 0.0 else 0.0,
        "palinstrophy": 0.5 * mean_gradient_square,
        "mean_gradient_norm": mean_gradient_norm,
        "domain_circulation": mean_vorticity * area,
    }


def established_diagnostics(
    vx: FloatArray,
    vy: FloatArray,
    spacing: object,
    boundary_mode: str = "finite",
) -> dict[str, float]:
    """Compute all established diagnostics from a velocity field.

    The vorticity is derived with the V29.18 boundary-consistent operator so the
    comparison matches how ITD itself sees the field.
    """
    boundary_mode = validate_boundary_mode(boundary_mode)
    vx_array = _finite_2d(vx, "vx")
    vy_array = _finite_2d(vy, "vy")
    if vx_array.shape != vy_array.shape:
        raise ValueError("vx and vy must share a shape.")

    omega = numerical_vorticity_with_boundary(
        vx_array, vy_array, spacing, boundary_mode
    )

    diagnostics = {
        "kinetic_energy_density": kinetic_energy_density(
            vx_array, vy_array, spacing, boundary_mode
        )
    }
    diagnostics.update(vorticity_diagnostics(omega, spacing, boundary_mode))
    return diagnostics
