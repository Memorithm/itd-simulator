# Post-V29 dimensional-validation report

Status: **research report** supporting a post-V29 research candidate. It does not
certify a new scientific revision. The certified baseline remains `ITD V29.18`
and its numerical behaviour is unchanged.

## 1. Repository and commit identification

* Baseline commit (untouched V29.18): `098240c1e9a95c128d58acc4e42eea642a875816`
* Scientific baseline: `ITD V29.18` (`MODEL_REVISION` unchanged)
* Software version: `0.2.0` (unchanged)
* Research namespace: `itd_research/` (new, isolated)
* Local validation interpreter: CPython 3.11.15, NumPy 2.3.5
* Reference environment (per `docs/reproducibility.md`): CPython 3.12, NumPy
  2.5.1

## 2. Baseline validation evidence

Before any change, the untouched baseline was installed from
`requirements-dev.lock` and validated:

* `ruff check .` — all checks passed;
* `pytest -q` — 56 passed;
* `./run_validation.sh` — `ITD V29.18 validation: PASSED` (185 tracked files);
* `git status --porcelain` — clean before and after validation;
* SHA-256 of the tracked V29.18 summary
  (`itd_v29_results/summary.csv`):
  `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b`.

The V29.18 core, its reference summary, the reviewed Rust fixture, and the
existing certification reports were not modified. All new work lives under
`itd_research/`, `docs/research/`, and new `tests/`.

## 3. Scientific question

Can the temporal deformation be nondimensionalized using an explicit,
physically interpretable characteristic time `tau_ref`, forming
`D* = tau_ref * D`, while preserving the raw rate and avoiding a hidden default?
See `POST_V29_DIMENSIONAL_VALIDATION_SPEC.md`.

## 4. Dimensional analysis

With velocity `[L/T]` and coordinates `[L]`: vorticity is `[T^-1]`; the raw
temporal deformation `D = RMS(Δomega)/(Δt · endpoint_RMS)` is `[T^-1]` because
the ratio of RMS quantities is dimensionless and the explicit `1/Δt` introduces
inverse time. The four spatial components are dimensionless. Consequently a
scalar aggregation mixing `b(D)` with dimensionless components is unit dependent.
Multiplying `tau_ref` (dimension `T`) gives `D* = tau_ref · D`, dimensionless.

## 5. Candidate characteristic-time policies

Four explicit policies were implemented and analysed (dimensions, inputs,
interpretation, invariance, failure modes, near-zero behaviour, scope,
cross-simulation comparability, circular dependence) in the specification:
`external`, `observation_duration`, `turnover`, `vorticity_timescale`. The
vorticity-timescale policy is flagged self-referential (and warned) when
`omega_ref` is taken from the field under study. No universal default was
selected.

## 6. Analytical benchmark definitions

The catalogue (`itd_research/analytical_cases.py`,
`itd_research/benchmark_runner.py`) contains: zero field; solid-body rotation;
uniform shear; Taylor-Green (periodic); Lamb-Oseen (regular core limit);
counter-rotating pair; amplitude-scaled pair; structure-changed pair;
translated periodic vortex. The quick and full suites both report **33/33**
analytical checks passing.

## 7. Analytical derivations

Full hand derivations are in `ANALYTICAL_ORACLES.md`. Highlights verified
against the implementation:

* solid-body rotation: `omega = 2 Omega` exact; `H=L=Q=M=0`; intensity `4Omega^2`;
* uniform shear: `omega = -gamma` exact; structural components `0`;
* Taylor-Green: localization `= 5/4` reproduced to `4.4e-16`; sign mixing `= 1`
  exactly; continuum enstrophy `U^2 k^2` and heterogeneity
  `(pi^2/8) sqrt(1-64/pi^4) ≈ 0.7225075`;
* amplitude scaling: `H,L,Q,M` invariant; intensity ratio `= (B/A)^2`;
* identical/full-period-translation: raw temporal deformation exactly `0`.

## 8. Convergence results

Grid refinement (`itd_research/convergence.py`), observed orders
`p = log(e_coarse/e_fine)/log(h_coarse/h_fine)`:

| Study | N sequence | finest error | observed order (finest pair) |
|---|---|---|---|
| Taylor-Green enstrophy `<omega^2>` | 16,32,64,128 | 8.03e-4 | 1.999 |
| Taylor-Green heterogeneity | 16,32,64,128 | 8.46e-4 | 2.000 |
| Lamb-Oseen vorticity RMS error | 17,33,65,129 | 8.47e-4 | 1.990 |

All three converge at second order, consistent with the V29.18 centred/edge
operators. Orders are **not** reported where the reference is zero, the error is
at roundoff level, or the error is non-decreasing (guarded in `observed_order`).
Localization and sign mixing for Taylor-Green are exact identities and are
therefore excluded from order estimation.

## 9. Sensitivity results

From `itd_research/sensitivity.py` (full run):

* **Time-unit conversion (seconds vs milliseconds, c=1000).** Raw-rate scaling
  residual `= 0.0`; maximum dimensionless residual across all four policies
  `= 0.0` (machine precision). `D*` is invariant under consistent conversion.
* **Structural length.** `raw_roughness / ell_s` is constant: slope spread
  `= 0.0` (exact linear law). The bounded map `b(Q)=Q/(1+Q)` makes the scalar
  contribution nonlinear in `ell_s`.
* **Curvature length.** Intensity grows with `exp(ell_c^2 R)`; amplification
  ratio `≈ 2.23` from `ell_c=0` to `ell_c=2` on the test curvature. The weight is
  rejected if it overflows the finite range.
