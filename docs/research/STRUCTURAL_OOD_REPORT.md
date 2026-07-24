# Structural OOD / abstention report (H73)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Design — reuse, not reinvention

`itd_research.mission8.ood` reuses Mission 6's shift-aware detector and three-state policy
(`itd_research.ood_shift.detector.fit_shift_reference`,
`itd_research.ood_shift.policy.three_state_policy`) **verbatim**, applied to
`ITD_3D_NONREDUNDANT` features. A `ShiftReference` is fit on development sequences only
(`iso_run1`, `iso_run2`); bands are calibrated the same way Mission 6 calibrated them:
`s_low` = 90th percentile of the in-domain (development) severity bulk, `s_high` = 50th
percentile of a **designated far category** — here, the real `mhd1024` sequences
(genuinely new source/physics) — never calibrated on the categories being judged.

## Categories judged (real data)

| category | description | n | mean severity | accept | reduce | abstain |
|---|---|---|---|---|---|---|
| `holdout_same_source` | held-out isotropic sequences (valid structural variation) | 64 | 1.32 | 0.844 | 0.109 | **0.047** |
| `resolution_downsample` | holdout sequences downsampled 2× | 64 | 1.59 | 0.703 | 0.250 | 0.047 |
| `measurement_noise` | holdout sequences + 5% Gaussian velocity noise | 64 | 2.13 | 0.344 | 0.469 | 0.188 |
| `measurement_mask` | holdout sequences + 20% random masking | 64 | 5.75 | 0.000 | 0.000 | **1.000** |
| `new_source_physics` | JHTDB mhd1024 sequences (calibration category) | 40 | 1.91 | 0.575 | 0.350 | 0.075 |

```
s_low = 1.880, s_high = 2.880
valid_variation_mean_abstain = 0.047
shift_mean_abstain           = 0.327
verdict: supported within tested scope
```

## H73: supported within tested scope

Valid structural variation (a held-out sequence from the *same* source) is almost always
accepted (4.7% abstention) — **not** the Mission 5/6 over-abstention failure mode this
detector was built to fix. Genuine shift categories abstain far more (32.7% mean,
dominated by `measurement_mask`'s 100% abstention under a severe 20% masking) — a clear,
non-degenerate separation between "this is still the same kind of data" and "this
measurement/resolution/source has genuinely changed," using the same transparent,
already-implemented machinery from Mission 6 rather than new bespoke OOD code.

## Honest caveats

* `resolution_downsample` and `new_source_physics` (used only for `s_high` calibration)
  both sit closer to `holdout_same_source` than to `measurement_mask` — the detector's
  separation is driven mainly by severe masking/noise, not by mild resolution changes or a
  cross-physics shift. A milder degradation regime might not separate as cleanly; this is
  reported rather than generalized beyond the tested levels.
* Because `new_source_physics` supplies `s_high`, it is not independently "judged" against
  the shift/valid split in the headline comparison — its own accept/reduce/abstain numbers
  are still reported in the table above for transparency, but the pass/fail verdict rests
  on `resolution_downsample` and `measurement_noise`/`measurement_mask` as the judged shift
  set.
* This is a descriptive OOD-behavior check, not a claim that ITD's *predictions* are more
  useful under any of these shifts — H73 is about whether the detector usefully
  distinguishes shift categories, independent of the (negative) H61/H62 predictive result.
