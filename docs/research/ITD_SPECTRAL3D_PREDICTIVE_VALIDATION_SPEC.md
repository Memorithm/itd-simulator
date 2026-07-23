# ITD spectral-3D and predictive-validation phase specification

Status: **research specification** for the next post-V29 phase. This document does
**not** define a certified revision and does **not** modify `ITD V29.18`. All new
work lives under `itd_research/` (new subpackages `spectral3d/`, `validation_lab/`,
`prediction/`, `realtime/`, `industrial/`, `dataset_discovery/`). Dependency
direction stays one-way: research modules may import `itd_v29_core`; the core never
imports research. Nothing here becomes `V29.19`/`V30` or a certified release.

## 0. Honesty rules (binding)

The following product statements are **hypotheses, not assumptions**, and are
reframed as falsifiable questions. None may be "proved" by dataset selection:

| Claim (rejected as an assumption) | Falsifiable question |
|---|---|
| ITD predicts failures | For which physically-defined transitions does ITD give earlier/more reliable warning than intensity-only baselines? |
| ITD is superior in every flow | Under which flow families/tasks/resolutions/noise is ITD statistically superior or complementary? |
| ITD components are universal | Which components preserve their interpretation across flows/resolutions/Re? |
| One universal ITD threshold exists | Does any threshold (raw/nondimensional/calibrated) transfer across a restricted flow class? |
| ITD channels are independent | Which channels carry non-redundant (linear or nonlinear/predictive) information? |
| The ITD-3D candidate is optimal | Does a reduced/modified candidate improve the accuracy–robustness–cost Pareto front? |
| Results generalize to every DNS | Do findings reproduce across independent DNS sources/boxes/times/resolutions? |
| PIV strongly validates every vortex region | On suitable vortical PIV, do ITD regions agree reproducibly with *independent* evidence? |
| ITD is real-time for all workloads | Which declared workload classes meet explicit latency/memory budgets? |
| ITD is industrially certifiable | Which pre-industrial readiness gates are met, short of formal certification? |

Every hypothesis result is classified as exactly one of:
`supported within tested scope` · `partially supported` · `not supported` ·
`inconclusive` · `blocked by unavailable evidence`. Negative and inconclusive
findings are valid outputs and are not to be optimised away.

## 1. Scientific scope

In scope this phase: incompressible, single-phase, Newtonian, periodic-box 3D flow;
2D flows already covered; analytical/manufactured oracles; local-solver DNS at
feasible resolution (16^3 … 64^3, larger only if the environment permits); external
DNS/PIV that are genuinely reusable. **Out of scope** (registered, never claimed as
supported until equations/units are reviewed): compressible, reacting, multiphase,
MHD, stratified, rotating-frame, geophysical, plasma flows.

## 2. Solver — governing equations

Incompressible 3D Navier-Stokes in a periodic box, velocity-pressure projection
form in Fourier space (authoritative):

    du/dt = -(u.grad)u - grad p + nu*laplacian(u) + f,   div u = 0.

Pressure is eliminated by the Leray/Helmholtz projection; the vorticity form is
only added if independently cross-checked against the velocity form.

## 3. Numerical method

3D periodic Cartesian grid; NumPy real FFT (`rfftn`/`irfftn`) reference backend;
spectral derivatives; Fourier-space incompressible projection; 2/3-rule dealiasing;
explicit viscosity; configurable deterministic forcing; classical RK4 (reference)
with CFL and divergence monitoring; deterministic checkpoint/restart. No integrator
more complex than RK4 is used before RK4 is validated.

### 3.1 Fourier conventions (authoritative, tested)

* Transform: NumPy `rfftn` over axes (0,1,2) = (x,y,z); `irfftn` back. NumPy's
  default `norm=None` (forward unnormalised, inverse divides by N) is used.
* Wavenumbers: `kx,ky = 2*pi*fftfreq(N, L/N)`; `kz = 2*pi*rfftfreq(N, L/N)`.
* Zero mode `k=0`: mean velocity is preserved by the equations; the projection and
  inverse-Laplacian set the `k=0` pressure/streamfunction contribution to zero.
* Nyquist: the Nyquist column of even-N rfft is real; derivative operators zero it
  to keep real-field reconstruction exact (documented, tested).
* Dealias mask: keep modes with `|kx|,|ky|,|kz| < (2/3) k_max` (2/3 rule).
* Derivative sign: `d/dx <-> i*kx`. A dedicated test detects a sign flip in each of
  x, y, z independently.

### 3.2 Projection

For `k != 0`: `u_perp_hat = u_hat - k (k.u_hat)/|k|^2`; `k=0` handled explicitly
(unchanged). Tested for: divergence to round-off; idempotence; solenoidal fields
unchanged; pure-gradient fields removed; no spurious energy gain.

### 3.3 Nonlinear term

Authoritative form: **rotational** `(u x omega)` plus the gradient of `|u|^2/2`
absorbed into pressure (removed by projection), 2/3-dealiased. Chosen for its good
discrete conservation; the advective form is provided only behind a tested
equivalence check, never as a silent alternative.

