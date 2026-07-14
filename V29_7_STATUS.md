# ITD V29.7

Quatrième extraction modulaire validée.

## Modules extraits

- itd_v29_core/constants.py
- itd_v29_core/time_geometry.py
- itd_v29_core/spatial_geometry.py
- itd_v29_core/geometric_transforms.py

## Transformations géométriques externalisées

- validate_orthogonal_matrix
- transform_coordinates
- transform_velocity_function
- transform_scalar_function
- validate_rotation_angle
- rotation_matrix
- validate_uniform_axis_coordinates
- validate_transform_origin
- BilinearTransformPlan
- make_sampled_transformed_velocity_function
- make_sampled_transformed_scalar_function

## Validations exécutées

- résumé historique identique bit à bit ;
- invariance géométrique V11 validée ;
- rotations arbitraires V14 validées ;
- interpolation exacte V14.1 validée ;
- symétries D4 réversibles bit à bit ;
- interface publique historique conservée.

Cette validation est relative à la suite déclarée.
Elle ne constitue pas une preuve universelle de correction.

## Révision de conditionnement V29.7-P1

- suppression des répertoires `__pycache__` ;
- suppression des fichiers `.pyc` et `.pyo` ;
- aucun fichier source ou résultat scientifique modifié ;
- manifeste SHA-256 entièrement régénéré.
