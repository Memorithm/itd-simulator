# Hard external predictive validation — preregistered specification (Mission 4)

Status: **preregistration**. Written *before* the final held-out evaluation. Not a
certified revision; does not modify `ITD V29.18`. The machine-readable, hashable
protocol is `configs/mission4/preregistered_protocol.toml`
(SHA-256 `b49049e02d28561326c170c32ae34055b9e712bfca8721eb09404fbd35e1523f`); this
document is its narrative. Once the final evaluation begins, the `[final_holdout]`
section and every locked decision are **immutable**.

## Central question

Does ITD retain **predictive or complementary** value on **unseen, difficult, noisy,
partially observed, cross-solver** vortex events under a **locked** protocol — enough
to distinguish it from established diagnostics? A negative answer is an acceptable,
reportable outcome. Experiments are **not** tuned after inspecting final results.

## Guardrails (carried from the mission brief)

* **V29.18 preserved** — core, equations, summaries, oracles, hashes untouched; no new
  revision number; all work experimental under `itd_research/`.
* **Mission 3 negatives preserved** — no universal superiority/threshold/channel
  interpretation, no optimal ITD-3D candidate, no strong whole-field PIV validation,
  no general real-time guarantee, no certification. These stand until *stronger*
  evidence contradicts them.
* **No circular validation** — event labels never derive from any ITD channel or an
  ITD-maximising threshold. Allowed: topology change, connected components of an
  established diagnostic, enstrophy-production crossing, circulation collapse, known
  solver event times, published annotations. Every label records provenance.

## Environment-bound scope (stated honestly up front)

This container has **no OpenFOAM/Nek5000** and **no CI network download**;
`h5py`/`netCDF4`/`vtk`/`sklearn` are absent. Therefore the **achievable** evidence is:

* **local-solver held-out** flows from the two in-repo solvers (2D `spectral_ns`,
  3D `spectral3d`), isolated by simulation seed/config; and
* **one external experimental PIV** field (biofilm), already committed, used as an
  **OOD control** (shear-dominated, not a vortex-event dataset).

Genuinely external CFD / DNS / tomographic-PIV integration is **gated behind manual
download workflows** and is marked **blocked** where unavailable — never fabricated.
Consequently H20 (cross-institution) and H24 (annotated vortical PIV) are declared
**blocked** in this environment, and H19 (cross-solver) is scoped to the achievable
2D↔3D dimensional transfer, with external finite-volume transfer blocked.

## Hypotheses H17–H26 and decision gates

| id | question | gate | class |
|---|---|---|---|
| H17 | predicts hard held-out transitions with useful lead time? | G | primary |
| H18 | **established + ITD** beats **established** on held-out data? | H | primary |
| H19 | calibrated on one solver, useful on another? | I | secondary (2D↔3D; FV blocked) |
| H20 | transfers across institutions/repositories? | I | **blocked** (one source) |
| H21 | robust to noise/filter/mask/downsample? | J | primary |
| H22 | robust to partial observation? | J | primary |
| H23 | detects out-of-domain flows and abstains? | K | primary |
| H24 | time-resolved PIV shows ITD leading annotated events? | L | **blocked** (no data) |
| H25 | different events need different channels? | — | exploratory |
| H26 | full streaming pipeline meets p95/p99? | M | primary |

**Gate decision rules** (from the brief): G — external/held-out events, independent
labels, no leakage, useful lead, CIs, acceptable false alarms. H — `established+ITD`
beats `established` on held-out data with a credible positive margin (≥ 0.02 AUC, CI
excluding 0). I — tested on a source not used for feature/threshold selection.
J — degradation quantified and bounded. K — abstention lowers OOD error without
collapsing coverage. L — independently annotated time-resolved events. M — p95/p99
deadlines met for the *complete* pipeline. **No gate authorises a certified revision.**

## Events and labels (ITD-independent)

* **Merger / pairing** (2D `spectral_ns`): strong-vorticity core count 2→1
  (connected components of `|ω| > 0.6·max`), the Mission 3 detector.
* **Taylor–Green breakdown** (3D `spectral3d`): first frame the enstrophy-production
  rate crosses a fixed fraction of its run maximum (a strain–vorticity quantity,
  ITD-free).
* **Tube interaction / fragmentation** (3D `spectral3d`): change in the count of
  `Q>0` connected components.

"Hard" is enforced by **weak events** (subtle precursors), **longer horizons**,
**noise/mask/downsample/partial-observation** degradation, and **cross-simulation /
cross-solver** held-out isolation — not by adding more easy synthetic flows.

## Features, baselines, models, splits, metrics

Locked in the TOML. Summary: established single diagnostics; a **locked
multi-feature established baseline**; ITD structural / full vectors; and the decisive
**`established` vs `established + ITD`** pair (H18). Models are interpretable first
(regularised logistic regression, LDA, small tree); deep nets are prohibited as
primary evidence; normalisation uses train statistics only. Splits are
**grouped by simulation** into `development` / `calibration` / `final_holdout`
(seeds locked in the TOML) — never frame-random. Metrics include ROC/PR-AUC,
balanced accuracy, sensitivity/specificity, F1, false-alarms-per-time, missed-event
rate, median lead + distribution, Brier, calibration error, all with **grouped
bootstrap** CIs (resampling whole runs).

## Locked evaluation discipline

The `final_holdout` runs are evaluated **exactly once**, after development and
calibration are frozen. After that point: no change to features, labels, thresholds,
preprocessing, or hyperparameters, and no removal of difficult cases. Any later
analysis is labelled **exploratory** and never replaces a preregistered result. The
report records the protocol's SHA-256 as the commitment and lists any deviation with
its reason.

## Reports produced

`HARD_EXTERNAL_PREDICTIVE_VALIDATION_REPORT`, `CROSS_SOLVER_TRANSFER_REPORT`,
`CROSS_SOURCE_GENERALIZATION_REPORT`, `NOISE_AND_PARTIAL_OBSERVATION_REPORT`,
`OOD_ABSTENTION_REPORT`, `HARD_PIV_PREDICTION_REPORT`, `EVENT_SPECIFIC_CHANNEL_REPORT`,
`END_TO_END_REALTIME_REPORT`, `MISSION4_DATASET_INVENTORY`. Each labels its evidence
class and preserves negative/blocked findings verbatim.