## 4. Datasets — selection rules

A dataset is usable only with: complete provenance (source, authors, DOI, licence,
redistribution rights, units, uncertainty), full velocity field(s), and no
authentication that CI would need. Categories: `integrated`, `integration-ready`,
`metadata-only`, `blocked by {licence,authentication,size,missing velocity field}`,
`rejected as scientifically unsuitable`. CI never touches the network; large raw
data is never committed; only small legally-redistributable excerpts + checksums +
fetch scripts.

## 5. Prediction targets

"Failure" is used only where a real labelled engineering event exists; fluid
transitions are called transitions, not failures. Event times are defined by an
**ITD-independent** criterion (e.g. rotation-component-count change, circulation
collapse, enstrophy-production threshold, published core coordinates). Protocol:
define event + horizon; chronological train/test split; no temporal/spatial/future
leakage; compare ITD against persistence, enstrophy, Q/lambda_2/swirl summaries,
vorticity RMS, and ITD+diagnostics; simple transparent models first (threshold,
logistic regression, LDA, small tree, change-point); event-level metrics
(ROC-AUC, PR-AUC, balanced accuracy, F1, false-alarm/missed-event rate, lead time,
Brier, calibration, CIs). Frame-level accuracy alone is never reported for rare
events.

## 6. Comparison metrics

Region overlap (Jaccard/Dice, uncertainty-aware where feasible); rank/linear
correlation; connected-component vortex counts; ranking tables and Pareto fronts
across accuracy, robustness, cross-resolution stability, cost, interpretability,
calibration, generalization. "Superior" is defined per-criterion; criteria are not
collapsed into a single winner.

## 7. Statistical methods (channel dependence)

Pearson, Spearman, partial correlation, covariance, variance-inflation factors,
condition number, PCA; mutual information with estimator-sensitivity notes; distance
correlation where feasible; redundancy clustering. Computed globally and per
flow-family/regime/Re/resolution/phase. Linear independence, nonlinear dependence,
physical non-redundancy, and predictive complementarity are distinguished. A
channel is not removed on high global Pearson alone.

## 8. Real-time targets

Workload classes with explicit budgets (indicative, hardware-declared in the report):

| class | size | budget (declared, measured p50/p95/p99) |
|---|---|---|
| RT-2D-S | 128^2 | interactive (<~5 ms/frame goal) |
| RT-2D-M | 512^2 | <~50 ms |
| RT-2D-L | 2048^2 | batch/near-real-time |
| RT-3D-S | 32^3 | <~50 ms |
| RT-3D-M | 64^3 | <~500 ms |
| RT-3D-L | 128^3 | offline/batch |

"Real-time" is only claimed against a declared deadline with p95/p99 measured, not
mean latency. Budgets are hypotheses to be tested, not guarantees.

## 9. Industrial-readiness gates

Maturity is reported on an IRL-0..9 scale (see `docs/industrial/INDUSTRIAL_READINESS_MODEL.md`),
never as legal certification. Scientific validation alone does not satisfy ISO 9001,
ISO 26262, DO-178C, IEC 61508, IEC 62304, ISO/IEC 17025, or sector standards; a gap
analysis is produced instead of a certification claim.

## 10. Decision gates

* **Gate A (solver):** derivative oracles pass; divergence controlled; projection
  correct; viscous decay correct; RK4 restart deterministic; Taylor-Green plausible
  and resolution-qualified; vorticity-budget closure quantified.
* **Gate B (prediction):** ITD-independent labels; no leakage; held-out events; ITD
  beats >=1 meaningful baseline; CIs reported; acceptable false alarms.
* **Gate C (generalization):** external held-out; cross-flow/source explicit;
  negative transfer documented; dataset identity never hidden.
* **Gate D (PIV):** genuinely vortical data; masks/uncertainty preserved; agreement
  vs independent evidence; preprocessing sensitivity reported.
* **Gate E (real-time):** explicit deadlines; p95/p99 measured; bounded memory;
  streaming failures handled; results match the CPU reference.
* **Gate F (industrial):** reported as a maturity level only.

No new certified revision is proposed automatically by any gate.

## 11. Hypotheses H7–H16

H7 predictive transitions; H8 conditional superiority; H9 component transferability;
H10 threshold transfer; H11 channel complementarity; H12 candidate optimisation;
H13 DNS generalization; H14 PIV vortex agreement; H15 real-time feasibility;
H16 industrial maturity. Each has a predefined scope, experiment, target, baseline,
acceptance/rejection criterion, evidence class, and limitations, recorded in the
per-topic reports and summarised in the final report.

## 12. Known limitations (declared up front)

No OpenFOAM-class external solver or GPU in the authoritative path; local DNS limited
to modest resolution (turbulence at 32^3–64^3 is under-resolved and labelled so);
open strongly-vortical experimental PIV is scarce; statistics are small-sample; the
environment is single-node CPU. These bound every claim below.
