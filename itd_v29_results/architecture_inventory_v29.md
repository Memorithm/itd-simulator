# ITD V29.1 — Inventaire architectural

Cet inventaire est produit automatiquement avant toute extraction de module.

Il ne modifie pas `itd_v29.py` et ne constitue pas encore une architecture définitive.

## Dimensions du fichier

- Lignes : **10031**
- Fonctions : **93**
- Classes : **4**
- Affectations globales : **8**
- Arêtes directes entre fonctions : **148**
- Arêtes inter-modules proposées : **36**

## Modules proposés

### `constants`

**Fonctions**

_Aucun_

**Classes**

_Aucun_

**Constantes et affectations**

- `BOUNDARY_MODES`
- `DEFAULT_STRUCTURAL_WEIGHTS`
- `STRUCTURAL_COMPONENT_NAMES`
- `STRUCTURAL_LENGTH`
- `TEMPORAL_DEFORMATION_MODES`
- `TRANSPORT_INTERPOLATIONS`
- `TRANSPORT_TRAJECTORY_METHODS`
- `ZERO_THRESHOLD`

### `geometry`

**Fonctions**

- `normalize_spatial_geometry`
- `periodic_coordinate_geometry`
- `scale_spatial_geometry`
- `spatial_geometry_metadata`
- `validate_mesh_geometry`
- `wrap_periodic_points`

**Classes**

- `RectilinearGeometry`
- `SpatialGeometry`
- `TemporalGeometry`

**Constantes et affectations**

_Aucun_

### `time_geometry`

**Fonctions**

- `normalize_time_grid`
- `validate_temporal_deformation_mode`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `differential_operators`

**Fonctions**

- `material_vorticity_interval`
- `numerical_vorticity_with_boundary`
- `scalar_gradient_with_boundary`
- `simulate_material_deformation`
- `validate_material_interval_fields`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `quadrature`

**Fonctions**

- `spatial_mean`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `departure_geometry`

**Fonctions**

- `normalize_periodic_departure_geometry`
- `periodic_departure_bounds`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `interpolation`

**Fonctions**

- `cubic_lagrange_weights_at_fraction`
- `periodic_backtrace`
- `periodic_bilinear_backtrace`
- `periodic_bilinear_departure_bounds`
- `periodic_bilinear_sample_at_departures`
- `periodic_cubic_backtrace`
- `periodic_cubic_lagrange_weights`
- `periodic_cubic_local_bounded_backtrace`
- `periodic_cubic_local_bounded_sample_at_departures`
- `periodic_cubic_local_sum_preserving_backtrace`
- `periodic_cubic_local_sum_preserving_sample_at_departures`
- `periodic_cubic_sample_at_departures`
- `periodic_sample_at_departures`
- `validate_transport_interpolation`

**Classes**

- `BilinearTransformPlan`

**Constantes et affectations**

_Aucun_

### `limiting_conservation`

**Fonctions**

- `bounded`
- `convex_local_bound_limiter`
- `periodic_expand_mask`
- `precise_discrete_sum`
- `restore_sum_with_local_bounds`
- `validate_boundary_mode`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `trajectory`

**Fonctions**

- `evaluate_periodic_transport_velocity`
- `rk4_periodic_departure_points`
- `transport_previous_vorticity_periodic`
- `validate_transport_trajectory_method`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `structural_metrics`

**Fonctions**

- `normalize_structural_weights`
- `structural_metrics`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `multiscale`

**Fonctions**

- `analyze_multiscale_profile_triplet`
- `derive_multiscale_profile`
- `simulate_multiscale`
- `validate_structural_length_grid`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `simulation`

**Fonctions**

- `simulate`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `scenarios_io`

**Fonctions**

- `main`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

### `unclassified`

**Fonctions**

- `analyze_result_triplet`
- `combine_decoupled_convergence_rows`
- `convergence_error_is_estimable`
- `convergence_row_key`
- `evaluate_translating_frame_vector`
- `extract_single_scale_diagnostics`
- `galilean_metadata`
- `galilean_source_coordinates`
- `galilean_transform_scalar_function`
- `galilean_transform_velocity_function`
- `interpolate_interval_series_to_nodes`
- `inverse_scale_coordinates`
- `make_sampled_transformed_scalar_function`
- `make_sampled_transformed_velocity_function`
- `normalized_field_rate`
- `richardson_triplet`
- `rotation_matrix`
- `scale_curvature_function`
- `scale_length`
- `scale_velocity_function`
- `summarize_convergence_rows`
- `summarize_decoupled_convergence_rows`
- `transform_coordinates`
- `transform_scalar_function`
- `transform_velocity_function`
- `translating_frame_metadata`
- `translating_frame_source_coordinates`
- `translating_frame_transform_scalar_function`
- `translating_frame_transform_velocity_function`
- `validate_axis_spacing`
- `validate_convergence_tolerance`
- `validate_field_shape_for_geometry`
- `validate_galilean_frame_velocity`
- `validate_galilean_reference_time`
- `validate_nonnegative_length`
- `validate_orthogonal_matrix`
- `validate_periodic_transport_mesh`
- `validate_positive_time_interval`
- `validate_rectilinear_axis_coordinates`
- `validate_refinement_ratio`
- `validate_rotation_angle`
- `validate_spacing`
- `validate_spatial_scale_factor`
- `validate_transform_origin`
- `validate_uniform_axis_coordinates`

