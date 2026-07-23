# Experimental 3D ITD candidate report

Status: **experimental research candidate**. Not a certified revision and not
`V29.19`/`V30`; does not modify `ITD V29.18`. Specified in
`ITD_3D_CANDIDATE_SPEC.md`; this report records its validation against exact 3D
analytical oracles and states what remains before it could be considered.

## 1. Why the 2D signature does not simply extend

In 3D the vorticity is a vector `omega = curl u`, not a scalar. Replacing scalar
`omega` by `|omega|` discards orientation, and the 2D **sign-mixing** component
has no scalar analogue — there is no single sign. Genuinely 3D processes
(vortex stretching/tilting, helicity) have no 2D counterpart. The candidate
therefore reports a **vector with more than five channels**: magnitude-based
intensity/heterogeneity/localization/roughness, an **orientation-dispersion**
replacement for sign-mixing, and complementary **helicity** and
**vortex-stretching** channels.

## 2. Analytical oracle validation (`tests/test_itd_3d.py`)

Every channel is checked against a field with a known exact answer. Observed
values (second-order operators; agreement to discretisation error):

| Oracle | Channel | Expected | Observed |
|---|---|---|--:|
| Rigid rotation (Ω=1.3) | intensity `I3 = (2Ω)^2` | 6.76 | 6.7600 |
| Rigid rotation | heterogeneity, orientation dispersion, helicity, stretching | 0 | ≤ 4e-16 |
| Burgers vortex (axial strain a=0.6) | stretching rate `= a` | 0.6 | 0.60000 |
| ABC / Beltrami flow (`curl u = u`) | normalized helicity | 1 | 1.000000 |
| Single vortex tube | orientation dispersion | ≈ 0 | 0.0091 |
| Antiparallel tubes | orientation dispersion | ≫ single | > 0.5 |
| Taylor-Green (amplitude scaled ×7) | magnitude channels invariant; `I3 ∝ A^2` | — | exact to 1e-10 |

The stretching channel recovering the Burgers axial strain **exactly** and the
normalized helicity equal to **1** for a Beltrami flow are clean, independent
oracles: the genuinely 3D channels compute the intended physics, not a re-labelled
2D quantity.

## 3. Relationship to established 3D diagnostics

The candidate is compared against — never asserted superior to — Q-criterion,
swirling strength (with swirl axis), and lambda_2 (Jeong-Hussain), all computed
from the same 3D velocity-gradient tensor and validated on the same analytical
fields (`tests/test_diagnostics_3d.py`). Helicity and stretching are
complementary channels those criteria do not provide.

## 4. Genuine external 3D DNS (JHTDB isotropic turbulence)

A `32^3` block of native grid nodes was retrieved from the JHU Turbulence
Database forced-isotropic-turbulence DNS (`isotropic1024coarse`, `GetVelocity`
point query, public testing token) with `tools/datasets/fetch_jhtdb_cutout.py`.
This is genuine independent 3D CFD data (component rms 0.5524; provenance and
checksum in `datasets/registry.json`, entry `jhtdb_isotropic1024`). The raw DNS
is not committed, per JHTDB terms; reproduce it with the fetch tool.

Observed on the DNS field:

| Channel / diagnostic | Value | Physical expectation | Verdict |
|---|--:|---|---|
| ITD orientation dispersion | 0.880 | near 1 (near-isotropic vorticity orientation) | as expected |
| ITD normalized helicity | −0.044 | ≈ 0 (no preferred handedness) | as expected |
| **ITD vortex-stretching rate** | **+2.88** | **> 0 (net stretching drives the cascade)** | **as expected** |
| ITD localization | 14.2 | large (intermittent vorticity) | as expected |
| Q>0 fraction | 0.281 | ~1/4–1/3 rotation-dominated | as expected |
| lambda_2<0 fraction | 0.266 | close to Q>0 fraction | as expected |
| Jaccard(Q>0, lambda_2<0) | 0.872 | high (both detect rotation) | as expected |
| corr(\|omega\|, swirling strength) | 0.890 | high but < 1 | as expected |

