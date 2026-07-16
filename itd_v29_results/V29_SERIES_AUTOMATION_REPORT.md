# ITD V29.xx — Rapport d'automatisation

- Généré le : `2026-07-16T17:26:31Z`

## V29.15

- Statut : **FAILED**
- Début : `2026-07-16T17:26:31Z`
- Fin : `2026-07-16T17:26:31Z`

### Erreur

```text
Validations en échec :
### MAIN
Traceback (most recent call last):
  File "/root/itd-simulator/itd_v29.py", line 1540, in <module>
    main()
  File "/root/itd-simulator/itd_v29.py", line 1353, in main
    simulate(
  File "/root/itd-simulator/itd_v29.py", line 869, in simulate
    eulerian_metrics = structural_metrics(
                       ^^^^^^^^^^^^^^^^^^^
  File "/root/itd-simulator/itd_v29_core/structural_metrics.py", line 132, in structural_metrics
    mean_square = mean_field(omega**2)
                  ^^^^^^^^^^^^^^^^^^^^
  File "/root/itd-simulator/itd_v29_core/structural_metrics.py", line 125, in mean_field
    return spatial_mean(
           ^^^^^^^^^^^^
NameError: name 'spatial_mean' is not defined
```
