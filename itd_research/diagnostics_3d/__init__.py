"""3D velocity-gradient diagnostics and analytical fields (post-V29 research).

This subpackage is part of the isolated ``itd_research`` namespace. It provides
structured-grid gradient/vorticity operators, established vortex-identification
diagnostics (Q-criterion, lambda_2, swirling strength, Okubo-Weiss), and
deterministic analytical 3D fields for their validation. It is layered on top of
the certified V29.18 baseline, never modifies it, and is never imported by
``itd_v29_core``. Importing it does not initialise Matplotlib.

Nothing here is a certified scientific revision; it is an experimental 3D and
external-validation research layer.
"""

from __future__ import annotations

from itd_research.diagnostics_3d.analytical_fields import (
    Grid3D,
    abc_flow,
    axisymmetric_stretch_rotation_gradient,
    burgers_vortex,
    burgers_vortex_axial_vorticity,
    finite_grid_3d,
    linear_velocity,
    periodic_grid_3d,
    pure_strain_gradient,
    rigid_rotation_gradient,
    rotation_plus_strain_gradient,
    simple_shear_gradient,
    taylor_green_3d,
    vortex_tube,
)
from itd_research.diagnostics_3d.itd_3d import (
    ITD3DResult,
    evaluate_itd3d,
    spatial_mean_3d,
)
from itd_research.diagnostics_3d.operators import (
    partial_derivative,
    velocity_gradient_2d,
    velocity_gradient_3d,
    vorticity_2d_from_gradient,
    vorticity_3d_from_gradient,
)
from itd_research.diagnostics_3d.velocity_gradient import (
    lambda2,
    okubo_weiss_2d,
    q_criterion,
    rotation_tensor,
    strain_rate_magnitude,
    strain_rate_tensor,
    swirling_strength,
    swirling_strength_with_axis,
)

__all__ = (
    # operators
    "partial_derivative",
    "velocity_gradient_2d",
    "velocity_gradient_3d",
    "vorticity_2d_from_gradient",
    "vorticity_3d_from_gradient",
    # diagnostics
    "strain_rate_tensor",
    "rotation_tensor",
    "q_criterion",
    "strain_rate_magnitude",
    "lambda2",
    "swirling_strength",
    "swirling_strength_with_axis",
    "okubo_weiss_2d",
    # analytical fields
    "Grid3D",
    "finite_grid_3d",
    "periodic_grid_3d",
    "linear_velocity",
    "rigid_rotation_gradient",
    "pure_strain_gradient",
    "simple_shear_gradient",
    "rotation_plus_strain_gradient",
    "axisymmetric_stretch_rotation_gradient",
    "burgers_vortex",
    "burgers_vortex_axial_vorticity",
    "taylor_green_3d",
    "vortex_tube",
    "abc_flow",
    # experimental 3D ITD candidate
    "evaluate_itd3d",
    "ITD3DResult",
    "spatial_mean_3d",
)
