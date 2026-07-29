# Compressibility decision note — admitting (or rejecting) a compressible external source

Status: **decision note**. Not a preregistration, not a hypothesis verdict, and **does not
commit to a Mission 9**. Not a certified revision; does not modify `ITD V29.18`. No data
has been fetched, ingested or evaluated.

Purpose: settle *in advance* how a compressible external source would be admitted, so that
if a cross-institution mission is ever launched the rule already exists and cannot be
chosen after seeing results.

Context: `EXTERNAL_SOURCE_PROSPECTS.md` identified The Well (Flatiron Institute, CC-BY-4.0)
as the first credible cross-institution candidate found across Missions 3–8, and flagged
compressibility as the blocker to resolve *before* any evaluation.

## Why compressibility is a problem for this pipeline

The velocity-gradient tensor `∇u` has characteristic equation `λ³ + Pλ² + Qλ + R = 0` with
`P = −∇·u`. Under incompressibility `P = 0` and the second invariant reduces to the
familiar form used throughout this repository:

```
Q = ½(‖Ω‖² − ‖S‖²)
```

For compressible flow `P ≠ 0`, so that expression is no longer the second invariant. λ₂ is
more fragile still: it derives from the pressure Hessian assuming incompressibility *and*
neglecting unsteady/viscous terms; compressible flow adds dilatational and baroclinic
contributions.

Both diagnostics remain *computable* — and `Q > 0` still expresses "rotation dominates
strain" locally — but their standard interpretation, and the link to a pressure minimum,
no longer hold as derived.

### The more dangerous failure mode: shocks

The algebra above is the lesser problem. The serious one is that **supersonic flow contains
shocks**, and shock surfaces carry enormous velocity gradients that are **not vortices**.

The Mission 8 event definition is a persistent change in the count of connected `Q > 0`
components. On shock-dominated data, that count would be driven by shock dynamics rather
than by vortex merger/split — silently corrupting the ITD-independent event label, which is
the single element this project has protected most carefully. Nothing downstream would
signal the corruption; the pipeline would produce confident, meaningless numbers.

## The decision

Do **not** attempt to settle "is Q valid for compressible flow?" in the abstract. Convert it
into an empirical gate that is fixed before any data is touched. Three parts:

### 1. A priori exclusion, on physics — before any data is fetched

For `polymathic-ai/MHD_64` (parameters `Ma ∈ {0.7, 2}`, `Ms ∈ {0.5, 0.7, 1.5, 2, 7}`),
retain **only `Ms ≤ 0.7`** — the four subsonic files (`Ma_0.7_Ms_0.5`, `Ma_0.7_Ms_0.7`,
`Ma_2_Ms_0.5`, `Ma_2_Ms_0.7`) per split.

`Ms ∈ {1.5, 2, 7}` are excluded because they are transsonic/supersonic and shocks would
corrupt the event definition. This is a **physics** decision, declarable in writing before
any file is downloaded — not a subset chosen after inspecting results.

### 2. Empirical admission gate — measured, with the threshold fixed in advance

The repository already owns the right instrument:
`itd_research.mission7.physics.validate_isotropic_dns` measures **relative divergence**
`‖∇·u‖ / ‖∇u‖` per frame. The JHTDB reference measured **0.6–1.0 %**.

Proposed rule, to be frozen in a preregistration before measuring: admit the source only if
the retained subset's relative divergence stays within **≈3× the JHTDB reference (≲ 3 %)**.

**This gate may well fail, and that is an acceptable outcome.** Density fluctuations grow
with `Ms`; even at `Ms = 0.5` the flow is *weakly* compressible, not incompressible, and
this note deliberately does **not** predict that the subset will pass. If it fails, the
correct action is to declare The Well out of scope for this event definition and publish
that — **not** to relax the threshold.

### 3. The event definition does not change

No modification to `Q`, `λ₂`, `min_cells`, `persistence`, or the feature sets. Adapting the
diagnostics to a compressible form (true second invariant with dilatation, or a
compressible-appropriate vortex identifier) would produce channels **not comparable** with
the merged H61–H74 results — destroying the only reason to run a cross-institution test in
the first place.

## Why this shape

* It reuses tested machinery instead of adding an unvalidated compressible path.
* It preserves comparability with the existing record.
* It is fully preregisterable: every choice is declarable before measurement.
* It **fails safe**: "source physically out of scope" is a legitimate, publishable result.

## Honest limits of what this would buy

Two caveats that should temper expectations if a Mission 9 is ever launched:

1. **The Well is an astrophysics corpus**, so compressibility is pervasive rather than
   incidental (`supernova_explosion`, `turbulent_radiative_layer`,
   `turbulence_gravity_cooling` are all compressible). The subsonic MHD subset is the
   *least-bad* option available, not an ideal one.
2. **The novelty would be institutional, not physical.** Mission 8's H65 already tested
   hydrodynamic → MHD transfer. A Mission 9 on The Well would add a genuinely independent
   *institution* — which is real value, since every external result in Missions 6–8 rests
   on JHTDB — but it would make the existing negative **more robust, not different**. It is
   not a path to overturning the Mission 8 conclusion.

## Status of this note

A decision rule, recorded before the data exists in this repository. Acting on it still
requires its own preregistration — fixing dataset, subset, thresholds, event definition and
decision rule before any evaluation, exactly as
`configs/mission8h65/preregistered_protocol.toml` did for the H65 follow-up.
