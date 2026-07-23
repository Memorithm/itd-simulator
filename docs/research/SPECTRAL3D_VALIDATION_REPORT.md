# Spectral-3D solver validation report (Gate A)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
The solver is an experimental in-environment CFD tool, not external empirical data.
Reproduce with `python -m itd_research.spectral3d validate --quick --output <dir>`
(also run in CI, step 10/12 of `run_validation.sh`).

## Solver

Incompressible 3D Navier-Stokes, periodic box, velocity-pressure projection
formulation, rotational nonlinear form, 2/3-rule dealiasing, classical RK4,
NumPy `rfftn`. Fourier/projection/dealias conventions are fixed in
`ITD_SPECTRAL3D_PREDICTIVE_VALIDATION_SPEC.md` §3 and tested.

## Gate-A results (all pass)

| check | result |
|---|---|
| derivative sign oracle (x, y, z) | ~1e-14 (each direction; cross-derivatives 0) |
| Laplacian on known field | exact to ~1e-11 |
| ABC curl u = u | ~1e-14 |
| projection: divergence to round-off | 0 |
| projection idempotent / gradient removed / no energy gain | verified |
| viscous single-mode decay vs exp(-nu k^2 t) | rel. error ~1e-15 |
| inviscid Taylor-Green energy conservation | drift ~1e-15 |
| Taylor-Green enstrophy growth (3D stretching) | +4-5 % over the run |
| divergence controlled throughout | ~5e-15 |
| deterministic (bitwise) re-run and seeded IC | identical |
| checkpoint save/load + restart | bit-for-bit; checksum-verified |

## Resolution study (inviscid Taylor-Green, 100 steps)

| N | energy drift | enstrophy growth | max divergence | runtime (s) |
|---:|---:|---:|---:|---:|
| 16 | ~1e-15 | 1.017 | ~3e-15 | 0.34 |
| 24 | ~1e-15 | 1.017 | ~6e-15 | 0.85 |
| 32 | ~1e-15 | 1.017 | ~5e-15 | 2.09 |

Conservation and divergence control are resolution-independent to round-off. Cost
scales as expected for 3D FFTs. Turbulence at 32^3-64^3 is **under-resolved** and
is labelled as such wherever used; it is adequate for solver verification and for
qualitative vortex-dynamics studies, not for quantitative DNS spectra.

## Gate A verdict: **passed**

Derivative oracles, divergence control, projection, viscous decay, inviscid
conservation, Taylor-Green plausibility (resolution-qualified), deterministic
checkpoint restart, and the vorticity-budget closure (see
`VORTICITY_BUDGET_REPORT.md`) are all satisfied.

## Unsupported / not done

No external reference DNS was compared quantitatively at matched resolution (the
JHTDB comparison is on queried data, not this solver); the solver is a minimal
pseudo-spectral code, not an OpenFOAM-class 3D package; no GPU/native backend is in
the authoritative path; forcing is limited to none/linear/low-band. These bound the
claims: the solver is a validated deterministic research tool, not a production DNS
code.
