# ITD V29.14

Extraction modulaire des diagnostics d’intervalle matériel.

## Architecture

Quatre fonctions ont été déplacées dans
`itd_v29_core/material_interval.py` :

- `validate_positive_time_interval` ;
- `validate_material_interval_fields` ;
- `normalized_field_rate` ;
- `material_vorticity_interval`.

L’interface publique historique reste disponible par réexportation
directe depuis `itd_v29.py`.

Aucune définition extraite ne subsiste dans le monolithe.

## Validation

- toutes les validations applicables ont réussi ;
- le simulateur principal a réussi ;
- le résumé principal est bit à bit identique à V29.13 ;
- les réexportations modulaires ont été contrôlées ;
- l’archive scientifique intégrale est protégée par manifeste SHA-256.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_14_material_interval_certification.md`

## Portée

Cette certification est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
