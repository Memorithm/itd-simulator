# Mission 8 — non-redundant structural events and external topological validation (preregistered spec)

Status: **preregistration**. Written *before* final external holdout evaluation. Not a
certified revision; does not modify `ITD V29.18`. Machine-readable protocol
`configs/mission8/preregistered_protocol.toml`
(SHA-256 `ddd64804b58b6661c22c5911f45832de7c0bc3afe2eed25de96d60ab40ec3206`). Once final
evaluation begins, `[final_holdout]` and the locked decisions are **immutable**.

## Why Mission 8, and why not repeat Mission 7

Mission 7 tested ITD on genuine external DNS for the first time and found a clean
negative: the event was an **enstrophy burst** (a magnitude threshold), the competent
established baseline reached **AUC 1.000** on it, and adding ITD changed the held-out AUC
by **exactly 0.000**. ITD's only channel that tracked the event, `intensity`, is
~redundant with enstrophy (ρ=+0.994). That experiment is **saturated and closed**; Mission
8 must not re-run it as if it were still open.

Mission 8 asks a narrower, honest question instead:

> Do ITD **structural** channels (never `intensity`) provide reproducible, transferable,
> incrementally useful information for external vortex **structure/topology** events —
> merger, split, fragmentation, reconnection, coherence loss — that competent established
> **structural** diagnostics do not already capture?

A negative, partial or blocked answer is fully acceptable and is preserved. No task is
retried after seeing its ITD performance; a saturated candidate is retained only for
descriptive/regression use, never as the primary incremental-value test.

## The saturation screen (the central methodological safeguard)

Before any candidate task can be the primary H62 test, its **established-only**
performance is measured on **development** frames only. If `established_roc_auc >= 0.98`
or `established_pr_auc >= 0.98`, the task is **saturated** and excluded from the primary
test (retained only for ingestion/physical/regression checks). This directly prevents
repeating Mission 7's saturated-enstrophy mistake and prevents "shopping" for an event
until ITD wins — the screen only ever looks at established performance.

## Datasets secured this session

| source | institution | role | comparability |
|---|---|---|---|
| **JHTDB isotropic1024coarse** (24³, 40 frames, dt=0.1) | Johns Hopkins | primary external structural source | — |
| **JHTDB mhd1024** (24³, 24 frames, dt=0.1) | Johns Hopkins | second source for H65 | same institution/modality, **different forcing physics** (MHD vs pure hydrodynamic) — honestly reported as *within-institution cross-physics transfer*, never claimed cross-institution |

Blocked (attempted, honestly recorded): cylinder Re≈3900 (GB-scale, unchanged since
Mission 6/7), time-resolved coherent-vortex PIV (no small redistributable source found),
JHTDB `transition_bl` (HTTP 500 from this session — its non-uniform wall-normal grid is
likely incompatible with the node-index fetch mode used here).

## The independent structural event: topology change via Q-criterion regions

Events are **never** defined using ITD. The label is the connected-component count of
**Q(gradient) > 0** regions (established Q-criterion; 6-connectivity 3D flood fill,
deterministic, dependency-free — the same style as the certified-adjacent
`prediction/events.py` 2D core-count labeller, extended to 3D and to both directions):

- **core_merger** — the component count drops to, and persistently holds, a lower value.
- **core_split** — the component count rises to, and persistently holds, a higher value.

An alternative label (λ₂<0 components) is computed for disagreement reporting; the
Q-based label is primary and is never replaced after seeing ITD's score.

## ITD feature sets (existing channels only — no new channels)

`ITD_MAGNITUDE_CONTROL` (`intensity`, control/consistency only — never primary evidence),
`ITD_STRUCTURAL` (`localization`, `heterogeneity`, `roughness`), `ITD_ORIENTATION`
(`orientation_dispersion`), `ITD_TEMPORAL` (frame-to-frame rate of change of the structural
+ orientation channels — a derived analog, not the certified 2D `temporal_deformation`),
`ITD_3D_NONREDUNDANT` (all structural + orientation + helicity + stretching channels),
`ITD_ALL_EXISTING` (every existing 3D channel, `intensity` included). The primary test set
is `ITD_3D_NONREDUNDANT`.

## Established baseline groups

