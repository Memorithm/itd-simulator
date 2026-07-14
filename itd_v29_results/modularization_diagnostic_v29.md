# ITD V29.2 — Diagnostic ciblé de modularisation

Aucun fichier scientifique n’a été modifié.

## Résumé

- `unclassified_symbols` : **45**
- `unclassified_functions` : **45**
- `unclassified_classes` : **0**
- `unclassified_assignments` : **0**
- `cycle_edges` : **31**
- `topological_layers` : **8**
- `leaf_functions` : **40**
- `first_extraction_candidates` : **18**

## Symboles non classés

### `analyze_result_triplet` (function)

- Lignes : 2442–2492
- Constantes globales : _aucune_
- Appelle : `extract_single_scale_diagnostics`, `richardson_triplet`
- Appelée par : _aucune fonction locale_

### `combine_decoupled_convergence_rows` (function)

- Lignes : 2915–3221
- Constantes globales : _aucune_
- Appelle : `convergence_error_is_estimable`, `convergence_row_key`, `validate_convergence_tolerance`
- Appelée par : _aucune fonction locale_

### `convergence_error_is_estimable` (function)

- Lignes : 2899–2912
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `combine_decoupled_convergence_rows`

### `convergence_row_key` (function)

- Lignes : 2850–2896
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `combine_decoupled_convergence_rows`

### `evaluate_translating_frame_vector` (function)

- Lignes : 5446–5511
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `translating_frame_metadata`, `translating_frame_source_coordinates`, `translating_frame_transform_velocity_function`

### `extract_single_scale_diagnostics` (function)

- Lignes : 2375–2439
- Constantes globales : `STRUCTURAL_COMPONENT_NAMES`
- Appelle : _aucune fonction locale_
- Appelée par : `analyze_result_triplet`

### `galilean_metadata` (function)

- Lignes : 5416–5443
- Constantes globales : _aucune_
- Appelle : `validate_galilean_frame_velocity`, `validate_galilean_reference_time`
- Appelée par : _aucune fonction locale_

### `galilean_source_coordinates` (function)

- Lignes : 5191–5266
- Constantes globales : _aucune_
- Appelle : `validate_galilean_frame_velocity`, `validate_galilean_reference_time`
- Appelée par : `galilean_transform_scalar_function`, `galilean_transform_velocity_function`

### `galilean_transform_scalar_function` (function)

- Lignes : 5269–5331
- Constantes globales : _aucune_
- Appelle : `galilean_source_coordinates`, `validate_galilean_frame_velocity`, `validate_galilean_reference_time`
- Appelée par : _aucune fonction locale_

### `galilean_transform_velocity_function` (function)

- Lignes : 5334–5413
- Constantes globales : _aucune_
- Appelle : `galilean_source_coordinates`, `validate_galilean_frame_velocity`, `validate_galilean_reference_time`
- Appelée par : _aucune fonction locale_

### `interpolate_interval_series_to_nodes` (function)

- Lignes : 4767–4808
- Constantes globales : _aucune_
- Appelle : `normalize_time_grid`
- Appelée par : `simulate_material_deformation`

### `inverse_scale_coordinates` (function)

- Lignes : 1177–1241
- Constantes globales : _aucune_
- Appelle : `validate_spatial_scale_factor`, `validate_transform_origin`
- Appelée par : `scale_curvature_function`, `scale_velocity_function`

### `make_sampled_transformed_scalar_function` (function)

- Lignes : 862–908
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : _aucune fonction locale_

### `make_sampled_transformed_velocity_function` (function)

- Lignes : 805–859
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : _aucune fonction locale_

### `normalized_field_rate` (function)

- Lignes : 4578–4615
- Constantes globales : `ZERO_THRESHOLD`
- Appelle : `spatial_mean`
- Appelée par : `material_vorticity_interval`

### `richardson_triplet` (function)

- Lignes : 2142–2372
- Constantes globales : _aucune_
- Appelle : `validate_convergence_tolerance`, `validate_refinement_ratio`
- Appelée par : `analyze_multiscale_profile_triplet`, `analyze_result_triplet`

