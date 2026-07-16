# ITD V29.16 — Certification

- Date UTC : `2026-07-16T21:30:02Z`
- Module : `itd_v29_core/simulation_engine.py`
- Référence : `V29.15`
- Résumé principal bit à bit identique : **oui**

## Portée

Extraction du moteur principal de simulation.

## Fonctions extraites

- `validate_temporal_deformation_mode`
- `simulate`
- `simulate_multiscale`

## Imports directs

- `from compare_scenarios import Config`
- `from compare_scenarios import curvature_field`
- `from itd_v29_core.constants import DEFAULT_STRUCTURAL_WEIGHTS`
- `from itd_v29_core.constants import STRUCTURAL_COMPONENT_NAMES`
- `from itd_v29_core.constants import STRUCTURAL_LENGTH`
- `from itd_v29_core.constants import TEMPORAL_DEFORMATION_MODES`
- `from itd_v29_core.multiscale_structure import derive_multiscale_profile`
- `from itd_v29_core.multiscale_structure import validate_structural_length_grid`
- `from itd_v29_core.periodic_transport import transport_previous_vorticity_periodic`
- `from itd_v29_core.periodic_transport import validate_periodic_transport_mesh`
- `from itd_v29_core.periodic_transport import validate_transport_interpolation`
- `from itd_v29_core.periodic_transport import validate_transport_trajectory_method`
- `from itd_v29_core.spatial_geometry import normalize_spatial_geometry`
- `from itd_v29_core.spatial_geometry import spatial_geometry_metadata`
- `from itd_v29_core.spatial_geometry import validate_mesh_geometry`
- `from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary`
- `from itd_v29_core.spatial_operators import spatial_mean`
- `from itd_v29_core.spatial_operators import validate_boundary_mode`
- `from itd_v29_core.structural_metrics import normalize_structural_weights`
- `from itd_v29_core.structural_metrics import structural_metrics`
- `from itd_v29_core.time_geometry import normalize_time_grid`
- `from typing import Callable`
- `import numpy as np`

## Validations

- `VALIDATE_RELEASE_V10` : **PASSED**
- `MAIN` : **PASSED**

## Exclusions historiques

- `validate_bounded_cubic_v27.py` : validateur historique du mode cubic_bounded_periodic
- `validate_accelerating_frames_v24.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v23', absent de tout l'historique Git du dépôt.
- `validate_arbitrary_rotations_v14.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v13', absent de tout l'historique Git du dépôt.
- `validate_asymptotic_local_limiter_v27.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v24', absent de tout l'historique Git du dépôt.
- `validate_boundary_conditions_v12.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v11', absent de tout l'historique Git du dépôt.
- `validate_conservation_v27.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v27', absent de tout l'historique Git du dépôt.
- `validate_cubic_transport_v25.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v24', absent de tout l'historique Git du dépôt.
- `validate_curvature_injection_v7.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v6', absent de tout l'historique Git du dépôt.
- `validate_curvature_weight_v6.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v6', absent de tout l'historique Git du dépôt.
- `validate_decoupled_error_budget_v20.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v19', absent de tout l'historique Git du dépôt.
- `validate_decoupled_error_budget_v20_1.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v19', absent de tout l'historique Git du dépôt.
- `validate_direct_departures_v29.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v28', absent de tout l'historique Git du dépôt.
- `validate_error_budget_v26.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v26', absent de tout l'historique Git du dépôt.
- `validate_exact_interpolation_v14_1.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v14', absent de tout l'historique Git du dépôt.
- `validate_galilean_objectivity_v23.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v22', absent de tout l'historique Git du dépôt.
- `validate_gamma_parametric_v25.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v25', absent de tout l'historique Git du dépôt.
- `validate_geometric_invariance_v11.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v11', absent de tout l'historique Git du dépôt.
- `validate_growth_family_v25.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v25', absent de tout l'historique Git du dépôt.
- `validate_heterogeneity_v8.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v7', absent de tout l'historique Git du dépôt.
- `validate_irrotational_invariance_v6.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v6', absent de tout l'historique Git du dépôt.
- `validate_local_bounded_v27.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v26', absent de tout l'historique Git du dépôt.
- `validate_locality_v28.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v28', absent de tout l'historique Git du dépôt.
- `validate_locality_v29_regression.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v24', absent de tout l'historique Git du dépôt.
- `validate_material_derivative_v22.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v21', absent de tout l'historique Git du dépôt.
- `validate_multiscale_structure_v18.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v17', absent de tout l'historique Git du dépôt.
- `validate_nonuniform_geometry_v16.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v15', absent de tout l'historique Git du dépôt.
- `validate_nonuniform_time_v6.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v6', absent de tout l'historique Git du dépôt.
- `validate_numerical_certification_v19.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v18', absent de tout l'historique Git du dépôt.
- `validate_phase_robust_limiter_v27.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v27', absent de tout l'historique Git du dépôt.
- `validate_rectangular_geometry_v13.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v12', absent de tout l'historique Git du dépôt.
- `validate_rk4_departure_consistency_v28.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v28', absent de tout l'historique Git du dépôt.
- `validate_rk4_departure_consistency_v29_regression.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v24', absent de tout l'historique Git du dépôt.
- `validate_rk4_transport_v26.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v25', absent de tout l'historique Git du dépôt.
- `validate_scaling_v6.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v6', absent de tout l'historique Git du dépôt.
- `validate_shape_stability_v26.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v26', absent de tout l'historique Git du dépôt.
- `validate_spatial_scaling_v17.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v16', absent de tout l'historique Git du dépôt.
- `validate_structural_length_v9.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v8', absent de tout l'historique Git du dépôt.
- `validate_structural_weights_v10.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v9', absent de tout l'historique Git du dépôt.
- `validate_sum_preserving_v28.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v27', absent de tout l'historique Git du dépôt.
- `validate_sum_preserving_v29_regression.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v27', absent de tout l'historique Git du dépôt.
- `validate_summary_semantics_v20_1.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v20_1', absent de tout l'historique Git du dépôt.
- `validate_temporal_geometry_v15.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v14_1', absent de tout l'historique Git du dépôt.
- `validate_temporal_interval_v6.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v6', absent de tout l'historique Git du dépôt.
- `validate_temporal_oracle.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v4', absent de tout l'historique Git du dépôt.
- `validate_temporal_oracle_v5.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v5', absent de tout l'historique Git du dépôt.
- `validate_transport_deformation_v21.py` : dépend (directement ou via un autre validateur réutilisé comme module d'aide) du monolithe historique 'itd_v20_1', absent de tout l'historique Git du dépôt.

## Architecture

- Définitions extraites restant dans `itd_v29.py` : **0**
- Réexportations directes : **3/3**

## Empreintes SHA-256

- `itd_v29.py` : `579d76c6b1f94cfeca9420d201181b1365fd5ef7d06e576cf3afdb239ac0ee84`
- `itd_v29_core/simulation_engine.py` : `d611ee0f6ee21d36ce7a551dba7548e1b1f389dc1bfec3756f6d23de44512375`
- `itd_v29_results/summary.csv` : `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b`

## Journaux

- `/tmp/itd_v29_16_certification_20260716T212953Z`

## Portée scientifique

Cette certification est relative aux suites de tests, oracles et configurations numériques déclarés. Elle ne constitue pas une preuve universelle de correction.

**FINAL STATUS: PASSED**