**Classes**

_Aucun_

**Constantes et affectations**

_Aucun_

## Dépendances entre modules proposés

- `constants` → _aucune dépendance directe_
- `geometry` → `unclassified`
- `time_geometry` → _aucune dépendance directe_
- `differential_operators` → `geometry`, `limiting_conservation`, `quadrature`, `simulation`, `time_geometry`, `unclassified`
- `quadrature` → `geometry`, `limiting_conservation`, `unclassified`
- `departure_geometry` → `geometry`
- `interpolation` → `departure_geometry`, `geometry`, `limiting_conservation`, `unclassified`
- `limiting_conservation` → _aucune dépendance directe_
- `trajectory` → `geometry`, `interpolation`
- `structural_metrics` → `differential_operators`, `geometry`, `limiting_conservation`, `quadrature`
- `multiscale` → `simulation`, `unclassified`
- `simulation` → `differential_operators`, `geometry`, `interpolation`, `limiting_conservation`, `quadrature`, `structural_metrics`, `time_geometry`, `trajectory`, `unclassified`
- `scenarios_io` → `simulation`
- `unclassified` → `geometry`, `quadrature`, `time_geometry`

## Cycles entre fonctions

_Aucun_

## Cycles entre modules proposés

- `geometry ↔ quadrature ↔ unclassified`
- `differential_operators ↔ simulation ↔ structural_metrics`

## Fonctions feuilles

Ces fonctions n’appellent aucune autre fonction définie dans `itd_v29.py`.

- `bounded`
- `convergence_error_is_estimable`
- `convergence_row_key`
- `convex_local_bound_limiter`
- `cubic_lagrange_weights_at_fraction`
- `evaluate_translating_frame_vector`
- `extract_single_scale_diagnostics`
- `make_sampled_transformed_scalar_function`
- `make_sampled_transformed_velocity_function`
- `normalize_structural_weights`
- `normalize_time_grid`
- `periodic_coordinate_geometry`
- `periodic_cubic_lagrange_weights`
- `periodic_expand_mask`
- `precise_discrete_sum`
- `spatial_geometry_metadata`
- `summarize_convergence_rows`
- `summarize_decoupled_convergence_rows`
- `validate_axis_spacing`
- `validate_boundary_mode`
- `validate_convergence_tolerance`
- `validate_field_shape_for_geometry`
- `validate_galilean_frame_velocity`
- `validate_galilean_reference_time`
- `validate_material_interval_fields`
- `validate_mesh_geometry`
- `validate_nonnegative_length`
- `validate_orthogonal_matrix`
- `validate_positive_time_interval`
- `validate_rectilinear_axis_coordinates`
- `validate_refinement_ratio`
- `validate_rotation_angle`
- `validate_spatial_scale_factor`
- `validate_structural_length_grid`
- `validate_temporal_deformation_mode`
- `validate_transform_origin`
- `validate_transport_interpolation`
- `validate_transport_trajectory_method`
- `validate_uniform_axis_coordinates`
- `wrap_periodic_points`

## Fonctions racines

Ces fonctions ne sont appelées par aucune autre fonction définie dans `itd_v29.py`.

- `analyze_multiscale_profile_triplet`
- `analyze_result_triplet`
- `combine_decoupled_convergence_rows`
- `galilean_metadata`
- `galilean_transform_scalar_function`
- `galilean_transform_velocity_function`
- `main`
- `make_sampled_transformed_scalar_function`
- `make_sampled_transformed_velocity_function`
- `rotation_matrix`
- `scale_curvature_function`
- `scale_length`
- `scale_spatial_geometry`
- `scale_velocity_function`
- `simulate_material_deformation`
- `simulate_multiscale`
- `summarize_convergence_rows`
- `summarize_decoupled_convergence_rows`
- `transform_scalar_function`
- `transform_velocity_function`
- `translating_frame_metadata`
- `translating_frame_transform_scalar_function`
- `translating_frame_transform_velocity_function`
- `validate_rectilinear_axis_coordinates`
- `validate_spacing`

## Limites

- La classification repose sur les noms et les dépendances directes.
- Les imports dynamiques ne sont pas interprétés.
- Les appels via attributs ou alias peuvent nécessiter une inspection humaine.
- Aucun module ne doit être extrait avant examen des cycles détectés.
