# External structural incremental value report (H61/H62 — the primary result)

Status: **research report, locked holdout evaluation** (`evaluations_allowed = 1` per the
preregistration). Not a certified revision; does not modify `ITD V29.18`.

## The test

Development: `iso_run1`, `iso_run2` (24 frames each). Holdout: `iso_topo` (40 frames),
`iso_run3` (24 frames) — an **unsaturated** task (see
`STRUCTURAL_BASELINE_SATURATION_REPORT.md`). Feature sets: `BASELINE_COMPETENT_COMBINED`
(established), `ITD_3D_NONREDUNDANT` (`intensity` excluded — Mission 7 showed it is
~redundant with enstrophy), and the union (augmented). Model: logistic regression, fit
once on all development sequences, scored once on all holdout sequences — no re-fitting,
no re-selection. Statistics: grouped bootstrap (independent unit = sequence, `n=2000`
resamples, seed `6161`), margin `0.02`.

## Result (final — corrected event detector, see `MISSION8_REPRODUCIBILITY_REPORT.md`)

```
holdout_auc_established = 0.519
holdout_auc_itd_only    = 0.246
holdout_auc_augmented   = 0.344

added_value (augmented - established):
  diff_mean = -0.168
  95% CI    = [-0.175, -0.153]
  margin    = 0.02
  verdict   = not supported
```

**H61 (do non-magnitude ITD channels predict the event?) — not supported.** ITD-only
holdout AUC (0.246) is **below chance** (0.5).

**H62 (established + ITD_STRUCTURAL beats established alone?) — not supported.** The
combined model (0.344) is *worse* than established alone (0.519); the added-value CI is
entirely negative and excludes zero — a stronger, more decisive negative than "no
measurable benefit." Adding these ITD channels actively **hurts** predictive performance
on this external holdout.

## Honest limitations

* The established holdout AUC itself (0.519) is only barely above chance — a genuinely
  hard, unsaturated task, but also a task where even the established combined baseline is
  a weak predictor. This is not evidence *for* ITD; it means neither approach solves the
  task well, and ITD's addition still makes it measurably worse.
* Only 2 holdout sequences (a preregistration-consistent operationalization, not a
  post-hoc choice — see `MISSION8_DATASET_INVENTORY.md`). The grouped bootstrap's
  resampling cardinality is correspondingly low; the CI's narrowness partly reflects that
  low cardinality, not unlimited precision. Stated here rather than oversold.
* This is the **single, locked** holdout evaluation on this dev/holdout split. It is not
  re-run after inspection. It *was* recomputed once, before any report was written, after
  fixing the topology-event-detector bug described in `STRUCTURAL_EVENT_LABEL_REPORT.md` —
  a measurement-definition correction, not a search for a different result.

## Conclusion carried into the final report

On the one preregistered, unsaturated, externally-sourced, ITD-independent structural
task tested this mission, existing non-magnitude ITD structural channels do not
demonstrate incremental predictive value over a competent established structural baseline
— and measurably reduce it when combined.
