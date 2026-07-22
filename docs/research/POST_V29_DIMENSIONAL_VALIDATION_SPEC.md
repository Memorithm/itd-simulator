# Post-V29 dimensional-validation research specification

Status: **research specification** for a post-V29 research candidate. This
document does not define a certified scientific revision and does not modify
`ITD V29.18`. The certified baseline remains `ITD V29.18`.

## 1. Motivation and the dimensional problem

The V29.18 structural signature has five components. Four of them are
dimensionless when the structural length shares the coordinate length unit:

* heterogeneity `H` — a ratio of vorticity-magnitude spread to its mean;
* localization `L = <omega^4>/<omega^2>^2 - 1` — a ratio of moments;
* roughness `Q = ell_s <|grad omega|>/omega_rms` — dimensionless if `[ell_s]=L`;
* sign mixing `M` — a ratio of signed to absolute mean vorticity.

The fifth component, Eulerian temporal deformation, is defined on an interval
`[t_{i-1}, t_i]` as

```
D = RMS(omega_i - omega_{i-1}) / (delta_t * mean_endpoint_vorticity_RMS)
```

Both `RMS(omega_i - omega_{i-1})` and `mean_endpoint_vorticity_RMS` have the
dimension of vorticity (`T^-1`). Their ratio is therefore dimensionless, but the
explicit division by `delta_t` gives `D` the dimension of **inverse time**
(`T^-1`).

### 1.1 Consequence for the scalar aggregation

The experimental scalar score aggregates bounded versions of all five
components:

```
S = w_H b(H) + w_L b(L) + w_Q b(Q) + w_M M + w_D b(D),   b(x) = x/(1+x)
```

Because `b` is applied to `D` in its raw inverse-time units, `S` depends on the
chosen time unit. Expressing the identical physical evolution in seconds versus
milliseconds multiplies `delta_t` by 1000, divides `D` by 1000, and therefore
changes `b(D)` and hence `S`. The empirical demonstration is in the sensitivity
study (`time_unit_conversion`): the raw rate transforms exactly as `1/c`.

This **does not invalidate the raw temporal rate**, which is a legitimate
inverse-time quantity. It limits the interpretation of any *scalar aggregation*
that mixes the raw inverse-time rate with dimensionless components.

## 2. Research question

> Can the temporal deformation be nondimensionalized using an explicit,
> physically interpretable characteristic time `tau_ref`, forming
> `D* = tau_ref * D`, while (a) preserving the raw rate, (b) avoiding any hidden
> arbitrary default, and (c) remaining invariant under consistent unit changes?

We deliberately **do not** select a single universal characteristic time. We
study a small set of explicit policies and record their properties.

## 3. Candidate characteristic-time policies

All policies produce `tau_ref` with dimension `T`, so `D* = tau_ref * D` is
dimensionless. Each is validated to reject zero, negative, NaN, and infinite
values, and each records the reference quantities that entered `tau_ref`.

### 3.1 Externally supplied characteristic time (`external`)

`tau_ref` is provided directly by the caller.

| Property | Value |
|---|---|
| Dimensions | `[tau_ref] = T` |
| Required inputs | one declared characteristic time |
| Physical interpretation | whatever the caller declares (record it) |
| Invariance | invariant if supplied consistently in the chosen unit |
| Failure modes | undocumented or unit-inconsistent choice |
| Behaviour near zero | rejected (`tau_ref > 0` required) |
| Scope | caller-defined (local/global/interval/experiment) |
| Cross-simulation comparison | only if the same declared value is reused |
| Circular dependence | none if independent of the field |

### 3.2 Observation-duration scaling (`observation_duration`)

`tau_ref = t_final - t_initial`.

| Property | Value |
|---|---|
| Dimensions | `T` |
| Required inputs | the observed time window endpoints |
| Physical interpretation | fraction of the record over which the field changed |
| Invariance | invariant under consistent time-unit change |
| Failure modes | meaningless for a single instant; window-length dependent |
| Behaviour near zero | rejected (requires a positive window) |
| Scope | interval/experiment-based (global in time) |
| Cross-simulation comparison | only across records of comparable duration |
| Circular dependence | none |

### 3.3 Turnover-time scaling (`turnover`)

`tau_ref = L_ref / U_ref` for declared reference length and velocity.

| Property | Value |
|---|---|
| Dimensions | `L / (L/T) = T` |
| Required inputs | reference length `L_ref`, reference velocity `U_ref` |
| Physical interpretation | eddy turnover time; the natural flow timescale |
| Invariance | invariant under consistent unit change (`U_ref ∝ 1/c`) |
| Failure modes | requires a meaningful `L_ref`, `U_ref`; ambiguous in multiscale flows |
| Behaviour near zero | rejected (`U_ref > 0`, `L_ref > 0`) |
| Scope | experiment/flow-based |
| Cross-simulation comparison | comparable across flows sharing a turnover definition |
| Circular dependence | none if `L_ref`, `U_ref` are declared independently |

### 3.4 Vorticity-timescale scaling (`vorticity_timescale`)

`tau_ref = 1 / omega_ref` for a declared reference vorticity.

| Property | Value |
|---|---|
| Dimensions | `1 / T^-1 = T` |
| Required inputs | a declared reference vorticity `omega_ref` |
| Physical interpretation | rotation timescale of the reference vorticity |
| Invariance | invariant under consistent unit change (`omega_ref ∝ 1/c`) |
| Failure modes | **circular** if `omega_ref` is taken from the same field |
| Behaviour near zero | rejected (`omega_ref > 0`) |
| Scope | field/flow-based |
| Cross-simulation comparison | comparable only with a shared `omega_ref` definition |
| Circular dependence | present when `omega_ref` is derived from the field under study |

The API marks a definition `self_referential=True` when `omega_ref` comes from
the field itself; the result then carries an explicit circular-dependence
warning. A field-derived vorticity timescale makes `D*` equal to a vorticity-RMS
normalization of the rate, which is dimensionless but couples the timescale to
the field's own magnitude.

## 4. What this specification commits to

* preserve the V29.18 raw temporal rate exactly and never replace it silently;
* require an explicit characteristic time — no implicit default;
* reject non-finite / non-positive characteristic times;
* record every reference quantity and the declared time-unit convention;
* keep the research code isolated from `itd_v29_core` (one-way dependency);
* demonstrate unit invariance of `D*` under consistent conversion;
* refrain from declaring a winning policy until the evidence justifies it.

## 5. Non-goals

This work does not claim that `D*` or ITD is a universal physical observable, an
entropy, an information measure, a turbulence metric, or an experimentally
validated quantity. It is a numerical-analysis study of a dimensionless
reformulation and its properties.
