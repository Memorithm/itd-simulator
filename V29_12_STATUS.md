# ITD V29.12

Extraction modulaire du sous-système de transport périodique.

## Architecture

- vingt-sept fonctions déplacées dans `itd_v29_core/periodic_transport.py` ;
- validation du maillage périodique déplacée ;
- géométrie et enveloppement des coordonnées périodiques déplacés ;
- interpolation bilinéaire et cubique périodique déplacée ;
- calcul des points de départ RK4 déplacé ;
- limiteurs locaux bornés déplacés ;
- restauration locale de la somme cubique déplacée ;
- adaptateurs historiques de rétrotraçage déplacés ;
- interface publique historique conservée par réexportation directe ;
- aucune définition extraite ne subsiste dans `itd_v29.py`.

## Validations déclarées

- résumé principal bit à bit identique à V29.11 ;
- simulateur principal validé ;
- interpolation cubique V25 validée ;
- rétrotraçage RK4 V26 validé ;
- bornes locales, enveloppe de phase et comportement asymptotique V27 validés ;
- audit de conservation V27 validé ;
- mode local à somme préservée V28 validé ;
- cohérence RK4, interpolation et bornes V28 validée ;
- API directe des points de départ V29 validée ;
- régressions de somme, RK4 et localité V29 validées ;
- vingt-sept réexportations modulaires contrôlées.

## Validateur historique

`validate_bounded_cubic_v27.py` cible l’ancien mode
`cubic_bounded_periodic`.

Ce validateur est conservé sans modification pour la traçabilité historique,
mais il n’est pas applicable au mode actuel
`cubic_local_bounded_periodic`, qui garantit les bornes locales sans
revendiquer la préservation exacte de la somme.

La préservation de la somme cubique est couverte par le mode
`cubic_local_sum_preserving_periodic` et par les validations V28 et V29.

## Certification

Le rapport détaillé est publié dans :

`itd_v29_results/v29_12_periodic_transport_certification.txt`

## Portée

Cette validation est relative aux suites de tests, oracles et études
numériques déclarés. Elle ne constitue pas une preuve universelle de
correction.
