# Out-of-distribution abstention report (Mission 4, H23)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce with `python -m itd_research.ood run --output <dir>` (a `--quick`/`validate`
form runs in CI). Evidence: **local-solver** in-distribution + **external PIV** control.

## Question (H23)

Can the system identify flows for which its calibration is unreliable and **abstain**,
rather than issue an unjustified prediction?

## Method

The OOD reference (Mahalanobis distance under a shrinkage covariance, with PCA-residual
and nearest-sample cross-checks) is fitted on **in-distribution** vortex-merger
features. It then scores genuinely different flows as out-of-distribution: a 3D
Taylor–Green midplane (different solver/physics) and the **real biofilm PIV** field
(shear-dominated). A mixed pool combines in-domain merger frames (with real prediction
errors) and OOD frames (a confident prediction on which is unjustified → error 1). The
system abstains where the OOD score exceeds the in-domain calibration domain.

## Results

| quantity | value |
|---|--:|
| mean OOD score, in-domain | ~1.9 |
| mean OOD score, OOD (TG + PIV) | ~5×10⁸ |
| OOD detection AUC (in-domain vs OOD) | **1.000** |
| full risk (no abstention) | 0.53 |
| **selective risk (with abstention)** | **0.007** |
| in-domain coverage retained | 0.80 |
| false-confidence rate on OOD | **0.000** |

## H23 classification: **supported within tested scope**

The distance-based detector separates in-distribution from out-of-distribution flows
perfectly here (AUC 1.0; the OOD Mahalanobis distances are orders of magnitude larger,
because the merger feature covariance simply does not contain Taylor–Green or a
shear-dominated boundary layer). Abstaining on high-OOD samples **cuts selective risk
from 0.53 to 0.007 while keeping 80 % of in-domain coverage and issuing zero confident
predictions on truly out-of-distribution flows.** This is the safety behaviour the
product requires: prefer abstention over unjustified extrapolation.

## Product integration

The end-to-end `ITDAnalysisResult` (see `END_TO_END_REALTIME_REPORT`) carries the OOD
score, a calibration profile (`in-domain` / `borderline` / `out-of-domain`),
`abstained`, and an `abstention_reason`, and its `validate()` rejects a bare alarm — so
an OOD flow yields an abstention with a reason, never a naked alarm.

## Limitations

The OOD separation here is *easy* (the OOD flows are extremely different from the
merger family), so AUC 1.0 reflects a large distribution gap, not a subtle detector. A
harder test — near-distribution shifts (a merger at an untrained Reynolds number, a
mildly perturbed geometry) — would stress the detector far more and is the correct next
step. The abstention benefit is demonstrated on one in-distribution family and two OOD
sources.
