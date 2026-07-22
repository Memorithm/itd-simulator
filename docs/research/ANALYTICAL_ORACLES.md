# Analytical oracles for the post-V29 research phase

This document records **hand-derived** analytical oracles for the ITD
quantities. Each value is derived from the field definition by hand and is
independent of the Python implementation. The machine-readable form is
`tests/fixtures/analytical_oracles.json`; the consumer is
`tests/test_analytical_oracles.py`.

## Category discipline

The Rust regression fixture (`tests/fixtures/oracle_data.rs`) is an
**implementation-generated snapshot**: Python produces the numbers, so agreement
only shows another implementation reproduces Python behaviour. The oracles here
are a **separate category** and must never be mixed with that snapshot. A future
pure-Rust suite can consume `analytical_oracles.json` without importing any
Python-generated numerical output.

Source classifications used:

* `hand_derived` — closed form obtained by hand (this document);
* `symbolic_derivation` — computer algebra with a retained human derivation
  (none required here);
* `manufactured_solution` — qualitative property of a constructed field (kept in
  the benchmark runner);
* `regression_reference` — implementation snapshot (kept in `oracle_data.rs`).

## Conventions

Vorticity `omega = d(vy)/dx - d(vx)/dy`. The V29.18 finite operator is exact for
polynomials of degree <= 2, and the periodic centred difference of a sinusoid
`sin(k x)` on spacing `h` equals the exact derivative times `sinc(kh) =
sin(kh)/(kh)`. The finite spatial mean is trapezoidal; the periodic spatial mean
is the arithmetic mean over an endpoint-excluded grid. For a numerically zero
vorticity RMS the V29.18 signature is defined to be zero.

## 1. Zero field

`vx = 0`, `vy = 0` ⇒ `omega = 0` everywhere ⇒ intensity `= 0` and, by the
zero-threshold rule, every structural component `= 0`. Exact at any resolution.

## 2. Solid-body rotation (`Omega`)

`vx = -Omega y`, `vy = Omega x`. Both components are linear, so the V29.18 finite
derivatives are exact:

```
omega = d(Omega x)/dx - d(-Omega y)/dy = Omega - (-Omega) = 2 Omega   (uniform)
```

* intensity (unit curvature weight) `= <(2 Omega)^2> = 4 Omega^2`;
* heterogeneity `= 0` (uniform `|omega|` has zero deviation);
* localization `= <omega^4>/<omega^2>^2 - 1 = 1 - 1 = 0`;
* roughness `= 0` (`grad omega = 0`);
* sign mixing `= 1 - |<omega>|/<|omega|> = 1 - 1 = 0` (single sign).

This field is **not periodic**, so it is an oracle for the `finite` mode only.

## 3. Uniform shear (`gamma`)

`vx = gamma y`, `vy = 0` ⇒ `omega = -gamma` (uniform, exact for linear input).
Intensity `= gamma^2`; heterogeneity, localization, roughness, sign mixing `= 0`.
`finite` mode oracle.

## 4. Taylor-Green vortex

`vx = U sin(kx) cos(ky)`, `vy = -U cos(kx) sin(ky)` on the periodic square of
period `2*pi/k`. Then

```
omega = 2 U k sin(kx) sin(ky).
```

**Exact oracles (any endpoint-excluded periodic grid with N >= 5).** The numeric
vorticity is a uniform scaling `s = sinc(kh)` of the analytic field, so scale
cancels in every ratio, and the discrete period averages `<sin^2> = 1/2`,
`<sin^4> = 3/8` are reproduced exactly:

* localization `= (3/8)^2 / (1/4)^2 - 1 = 9/4 - 1 = 5/4` (verified to 4e-16);
* sign mixing `= 1` because `<omega> = 0` exactly on the symmetric grid.

**Continuum oracles (second-order limit).** With `<sin^2> = 1/2` exactly:

* `<omega^2> = U^2 k^2`; the discrete value converges as `U^2 k^2 (kh)^2/3`;
* `<|omega|> = (8/pi^2) U k`, giving continuum heterogeneity

```
H_inf = (pi^2/8) sqrt(1 - 64/pi^4) ≈ 0.7225075.
```

The measured convergence orders for `<omega^2>` and `H` are both ~2.0 (see the
report).

## 5. Lamb-Oseen vortex

Azimuthal velocity `u_theta = (Gamma/(2 pi r))(1 - exp(-r^2/rc^2))` with the
regular core limit `u_theta/r -> Gamma/(2 pi rc^2)` as `r -> 0`. Analytic
vorticity

```
omega(r) = (Gamma/(pi rc^2)) exp(-r^2/rc^2),   peak omega(0) = Gamma/(pi rc^2).
```

No simple closed form is claimed for the ITD components. It is used as a
convergence oracle for the numeric vorticity (RMS error against the analytic
field converges at ~2.0) and for finite-domain truncation studies.

## 6. Identical consecutive fields

If `omega_i = omega_{i-1}` then `RMS(omega_i - omega_{i-1}) = 0`, so the raw
temporal deformation is exactly `0` and `D* = tau_ref * 0 = 0`.

## 7. Exact full-period translation

Translating a periodic field by an integer number of full spatial periods maps
each node to an identical sampled value; the field is unchanged, so the raw
Eulerian temporal deformation is exactly `0`. (Sub-period translation is a
non-zero Eulerian change that transport compensation is designed to remove; that
is a manufactured demonstration, not an exact oracle.)

## 8. Amplitude scaling

Multiplying `omega` by a constant `a`:

* `H`, `L`, `Q`, `M` are scale-invariant (the constant cancels in each ratio), so
  two amplitudes give identical values (delta `= 0`);
* intensity `= <omega^2>` scales as `a^2`, so the intensity ratio for amplitudes
  `A` and `B` is `(B/A)^2`.

## Reproducing the oracles

```bash
python -m pytest -q tests/test_analytical_oracles.py
```

The test reconstructs each field with `itd_research.analytical_cases`, computes
the quantity through the V29.18 core, and checks the recorded value within its
tolerance. It also asserts that this file contains only `hand_derived` sources.
