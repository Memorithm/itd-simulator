# Region-level localization report (H69)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Question

Does ITD improve **region-level** localization (IoU, Dice, centroid distance, a
Hausdorff-like max-nearest-distance) against the established Q-criterion region ground
truth, rather than only whole-field scalar prediction?

## Verdict: blocked — architectural, not data-blocked

`itd_research.mission8.localization.evaluate_region_localization` returns:

```
verdict: blocked
reason:  Existing ITD-3D channels (intensity, heterogeneity, localization, roughness,
         orientation_dispersion, helicity_mean, normalized_helicity, stretching_rate)
         are GLOBAL per-snapshot scalars, not per-cell fields. Region-level IoU/Dice/
         centroid comparison against the established Q-criterion ground truth requires
         a spatial ITD map, which does not exist in the current signature.
```

The Mission 8 instructions and preregistration explicitly forbid inventing a new channel
to manufacture a testable region-level output ("do not create new ITD channels merely to
obtain a positive result"). H69 is therefore reported as **honestly blocked**, not
data-blocked and not silently skipped: the region-metric machinery itself
(`itd_research.mission8.vortex_regions`: `iou`, `dice`, `centroid_distance`,
`max_nearest_distance`) is complete, tested (`tests/test_mission8.py::
test_iou_dice_identical_and_disjoint_masks`, and the manufactured-oracle region tests),
and reusable the moment a future, explicitly-scoped mission adds a spatial channel — but
no such channel exists today, and none was added this mission.

## What this means for the mission's central question

Since ITD produces no per-cell spatial output, it cannot even in principle localize a
region better or worse than the established Q-criterion mask — there is nothing to
compare. This is a real, structural limitation of the *existing* ITD-3D channel set
(intensity, heterogeneity, localization, roughness, orientation_dispersion, helicity_mean,
normalized_helicity, stretching_rate — every one a scalar per snapshot), not a limitation
introduced by this mission's evaluation design.
