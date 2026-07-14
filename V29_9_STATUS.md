# ITD V29.9

Extraction modulaire de la structure multi-échelle.

## Architecture

- `validate_structural_length_grid` déplacée dans `itd_v29_core/multiscale_structure.py` ;
- `derive_multiscale_profile` déplacée dans `itd_v29_core/multiscale_structure.py` ;
- `simulate_multiscale` reste temporairement dans `itd_v29.py` car elle dépend de `simulate` ;
- interface publique historique conservée par réexportation.

## Validations déclarées

- résumé principal bit à bit identique à V29.8 ;
- validation multi-échelle V18 réussie ;
- compatibilité V17 vers V18 sans erreur ;
- profil dérivé équivalent aux simulations directes ;
- covariance multi-échelle validée aux erreurs d’arrondi flottant ;
- certification numérique V19 réussie ;
- compatibilité V18 vers V19 sans erreur ;
- étude de résolution et oracle de Richardson validés.

## Portée

Cette validation est relative aux suites de tests et aux oracles numériques déclarés. Elle ne constitue pas une preuve universelle de correction.
