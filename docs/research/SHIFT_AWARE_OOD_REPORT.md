# Shift-aware OOD report — per-axis localization vs a global radius (H43)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **local-solver** (controlled merger band + progressive shifts).

## The question (H43)

Mission 5's near-OOD detector collapsed every deviation into **one** global Mahalanobis
radius: it could say *how far* a sample was, never *along which axis*. H43 asks whether a
**per-axis standardized-deviation** detector localizes the shift **axis** and tracks its
**severity** better than the single global radius.

## Method

`itd_research/ood_shift/detector.py`. Fit on an in-distribution merger band; for each
frame compute the absolute standardized deviation per feature channel, a robust
**severity** (mean of the top-3 per-axis deviations), and an **attribution** (the
most-shifted channel). Challenge with progressive sweeps of growing magnitude in
circulation, viscosity, and resolution, each with a known ordinal level. Severity
ordering is scored by `monotone_separation` (rank-agreement with the known level;
1.0 = perfect, 0.5 = chance).

## Results (full campaign)

Severity ordering (rank-agreement with the known shift level):

| axis | per-axis severity | global Mahalanobis |
|---|---|---|
| circulation | 1.000 | 1.000 |
| resolution | 1.000 | 1.000 |
| viscosity | 0.732 | 0.932 |
| **mean** | **0.911** | **0.977** |

Axis attribution (which channel the per-axis detector flags — global **cannot** do this):

| swept axis | dominant channel(s) |
|---|---|
| circulation | `intensity` |
| resolution | `sign_mixing` |
| viscosity | `roughness`, `temporal_deformation` |

## Honest reading — H43 **partially supported**

- On **severity ordering**, the per-axis detector is **not better** than the global
  radius (mean 0.911 vs 0.977); a well-conditioned Mahalanobis distance is already a
  strong global severity measure, and the per-axis top-k aggregate is slightly noisier on
  the viscosity sweep.
- On **axis attribution**, the per-axis detector provides interpretable localization that
  a scalar radius **fundamentally cannot**, and the attributions are physically
  plausible (circulation→vorticity magnitude/`intensity`; resolution→small-scale
  `sign_mixing`; viscosity→`roughness`). This is a genuine capability gain.

**Verdict: H43 partially supported.** Per-axis adds real, interpretable attribution but
does **not** beat the global radius on pure severity ordering — reported honestly rather
than claimed as a clean win. The attribution is what enables the three-state policy
(`RISK_COVERAGE_ABSTENTION_REPORT.md`); whether that policy actually wins is a separate,
and more critical, question answered there.
