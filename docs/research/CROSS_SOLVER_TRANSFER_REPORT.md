# Cross-solver transfer report (Mission 4, H19)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **local-solver** (2D `spectral_ns` ↔ 3D `spectral3d`). External
finite-volume transfer (OpenFOAM) is **blocked** — no such solver in this environment.

## Question (H19)

Does a predictor calibrated on one solver retain useful performance on another solver?

## Method

The two solver families share the same 2D feature space (the 3D run contributes its
z-midplane). A logistic predictor is trained on all runs of one family and scored,
without refitting, on the held-out runs of the *other* family. Both events are
ITD-independent (merger core count; Taylor–Green enstrophy-production peak). AUC is on
the held-out family.

## Results

| train → test | held-out AUC |
|---|--:|
| within merger (reference) | 0.992 |
| within Taylor–Green (reference) | 0.990 |
| **merger → Taylor–Green** | **0.052** |
| **Taylor–Green → merger** | **0.500** |

## H19 classification: **not supported**

A predictor calibrated on one solver family **does not transfer** to the other:
merger→Taylor–Green collapses far below chance (0.05 — the learned direction is
actively wrong on the other flow), and Taylor–Green→merger sits exactly at chance
(0.50). Within-family performance is ~0.99, so the failure is transfer, not the model.
The feature *distributions* and the event physics differ enough between a co-rotating
merger and a Taylor–Green breakdown that a fixed decision rule does not carry over —
consistent with the Mission 3 finding that ITD thresholds and component relationships
do not transfer across flow families.

## Limitations

Two families, one plane, modest resolution; external finite-volume and cross-code
transfer are unavailable here (`blocked-by-tooling`). The result bounds transfer for
these two pseudo-spectral solvers only; a genuine cross-code campaign (OpenFOAM,
Nek5000, external DNS) is the correct next step and is gated behind manual workflows.
