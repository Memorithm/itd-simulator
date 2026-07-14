# ITD V29.6

Troisième extraction modulaire validée.

## Modules extraits

- `itd_v29_core/constants.py`
- `itd_v29_core/time_geometry.py`
- `itd_v29_core/spatial_geometry.py`

## Géométrie spatiale extraite

- `SpatialGeometry`
- `RectilinearGeometry`
- `validate_axis_spacing`
- `validate_spacing`
- `validate_rectilinear_axis_coordinates`
- `normalize_spatial_geometry`
- `spatial_geometry_metadata`
- `validate_field_shape_for_geometry`
- `validate_mesh_geometry`

## Validations exécutées

- résumé historique identique bit à bit ;
- géométrie rectangulaire V13 validée ;
- géométrie rectiligne non uniforme V16 validée ;
- conditions aux frontières V12 validées ;
- covariance d’échelle spatiale V17 validée ;
- API publique historique conservée.

Cette certification est relative à la suite de validation déclarée.
Elle ne constitue pas une preuve universelle de correction numérique.
