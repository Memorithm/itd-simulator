# Mission 8 final report — non-redundant structural and topological external validation

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

> **Update (H65-conclusive follow-up).** H65 was originally reported *inconclusive* because
> the two JHTDB MHD windows fetched contained zero qualifying events — a collection
> artefact, not a finding. A separately preregistered follow-up
> (`configs/mission8h65/preregistered_protocol.toml`, SHA-256 `83c20f85…`, committed and
> pushed before any new data was fetched) acquired six windows / 156 frames / 7 events and
> resolved it to **not supported** (augmented transfer AUC 0.477, below chance). The H65
> row and final question 8 below are updated; every other verdict is unchanged, and the
> follow-up did **not** re-litigate H62.

Preregistration `configs/mission8/preregistered_protocol.toml`
(SHA-256 `ddd64804b58b6661c22c5911f45832de7c0bc3afe2eed25de96d60ab40ec3206`), committed
`73adbdc`, before final external evaluation. Baseline commit `6480973` (Mission 7 merge).
No experiment was tuned after inspecting final results; success margins were not lowered;
no event was chosen post-hoc to flatter ITD; `intensity` was never used as primary ITD
evidence.

## The central question and honest answer

*Do existing non-magnitude ITD structural channels provide reproducible, transferable,
incrementally useful information for external vortex-**structure** events that competent
established structural diagnostics do not already capture?*

**No — on the one unsaturated, ITD-independent, externally-sourced structural task tested
this mission, existing non-magnitude ITD channels do not predict the event
(H61 not supported), do not add value beyond a competent established structural baseline
(H62 not supported: added value −0.168, 95% CI [−0.175, −0.153], entirely negative), and
measurably reduce combined-model performance.** This is not a repeat of Mission 7's
saturated experiment: the established baseline here is genuinely non-saturated
(development AUC 0.709, well below the 0.98 saturation gate) and only barely above chance
on holdout (0.519) — a genuinely hard, unsaturated task, on which ITD still does not
help. One descriptive finding stands out as worth future attention: two channels
(`helicity_mean`, `normalized_helicity`) show a 100%-sign-consistent response across the
(small, partly non-independent) set of observed topology-change events — but this
descriptive consistency does not translate into predictive or non-redundant value (H63,
H64 pooled — see below).

## H61-H74 verdicts

