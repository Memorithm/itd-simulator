# Structural baseline saturation report (H62 gate)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Purpose

Mission 7 showed ITD adds no value on an event **already saturated** by an established
magnitude diagnostic (baseline AUC 1.000). Mission 8's preregistration makes this a hard
gate: a candidate task is screened for saturation on **development data only**, using
`BASELINE_COMPETENT_COMBINED` (never ITD), via leave-one-dev-sequence-out cross-validation.
Established ROC-AUC or PR-AUC `>= 0.98` excludes the task from the primary H62 test
(descriptive/regression use only); events are always chosen on physical relevance, never
by re-searching until ITD wins.

## Screening result (the one task tested)

Task: `jhtdb_isotropic_core_topology_change` (Q-criterion core-merger/split), development
sequences `iso_run1`, `iso_run2`, leave-one-out established-only scoring:

```
established_development_auc    = 0.709
established_development_pr_auc = 0.372
saturation_status               = unsaturated
selected_for_primary_test        = true
```

**This is the opposite of Mission 7's saturated enstrophy-burst task.** The established
combined baseline (`BASELINE_COMPETENT_COMBINED`: enstrophy, vorticity RMS, Q⁺/λ₂⁻
fraction, swirl mean, region count, core-tracking volume/displacement, temporal rates) is
a real, non-trivial, non-saturated classifier (AUC well below 1.0, well below the 0.98
gate) on this task — exactly what Mission 8 set out to find before testing ITD. The task
was selected on physical relevance (a genuine topology-change event, defined independently
of ITD) and screened once; it was not re-selected after seeing how ITD performed.

## Implication

Because the screen passed *before* ITD was ever consulted, the holdout result in
`EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md` is eligible to serve as primary
evidence for H61/H62 — a genuine test of whether ITD adds value on a task the established
baseline does **not** already solve, unlike Mission 7's exhausted experiment.
