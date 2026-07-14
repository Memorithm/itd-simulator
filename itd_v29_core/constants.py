"""Constantes publiques du simulateur ITD V29."""

ZERO_THRESHOLD = 1.0e-12
STRUCTURAL_LENGTH = 0.5

STRUCTURAL_COMPONENT_NAMES = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)

DEFAULT_STRUCTURAL_WEIGHTS = (
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
)

TEMPORAL_DEFORMATION_MODES = (
    "eulerian",
    "transport_compensated",
)

TRANSPORT_INTERPOLATIONS = (
    "bilinear_periodic",
    "cubic_periodic",
    "cubic_local_bounded_periodic",
    "cubic_local_sum_preserving_periodic",
)

TRANSPORT_TRAJECTORY_METHODS = (
    "midpoint_time_velocity",
    "rk4_backtrace",
)

BOUNDARY_MODES = (
    "finite",
    "periodic",
)
