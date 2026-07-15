# ITD V29.13

Extraction modulaire des opérateurs spatiaux et des conventions de frontière.

## Architecture

Cinq fonctions ont été déplacées dans
`itd_v29_core/spatial_operators.py` :

- `validate_boundary_mode` ;
- `numerical_vorticity_with_boundary` ;
- `scalar_gradient_with_boundary` ;
- `bounded` ;
- `spatial_mean`.

L’interface publique historique est conservée par réexportation directe
depuis `itd_v29.py`.

Aucune définition extraite ne subsiste dans le monolithe.

## Validations déclarées

- conditions aux limites V12 validées ;
- géométrie rectangulaire V13 validée ;
- interpolation exacte V14.1 validée ;
- géométrie non uniforme V16 validée ;
- mise à l’échelle spatiale V17 validée ;
- structure multi-échelle V18 validée ;
- dérivée matérielle V22 validée ;
- objectivité galiléenne V23 validée ;
- référentiels accélérés V24 validés ;
- conservation V27 validée ;
- limiteur local borné V27 validé ;
- mode à somme préservée V28 validé ;
- points de départ directs V29 validés ;
- régression de localité V29 validée ;
- simulateur principal validé.

Le résumé principal est bit à bit identique à V29.12.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_13_spatial_operators_certification.txt`

## Portée

Cette validation est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
