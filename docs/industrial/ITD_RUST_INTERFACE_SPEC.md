# ITD Rust interface / production-port specification

Status: **research/process document** (IRL-6 direction). Not a certified revision;
does not modify `ITD V29.18`. It specifies the frozen numerical and data contract a
future Rust production port MUST satisfy, and how it is validated against the existing
oracle fixtures. It authorizes **no** change to the certified core and proposes **no**
new revision.

## Purpose and non-goals

A Rust port would give a memory-safe, deterministic, embeddable engine for the ITD
V29.18 numerics and the experimental research channels. This document freezes the
interface so a port is a *reimplementation to a fixed contract*, not a redesign.

**Non-goals:** the port does not certify ITD, does not change any V29.18 equation or
output, and is never the authority — the Python reference and the oracle fixtures are.
The dependency is one-way: **the Rust port is validated against the reference; the
reference never depends on the port.**

## Frozen numerical contract (must match to float64 tolerance)

The port must reproduce, on the committed oracle inputs, every reference array within
a stated tolerance (regression-level, `~1e-12` relative on smooth fields):

* **Vorticity / boundary operator** — `numerical_vorticity_with_boundary` for
  `finite`, `isolated`, and rectangular grids (oracle arrays `VORT_UF`, `VORT_UF_ISO`,
  `VORT_UP`, `VORT_RECT`; gradients `GRAD_*`). Axis order is `[y, x]`, row-major.
* **Curvature-weighted rotational intensity** — `<ω² · exp(ℓ²·κ)>` with the V29.18
  `characteristic_length` and boundary-consistent mean.
* **Structural signature** — the five components (heterogeneity, localization,
  roughness, sign-mixing, temporal-deformation) and the bounded `structure_score`,
  exactly as `itd_v29_core.structural_metrics` computes them, including the structural
  length and default weights.

The authoritative fixtures are `tests/fixtures/oracle_data.rs` (Rust-includable) and
`tests/fixtures/analytical_oracles.json`. The port's test suite `include!`s the former
and asserts elementwise agreement.

## Data interface

| item | contract |
|---|---|
| input velocity | two (2D) or three (3D) `f64` arrays, row-major, axis order `[y, x]` / `[z, y, x]` |
| coordinates | per-axis strictly-increasing `f64` coordinate vectors (non-uniform allowed) |
| boundary mode | enum `{finite, isolated}`; validated, no silent default |
| output (V29.18) | `intensity: f64`, `signature: [f64; 5]`, `structure_score: f64`, `vorticity_rms: f64` |
| output (research 3D) | the 8-channel superset as a named `f64` map; explicitly experimental |
| determinism | float64 throughout; no parallel reduction that reorders float sums unless proven bit-stable |

## Validation gates for the port (before any use)

1. **Oracle gate** — all `oracle_data.rs` arrays reproduced within tolerance.
2. **Analytical gate** — the analytical oracles (rigid rotation, Burgers stretching,
   ABC helicity) reproduced (`analytical_oracles.json`).
3. **Determinism gate** — bitwise-identical output across repeated runs and thread
   counts; documented reduction order.
4. **Cross-check gate** — on random fields, agreement with the Python reference within
   tolerance (the reference stays the authority).
5. **Performance gate** — measured against the H15 real-time envelope; a faster backend
   must pass gates 1–4 *before* its timings are quoted.

## Scope boundary

The port MAY implement the V29.18 core and the experimental research channels; it MUST
keep them labelled distinctly (certified vs experimental) exactly as the Python
packages do (`itd_v29_core` vs `itd_research`). A port passing gates 1–5 raises the
interface-maturity criterion toward IRL-6; it does **not** by itself raise the process
band (IRL-7+), which remains a quality-management effort.
