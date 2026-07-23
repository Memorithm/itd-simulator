# Rust V29 equivalence report — extended 2D diagnostics subset (H47)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **software-equivalence**. Tolerance-level equivalence **never** implies
certification.

## Scope (honest boundary)

The Rust workspace (`itd-rs/`, pure-std, offline `cargo test`) reproduces a **clearly-
defined periodic-central-difference subset** of the ITD 2D diagnostics. It does **not**
reproduce the certified V29.18 signature — the finite-boundary operator and the
`structural_metrics` / multiscale pipeline remain Python-only and are never re-derived in
Rust. This is stated up front so "Rust equivalence" is not mistaken for "Rust
certification".

## What Mission 6 added (H47)

- **Two new quantities**: `palinstrophy` (`0.5⟨|∇ω|²⟩`) and `vorticity_flatness`
  (`⟨ω⁴⟩/⟨ω²⟩²`), joining the Mission 5 enstrophy, vorticity RMS, and localization — all
  via the same periodic central-difference operator (`itd_field::grad_sq_mean`).
- **Seven named fixture fields** (up from one): `zero_field`, `rigid_rotation`,
  `simple_shear`, `taylor_green`, `lamb_oseen`, `vortex_pair`, `noisy_field`. These
  exercise the operators across zero-field, constant-vorticity, smooth, and noisy inputs,
  covering the preregistered "zero-field" and "finite-value validation" elements.

## Shared-oracle protocol

`tools/rust/generate_diagnostics_fixture.py` (Python) writes
`itd-rs/fixtures/diagnostics.txt`: for each field, the velocity components and the five
Python-computed expected diagnostics. Two independent checks must both pass:

1. **Rust** (`cargo test --workspace`) reads the fixture and reproduces every value within
   the preregistered relative tolerance **1e-9** — all 7 fields × 5 quantities.
2. **Python** (`tests/test_rust_equivalence.py`) recomputes the same values from each
   field and matches the fixture within 1e-12, and confirms the generator is not stale.

## Equivalence level

| element | result |
|---|---|
| enstrophy, vorticity_rms, localization, palinstrophy, vorticity_flatness | within **relative_tolerance 1e-9** across all 7 fields |
| zero-field handling (rms → 0 guards) | exact (localization/flatness = 0) |
| derivative convention / boundary treatment | identical periodic central difference on both sides |

**Verdict: H47 supported within the periodic subset.** Rust reproduces a strictly larger,
clearly-defined 2D diagnostics subset than Mission 5 within the preregistered tolerance,
across seven fixture fields. It remains a research reference, never the scientific oracle,
and does not reproduce the certified finite-boundary signature.
