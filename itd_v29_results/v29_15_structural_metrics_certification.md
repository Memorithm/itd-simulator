# ITD V29.15 — Certification

- Date UTC : `2026-07-16T21:23:02Z`
- Module : `itd_v29_core/structural_metrics.py`
- Référence : `V29.14`
- Résumé principal bit à bit identique : **oui**

## Portée

Extraction de la signature structurelle et de ses poids.

## Fonctions extraites

- `normalize_structural_weights`
- `structural_metrics`

## Imports directs

- `from itd_v29_core.constants import DEFAULT_STRUCTURAL_WEIGHTS`
- `from itd_v29_core.constants import STRUCTURAL_LENGTH`
- `from itd_v29_core.constants import ZERO_THRESHOLD`
- `from itd_v29_core.spatial_geometry import normalize_spatial_geometry`
- `from itd_v29_core.spatial_operators import bounded`
- `from itd_v29_core.spatial_operators import scalar_gradient_with_boundary`
- `from itd_v29_core.spatial_operators import spatial_mean`
- `from itd_v29_core.spatial_operators import validate_boundary_mode`
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

- `itd_v29.py` : `be4afb06f2adf0e6405a3b746c6dc715808a3ecb773edf531d846523447c72e0`
- `itd_v29_core/structural_metrics.py` : `573f52b9aca8a99583cd10f710cb9dd329d3c29950e731c17ddedc8c12f45bf5`
- `itd_v29_results/summary.csv` : `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b`

## Journaux

- `/tmp/itd_v29_15_certification_20260716T212256Z`

## Portée scientifique

Cette certification est relative aux suites de tests, oracles et configurations numériques déclarés. Elle ne constitue pas une preuve universelle de correction.

**FINAL STATUS: PASSED**
