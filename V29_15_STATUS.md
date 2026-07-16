# ITD V29.15

Extraction modulaire de la signature structurelle et de ses poids.

## Architecture

Deux fonctions ont été déplacées dans
`itd_v29_core/structural_metrics.py` :

- `normalize_structural_weights` ;
- `structural_metrics`.

L'interface publique historique reste disponible par réexportation
directe depuis `itd_v29.py`.

Aucune définition extraite ne subsiste dans le monolithe.

## Analyseur de dépendances

Cette extraction a nécessité de remplacer l'analyseur de variables
libres de `tools/finish_v29_series.py` par une analyse lexicale
récursive fondée sur `symtable`, afin de calculer correctement les
dépendances des portées imbriquées (notamment la fermeture
`mean_field` -> `spatial_mean` à l'intérieur de `structural_metrics`).
L'analyseur est couvert par 22 tests déterministes dans
`tools/test_dependency_analyser.py`.

## Validation

Cette extraction a aussi été l'occasion d'auditer honnêtement
l'applicabilité de la suite de validateurs historiques : 45
validateurs supplémentaires importent, directement ou via un autre
validateur réutilisé comme module d'aide, un monolithe historique
`itd_vN` absent de tout l'historique Git du dépôt, et ne peuvent donc
s'exécuter dans aucun clone de ce dépôt. Ils sont documentés
individuellement dans `EXCLUDED_VALIDATORS` et dans le rapport de
certification, au même titre que `validate_bounded_cubic_v27.py`.

- la suite de validateurs historiques réellement applicable
  (`validate_release_v10.py`) a réussi ;
- le simulateur principal a réussi ;
- le résumé principal est bit à bit identique à V29.14 ;
- les réexportations modulaires ont été contrôlées ;
- l'archive scientifique intégrale est protégée par manifeste SHA-256.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_15_structural_metrics_certification.md`

## Portée

Cette certification est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