* **Spatial/temporal resolution.** Components converge with resolution; the raw
  temporal rate is a finite-difference approximation of the instantaneous rate
  (limit estimate `≈ 0.4000` for the uniformly translated pattern).
* **Boundary mode.** The same periodic sample under the finite operators differs
  from the periodic operators by up to `0.068` — a convention sensitivity, not a
  physical change.
* **Noise (seeded, amplitudes up to 10%).** Maximum component deltas:
  heterogeneity `1.20`, localization `1.09`, roughness `0.44`, sign mixing
  `0.25`. This is a synthetic robustness probe, not empirical validation.
* **Scalar weights.** Rankings change with weights: an equal-weight ordering
  `[counter-rotating, Taylor-Green, Lamb-Oseen]` becomes
  `[counter-rotating, Lamb-Oseen, Taylor-Green]` under a localization-heavy
  weighting. The scalar score is preference-dependent.

## 10. Comparison with established diagnostics

`itd_research/established_diagnostics.py` computes kinetic energy density,
enstrophy, palinstrophy, domain circulation, vorticity RMS/absolute-mean,
vorticity flatness/excess kurtosis, and mean gradient norm, all with the V29.18
operators. Relationships:

* ITD localization `= flatness - 1 = excess_kurtosis + 2` (cross-checked
  numerically);
* for a curvature weight of 1, ITD intensity `= <omega^2>` and enstrophy
  `= <omega^2>/2`, so intensity `= 2 × enstrophy`; on solid-body rotation
  intensity `= 4 Omega^2` and enstrophy `= 2 Omega^2`. They differ only by the
  constant factor `1/2`, so for single-scale fields they carry equivalent
  information;
* roughness relates to the mean gradient norm normalized by vorticity RMS.

Where a single vorticity magnitude scale is all that matters, intensity and
enstrophy are redundant (proportional). The structural vector adds information
exactly when fields differ in shape at equal magnitude (next section).

## 11. Unit-invariance results

The raw temporal rate transforms as `1/c` between second and millisecond units
(scaling residual `0.0`). Each of the four dimensionless candidates
(`external`, `observation_duration`, `turnover`, `vorticity_timescale`) is
invariant to machine precision (residual `0.0`) when every time quantity is
converted consistently. This is the central positive result: an explicit
characteristic time removes the unit dependence of the temporal component.

## 12. Cases where the structural vector adds information

The structure-changed pair uses a localized single-sign Lamb-Oseen vortex and a
rescaled sign-balanced Taylor-Green field set to the **same intensity**
(`0.15884`). Their raw vectors `(H, L, Q, M)` are:

| Field | intensity | H | L | Q | M |
|---|---|---|---|---|---|
| Lamb-Oseen (A) | 0.15884 | 3.03 | 19.33 | 0.55 | 0.0001 |
| Taylor-Green (B) | 0.15884 | 0.79 | 1.62 | 1.53 | 1.0000 |

A single intensity value cannot distinguish these fields; the five-component
vector separates them decisively (sign mixing `0.0001` vs `1.0`, localization
`19.3` vs `1.6`). The counter-rotating pair likewise has sign mixing `≈ 1` and
near-zero net circulation, unlike a single vortex with the same magnitude.

## 13. Cases where scalar aggregation hides information

* The scalar score `S` collapses the vector; the weight study shows its ranking
  of cases is weight-dependent, so different weightings hide different structure.
* The bounded map saturates: two very different raw roughness values map to
  nearby `b(Q)`, so large structural differences can be compressed in `S`.
* Because raw `D` is inverse-time, any `S` that includes `b(D)` is unit
  dependent (Section 4) — the scalar hides a unit convention.

## 14. Limitations

* No empirical or CFD validation is performed; all fields are synthetic.
* Lamb-Oseen ITD components have no claimed closed form; only convergence and
  truncation behaviour are studied.
* The dimensionless candidate `D*` is defined and shown unit-invariant, but its
  physical interpretation depends entirely on the declared `tau_ref`.
* Boundary-mode comparisons quantify convention sensitivity, not physics.
* Synthetic seeded noise is a robustness probe, not experimental noise.
* Determinism is claimed for repeated runs in one locked environment; last-bit
  cross-environment differences are possible.

## 15. Unresolved scientific questions

* Which characteristic-time policy (if any) is defensible as a default, and for
  which restricted class of flows?
* How should a field-derived (self-referential) vorticity timescale be treated
  when no external reference exists?
* Should the raw temporal rate be reported strictly separately from any scalar
  score in the certified model?
* What experimental or CFD datasets could move `D*` from "numerical experiment"
  to "empirically supported"?

## 16. Recommendation

Evidence-based conclusion:

1. **No new certified scientific revision is justified yet.** The dimensionless
   reformulation is promising and unit-invariant, but it remains an experimental
   candidate without empirical validation.
2. **The raw temporal deformation should remain separate from the default scalar
   score.** The unit dependence of any `b(D)`-containing scalar is a real
   interpretation hazard; the raw inverse-time rate is legitimate and should be
   reported on its own axis.
3. **If a dimensionless temporal component is adopted later, the characteristic
   time must be explicit and recorded**, never a hidden default. The
   `observation_duration` and `turnover` policies are the most defensible for
   time-resolved records and flows with a declared turnover time, respectively;
   the vorticity timescale is acceptable only with an externally declared
   `omega_ref`.
4. **The five-component vector must stay the primary reported structural
   result.** The scalar score is preference-dependent and lossy.

Further empirical validation against CFD or experimental data is required before
any of these candidates could be considered for certification.