### `rotation_matrix` (function)

- Lignes : 282–304
- Constantes globales : _aucune_
- Appelle : `validate_rotation_angle`
- Appelée par : _aucune fonction locale_

### `scale_curvature_function` (function)

- Lignes : 1329–1398
- Constantes globales : _aucune_
- Appelle : `inverse_scale_coordinates`, `validate_spatial_scale_factor`, `validate_transform_origin`
- Appelée par : _aucune fonction locale_

### `scale_length` (function)

- Lignes : 1160–1174
- Constantes globales : _aucune_
- Appelle : `validate_nonnegative_length`, `validate_spatial_scale_factor`
- Appelée par : _aucune fonction locale_

### `scale_velocity_function` (function)

- Lignes : 1244–1326
- Constantes globales : _aucune_
- Appelle : `inverse_scale_coordinates`, `validate_spatial_scale_factor`, `validate_transform_origin`
- Appelée par : _aucune fonction locale_

### `summarize_convergence_rows` (function)

- Lignes : 2761–2847
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : _aucune fonction locale_

### `summarize_decoupled_convergence_rows` (function)

- Lignes : 3224–3452
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : _aucune fonction locale_

### `transform_coordinates` (function)

- Lignes : 107–129
- Constantes globales : _aucune_
- Appelle : `validate_orthogonal_matrix`
- Appelée par : `transform_scalar_function`, `transform_velocity_function`

### `transform_scalar_function` (function)

- Lignes : 177–210
- Constantes globales : _aucune_
- Appelle : `transform_coordinates`, `validate_orthogonal_matrix`
- Appelée par : _aucune fonction locale_

### `transform_velocity_function` (function)

- Lignes : 132–174
- Constantes globales : _aucune_
- Appelle : `transform_coordinates`, `validate_orthogonal_matrix`
- Appelée par : _aucune fonction locale_

### `translating_frame_metadata` (function)

- Lignes : 5719–5765
- Constantes globales : _aucune_
- Appelle : `evaluate_translating_frame_vector`
- Appelée par : _aucune fonction locale_

### `translating_frame_source_coordinates` (function)

- Lignes : 5514–5561
- Constantes globales : _aucune_
- Appelle : `evaluate_translating_frame_vector`
- Appelée par : `translating_frame_transform_scalar_function`, `translating_frame_transform_velocity_function`

### `translating_frame_transform_scalar_function` (function)

- Lignes : 5564–5622
- Constantes globales : _aucune_
- Appelle : `translating_frame_source_coordinates`
- Appelée par : _aucune fonction locale_

### `translating_frame_transform_velocity_function` (function)

- Lignes : 5625–5716
- Constantes globales : _aucune_
- Appelle : `evaluate_translating_frame_vector`, `translating_frame_source_coordinates`
- Appelée par : _aucune fonction locale_

### `validate_axis_spacing` (function)

- Lignes : 8070–8095
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `normalize_spatial_geometry`, `validate_spacing`

### `validate_convergence_tolerance` (function)

- Lignes : 2113–2139
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `combine_decoupled_convergence_rows`, `richardson_triplet`

### `validate_field_shape_for_geometry` (function)

- Lignes : 8486–8501
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `material_vorticity_interval`, `numerical_vorticity_with_boundary`, `scalar_gradient_with_boundary`, `spatial_mean`

### `validate_galilean_frame_velocity` (function)

- Lignes : 5123–5162
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `galilean_metadata`, `galilean_source_coordinates`, `galilean_transform_scalar_function`, `galilean_transform_velocity_function`

### `validate_galilean_reference_time` (function)

- Lignes : 5165–5188
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `galilean_metadata`, `galilean_source_coordinates`, `galilean_transform_scalar_function`, `galilean_transform_velocity_function`

### `validate_nonnegative_length` (function)

- Lignes : 1132–1157
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `scale_length`

### `validate_orthogonal_matrix` (function)

