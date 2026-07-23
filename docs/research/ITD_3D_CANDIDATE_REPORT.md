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

## 4. Status and what remains

* **Code verification:** complete on exact 3D analytical inputs.
* **Numerical validation:** magnitude channels amplitude-invariant; nonlinear
  fields (Burgers, Taylor-Green) recovered to discretisation error.
* **External validation:** **not done.** No genuine 3D CFD or volumetric
  experimental dataset was processed (the environment has no solver and no
  volumetric PIV/tomographic data; the one external field available here is 2D
  PIV). Hypothesis H6 — that a meaningful 3D extension requires
  orientation/stretching/helicity channels — is **supported analytically** by the
  oracles above but awaits confirmation on real 3D data.

## 5. Decision

The 3D candidate **remains experimental**. No scalar aggregation of the channel
vector is defined or treated as authoritative. Certification is deferred per the
decision gates in `EXTERNAL_CFD_PIV_3D_VALIDATION_SPEC.md` §8 until the candidate
is validated on genuine 3D CFD or volumetric experimental data and independently
reviewed.
