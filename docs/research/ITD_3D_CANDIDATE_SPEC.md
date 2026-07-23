# Experimental 3D ITD candidate specification

Status: **experimental research candidate**. This is not a certified scientific
revision and does not modify `ITD V29.18`. It lives in `itd_research/` and stays
experimental until validated on genuine 3D CFD or volumetric experimental data.

## Why the 2D signature does not generalise directly

The 2D signature uses the scalar out-of-plane vorticity `omega`. In 3D the
vorticity is a vector `omega = curl u`, so:

* replacing `omega` by the magnitude `|omega|` throws away all orientation
  information (a single tube and two antiparallel tubes can share the same
  `|omega|` distribution);
* the 2D **sign mixing** component `1 - |<omega>|/<|omega|>` has no scalar analogue
  because there is no single sign — it must be replaced by an **orientation**
  measure;
* genuinely 3D processes (vortex **stretching/tilting** and **helicity**) have no
  2D counterpart and are arguably more physically meaningful than forcing every
  2D component into a 3D magnitude analogue.

The candidate therefore reports a **vector with more than five channels**, keeping
magnitude-based analogues *and* explicit orientation, helicity, and stretching
channels, rather than collapsing them prematurely.

## Channels (single snapshot)

Let `omega(x)` be the vorticity vector field, `A = |omega|`, `S` the strain-rate
tensor, and `u` the velocity. All spatial means are boundary-consistent.

1. **Rotational intensity** `I3 = <A^2 * exp(lc^2 R)>` (curvature weight optional;
   with `R=0`, `I3 = <|omega|^2>`). Studied alongside whether orientation/helicity
   should be reported separately rather than folded into `I3`.
2. **Heterogeneity** `H3 = sqrt(<(A - <A>)^2>) / max(<A>, eps)` — spatial spread of
   vorticity magnitude. Zero for uniform `|omega|` (e.g. rigid rotation).
3. **Localization** `L3 = <A^4>/max(<A^2>^2, eps) - 1` — magnitude flatness minus
   one (relates to the vorticity-magnitude flatness `<A^4>/<A^2>^2`).
4. **Roughness** `Q3 = ell_s * <||grad omega||_F> / max(rms(A), eps)`, where
   `grad omega` is the 3x3 vorticity-gradient tensor `d omega_i / d x_j` and
   `||.||_F` is the Frobenius norm. The gradient choice (Frobenius of the full
   tensor) is stated explicitly and not hidden.
5. **Orientation dispersion** `O3 = clip(1 - ||<omega>|| / max(<A>, eps), 0, 1)` —
   the vector replacement for sign mixing. Zero when the vorticity points in one
   direction everywhere (single tube); near one when orientations cancel
   (antiparallel tubes, isotropic orientation).
6. **Mean helicity** `Hel = <u . omega>` and **normalized helicity**
   `<(u.omega)/(|u||omega|)>` over the region where both magnitudes exceed the
   threshold. A complementary, genuinely 3D channel with no 2D analogue.
7. **Vortex-stretching rate** `Str = <(omega^T S omega) / max(|omega|^2, eps)>` —
   the rate at which the strain field stretches vorticity along its own
   direction. For a Burgers vortex with axial strain `a`, `Str = a` exactly.

The raw vector `(I3, H3, L3, Q3, O3, Hel, Str, ...)` is always reported; no scalar
aggregation is defined yet, and none is treated as authoritative.

## Temporal channels (time-resolved data)

For time-resolved 3D data the temporal deformation is decomposed rather than
collapsed to one scalar: magnitude change, orientation change, advection,
stretching/tilting, and an unresolved residual. Because the certified V29.18
temporal deformation and the earlier post-V29 dimensional study established that
Eulerian change responds to translation, transport compensation is applied and
the residual is not called a material derivative unless the implementation
corresponds to one. These channels are exercised in the external-validation
experiments layer.

## Validation

Exact analytical checks (`tests/test_itd_3d.py`):

* rigid rotation about z: `H3 = L3 = Q3 = O3 = 0`, `Hel = 0`, `Str = 0`,
  `I3 = (2 Omega)^2`;
* Burgers vortex: `Str = a` (axial strain) to discretisation error (its mean
  helicity vanishes by z-symmetry on a symmetric box);
* ABC/Beltrami flow (`curl u = u`): normalized helicity `= 1` (a clean helicity
  oracle);
* single vortex tube vs antiparallel tubes: `O3` near 0 vs substantially larger;
* magnitude channels (`H3, L3, Q3, O3`) are amplitude invariant; `I3` scales as
  amplitude squared.

## Non-goals

No physical-observable, universality, or superiority claim is made. The candidate
is a structured set of channels for comparison against Q, swirling strength,
lambda_2, helicity, and stretching on genuine 3D data. Certification is deferred
per the decision gates in `EXTERNAL_CFD_PIV_3D_VALIDATION_SPEC.md`.
