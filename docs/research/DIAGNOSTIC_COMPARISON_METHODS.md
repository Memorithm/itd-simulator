# Diagnostic comparison methods

Status: **research methodology**. Not a certified revision; does not modify
`ITD V29.18`. Defines exactly how the ITD signature is compared with established
vortex-identification diagnostics, so the external-validation results are
reproducible and honestly scoped.

## 1. Diagnostics under comparison

All diagnostics are computed from the **same** second-order velocity-gradient
tensor `J[i,j] = d u_i / d x_j` (`itd_research.diagnostics_3d.operators`), so no
comparison is confounded by a different derivative stencil.

| Diagnostic | Definition | Type | Dimensions | Vortex convention |
|---|---|---|---|---|
| Vorticity (2D) | `omega = dv/dx - du/dy` | local, signed | `T^-1` | sign = rotation sense |
| Vorticity magnitude | `|omega|` | local | `T^-1` | large in shear *and* rotation |
| Strain-rate magnitude | `||S||_F`, `S = (J+J^T)/2` | local | `T^-1` | — |
| Q-criterion | `Q = 0.5(||Omega||_F^2 - ||S||_F^2)` | local | `T^-2` | `Q > 0` is rotation-dominated |
| Swirling strength | `|Im(eig(J))|` | local | `T^-1` | `> 0` only with a complex eigenpair |
| Okubo-Weiss (2D) | `W = s_n^2 + s_s^2 - omega^2` | local | `T^-2` | `W < 0` is rotation-dominated |
| lambda_2 (3D) | middle eigenvalue of `S^2 + Omega^2` | local | `T^-2` | `lambda_2 < 0` is a vortex |
| Enstrophy | `<omega^2>/2` | global | `T^-2` | — |
| Palinstrophy | `<||grad omega||^2>/2` | global | `L^-2 T^-2` | — |
| ITD intensity | `<omega^2 exp(lc^2 R)>` | global | `T^-2` | — |
| ITD signature | heterogeneity, localization, roughness, sign-mixing, temporal | global | mixed / dimensionless | — |

The critical distinction the comparison is built around: **vorticity magnitude
(and therefore ITD's rotational intensity and enstrophy) is large in pure shear,
whereas Q, swirling strength, Okubo-Weiss, and lambda_2 vanish in pure shear**
because they isolate rotation from strain. Simple shear has one nonzero
velocity-gradient entry, so its two eigenvalues are real and equal (zero), giving
`Q = 0`, `W = 0`, zero swirling strength — yet `omega != 0`.

## 2. Reducing local fields to comparable quantities

A **local** field cannot be compared directly with a **global** ITD component; it
is reduced by an explicit, documented aggregation:

* **Region by sign** — `threshold_region(field, sign="positive"/"negative")`
  (e.g. the rotation region `Q > 0`, the Okubo-Weiss vortex region `W < 0`).
* **Region by quantile** — `threshold_region(field, quantile=q, absolute=...)`
  selects nodes at or above the `q`-quantile (over valid nodes). The
  high-vorticity region uses the `|omega|` 0.8-quantile (top 20 % by magnitude).
* **Area fraction** — fraction of (valid) nodes in a region.
* **Connected components** — `connected_components` counts and sizes connected
  regions with a deterministic 4- or 8-connectivity flood fill; the rotation
  region's component count is an ITD-independent vortex count.

## 3. Region and field agreement

* **Region overlap** — `region_overlap` reports Jaccard `|A∩B|/|A∪B|`, Dice
  `2|A∩B|/(|A|+|B|)`, and directional containment. The headline metric is
  Jaccard between the high-vorticity-magnitude region and the rotation region
  `Q > 0`: near 1 means "vorticity magnitude and rotation coincide"; near 0 means
  "vorticity magnitude is dominated by shear, not rotation".
* **Rank/linear correlation** — `pearson_correlation`, `spearman_correlation`
  over valid nodes, returning `None` when a field is (near-)constant so an
  undefined coefficient is reported as undefined, never as a spurious number.

## 4. Transport versus deformation

`transport_decomposition` forms the Eulerian change `(s1 - s0)/dt`, the advective
term `u . grad s`, and the residual `partial s/partial t + u . grad s`. The
residual is an **advective estimate** of the material derivative on a fixed grid
(forward difference in time, centred in space); it is not called the material
derivative in any stronger sense. `translate_periodic` provides an exact spectral
translation so a controlled pure-translation test can be built.

## 5. Masks, validity, and honesty rules

* PIV invalid vectors are handled by the mask policy (True = valid). Diagnostics
  that require finite gradients are computed on the largest fully-valid interior
  rectangle; the crop is reported.
* No diagnostic is asserted superior or inferior; the metrics quantify **where
  ITD agrees with rotation-based identification and where it departs from it**.
* Synthetic fields are labelled synthetic and never presented as external
  empirical validation. Correlation is reported as statistical association, not
  causation.
