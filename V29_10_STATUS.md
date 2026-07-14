# ITD V29.10

Extraction modulaire de la certification numérique et des analyses de convergence.

## Architecture

- onze fonctions déplacées dans `itd_v29_core/numerical_certification.py` ;
- validation des paramètres de convergence déplacée ;
- extrapolation de Richardson déplacée ;
- analyse des triplets simple et multi-échelle déplacée ;
- combinaison et synthèse des budgets spatio-temporels déplacées ;
- interface publique historique conservée par réexportation.

## Validations déclarées

- résumé principal bit à bit identique à V29.9 ;
- rapports V19 CSV et JSON bit à bit identiques à V29.9 ;
- validation numérique V19 réussie ;
- validation du budget découplé V20 réussie ;
- validation du budget découplé V20.1 réussie ;
- validation de la sémantique du résumé V20.1 réussie ;
- onze réexportations contrôlées après exécution ;
- exécution parallèle V19, V20 et V20.1 réussie.

## Portée

Cette validation est relative aux suites de tests, études de résolution et oracles numériques déclarés. Elle ne constitue pas une preuve universelle de correction.
