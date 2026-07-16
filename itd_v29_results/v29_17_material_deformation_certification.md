# ITD V29.17 — Certification

- Date UTC : `2026-07-16T21:35:59Z`
- Module : `itd_v29_core/material_deformation.py`
- Référence : `V29.16`
- Résumé principal bit à bit identique : **oui**

## Portée

Extraction de l'orchestration de déformation matérielle.

## Fonctions extraites

- `interpolate_interval_series_to_nodes`
- `simulate_material_deformation`

## Imports directs

- `from compare_scenarios import Config`
- `from compare_scenarios import curvature_field`
- `from itd_v29_core.constants import DEFAULT_STRUCTURAL_WEIGHTS`
- `from itd_v29_core.constants import STRUCTURAL_LENGTH`
- `from itd_v29_core.material_interval import material_vorticity_interval`
- `from itd_v29_core.simulation_engine import simulate`
- `from itd_v29_core.spatial_geometry import normalize_spatial_geometry`
- `from itd_v29_core.spatial_geometry import validate_mesh_geometry`
- `from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary`
- `from itd_v29_core.spatial_operators import validate_boundary_mode`
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
- Réexportations directes : **2/2**

## Empreintes SHA-256

- `itd_v29.py` : `9868d795ed77916fcfe8ca6326e041e15cc0bb99841bab4c9e302aefdc1ba3a0`
- `itd_v29_core/material_deformation.py` : `21540507edc0ecceed847b699004eb3f70d3a3bfff329e56603c66135dfcef32`
- `itd_v29_results/summary.csv` : `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b`

## Journaux

- `/tmp/itd_v29_17_certification_20260716T213552Z`

## Portée scientifique

Cette certification est relative aux suites de tests, oracles et configurations numériques déclarés. Elle ne constitue pas une preuve universelle de correction.

**FINAL STATUS: PASSED**