| id | gate | hypothesis | verdict |
|---|---|---|---|
| H61 | AF | Existing non-magnitude ITD channels predict an independently labelled external structural (topology) vortex event | **not supported** (ITD-only holdout AUC 0.246, below chance) |
| H62 | AG | Adding non-magnitude ITD channels to BASELINE_COMPETENT_COMBINED improves held-out event prediction by the preregistered margin | **not supported** (added value −0.168, CI excludes zero in the negative direction) |
| H63 | AH | At least one ITD structural channel carries reproducible information not explainable by a magnitude diagnostic | **not supported** (pooled check: no channel has both low correlation with enstrophy AND non-trivial partial correlation with the event) |
| H64 | AD | ITD structural channels respond consistently to independently defined topology changes | **supported within tested scope** (`helicity_mean`, `normalized_helicity`: 100% sign-consistent across 4 instances / 3 independent sequences) |
| H65 | AJ | A structural profile calibrated on one external source remains useful on a comparable independent source | **not supported** — *updated after the H65-conclusive follow-up* (was inconclusive; six preregistered MHD windows / 156 frames / 7 events now make it computable: augmented transfer AUC 0.477, below chance) |
| H66 | AD | Structural ITD signals remain useful after controlled spatial-resolution changes | **not supported** (downsample 2× added-value CI `[−0.269, +0.198]` includes zero) |
| H67 | AK | ITD structural channels retain or gain incremental value when only part of the structure is observable | **not supported / inconclusive** (`central_crop` collapses to an uncomputable AUC — event scarcity under cropping) |
| H68 | AK | ITD structural channels provide incremental value under realistic noise/masking | **not supported** (`noise=0.05` added value sub-margin; `mask=0.20` uncomputable) |
| H69 | AI | ITD structural channels improve localization of independently identified vortex regions | **blocked** (architectural: existing ITD-3D channels are global scalars, no spatial output) |
| H70 | AF | ITD structural channels change before the independently defined event with useful lead time | **not supported** (ITD-only/augmented detect only 1/4 events with lead time vs. established alone's 2/4 — adding ITD makes lead-time detection *worse*) |
| H71 | AD | The selected structural ITD channel profile remains stable across runs and sources | **supported within tested scope, but fragile** (Jaccard 0.50 across 4 sequences, 2 of which flag zero channels) |
| H72 | AL | ITD structural channels agree with independently documented coherent-vortex evolution in time-resolved PIV/PTV | **blocked** (no open, time-resolved, vortex-dominated PIV/PTV dataset secured despite a genuine search this mission) |
| H73 | AM | Domain-shift detection distinguishes loss of calibration from valid structural variation without excessive abstention | **supported within tested scope** (valid-variation abstention 4.7% vs. shift-category abstention 32.7%) |
| H74 | AN | A profile-driven implementation computes only necessary structural diagnostics and reduces latency without changing results | **not supported** (results are bitwise-identical on shared channels, but the profile path is *slower*, not faster — no short-circuiting exists to skip unneeded channels) |

None of decision gates AD-AN automatically authorizes a certified revision; none does so
here — every gate's outcome above is either a negative, a fragile/caveated partial, or a
documented block.

## Sub-reports

`MISSION8_STRUCTURAL_TOPOLOGICAL_EXTERNAL_SPEC`, `MISSION8_DATASET_INVENTORY`,
`STRUCTURAL_EVENT_LABEL_REPORT`, `STRUCTURAL_BASELINE_SATURATION_REPORT`,
`EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT`, `EXTERNAL_TOPOLOGY_VALIDATION_REPORT`,
`REGION_LEVEL_LOCALIZATION_REPORT`, `CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT`,
`PARTIAL_OBSERVATION_STRUCTURAL_REPORT`, `STRONGLY_VORTICAL_PIV_M8_REPORT`,
`STRUCTURAL_OOD_REPORT`, `STRUCTURAL_PROFILE_PERFORMANCE_REPORT`,
`MISSION8_REPRODUCIBILITY_REPORT`.

## The fifteen final questions — answered explicitly

1. **Was an unsaturated task obtained?** Yes — development established AUC 0.709 (H62's
   gate), well below the 0.98 saturation threshold, unlike Mission 7's saturated event.
2. **Was the event ITD-independent?** Yes — Q-criterion connected-component count change,
   ITD never consulted; a λ₂-based disagreement check is reported separately.
3. **Do non-magnitude channels predict it?** No — ITD-only holdout AUC 0.246, below
   chance (H61 not supported).
4. **Does ITD add value beyond competent structural diagnostics?** No — added value
   −0.168, CI entirely negative (H62 not supported); the combined model is measurably
   worse than established alone.
5. **Is any channel genuinely non-redundant?** No — the pooled H63 check found no channel
   with both low correlation to enstrophy and non-trivial partial correlation with the
   event label.
6. **Does ITD improve region localization?** Blocked — no existing ITD-3D channel
   produces a per-cell spatial field (H69).
7. **Does ITD detect topology changes?** Descriptively, two channels (`helicity_mean`,
   `normalized_helicity`) respond with a consistent sign at every observed event (H64
   supported within tested scope) — but this does not translate into predictive value.
8. **Does the result transfer across sources?** **No** — *answer updated by the
   H65-conclusive follow-up.* Mission 8 originally left this inconclusive because the two
   MHD windows fetched contained zero qualifying events. Six preregistered windows (156
   frames, 7 events, both classes) now make it computable: the calibrated profile
   transfers at **0.477 augmented AUC — below chance**. The drop versus source A is small
   (−0.132), but that reflects a near-chance model staying near-chance, not successful
   transfer. See `CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT.md`.
9. **Is ITD more useful under partial observation?** No — `central_crop` collapses to an
   uncomputable holdout AUC; no level tested shows a margin-exceeding ITD-specific gain
   (H67 not supported/inconclusive).
10. **Under noise/masking?** No — `noise=0.05`'s positive added value (+0.006) does not
    reach the preregistered margin; `mask=0.20` collapses to an uncomputable AUC (H68 not
    supported).
11. **Does vortical PIV support ITD?** Blocked — a genuine search this mission (VIVALDy
    2D VIV-PIV, Tomo-PTV vortex-ring literature) found no open, downloadable,
    time-resolved, vortex-dominated dataset (H72).
12. **Is structural OOD useful?** Yes, within tested scope — the shift-aware detector
    (reused from Mission 6) separates valid structural variation (4.7% abstention) from
    genuine shift categories (32.7% mean abstention) without the Mission 5/6
    over-abstention failure mode (H73 supported within tested scope).
13. **Did profile-driven computation reduce cost?** No — numerically bitwise-identical
    but *slower* (0.92× "speedup"), because no channel short-circuiting exists yet (H74
    not supported).
14. **Has industrial maturity advanced beyond IRL-4?** No — a decisive negative result on
    a genuinely unsaturated external task, plus a working, tested, reusable structural/
    topological research infrastructure, is not the same as advancing production
    readiness; maturity remains **IRL-4**.
15. **Is a new certified revision justified?** **No.**

## Final strategic statement

Per this mission's explicit final rule: competent external structural baselines
outperform ITD on the primary test (established AUC 0.519 vs. ITD-only 0.246, augmented
0.344), and no reproducible incremental or localization value was found beyond a single
fragile descriptive pattern (H64) that does not survive contact with the predictive test.
Therefore, stated plainly:

**The tested ITD structural channels do not demonstrate distinct external scientific
value beyond established diagnostics within the evaluated domains.**

No new channel is invented in response. No certified revision is created. ITD is
repositioned, as of this mission, as an **experimental diagnostics framework** — its value
preserved as a reproducible validation and comparison laboratory (manufactured oracles,
region/topology machinery, saturation screening, grouped statistics, shift-aware OOD),
with future priority on ingestion, provenance, benchmarking, OOD, and deployment
infrastructure rather than unsupported claims of scientific superiority.

## Guardrail compliance

`itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, certified
equations/oracles/Rust fixtures/reference summaries/public hashes/certification reports
**unchanged** — the diff touches only `itd_research/mission8/`, `tests/`, `docs/research/`,
`configs/mission8/`, and `run_validation.sh`. One-way dependency preserved (`itd_v29_core`
never imports `itd_research`; verified by `tests/test_research_boundaries.py`). **No**
V29.19, V30, certified ITD-3D, universal structural score, universal topology predictor,
or production-certified ITD introduced. Mission 3-7 findings preserved verbatim (ITD
predicts some controlled internal events; did not beat competent established baselines;
universal thresholds not supported; cross-flow transfer weak; cross-code evidence
promising but confounded; near-OOD abstention over-abstained; external JHTDB incremental
value exactly zero; `intensity` nearly redundant with enstrophy; external coherent-vortex
PIV blocked; industrial maturity remained IRL-4) — Mission 8 extends this record to
structural/topological, non-magnitude channels and a genuinely unsaturated task, and adds
no exception to it.

## Net conclusion

Mission 8 built the infrastructure Mission 7 lacked to test a genuinely different kind of
question — structural/topological, not magnitude — on a genuinely unsaturated task, and
still found a clean, preregistered, doubly-confirmed (pre- and post-bug-fix) negative:
existing non-magnitude ITD channels do not predict this external structural event, do not
add value combined with a competent established baseline, and actively hurt when
combined. One honest, fragile descriptive signal (H64/H71) and one solid piece of reused
infrastructure (H73's shift-aware OOD) are the positive-leaning findings; neither changes
the central verdict. Nothing was forced positive. No certified revision is justified.

## Reproduction

`configs/mission8/ci.toml` + `python -m itd_research.mission8 validate` (offline,
deterministic, ~10-30s, `run_validation.sh` step 27). Real-data numbers require the manual
JHTDB fetch workflow (network-blocked in normal CI) — see `MISSION8_DATASET_INVENTORY.md`
and `MISSION8_REPRODUCIBILITY_REPORT.md`. Determinism: `PYTHONHASHSEED=0`, single-thread
BLAS, float64, `numpy.default_rng(seed)`.