The three genuinely 3D channels behave correctly on real turbulence and none has
a 2D analogue: orientation dispersion recovers the near-isotropic orientation
(the vector replacement for sign-mixing works on real data), normalized helicity
recovers the vanishing mean helicity, and the **positive** mean vortex-stretching
rate recovers the cascade mechanism. That the two independent rotation criteria
(Q and lambda_2) agree at Jaccard 0.87 also validates the established-diagnostic
implementations on real data.

### 4.1 Ensemble across six independent DNS regions

To distinguish a robust property from a single-box coincidence, six `24^3`
cutouts were taken at different origins across the domain (component rms 0.46 to
0.87 — genuine spatial variation). Summary (`aggregate_3d_channels`):

| Channel | mean ± std | range | note |
|---|--:|--:|---|
| vortex-stretching rate | +2.33 ± 0.91 | [+1.14, +3.48] | **positive in 6/6 boxes** (cascade) |
| Jaccard(Q>0, lambda_2<0) | 0.892 ± 0.009 | [0.876, 0.905] | criteria agree, very stable |
| normalized helicity | +0.027 ± 0.130 | [−0.11, +0.26] | scattered about 0 (no net handedness) |
| rotation fraction (Q>0) | 0.376 ± 0.058 | [0.29, 0.44] | consistent |
| orientation dispersion | 0.657 ± 0.168 | [0.39, 0.90] | high; smaller boxes cancel less, so lower/more variable than the `32^3` box (0.88) |

The **positive mean vortex-stretching rate in every box** and the **helicity
scattered symmetrically about zero** are the robust, physically expected
signatures of forced isotropic turbulence. Orientation dispersion is
domain-size sensitive (a smaller box has less orientation cancellation), stated
rather than hidden.

### 4.2 Time-resolved transport versus deformation (real DNS)

The same box was queried at consecutive DNS times (`dt = 0.002`). The 3D
transport decomposition of the vorticity magnitude separates transport from
material change:

| Quantity | Value |
|---|--:|
| rms Eulerian change d\|omega\|/dt | 966 |
| rms advective term u.grad\|omega\| | 803 |
| rms residual (material change) | 506 |
| residual / Eulerian | 0.524 |

Transport compensation removes ~48 % of the raw Eulerian change; the large
remaining residual is **genuine deformation** (in 3D, vorticity magnitude is not
materially conserved — vortex stretching changes it). This is the honest contrast
with the synthetic pure-translation test (residual fraction 0.033, ~97 % removed):
a rigidly translated pattern is almost all transport, whereas real turbulence
carries substantial genuine deformation. The residual connects directly to the
positive stretching-rate channel above.

## 5. Status and what remains

* **Code verification:** complete on exact 3D analytical inputs.
* **Numerical validation:** magnitude channels amplitude-invariant; nonlinear
  fields (Burgers, Taylor-Green) recovered to discretisation error.
* **External validation:** the candidate was run on genuine external 3D DNS —
  a `32^3` cutout (§4), a six-region ensemble (§4.1), and a time-resolved series
  (§4.2) — and its genuinely-3D channels are physically correct and robust across
  regions. This **supports** hypothesis H6 — that a meaningful 3D extension
  requires orientation/stretching/helicity channels. Remaining: other DNS
  datasets (channel, transitional boundary layer) and, ideally, a *volumetric
  experimental* (tomographic PIV) field; and independent review. The ensemble is
  small (six `24^3` boxes from one dataset), so it is early statistical evidence,
  not a full campaign.

## 6. Decision

The 3D candidate **remains experimental**. No scalar aggregation of the channel
vector is defined or treated as authoritative. Certification is deferred per the
decision gates in `EXTERNAL_CFD_PIV_3D_VALIDATION_SPEC.md` §8 until the candidate
is validated across genuine 3D CFD (multiple regions/datasets) and, ideally,
volumetric experimental data, and independently reviewed.
