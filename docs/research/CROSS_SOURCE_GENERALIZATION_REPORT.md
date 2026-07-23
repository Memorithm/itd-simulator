# Cross-source generalization report (Mission 4, H20)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **cross-source** (attempted). 

## Question (H20)

Does a predictor calibrated on one data source transfer to an **independent
institution or repository**?

## H20 classification: **blocked**

Cross-institution transfer requires at least **two** independent external sources with
predictable, independently-labelled vortex events. In this environment only **one**
external empirical source is available and committed — the biofilm PIV mean field
(Zenodo 1175014), which is shear-dominated and carries no vortex-event labels (it is
used as an OOD control, not a prediction source). CI has no network and cannot download
new datasets; there is no OpenFOAM/Nek5000 to generate a second independent source
locally. Therefore H20 **cannot be evaluated** and is recorded as **blocked-by-{network,
authentication, missing-ground-truth}**, not as supported or not-supported.

## What would unblock it (documented path)

1. Integrate the `integration-ready` external target from `MISSION4_DATASET_INVENTORY.md`
   — the **Re=3900 cylinder-wake DNS** (Eulerian+Lagrangian, purpose-built for PIV/PTV
   validation, with independent force/pressure labels) — via the manual, network-enabled
   dataset workflow (download, checksum, convert, provenance).
2. Add a second independent JHTDB flow (rotating / MHD / mixing layer) through the
   existing `fetch_jhtdb_cutout` path.
3. Calibrate a predictor on one source; evaluate, without refitting, on the other,
   using the same leakage-safe grouped protocol as `HARD_EXTERNAL_PREDICTIVE_VALIDATION_
   REPORT`. Report the performance drop, threshold transfer, and failure cases.

Given the Mission 3 cross-family results and the Mission 4 cross-solver result (H19,
merger→Taylor–Green AUC 0.05), the *prior expectation* is that cross-source transfer
will be weak; but that must be **measured** on genuine external sources, not asserted.

## Limitations

No cross-source evaluation was performed. This report states the blockage and the
unblocking path honestly; it makes no claim about ITD's cross-source behaviour.
