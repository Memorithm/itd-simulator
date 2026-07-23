# ITD predictive-validation report (H7)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce with `python -m itd_research.prediction run --output <dir>` (a tiny
`--quick` form runs in CI, step 12/14 of `run_validation.sh`; `--quick` is a pipeline
check, **not** a scientific result).

## Question (H7, falsifiable)

Does the ITD signature **predict an impending vortex merger earlier or more reliably**
than established scalar diagnostics, on held-out runs, with no leakage?

## Design

An ensemble of 12 deterministic 2D co-rotating vortex-pair runs (fixed initial
separation 1.2; varied circulation ∈ {1.0, 1.3, 1.6, 1.9} and viscosity ∈ {0.002,
0.003, 0.004}) is integrated with the pseudo-spectral solver until each pair merges.

* **ITD-independent label.** The merger frame is defined by the strong-vorticity
  **core count** (connected components of `|ω| > 0.6·max|ω|`, ≥ min-cells) dropping to
  a persistent single core. ITD never sees this label. Event frames span 9–17 of ~21,
  so every run has a real pre-event window.
* **Prediction target.** A frame is positive iff the merger is within a horizon of
  `H` frames (primary `H = 4`; one frame = 0.28 time units). Post-event frames are
  dropped, so the task is *predicting the onset*, not *detecting the merged state*.
* **Leakage-safe evaluation.** Leave-one-run-out: each held-out run is scored by an
  IRLS logistic model fit on the other runs only, standardized on the training runs
  only. No frame trains a model that scores it; features are instantaneous (no future
  information). ROC-AUC is rank-based; the CI is a run-level bootstrap.

Feature sets compared: naive single scalars (`enstrophy`, `vorticity_rms`), the
multi-feature established-diagnostic baseline (enstrophy, palinstrophy, vorticity RMS,
flatness, mean gradient norm), the ITD structural vector, the full ITD signature, and
ITD+baseline.

## Results (12 runs, 12 events, primary horizon H = 4)

| feature set | AUC | 95% CI | median lead (t) | missed | false-alarm |
|---|--:|--:|--:|--:|--:|
| baseline `enstrophy` | 0.40 | [0.33, 0.44] | 3.64 | 0.75 | 0.30 |
| baseline `vorticity_rms` | 0.41 | [0.34, 0.44] | 3.64 | 0.75 | 0.32 |
| baseline diagnostics (5) | 1.00 | [1.00, 1.00] | 1.40 | 0.00 | 0.11 |
| ITD structural (5) | 1.00 | [1.00, 1.00] | 1.40 | 0.00 | 0.10 |
| ITD full (7) | 1.00 | [1.00, 1.00] | 1.40 | 0.00 | 0.10 |
| ITD + baseline (12) | 1.00 | [1.00, 1.00] | 1.40 | 0.00 | 0.10 |

## Horizon sensitivity (verdict is robust)

Evaluated at horizons {2, 3, 4, 6} on the same ensemble: ITD stays at AUC 0.998–1.000
and the multi-feature baseline at 0.997–1.000 at **every** horizon, with overlapping
CIs; the naive single scalars stay at or below chance (AUC 0.40–0.50) throughout. The
verdict does not depend on the horizon choice.

## H7 classification: **partially supported**

Two honest halves:

1. **ITD is a valid, reliable early predictor.** It reaches AUC ≈ 1.0 with **zero
   missed events**, a low false-alarm rate (~0.10), and a median lead time of ~1.4
   time units (≈ 5 frames) before the merger completes — and it decisively beats the
   **naive single-scalar precursors**. Notably, raw `enstrophy` and `vorticity_rms`
   predict *below chance* (AUC ≈ 0.40): in a viscous merger, enstrophy *decays* toward
   the event, so a naive "enstrophy rising ⇒ merger" reading points the wrong way.
2. **ITD does not beat the established multi-feature baseline.** The five standard
   velocity-gradient/vorticity scalars predict the merger *just as well* (AUC ≈ 1.0,
   identical lead time). Under Gate B, superiority requires non-overlapping bootstrap
   CIs and a ≥ 0.02 AUC margin; ITD and the baseline are tied at the ceiling, so the
   superiority claim is **not** met.

So ITD **predicts vortex transitions** within this scope, but is **not shown superior**
to diagnostics practitioners already have. The strong claim "ITD predicts failures"
is not supported; the falsifiable, scoped version — "ITD predicts this transition as
well as, not better than, established multi-feature diagnostics, and far better than
naive single scalars" — is.

## Gate B checklist

| requirement | status |
|---|---|
| ITD-independent event labels | met (core-count criterion) |
| no leakage (LOO, train-only standardization, instantaneous features) | met |
| held-out events | met (12 held-out runs) |
| ITD beats ≥ 1 meaningful baseline | met (naive enstrophy / vorticity RMS) |
| CIs reported | met (run-level bootstrap) |
| acceptable false alarms | met (~0.10 at the operating point) |
| ITD beats the *best* baseline | **not met** (ceiling tie with multi-feature diagnostics) |

## Limitations

A single flow *type* (2D co-rotating merger) at one initial geometry; timing/intensity
variation only; under-resolved 2D solver (not external DNS). The frame-level task
saturates (AUC ceiling) because features trend monotonically toward the merger, so
this design cannot separate two already-excellent predictors — a harder target (weaker
events, noisy/partial fields, 3D reconnection, real labelled engineering failures)
would be needed to test superiority. "Failure" is deliberately avoided: this is a
fluid *transition*, not an engineering failure. No result here certifies ITD for
prediction; it establishes that ITD is a competitive — not a dominant — merger
predictor on this controlled family.
