# ITD V29.18

Extraction modulaire du point d'entrée final. Ceci conclut la série de
modularisation V29.

## Architecture

Une fonction a été déplacée dans `itd_v29_core/entrypoint.py` :

- `main`.

L'interface publique historique reste disponible par réexportation
directe depuis `itd_v29.py`.

`itd_v29.py` ne contient désormais plus aucune définition de fonction :
c'est une façade de compatibilité mince, composée uniquement
d'imports directs, de réexportations directes, et du point d'entrée
exécutable :

```python
if __name__ == "__main__":
    main()
```

## Validation

- la suite de validateurs historiques réellement applicable
  (`validate_release_v10.py`) a réussi ;
- le simulateur principal a réussi ;
- le résumé principal est bit à bit identique à V29.17 ;
- les réexportations modulaires ont été contrôlées ;
- aucun module `itd_v29_core` n'importe la façade `itd_v29` ;
- l'archive scientifique intégrale est protégée par manifeste SHA-256.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_18_entrypoint_certification.md`

## Portée

Cette certification est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
