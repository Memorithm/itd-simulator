"""Single-snapshot ITD evaluation built directly on the V29.18 core (research).

This is a thin research convenience: it derives the vorticity with the V29.18
boundary operator, computes the curvature-weighted rotational intensity exactly
as the V29.18 simulator does for one instant, and delegates the five-component
signature to :func:`itd_v29_core.structural_metrics.structural_metrics`. It adds
no new scientific formula and does not alter V29.18 outputs; it only packages a
one-shot evaluation so the benchmark, convergence, and sensitivity runners share
identical numerics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_v29_core.constants import (
    DEFAULT_STRUCTURAL_WEIGHTS,
    STRUCTURAL_LENGTH,
)
from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    spatial_mean,
    validate_boundary_mode,
)
from itd_v29_core.structural_metrics import structural_metrics

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class SignatureResult:
    """Intensity plus the raw five-component structural signature.

    The raw (unbounded) components are preserved exactly as V29.18 reports them.
    ``structure_score`` is the experimental bounded scalar aggregation and is
    always reported together with the raw vector, never in place of it.
    """

    intensity: float
    heterogeneity: float
    localization: float
    roughness: float
    sign_mixing: float
    temporal_deformation: float
    structure_score: float
    vorticity_rms: float

    def component_vector(self) -> tuple[float, float, float, float, float]:
        """Return the raw five-component vector in the canonical order."""
        return (
            self.heterogeneity,
            self.localization,
            self.roughness,
            self.sign_mixing,
            self.temporal_deformation,
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "intensity": self.intensity,
            "heterogeneity": self.heterogeneity,
            "localization": self.localization,
            "roughness": self.roughness,
            "sign_mixing": self.sign_mixing,
            "temporal_deformation": self.temporal_deformation,
            "structure_score": self.structure_score,
            "vorticity_rms": self.vorticity_rms,
        }


def evaluate_signature(
    vx: FloatArray,
    vy: FloatArray,
    spacing: object,
    boundary_mode: str = "finite",
    *,
    curvature: FloatArray | None = None,
    characteristic_length: float = 0.5,
    structural_length: float = STRUCTURAL_LENGTH,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
    previous_omega: FloatArray | None = None,
    delta_time: float | None = None,
) -> SignatureResult:
    """Evaluate intensity and the V29.18 signature for one velocity snapshot.

    ``curvature`` defaults to a zero field, giving a unit curvature weight and
    therefore ``intensity = <omega^2>``. When a curvature field is supplied the
    intensity is ``<omega^2 * exp(characteristic_length^2 * curvature)>``,
    matching the V29.18 definition.
    """
    boundary_mode = validate_boundary_mode(boundary_mode)
    vx_array = np.asarray(vx, dtype=np.float64)
    vy_array = np.asarray(vy, dtype=np.float64)

    length = float(characteristic_length)
    if not np.isfinite(length) or length < 0.0:
        raise ValueError("characteristic_length must be finite and non-negative.")

    omega = numerical_vorticity_with_boundary(
        vx_array, vy_array, spacing, boundary_mode
    )

    if curvature is None:
        weight: FloatArray = np.ones_like(omega)
    else:
        curvature_array = np.asarray(curvature, dtype=np.float64)
        if curvature_array.shape != omega.shape:
            raise ValueError("curvature must match the velocity field shape.")
        if not np.all(np.isfinite(curvature_array)):
            raise ValueError("curvature contains a non-finite value.")
        weight = np.exp(length**2 * curvature_array)
        if not np.all(np.isfinite(weight)):
            raise ValueError("curvature weight exceeds the finite numeric range.")

    intensity = float(spatial_mean(omega**2 * weight, spacing, boundary_mode))
    vorticity_rms = float(
        np.sqrt(max(spatial_mean(omega**2, spacing, boundary_mode), 0.0))
    )

    metrics = structural_metrics(
        omega,
        spacing,
        previous_omega,
        delta_time,
        structural_length=structural_length,
        structural_weights=structural_weights,
        boundary_mode=boundary_mode,
    )

    return SignatureResult(
        intensity=intensity,
        heterogeneity=float(metrics["heterogeneity"]),
        localization=float(metrics["localization"]),
        roughness=float(metrics["roughness"]),
        sign_mixing=float(metrics["sign_mixing"]),
        temporal_deformation=float(metrics["temporal_deformation"]),
        structure_score=float(metrics["structure_score"]),
        vorticity_rms=vorticity_rms,
    )
