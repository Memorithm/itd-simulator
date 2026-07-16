# ITD V29.14 — Certification

- Date UTC : `2026-07-15T20:46:04Z`
- Module : `itd_v29_core/material_interval.py`
- Référence : `V29.13`
- Résumé principal bit à bit identique : **oui**

## Portée

Extraction des diagnostics d'intervalle matériel.

## Fonctions extraites

- `validate_positive_time_interval`
- `validate_material_interval_fields`
- `normalized_field_rate`
- `material_vorticity_interval`

## Imports directs

- `from itd_v29_core.constants import ZERO_THRESHOLD`
- `from itd_v29_core.spatial_geometry import normalize_spatial_geometry`
- `from itd_v29_core.spatial_geometry import validate_field_shape_for_geometry`
- `from itd_v29_core.spatial_operators import scalar_gradient_with_boundary`
- `from itd_v29_core.spatial_operators import spatial_mean`
- `from itd_v29_core.spatial_operators import validate_boundary_mode`
- `import numpy as np`

## Validations

- `VALIDATE_ACCELERATING_FRAMES_V24` : **PASSED**
- `VALIDATE_ARBITRARY_ROTATIONS_V14` : **PASSED**
- `VALIDATE_ASYMPTOTIC_LOCAL_LIMITER_V27` : **PASSED**
- `VALIDATE_BOUNDARY_CONDITIONS_V12` : **PASSED**
- `VALIDATE_CONSERVATION_V27` : **PASSED**
- `VALIDATE_CUBIC_TRANSPORT_V25` : **PASSED**
- `VALIDATE_CURVATURE_INJECTION_V7` : **PASSED**
- `VALIDATE_CURVATURE_WEIGHT_V6` : **PASSED**
- `VALIDATE_DECOUPLED_ERROR_BUDGET_V20` : **PASSED**
- `VALIDATE_DECOUPLED_ERROR_BUDGET_V20_1` : **PASSED**
- `VALIDATE_DIRECT_DEPARTURES_V29` : **PASSED**
- `VALIDATE_ERROR_BUDGET_V26` : **PASSED**
- `VALIDATE_EXACT_INTERPOLATION_V14_1` : **PASSED**
- `VALIDATE_GALILEAN_OBJECTIVITY_V23` : **PASSED**
- `VALIDATE_GAMMA_PARAMETRIC_V25` : **PASSED**
- `VALIDATE_GEOMETRIC_INVARIANCE_V11` : **PASSED**
- `VALIDATE_GROWTH_FAMILY_V25` : **PASSED**
- `VALIDATE_HETEROGENEITY_V8` : **PASSED**
- `VALIDATE_IRROTATIONAL_INVARIANCE_V6` : **PASSED**
- `VALIDATE_LOCAL_BOUNDED_V27` : **PASSED**
- `VALIDATE_LOCALITY_V28` : **PASSED**
- `VALIDATE_LOCALITY_V29_REGRESSION` : **PASSED**
- `VALIDATE_MATERIAL_DERIVATIVE_V22` : **PASSED**
- `VALIDATE_MULTISCALE_STRUCTURE_V18` : **PASSED**
- `VALIDATE_NONUNIFORM_GEOMETRY_V16` : **PASSED**
- `VALIDATE_NONUNIFORM_TIME_V6` : **PASSED**
- `VALIDATE_NUMERICAL_CERTIFICATION_V19` : **PASSED**
- `VALIDATE_PHASE_ROBUST_LIMITER_V27` : **PASSED**
- `VALIDATE_RECTANGULAR_GEOMETRY_V13` : **PASSED**
- `VALIDATE_RELEASE_V10` : **PASSED**
- `VALIDATE_RK4_DEPARTURE_CONSISTENCY_V28` : **PASSED**
- `VALIDATE_RK4_DEPARTURE_CONSISTENCY_V29_REGRESSION` : **PASSED**
- `VALIDATE_RK4_TRANSPORT_V26` : **PASSED**
- `VALIDATE_SCALING_V6` : **PASSED**
- `VALIDATE_SHAPE_STABILITY_V26` : **PASSED**
- `VALIDATE_SPATIAL_SCALING_V17` : **PASSED**
- `VALIDATE_STRUCTURAL_LENGTH_V9` : **PASSED**
- `VALIDATE_STRUCTURAL_WEIGHTS_V10` : **PASSED**
- `VALIDATE_SUM_PRESERVING_V28` : **PASSED**
- `VALIDATE_SUM_PRESERVING_V29_REGRESSION` : **PASSED**
- `VALIDATE_SUMMARY_SEMANTICS_V20_1` : **PASSED**
- `VALIDATE_TEMPORAL_GEOMETRY_V15` : **PASSED**
- `VALIDATE_TEMPORAL_INTERVAL_V6` : **PASSED**
- `VALIDATE_TEMPORAL_ORACLE` : **PASSED**
- `VALIDATE_TEMPORAL_ORACLE_V5` : **PASSED**
- `VALIDATE_TRANSPORT_DEFORMATION_V21` : **PASSED**
- `MAIN` : **PASSED**

## Exclusions historiques

- `validate_bounded_cubic_v27.py` : validateur historique du mode cubic_bounded_periodic

## Architecture

- Définitions extraites restant dans `itd_v29.py` : **0**
- Réexportations directes : **4/4**

## Empreintes SHA-256

- `itd_v29.py` : `fc0deb7a0c9e2ca9d14504760c8fc1dedc9cb8e2033a8446cb07187c55f840e7`
- `itd_v29_core/material_interval.py` : `06468e0c0f23a2de8d71e17f8382527a4c56dcb58d11ebf57bdb7987536c1b83`
- `itd_v29_results/summary.csv` : `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b`

## Journaux

- `/tmp/itd_v29_14_certification_20260715T203901Z`

## Portée scientifique

Cette certification est relative aux suites de tests, oracles et configurations numériques déclarés. Elle ne constitue pas une preuve universelle de correction.

**FINAL STATUS: PASSED**