- Lignes : 49–104
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `transform_coordinates`, `transform_scalar_function`, `transform_velocity_function`

### `validate_periodic_transport_mesh` (function)

- Lignes : 3491–3691
- Constantes globales : _aucune_
- Appelle : `normalize_spatial_geometry`, `validate_uniform_axis_coordinates`
- Appelée par : `simulate`

### `validate_positive_time_interval` (function)

- Lignes : 4477–4501
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `material_vorticity_interval`

### `validate_rectilinear_axis_coordinates` (function)

- Lignes : 8110–8180
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : _aucune fonction locale_

### `validate_refinement_ratio` (function)

- Lignes : 2086–2110
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `richardson_triplet`

### `validate_rotation_angle` (function)

- Lignes : 259–279
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `rotation_matrix`

### `validate_spacing` (function)

- Lignes : 8098–8107
- Constantes globales : _aucune_
- Appelle : `validate_axis_spacing`
- Appelée par : _aucune fonction locale_

### `validate_spatial_scale_factor` (function)

- Lignes : 1105–1129
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `inverse_scale_coordinates`, `scale_curvature_function`, `scale_length`, `scale_spatial_geometry`, `scale_velocity_function`

### `validate_transform_origin` (function)

- Lignes : 374–403
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `inverse_scale_coordinates`, `scale_curvature_function`, `scale_spatial_geometry`, `scale_velocity_function`

### `validate_uniform_axis_coordinates` (function)

- Lignes : 307–371
- Constantes globales : _aucune_
- Appelle : _aucune fonction locale_
- Appelée par : `periodic_bilinear_backtrace`, `periodic_cubic_backtrace`, `validate_periodic_transport_mesh`

## Arêtes participant aux cycles de modules

- `geometry`.`scale_spatial_geometry` → `unclassified`.`validate_spatial_scale_factor`
- `geometry`.`scale_spatial_geometry` → `unclassified`.`validate_transform_origin`
- `unclassified`.`validate_periodic_transport_mesh` → `geometry`.`normalize_spatial_geometry`
- `unclassified`.`normalized_field_rate` → `quadrature`.`spatial_mean`
- `differential_operators`.`material_vorticity_interval` → `geometry`.`normalize_spatial_geometry`
- `differential_operators`.`material_vorticity_interval` → `unclassified`.`normalized_field_rate`
- `differential_operators`.`material_vorticity_interval` → `quadrature`.`spatial_mean`
- `differential_operators`.`material_vorticity_interval` → `unclassified`.`validate_field_shape_for_geometry`
- `differential_operators`.`material_vorticity_interval` → `unclassified`.`validate_positive_time_interval`
- `differential_operators`.`simulate_material_deformation` → `unclassified`.`interpolate_interval_series_to_nodes`
- `differential_operators`.`simulate_material_deformation` → `geometry`.`normalize_spatial_geometry`
- `differential_operators`.`simulate_material_deformation` → `simulation`.`simulate`
- `differential_operators`.`simulate_material_deformation` → `geometry`.`validate_mesh_geometry`
- `geometry`.`normalize_spatial_geometry` → `unclassified`.`validate_axis_spacing`
- `differential_operators`.`numerical_vorticity_with_boundary` → `geometry`.`normalize_spatial_geometry`
- `differential_operators`.`numerical_vorticity_with_boundary` → `unclassified`.`validate_field_shape_for_geometry`
- `differential_operators`.`scalar_gradient_with_boundary` → `geometry`.`normalize_spatial_geometry`
- `differential_operators`.`scalar_gradient_with_boundary` → `unclassified`.`validate_field_shape_for_geometry`
- `quadrature`.`spatial_mean` → `geometry`.`normalize_spatial_geometry`
- `quadrature`.`spatial_mean` → `unclassified`.`validate_field_shape_for_geometry`
- `structural_metrics`.`structural_metrics` → `geometry`.`normalize_spatial_geometry`
- `structural_metrics`.`structural_metrics` → `differential_operators`.`scalar_gradient_with_boundary`
- `structural_metrics`.`structural_metrics` → `quadrature`.`spatial_mean`
- `simulation`.`simulate` → `geometry`.`normalize_spatial_geometry`
- `simulation`.`simulate` → `structural_metrics`.`normalize_structural_weights`
- `simulation`.`simulate` → `differential_operators`.`numerical_vorticity_with_boundary`
- `simulation`.`simulate` → `geometry`.`spatial_geometry_metadata`
- `simulation`.`simulate` → `quadrature`.`spatial_mean`
- `simulation`.`simulate` → `structural_metrics`.`structural_metrics`
- `simulation`.`simulate` → `geometry`.`validate_mesh_geometry`
- `simulation`.`simulate` → `unclassified`.`validate_periodic_transport_mesh`

