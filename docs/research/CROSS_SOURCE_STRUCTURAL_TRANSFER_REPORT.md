# Cross-source structural transfer report (H65)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Design

Calibrate (fit) `BASELINE_COMPETENT_COMBINED` and `BASELINE_COMPETENT_COMBINED +
ITD_3D_NONREDUNDANT` models on source A's development sequences (`iso_run1`, `iso_run2`,
JHTDB isotropic1024coarse), evaluate **without refitting** on source A's own holdout
(`iso_topo`, `iso_run3`) and on source B (`mhd_topo`, `mhd_topo_run2`, JHTDB mhd1024) —
same event/feature definitions, source-level grouping throughout.
`itd_research.mission8.transfer.evaluate_cross_source_transfer` states explicitly in its
`comparability_note` that both sources are JHTDB (same institution, same access
modality): this is a **within-institution cross-physics** transfer test (isotropic
hydrodynamic → forced MHD turbulence), never claimed as cross-institution generalization.

## Result: inconclusive — not a transfer failure, an event-scarcity block

```
development_auc_established = 0.903   (source A dev, in-sample)
development_auc_augmented   = 1.000   (source A dev, in-sample)
transfer_auc_established    = NaN
transfer_auc_augmented      = NaN
performance_drop_established = NaN
performance_drop_augmented   = NaN
verdict: inconclusive
```

Both fetched MHD sequences (`mhd_topo`, `mhd_topo_run2`) have **zero** qualifying
Q-criterion core-merger/split events under the corrected, ITD-independent event
definition (see `STRUCTURAL_EVENT_LABEL_REPORT.md`) — their frame labels are all-negative,
so no ROC-AUC is computable on source B at all. This is an honest limitation of the two
specific MHD cutouts fetched this session (24 and 16 frames at `min_cells=8`), not
evidence that ITD does or does not transfer across physics. H65 is reported as
**inconclusive/blocked-by-event-scarcity**, not forced into either a positive or negative
verdict.

## What would be needed to actually test H65

A longer or differently-windowed MHD cutout (or a lower `min_cells`/different
persistence) that contains at least one qualifying topology-change event with a genuine
label imbalance, so a held-out AUC becomes computable. This was not pursued further this
session, consistent with the preregistration's rule against re-searching for a dataset
window until a target event appears — the two MHD windows already fetched (chosen for
provenance and origin diversity, not for event content) are the ones reported on.
