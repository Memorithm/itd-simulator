# ITD Simulator V29.0-R1

V29 introduit une API directe en coordonnées de départ périodiques.

## Changement architectural

Le chemin RK4 transmet directement les coordonnées de départ aux
interpolateurs. Le détour par une vitesse effective a été supprimé.

## Compatibilité

Le chemin historique `midpoint_time_velocity` reste bit à bit identique
à V28.

Le chemin RK4 reste équivalent à V28 à l'arrondi machine.

## Propriétés régressées

Les suites V28, V28.1 et V28.2 ont été réexécutées avec le moteur V29 :

- bornes locales ;
- somme du candidat cubique ;
- signature de convergence multi-normes ;
- localité de la correction ;
- cohérence des départs RK4.

V29.0 n'introduit aucune nouvelle quantité scientifique.
Il s'agit d'une refactorisation architecturale validée.
