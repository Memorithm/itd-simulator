# ITD V29.11

Extraction modulaire des transformations de référentiels galiléens et translatoires.

## Architecture

- onze fonctions déplacées dans `itd_v29_core/reference_frames.py` ;
- validation de la vitesse du référentiel galiléen déplacée ;
- validation du temps de référence déplacée ;
- transformation des coordonnées, champs scalaires et champs de vitesse déplacée ;
- métadonnées galiléennes déplacées ;
- transformations sous translation dépendante du temps déplacées ;
- interface publique historique conservée par réexportation directe.

## Validations déclarées

- résumé principal bit à bit identique à V29.10 ;
- objectivité galiléenne V23 validée ;
- compatibilité V22 vers V23 sans erreur numérique ;
- lois galiléennes locales et composition des référentiels validées ;
- objectivité matérielle et semi-lagrangienne validée ;
- référentiels en translation accélérée V24 validés ;
- compatibilité V23 vers V24 sans erreur numérique ;
- réduction du cas accéléré au cas galiléen validée ;
- composition des translations temporelles validée ;
- onze réexportations contrôlées après exécution.

## Portée

Cette validation est relative aux suites de tests, oracles et études numériques déclarés. Elle ne constitue pas une preuve universelle de correction.
