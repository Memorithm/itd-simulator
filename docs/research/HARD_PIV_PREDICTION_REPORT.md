# Hard PIV prediction report (Mission 4, H24)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **experimental-PIV** (attempted).

## Question (H24)

Does **time-resolved PIV** provide evidence that ITD changes *before* independently
annotated vortex events?

## H24 classification: **blocked** (evidence unavailable)

H24 requires a **strongly-vortical**, **time-resolved**, **independently-annotated**
PIV dataset (core tracks, pressure minima, or expert labels). None is available or
committed in this environment:

* the one committed external PIV field (biofilm, Zenodo 1175014) is a **time-averaged
  mean** of a **shear-dominated** boundary layer — no coherent vortex events, no time
  resolution, no annotations. It is deliberately retained as the **negative/OOD
  control** (see `PIV_VALIDATION_EXPANSION_REPORT`, Mission 3: whole-field ITD
  intensity is uncorrelated with rotation strength there);
* the instantaneous biofilm frames (22 GB) are not downloaded (`blocked-by-size`);
* no tomographic/volumetric PIV is integrated (`blocked-by-{licence,authentication}`).

CI has no network, so no annotated vortical PIV can be fetched here.

## What Mission 3 already established on real PIV (carried forward, not re-run)

On the committed biofilm excerpt, ITD's rotational intensity agrees with an independent
rotation-strength diagnostic **only inside genuine rotation regions** (Spearman +0.45)
and not whole-field (−0.11); shear inflates ITD intensity. That negative/partial PIV
result stands. H24 adds the *temporal-prediction* question, which needs data that is
not present.

## Unblocking path (documented)

Integrate the **Re=3900 cylinder-wake** dataset (time-resolved velocity + Lagrangian
tracks + pressure — independent event labels) or a canonical PIV-Challenge vortex case
via the manual dataset workflow, then apply the leakage-safe temporal protocol:
independently annotate the event time (pressure minimum / core-track topology change),
and test whether ITD channels change before it, reporting lead time and preprocessing
sensitivity. This is the single highest-value external target.

## Limitations

No time-resolved annotated PIV was evaluated. The report states the blockage and the
path; it makes no claim that PIV supports or refutes ITD prediction.