## Couches topologiques des fonctions

### Couche 0

- `limiting_conservation`.`bounded`
- `unclassified`.`convergence_error_is_estimable`
- `unclassified`.`convergence_row_key`
- `limiting_conservation`.`convex_local_bound_limiter`
- `interpolation`.`cubic_lagrange_weights_at_fraction`
- `unclassified`.`evaluate_translating_frame_vector`
- `unclassified`.`extract_single_scale_diagnostics`
- `unclassified`.`make_sampled_transformed_scalar_function`
- `unclassified`.`make_sampled_transformed_velocity_function`
- `structural_metrics`.`normalize_structural_weights`
- `time_geometry`.`normalize_time_grid`
- `geometry`.`periodic_coordinate_geometry`
- `interpolation`.`periodic_cubic_lagrange_weights`
- `limiting_conservation`.`periodic_expand_mask`
- `limiting_conservation`.`precise_discrete_sum`
- `geometry`.`spatial_geometry_metadata`
- `unclassified`.`summarize_convergence_rows`
- `unclassified`.`summarize_decoupled_convergence_rows`
- `unclassified`.`validate_axis_spacing`
- `limiting_conservation`.`validate_boundary_mode`
- `unclassified`.`validate_convergence_tolerance`
- `unclassified`.`validate_field_shape_for_geometry`
- `unclassified`.`validate_galilean_frame_velocity`
- `unclassified`.`validate_galilean_reference_time`
- `differential_operators`.`validate_material_interval_fields`
- `geometry`.`validate_mesh_geometry`
- `unclassified`.`validate_nonnegative_length`
- `unclassified`.`validate_orthogonal_matrix`
- `unclassified`.`validate_positive_time_interval`
- `unclassified`.`validate_rectilinear_axis_coordinates`
- `unclassified`.`validate_refinement_ratio`
- `unclassified`.`validate_rotation_angle`
- `unclassified`.`validate_spatial_scale_factor`
- `multiscale`.`validate_structural_length_grid`
- `time_geometry`.`validate_temporal_deformation_mode`
- `unclassified`.`validate_transform_origin`
- `interpolation`.`validate_transport_interpolation`
- `trajectory`.`validate_transport_trajectory_method`
- `unclassified`.`validate_uniform_axis_coordinates`
- `geometry`.`wrap_periodic_points`

### Couche 1

- `unclassified`.`combine_decoupled_convergence_rows`
- `multiscale`.`derive_multiscale_profile`
- `trajectory`.`evaluate_periodic_transport_velocity`
- `unclassified`.`galilean_metadata`
- `unclassified`.`galilean_source_coordinates`
- `unclassified`.`interpolate_interval_series_to_nodes`
- `unclassified`.`inverse_scale_coordinates`
- `departure_geometry`.`normalize_periodic_departure_geometry`
- `geometry`.`normalize_spatial_geometry`
- `interpolation`.`periodic_bilinear_backtrace`
- `interpolation`.`periodic_bilinear_departure_bounds`
- `interpolation`.`periodic_cubic_backtrace`
- `limiting_conservation`.`restore_sum_with_local_bounds`
- `unclassified`.`richardson_triplet`
- `unclassified`.`rotation_matrix`
- `unclassified`.`scale_length`
- `unclassified`.`transform_coordinates`
- `unclassified`.`translating_frame_metadata`
- `unclassified`.`translating_frame_source_coordinates`
- `unclassified`.`validate_spacing`

