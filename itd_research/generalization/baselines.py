"""Established velocity-gradient baseline features per sub-cube (research).

For a fair comparison, ITD-3D channels are set against the standard vortex
diagnostics aggregated on the same sub-cube: enstrophy, the Q-criterion (mean and
positive-volume fraction), swirling strength, strain-rate magnitude, and the
lambda-2 negative-volume fraction. These are exactly the quantities practitioners
already compute, so "does ITD add anything?" is asked against a real baseline, not a
straw man.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d import (
    lambda2,
    q_criterion,
    strain_rate_magnitude,
    swirling_strength,
    velocity_gradient_3d,
    vorticity_3d_from_gradient,
)

FloatArray: TypeAlias = NDArray[np.float64]

BASELINE_FEATURES: tuple[str, ...] = (
    "enstrophy",
    "q_mean",
    "q_positive_fraction",
    "swirl_mean",
    "strain_mean",
    "lambda2_negative_fraction",
)


def baseline_features_on_subcube(
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    boundary_mode: str = "finite",
) -> dict[str, float]:
    """Aggregate the established velocity-gradient diagnostics on a sub-cube."""
    gradient = velocity_gradient_3d(u, v, w, x, y, z, boundary_mode)
    omega = vorticity_3d_from_gradient(gradient)
    enstrophy = 0.5 * float(np.mean(np.sum(omega**2, axis=-1)))
    q = q_criterion(gradient)
    swirl = swirling_strength(gradient)
    strain = strain_rate_magnitude(gradient)
    l2 = lambda2(gradient)
    return {
        "enstrophy": enstrophy,
        "q_mean": float(np.mean(q)),
        "q_positive_fraction": float(np.mean(q > 0.0)),
        "swirl_mean": float(np.mean(swirl)),
        "strain_mean": float(np.mean(strain)),
        "lambda2_negative_fraction": float(np.mean(l2 < 0.0)),
    }
