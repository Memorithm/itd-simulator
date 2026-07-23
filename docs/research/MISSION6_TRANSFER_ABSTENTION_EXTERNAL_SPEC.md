# Mission 6 — transferability, calibrated abstention, external evidence (preregistered spec)

Status: **preregistration**. Written *before* final evaluation. Not a certified
revision; does not modify `ITD V29.18`. Machine-readable protocol
`configs/mission6/preregistered_protocol.toml`
(SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`). Once final
evaluation begins, `[final_holdout]` and the locked decisions are **immutable**.

## Central questions

1. Does ITD preserve **transferable structural information** between numerical methods
   **after fair temporal, amplitude and resolution normalization** — i.e. against a
   *competent, non-degenerate* established baseline, not the Mission 5 raw baseline that
   anti-transferred (AUC 0.03)?
2. Can the product **reduce confidence intelligently** under domain shift **without
   unnecessarily rejecting useful data** (the Mission 5 near-OOD over-abstained on ~85%
   of still-predictable shifts)?

A negative or blocked answer is acceptable. No experiment is tuned after inspecting
final results; the 0.02 margin is not lowered; **a below-chance baseline is never used
as evidence of ITD value**; signs are never reversed after seeing holdout labels.

## Guardrails

`itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, oracles, hashes
unchanged; no new revision; one-way dependency (research → core). Mission 3/4/5
negatives preserved, including: ITD added no significant value over strong baselines
(M4 H18); thresholds/component maps not universal; cross-flow transfer weak; the M5
cross-code result is promising **but confounded** (ITD 0.85 vs a below-chance 0.03
baseline); near-OOD over-abstains.

## The Mission 5 → Mission 6 hypothesis about the mechanism

The M5 established features anti-transferred because they are **scale/amplitude-
dependent** across codes, while ITD channels are **dimensionless ratios** (e.g.
localization `<ω⁴>/<ω²>² − 1`), hence scale-invariant. Mission 6 tests directly whether
a **rank-normalized / dimensionless / orientation-corrected** established baseline
transfers just as well — in which case ITD's apparent advantage is *normalization, not
structure* (H38 would then be **not supported**). This is the honest, likely outcome to
falsify.

## Environment-bound achievability

No OpenFOAM/Nek5000, no CI network, no h5py/netCDF4/vtk/sklearn; **cargo/rustc present**.
Achievable: **H37–H45** (two in-repo codes), **H47** (Rust V29 2D signature), **H48**
(full-volume selective/optimized). **H46** (external cylinder) is *attempted* via a
manual, network-enabled, checksum-verified workflow and is **blocked-in-CI**.

## Hypotheses H37–H48 and gates

| id | question | gate |
|---|---|---|
| H37 | ITD-only stays predictive across codes (larger ensemble, controlled) | W |
| H38 | ITD beats a **competent** (normalized) baseline | V |
| H39 | competent + ITD beats competent-only by the margin | X |
| H40 | transfer useful in **both** directions | W |
| H41 | transfer useful across resolution changes | W |
| H42 | result survives temporal-alignment policies (not a timing artefact) | W |
| H43 | shift-aware detector localizes axis/severity better than global Mahalanobis | Y |
| H44 | three-state accept/reduce/abstain beats binary abstention | Y |
| H45 | unnecessary abstention drops far below ~0.85, risk controlled | Y |
| H46 | real cylinder subset integrated outside CI | AA |
| H47 | Rust reproduces the V29.18 2D signature within tolerance | AC |
| H48 | full-volume latency improves, numerics preserved | AB |

**No gate creates a certified revision.**

## Method (locked; see the TOML for the machine form)

Cross-code: two solvers, Taylor-Green, resolutions/viscosities/seeds locked, grouped by
simulation+source, **bidirectional**, competent baselines A–F (selected on dev folds
only), multiple event definitions and time-alignment policies (disagreements reported).
H38 requires the competent baseline **above chance**; H39 requires a credible margin
with CI excluding 0. Shift-aware OOD: per-axis standardized distances vs a global one, a
transparent monotone confidence discount, a three-state policy, and a **utility**
(false-confidence cost 4×, unnecessary-abstention cost 1×) with risk-coverage curves.
Rust: exact V29.18 2D operator against Python-generated shared fixtures with explicit
equivalence levels (bitwise / abs-tol / rel-tol / not-equivalent). Full-volume:
selective channel execution with shared-gradient reuse, optimizations validated for
numerical equivalence.

## Reports produced

`MISSION6_FINAL_REPORT`, `H29_COMPETENT_BASELINE_REPORT`,
`H29_BIDIRECTIONAL_TRANSFER_REPORT`, `CROSS_CODE_CHANNEL_STABILITY_REPORT`,
`SHIFT_AWARE_OOD_REPORT`, `CONFIDENCE_DEGRADATION_REPORT`,
`RISK_COVERAGE_ABSTENTION_REPORT`, `CYLINDER_RE3900_INTEGRATION_STATUS`,
`FULL_VOLUME_OPTIMIZATION_REPORT`, `RUST_V29_EQUIVALENCE_REPORT`. Each states evidence
class, commit, config hash, data source, limitations, negatives, and blocked items.
