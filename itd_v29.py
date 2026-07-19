#!/usr/bin/env python3
"""Compatibility facade for the ITD V29.18 numerical implementation.

Every callable below is imported directly from its implementation module.  The
facade intentionally defines no functions and remains compatible with
``import itd_v29`` and ``python itd_v29.py``.
"""

from __future__ import annotations

from compare_scenarios import (
    Config,
    calm_field,
    coherent_vortex,
    curvature_field,
    multi_vortex_field,
    numerical_vorticity,
)
from itd_v29_core.constants import (
    BOUNDARY_MODES,
    DEFAULT_STRUCTURAL_WEIGHTS,
    STRUCTURAL_COMPONENT_NAMES,
    STRUCTURAL_LENGTH,
    TEMPORAL_DEFORMATION_MODES,
    TRANSPORT_INTERPOLATIONS,
    TRANSPORT_TRAJECTORY_METHODS,
    ZERO_THRESHOLD,
)
from itd_v29_core.entrypoint import main
from itd_v29_core.geometric_transforms import (
    BilinearTransformPlan,
    make_sampled_transformed_scalar_function,
    make_sampled_transformed_velocity_function,
    rotation_matrix,
    transform_coordinates,
    transform_scalar_function,
    transform_velocity_function,
    validate_orthogonal_matrix,
    validate_rotation_angle,
    validate_transform_origin,
    validate_uniform_axis_coordinates,
)
from itd_v29_core.material_deformation import (
    interpolate_interval_series_to_nodes,
    simulate_material_deformation,
)
from itd_v29_core.material_interval import (
    material_vorticity_interval,
    normalized_field_rate,
    validate_material_interval_fields,
    validate_positive_time_interval,
)
from itd_v29_core.multiscale_structure import (
    derive_multiscale_profile,
    validate_structural_length_grid,
)
from itd_v29_core.numerical_certification import (
    analyze_multiscale_profile_triplet,
    analyze_result_triplet,
    combine_decoupled_convergence_rows,
    convergence_error_is_estimable,
    convergence_row_key,
    extract_single_scale_diagnostics,
    richardson_triplet,
    summarize_convergence_rows,
    summarize_decoupled_convergence_rows,
    validate_convergence_tolerance,
    validate_refinement_ratio,
)
from itd_v29_core.periodic_transport import (
    convex_local_bound_limiter,
    cubic_lagrange_weights_at_fraction,
    evaluate_periodic_transport_velocity,
    normalize_periodic_departure_geometry,
    periodic_backtrace,
    periodic_bilinear_backtrace,
    periodic_bilinear_departure_bounds,
    periodic_bilinear_sample_at_departures,
    periodic_coordinate_geometry,
    periodic_cubic_backtrace,
    periodic_cubic_lagrange_weights,
    periodic_cubic_local_bounded_backtrace,
    periodic_cubic_local_bounded_sample_at_departures,
    periodic_cubic_local_sum_preserving_backtrace,
    periodic_cubic_local_sum_preserving_sample_at_departures,
    periodic_cubic_sample_at_departures,
    periodic_departure_bounds,
    periodic_expand_mask,
    periodic_sample_at_departures,
    precise_discrete_sum,
    restore_sum_with_local_bounds,
    rk4_periodic_departure_points,
    transport_previous_vorticity_periodic,
    validate_periodic_transport_mesh,
    validate_transport_interpolation,
    validate_transport_trajectory_method,
    wrap_periodic_points,
)
from itd_v29_core.reference_frames import (
    evaluate_translating_frame_vector,
    galilean_metadata,
    galilean_source_coordinates,
    galilean_transform_scalar_function,
    galilean_transform_velocity_function,
    translating_frame_metadata,
    translating_frame_source_coordinates,
    translating_frame_transform_scalar_function,
    translating_frame_transform_velocity_function,
    validate_galilean_frame_velocity,
    validate_galilean_reference_time,
)
from itd_v29_core.simulation_engine import (
    simulate,
    simulate_multiscale,
    validate_temporal_deformation_mode,
)
from itd_v29_core.spatial_geometry import (
    RectilinearGeometry,
    SpatialGeometry,
    normalize_spatial_geometry,
    spatial_geometry_metadata,
    validate_axis_spacing,
    validate_field_shape_for_geometry,
    validate_mesh_geometry,
    validate_rectilinear_axis_coordinates,
    validate_spacing,
)
from itd_v29_core.spatial_operators import (
    bounded,
    numerical_vorticity_with_boundary,
    scalar_gradient_with_boundary,
    spatial_mean,
    validate_boundary_mode,
)
from itd_v29_core.spatial_scaling import (
    inverse_scale_coordinates,
    scale_curvature_function,
    scale_length,
    scale_spatial_geometry,
    scale_velocity_function,
    validate_nonnegative_length,
    validate_spatial_scale_factor,
)
from itd_v29_core.structural_metrics import (
    normalize_structural_weights,
    structural_metrics,
)
from itd_v29_core.time_geometry import TemporalGeometry, normalize_time_grid

