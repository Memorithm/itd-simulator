# ITD V29.16

Extraction modulaire du moteur principal de simulation.

## Architecture

Trois fonctions ont été déplacées dans
`itd_v29_core/simulation_engine.py` :

- `validate_temporal_deformation_mode` ;
- `simulate` ;
- `simulate_multiscale`.

L'interface publique historique reste disponible par réexportation
directe depuis `itd_v29.py`.

Aucune définition extraite ne subsiste dans le monolithe.

## Audit de dépendances

Avant l'extraction, le graphe de dépendances réel des six fonctions
encore présentes dans `itd_v29.py` (`validate_temporal_deformation_mode`,
`simulate`, `simulate_multiscale`, `interpolate_interval_series_to_nodes`,
`simulate_material_deformation`, `main`) a été calculé avec l'analyseur
lexical corrigé :

- `validate_temporal_deformation_mode` ne dépend d'aucune des cinq
  autres ;
- `simulate` dépend uniquement de `validate_temporal_deformation_mode` ;
- `simulate_multiscale` dépend uniquement de `simulate` ;
- `simulate_material_deformation` dépend de `simulate` et de
  `interpolate_interval_series_to_nodes` (V29.17) ;
- `main` dépend uniquement de `simulate` (V29.18).

Aucun cycle n'a été trouvé : le regroupement provisoire V29.16 →
V29.17 → V29.18 est confirmé correct sans réordonnancement.

## Validation

- la suite de validateurs historiques réellement applicable
  (`validate_release_v10.py`) a réussi ;
- le simulateur principal a réussi ;
- le résumé principal est bit à bit identique à V29.15 ;
- les réexportations modulaires ont été contrôlées ;
- aucun module `itd_v29_core` n'importe la façade `itd_v29` ;
- l'archive scientifique intégrale est protégée par manifeste SHA-256.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_16_simulation_engine_certification.md`

## Portée

Cette certification est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
