# Mission 5 — genuine external cross-code validation (preregistered spec)

Status: **preregistration**. Written *before* the final cross-code / external
evaluation. Not a certified revision; does not modify `ITD V29.18`. Machine-readable,
hashable protocol: `configs/mission5/preregistered_protocol.toml`
(SHA-256 `1142668b6a119cb95890e97ad11401479b6c22eae01454b8e5c099e015b45fbb`). Once the
final evaluation begins, `[final_holdout]` and the locked decisions are **immutable**.

## Central question

*Does ITD contribute information that stays useful across independent solvers, datasets
and measurement systems when the physical event is held as constant as possible?* A
negative or blocked answer is acceptable and reported. No experiment is tuned after
inspecting final results, and the 0.02 added-value margin is not lowered.

## Guardrails (carried forward)

`itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, oracles, hashes
unchanged; no new revision number; all work under `itd_research/`. Mission 3 and
Mission 4 negatives remain visible: ITD predicts controlled events but did **not** add
the preregistered value over strong baselines, thresholds/components did not transfer
universally, cross-domain prediction collapsed, magnitude channels were redundant,
helicity/stretching stayed non-redundant, PIV evidence stayed limited, the Mission 4
OOD test was easy, full-volume 3D real time was not shown, maturity stayed IRL-4, and
no revision was justified.

## Correcting the Mission 4 confound (section 5)

Mission 4 compared a 2D merger against a plane of a 3D Taylor–Green breakdown, which
**confounded** solver, dimensionality, event type, flow family, label definition, and
mechanism. Mission 5 separates them:

* **Test A — same physics, different solver**: Taylor–Green through the pseudo-spectral
  `spectral3d` **and a new independent finite-difference projection solver**. This is
  the flagship (H29). It is **cross-code (two in-repo numerical methods)**, *not*
  cross-institution — labelled as such everywhere.
* **Test B — same solver, different physics**: `spectral3d` Taylor–Green vs co-rotating
  tubes (event transfer independent of solver).
* **Test C — same physics+solver, different resolution**: 24³ / 32³ / 48³.
* **Test D — simulated vs experimentally measured**: **blocked** (no integrable
  experiment/PIV).

## Environment-bound achievability (stated up front)

No OpenFOAM/Nek5000, no CI network, no h5py/netCDF4/vtk/sklearn; **cargo/rustc are
present**. Achievable: **H29** (cross-code), **H31** (near-OOD), **H33**
(degradation-specific value), **H34** (profile stability), **H35** (full-volume 3D
perf), **H36** (Rust equivalence). **Blocked**: **H27/H28** (external prediction /
incremental value — no integrable external labelled dataset in CI), **H30**
(cross-institution), **H32** (annotated vortical PIV). The Re=3900 cylinder-wake
integration is *attempted* (workflow + honest status), not faked.

## Hypotheses H27–H36 and gates

| id | question | gate | achievability |
|---|---|---|---|
| H27 | predicts an external labelled event? | N | **blocked** |
| H28 | adds value on external holdouts? | O | **blocked** (proxy: H29) |
| H29 | same-physics cross-code transfer + added value? | P | achievable |
| H30 | cross-institution transfer? | Q | **blocked** |
| H31 | near-OOD abstention reduces risk, keeps coverage? | R | achievable |
| H32 | strongly-vortical PIV agreement? | S | **blocked** |
| H33 | ITD adds *more* value under degradation? | — | achievable |
| H34 | event-channel profiles stable across sources? | — | achievable |
| H35 | full-volume ITD-3D meets performance envelopes? | T | achievable |
| H36 | Rust reproduces Python within tolerance? | U | achievable |

**No gate authorises a certified revision.**

## Locked method (see the TOML for the machine-readable form)

Same-physics comparison uses **integral / phase / spectral metrics and event times,
never pointwise fields across different grids/methods**. Event labels are
ITD-independent (enstrophy-production peak; core-count; lift/shedding if a cylinder
dataset is integrated). Features: established set, ITD set, and the decisive
`established` vs `established + ITD` pair, plus ITD-only / established-only / a single
physical scalar / persistence / temporal baselines. Splits are grouped by **source and
seed**; the holdout source (finite-difference) is never used for feature/threshold
selection. Models are interpretable (logistic, LDA). AUC CIs are grouped bootstraps.
The `final_holdout` (finite-difference Taylor–Green, seeds 90–95) is evaluated **once**.

## Reports produced

`MISSION5_FINAL_REPORT`, `SAME_PHYSICS_CROSS_CODE_REPORT`,
`EXTERNAL_INCREMENTAL_VALUE_REPORT`, `NEAR_OOD_ABSTENTION_REPORT`,
`STRONGLY_VORTICAL_PIV_REPORT`, `FULL_VOLUME_3D_PERFORMANCE_REPORT`,
`EVENT_PROFILE_STABILITY_REPORT`, `RUST_REFERENCE_EQUIVALENCE_REPORT`,
`CYLINDER_RE3900_INTEGRATION_REPORT`. Each labels its evidence class and preserves
negative/blocked findings.