### Couche 2

- `multiscale`.`analyze_multiscale_profile_triplet`
- `unclassified`.`analyze_result_triplet`
- `unclassified`.`galilean_transform_scalar_function`
- `unclassified`.`galilean_transform_velocity_function`
- `differential_operators`.`numerical_vorticity_with_boundary`
- `interpolation`.`periodic_bilinear_sample_at_departures`
- `interpolation`.`periodic_cubic_local_bounded_backtrace`
- `interpolation`.`periodic_cubic_local_sum_preserving_backtrace`
- `interpolation`.`periodic_cubic_sample_at_departures`
- `departure_geometry`.`periodic_departure_bounds`
- `trajectory`.`rk4_periodic_departure_points`
- `differential_operators`.`scalar_gradient_with_boundary`
- `unclassified`.`scale_curvature_function`
- `geometry`.`scale_spatial_geometry`
- `unclassified`.`scale_velocity_function`
- `quadrature`.`spatial_mean`
- `unclassified`.`transform_scalar_function`
- `unclassified`.`transform_velocity_function`
- `unclassified`.`translating_frame_transform_scalar_function`
- `unclassified`.`translating_frame_transform_velocity_function`
- `unclassified`.`validate_periodic_transport_mesh`

### Couche 3

- `unclassified`.`normalized_field_rate`
- `interpolation`.`periodic_backtrace`
- `interpolation`.`periodic_cubic_local_bounded_sample_at_departures`
- `interpolation`.`periodic_cubic_local_sum_preserving_sample_at_departures`
- `structural_metrics`.`structural_metrics`

### Couche 4

- `differential_operators`.`material_vorticity_interval`
- `interpolation`.`periodic_sample_at_departures`

### Couche 5

- `trajectory`.`transport_previous_vorticity_periodic`

### Couche 6

- `simulation`.`simulate`

### Couche 7

- `scenarios_io`.`main`
- `differential_operators`.`simulate_material_deformation`
- `multiscale`.`simulate_multiscale`

## Candidats à la première extraction

- `differential_operators`.`validate_material_interval_fields` (appelants : 1, globales : 0)
- `geometry`.`spatial_geometry_metadata` (appelants : 1, globales : 0)
- `geometry`.`validate_mesh_geometry` (appelants : 2, globales : 0)
- `geometry`.`periodic_coordinate_geometry` (appelants : 3, globales : 0)
- `geometry`.`wrap_periodic_points` (appelants : 3, globales : 0)
- `interpolation`.`cubic_lagrange_weights_at_fraction` (appelants : 1, globales : 0)
- `interpolation`.`periodic_cubic_lagrange_weights` (appelants : 1, globales : 0)
- `interpolation`.`validate_transport_interpolation` (appelants : 3, globales : 1)
- `limiting_conservation`.`bounded` (appelants : 1, globales : 0)
- `limiting_conservation`.`periodic_expand_mask` (appelants : 1, globales : 0)
- `limiting_conservation`.`precise_discrete_sum` (appelants : 3, globales : 0)
- `limiting_conservation`.`convex_local_bound_limiter` (appelants : 4, globales : 0)
- `limiting_conservation`.`validate_boundary_mode` (appelants : 7, globales : 1)
- `multiscale`.`validate_structural_length_grid` (appelants : 2, globales : 0)
- `structural_metrics`.`normalize_structural_weights` (appelants : 2, globales : 0)
- `time_geometry`.`validate_temporal_deformation_mode` (appelants : 1, globales : 1)
- `time_geometry`.`normalize_time_grid` (appelants : 3, globales : 0)
- `trajectory`.`validate_transport_trajectory_method` (appelants : 2, globales : 1)

## Limites

- Le diagnostic ne décide pas seul de l’architecture finale.
- Une fonction feuille peut malgré tout partager des types ou des constantes.
- Les responsabilités doivent être validées humainement avant extraction.

