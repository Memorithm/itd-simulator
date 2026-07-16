#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

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




# Longueur physique de référence utilisée pour rendre
# la rugosité adimensionnelle. Elle est indépendante
# du pas numérique de la grille.




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


from itd_v29_core.structural_metrics import (
    normalize_structural_weights,
    structural_metrics,
)



from itd_v29_core.time_geometry import (
    TemporalGeometry,
    normalize_time_grid,
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


from itd_v29_core.multiscale_structure import (
    derive_multiscale_profile,
    validate_structural_length_grid,
)


from itd_v29_core.simulation_engine import (
    validate_temporal_deformation_mode,
    simulate,
    simulate_multiscale,
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
    validate_periodic_transport_mesh,
    periodic_bilinear_backtrace,
    periodic_coordinate_geometry,
    wrap_periodic_points,
    evaluate_periodic_transport_velocity,
    rk4_periodic_departure_points,
    transport_previous_vorticity_periodic,
    validate_transport_interpolation,
    validate_transport_trajectory_method,
    periodic_cubic_lagrange_weights,
    periodic_cubic_backtrace,
    periodic_bilinear_departure_bounds,
    normalize_periodic_departure_geometry,
    periodic_bilinear_sample_at_departures,
    cubic_lagrange_weights_at_fraction,
    periodic_cubic_sample_at_departures,
    periodic_departure_bounds,
    periodic_cubic_local_bounded_sample_at_departures,
    periodic_cubic_local_sum_preserving_sample_at_departures,
    periodic_sample_at_departures,
    convex_local_bound_limiter,
    periodic_cubic_local_bounded_backtrace,
    precise_discrete_sum,
    periodic_expand_mask,
    restore_sum_with_local_bounds,
    periodic_cubic_local_sum_preserving_backtrace,
    periodic_backtrace,
)




from itd_v29_core.material_interval import (
    validate_positive_time_interval,
    validate_material_interval_fields,
    normalized_field_rate,
    material_vorticity_interval,
)









from itd_v29_core.material_deformation import (
    interpolate_interval_series_to_nodes,
    simulate_material_deformation,
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








from itd_v29_core.spatial_operators import (
    validate_boundary_mode,
    numerical_vorticity_with_boundary,
    scalar_gradient_with_boundary,
    bounded,
    spatial_mean,
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











from itd_v29_core.entrypoint import (
    main,
)



if __name__ == "__main__":
    main()