`BASELINE_MAGNITUDE` (enstrophy, vorticity RMS), `BASELINE_STRUCTURAL` (Q⁺ fraction, λ₂⁻
fraction, swirl mean, region count), `BASELINE_CORE_TRACKING` (mean/std region volume,
centroid displacement rate), `BASELINE_TEMPORAL` (rate of change of region count and Q⁺
fraction), and `BASELINE_COMPETENT_COMBINED` (their union) — the primary comparison is
`BASELINE_COMPETENT_COMBINED` vs `BASELINE_COMPETENT_COMBINED + ITD_STRUCTURAL`.

## Manufactured oracles (A–J)

Deterministic, offline, dependency-free software/interpretation oracles validate the
region-tracking, topology-labelling and structural-feature machinery **before** any
external claim: two separated vortices, controlled merger, controlled split, rigid
translation, rotation, amplitude scaling, a resolution sweep, masking, noise, and a
no-vortex pure-shear control. These are not external scientific evidence.

## Statistics

Grouped by **DNS sequence** (never individual frames); 2000-resample grouped bootstrap;
metrics beyond ROC-AUC: PR-AUC, event recall, false alerts per unit time, IoU, Dice,
centroid error, core-count accuracy, lead time. H62 requires the added-value margin (0.02)
with a bootstrap CI excluding 0, on an **unsaturated** task. H63 (non-redundancy) requires
more than low correlation: partial correlation controlling for enstrophy **and** a grouped
ablation predictive/localization effect.

## Hypotheses H61–H74 and gates

| id | question | gate |
|---|---|---|
| H61 | non-magnitude ITD predicts an independent structural event | AF |
| H62 | ITD_STRUCTURAL adds value beyond BASELINE_COMPETENT_COMBINED | AG |
| H63 | an ITD structural channel is non-redundant vs magnitude | AH |
| H64 | ITD structural channels respond consistently to topology change | AD |
| H65 | calibration transfers to a comparable second source | AJ |
| H66 | structural signal stable across resolution | AD |
| H67 | ITD value under partial observation | AK |
| H68 | ITD value under noise/masking | AK |
| H69 | ITD improves region/core localization | AI |
| H70 | ITD channels lead the event with useful lead time | AF |
| H71 | the structural profile is stable across runs/sources | AD |
| H72 | ITD agrees with documented coherent-vortex PIV/PTV | AL |
| H73 | structural OOD distinguishes shift types without over-abstaining | AM |
| H74 | profile-driven computation reduces cost, preserves results | AN |

Verdicts: `supported within tested scope | partially supported | not supported |
inconclusive | blocked`. **No gate authorizes a certified revision.**

## Guardrails

`itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, oracles, hashes,
reference summaries unchanged; one-way dependency (research → core); no new revision; no
V29.19/V30/certified ITD-3D/universal structural score/universal topology
predictor/production ITD. Mission 3–7 negatives preserved, including Mission 7's saturated
enstrophy-event negative (retained as a regression reference, never re-litigated as if
open).

## Final strategic rule (verbatim commitment)

If competent external structural baselines again match or outperform ITD, and no
reproducible incremental or localization value is found, the report will state plainly:
**"The tested ITD structural channels do not demonstrate distinct external scientific
value beyond established diagnostics within the evaluated domains."** In that case no new
channel is invented and no certified revision is created; ITD is repositioned as an
experimental diagnostics/validation framework, and infrastructure (ingestion, provenance,
benchmarking, OOD, deployment) is prioritized over unsupported superiority claims.

## Reports produced

`MISSION8_FINAL_REPORT`, `MISSION8_DATASET_INVENTORY`, `STRUCTURAL_EVENT_LABEL_REPORT`,
`STRUCTURAL_BASELINE_SATURATION_REPORT`, `EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT`,
`EXTERNAL_TOPOLOGY_VALIDATION_REPORT`, `REGION_LEVEL_LOCALIZATION_REPORT`,
`CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT`, `PARTIAL_OBSERVATION_STRUCTURAL_REPORT`,
`STRONGLY_VORTICAL_PIV_M8_REPORT`, `STRUCTURAL_OOD_REPORT`,
`STRUCTURAL_PROFILE_PERFORMANCE_REPORT`, `MISSION8_REPRODUCIBILITY_REPORT`. Each states
status, evidence class, commit, protocol hash, dataset source, independent-unit count,
limitations, negatives and blocked items.
