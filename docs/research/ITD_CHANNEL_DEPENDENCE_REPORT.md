# ITD channel dependence and redundancy report (H11)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce with `python -m itd_research.validation_lab run --config
configs/validation_lab/ci.toml --output <dir>`.

## Question (H11, falsifiable)

Which ITD-3D channels carry information not recoverable from the others (linear or
nonlinear/predictive)? A channel that is merely correlated is **not** removed on
that basis alone; the question is complementarity.

## Method

The channel superset (`intensity, heterogeneity, localization, roughness,
orientation_dispersion, helicity_mean, normalized_helicity, stretching_rate`) is
evaluated on sub-cubes of a deterministic local-flow catalogue (laminar/coherent,
transitional, turbulent; 9 flows), giving a data matrix (243 sub-cube samples at
the CI resolution `24^3`, `3^3` sub-cubes/flow). Statistics: Pearson/Spearman
matrices, variance-inflation factors (VIF), condition number, PCA, a
participation-ratio effective rank, and a binned mutual-information estimate
(reported with its bin/sample caveat).

## Results (CI resolution; larger runs agree qualitatively)

| channel | VIF | interpretation |
|---|--:|---|
| roughness | 18.4 | strongly linearly redundant |
| intensity | 10.1 | strongly redundant |
| orientation_dispersion | 8.3 | redundant (with magnitude channels here) |
| heterogeneity | 4.7 | moderately redundant |
| localization | 3.9 | moderately redundant |
| helicity_mean | 1.6 | **non-redundant** |
| normalized_helicity | 1.4 | **non-redundant** |
| stretching_rate | 1.0 | **non-redundant** |

* **Effective rank 3.9 / 8**; the correlation-matrix condition number is ~90.
* **PCA**: four components explain ~90 % of the variance; the last four channels
  together explain <10 %.
* The magnitude/structure channels (intensity, heterogeneity, localization,
  roughness) are mutually redundant — they are different summaries of the same
  vorticity-magnitude distribution.
* The **genuinely-3D channels (stretching_rate, normalized_helicity, and
  helicity_mean) are non-redundant** (VIF ~1–1.6): they carry information the
  magnitude channels cannot reproduce.

## H11 classification: **partially supported**

*Supported within tested scope:* at least three channels — stretching rate and
(normalized) helicity — are statistically non-redundant with the magnitude
channels across the tested flows. *Not supported:* the claim that all eight
channels are independent — five are linearly redundant (VIF > 3), and the vector
effectively spans ~4 dimensions.

## Limitations

Nine deterministic local flows at modest resolution; VIF/redundancy are
sample-dependent (`orientation_dispersion` in particular shifts between redundant
and marginal across resolutions). Turbulent cases are under-resolved. Mutual
-information estimates are bin-sensitive. This is linear/rank redundancy on a
controlled set — it bounds, but does not settle, *predictive* complementarity,
which is examined per-task in the ablation and prediction studies.
