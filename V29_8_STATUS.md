# ITD V29.8

Cinquième extraction modulaire validée.

## Modules extraits

- `itd_v29_core/constants.py`
- `itd_v29_core/time_geometry.py`
- `itd_v29_core/spatial_geometry.py`
- `itd_v29_core/geometric_transforms.py`
- `itd_v29_core/spatial_scaling.py`

## Noyau d’échelle spatiale externalisé

- `validate_spatial_scale_factor`
- `validate_nonnegative_length`
- `scale_length`
- `inverse_scale_coordinates`
- `scale_velocity_function`
- `scale_curvature_function`
- `scale_spatial_geometry`

## Validations exécutées

- compilation et réexports publics validés ;
- résumé historique identique bit à bit ;
- covariance d’échelle spatiale V17 validée ;
- grilles uniformes et rectilignes validées ;
- composition des dilatations validée ;
- contrôles des paramètres invalides conservés.

Cette validation est relative à la suite déclarée.
Elle ne constitue pas une preuve universelle de correction.
