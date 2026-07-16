# ITD V29.17

Extraction modulaire de l'orchestration de déformation matérielle.

## Architecture

Deux fonctions ont été déplacées dans
`itd_v29_core/material_deformation.py` :

- `interpolate_interval_series_to_nodes` ;
- `simulate_material_deformation`.

L'interface publique historique reste disponible par réexportation
directe depuis `itd_v29.py`.

Aucune définition extraite ne subsiste dans le monolithe, à l'exception
de `main`, seule fonction restante avant V29.18.

## Dépendances

`itd_v29_core/material_deformation.py` importe directement :

- `material_vorticity_interval` depuis `itd_v29_core.material_interval`
  (V29.14) ;
- `simulate` depuis `itd_v29_core.simulation_engine` (V29.16).

Conformément à l'audit de dépendances effectué avant V29.16, aucun
cycle n'existe : `itd_v29_core.simulation_engine` ne dépend pas de
`itd_v29_core.material_deformation`, et aucun module `itd_v29_core`
n'importe la façade `itd_v29`.

## Validation

- la suite de validateurs historiques réellement applicable
  (`validate_release_v10.py`) a réussi ;
- le simulateur principal a réussi ;
- le résumé principal est bit à bit identique à V29.16 ;
- les réexportations modulaires ont été contrôlées ;
- l'archive scientifique intégrale est protégée par manifeste SHA-256.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_17_material_deformation_certification.md`

## Portée

Cette certification est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