STABLE_PUBLIC_API = (
    "BOUNDARY_MODES",
    "Config",
    "DEFAULT_STRUCTURAL_WEIGHTS",
    "RectilinearGeometry",
    "STRUCTURAL_COMPONENT_NAMES",
    "STRUCTURAL_LENGTH",
    "SpatialGeometry",
    "TEMPORAL_DEFORMATION_MODES",
    "TRANSPORT_INTERPOLATIONS",
    "TRANSPORT_TRAJECTORY_METHODS",
    "TemporalGeometry",
    "main",
    "normalize_spatial_geometry",
    "normalize_structural_weights",
    "normalize_time_grid",
    "numerical_vorticity_with_boundary",
    "scalar_gradient_with_boundary",
    "simulate",
    "simulate_material_deformation",
    "simulate_multiscale",
    "spatial_mean",
    "structural_metrics",
)

ADVANCED_PUBLIC_API = (
    "BilinearTransformPlan",
    "ZERO_THRESHOLD",
    "analyze_multiscale_profile_triplet",
    "analyze_result_triplet",
    "bounded",
    "combine_decoupled_convergence_rows",
    "convex_local_bound_limiter",
    "convergence_error_is_estimable",
    "convergence_row_key",
    "cubic_lagrange_weights_at_fraction",
    "derive_multiscale_profile",
    "evaluate_periodic_transport_velocity",
    "evaluate_translating_frame_vector",
    "extract_single_scale_diagnostics",
    "galilean_metadata",
    "galilean_source_coordinates",
    "galilean_transform_scalar_function",
    "galilean_transform_velocity_function",
    "interpolate_interval_series_to_nodes",
    "inverse_scale_coordinates",
    "make_sampled_transformed_scalar_function",
    "make_sampled_transformed_velocity_function",
    "material_vorticity_interval",
    "normalize_periodic_departure_geometry",
    "normalized_field_rate",
    "periodic_backtrace",
    "periodic_bilinear_backtrace",
    "periodic_bilinear_departure_bounds",
    "periodic_bilinear_sample_at_departures",
    "periodic_coordinate_geometry",
    "periodic_cubic_backtrace",
    "periodic_cubic_lagrange_weights",
    "periodic_cubic_local_bounded_backtrace",
    "periodic_cubic_local_bounded_sample_at_departures",
    "periodic_cubic_local_sum_preserving_backtrace",
    "periodic_cubic_local_sum_preserving_sample_at_departures",
    "periodic_cubic_sample_at_departures",
    "periodic_departure_bounds",
    "periodic_expand_mask",
    "periodic_sample_at_departures",
    "precise_discrete_sum",
    "restore_sum_with_local_bounds",
    "richardson_triplet",
    "rk4_periodic_departure_points",
    "rotation_matrix",
    "scale_curvature_function",
    "scale_length",
    "scale_spatial_geometry",
    "scale_velocity_function",
    "spatial_geometry_metadata",
    "summarize_convergence_rows",
    "summarize_decoupled_convergence_rows",
    "transform_coordinates",
    "transform_scalar_function",
    "transform_velocity_function",
    "translating_frame_metadata",
    "translating_frame_source_coordinates",
    "translating_frame_transform_scalar_function",
    "translating_frame_transform_velocity_function",
    "transport_previous_vorticity_periodic",
    "validate_axis_spacing",
    "validate_boundary_mode",
    "validate_convergence_tolerance",
    "validate_field_shape_for_geometry",
    "validate_galilean_frame_velocity",
    "validate_galilean_reference_time",
    "validate_material_interval_fields",
    "validate_mesh_geometry",
    "validate_nonnegative_length",
    "validate_orthogonal_matrix",
    "validate_periodic_transport_mesh",
    "validate_positive_time_interval",
    "validate_rectilinear_axis_coordinates",
    "validate_refinement_ratio",
    "validate_rotation_angle",
    "validate_spacing",
    "validate_spatial_scale_factor",
    "validate_structural_length_grid",
    "validate_temporal_deformation_mode",
    "validate_transform_origin",
    "validate_transport_interpolation",
    "validate_transport_trajectory_method",
    "validate_uniform_axis_coordinates",
    "wrap_periodic_points",
)

LEGACY_COMPATIBILITY_API = (
    "calm_field",
    "coherent_vortex",
    "curvature_field",
    "multi_vortex_field",
    "numerical_vorticity",
)

__all__ = (
    *STABLE_PUBLIC_API,
    *ADVANCED_PUBLIC_API,
    *LEGACY_COMPATIBILITY_API,
)


if __name__ == "__main__":
    main()
