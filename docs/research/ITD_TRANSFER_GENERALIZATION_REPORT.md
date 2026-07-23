# ITD cross-flow transfer and generalization report (H8/H9/H10/H13)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
No threshold, candidate, or claim is certified. Reproduce with
`python -m itd_research.generalization run --output <dir>` (a quick form runs in CI,
step 13/14 of `run_validation.sh`).

## Questions (falsifiable)

* **H13** — does ITD *generalize* to an unseen flow of a seen family as well as
  established velocity-gradient diagnostics?
* **H8** — is ITD *conditionally* superior (better on some flows/families, not all)?
* **H9** — do ITD component *relationships* (channel → physical diagnostic) transfer
  to an *unseen family*, i.e. are the components universal?
* **H10** — does a *single ITD threshold* transfer across flows?

## Protocol (leakage-safe, ITD-independent labels)

The deterministic 3D catalogue (9 flows across `laminar_coherent`, `transitional`,
`turbulent`) is partitioned into 243 sub-cubes. On each sub-cube we evaluate the
8-channel ITD-3D superset and six established diagnostics (enstrophy, Q mean, Q⁺
volume fraction, swirling strength, strain magnitude, λ₂⁻ fraction). Held-out sets
are explicit: **leave-one-flow-out** (H13/H10) and the harder **leave-one-family-out**
(H9). Standardization uses training statistics only. All labels (family, "majority
Q>0 rotation-dominated") are computed without ITD.

## H13 — generalization to unseen flows (leave-one-flow-out family classification)

| method | balanced accuracy | laminar | transitional | turbulent |
|---|--:|--:|--:|--:|
| **ITD (8 channels)** | **0.525** | 0.44 | 0.13 | 1.00 |
| established gradient diagnostics (6) | 0.387 | 0.16 | 0.00 | 1.00 |

Chance = 0.33. **H13: partially supported.** ITD generalizes to unseen flows *better
than the multi-feature gradient baseline* (0.53 vs 0.39) and perfectly separates the
turbulent family, but generalization is **family-dependent**: the transitional family
is barely recalled (0.13) by either method. ITD generalizes above chance but not
uniformly.

## H8 — conditional superiority (which baseline, which flow)

The comparison is explicitly **not** a single winner:

* against the six-feature **gradient-diagnostic** baseline, ITD is *superior* here
  (0.53 > 0.39);
* against a **single intensity scalar** (the H12 ablation baseline, balanced accuracy
  0.59), ITD is *inferior* on the same task;
* by family, every method is perfect on turbulent and weak on transitional.

**H8: supported within tested scope** — ITD's superiority is conditional on the
baseline and the flow family, exactly as the hypothesis predicts. No method
dominates; "superior" is only meaningful per-baseline, per-family.

## H9 — component transferability to an unseen family (leave-one-family-out R²)

Linear regression from the ITD channels onto an established diagnostic, fit on two
families and tested on the third:

| target diagnostic | in-family R² | out-of-family R² (mean) | worst held-out family |
|---|--:|--:|--:|
| enstrophy | 0.998 | 0.219 | turbulent −0.37 |
| swirl mean | 0.969 | −89.6 | turbulent −269 |
| Q⁺ fraction | 0.639 | −1465 | turbulent −4396 |

**H9: not supported.** The ITD→physics relationship is strong *within* a family
(R² up to 0.998) but **collapses on an unseen family** — the fitted relation
extrapolates anti-predictively (R² ≪ 0 means worse than predicting the mean). Only
enstrophy transfers even weakly, because it is nearly a linear image of the intensity
channel. The ITD components are **not universal**: their mapping to physical
quantities is family-specific. This is a clean negative result.

## H10 — threshold transfer across flows (detect majority-Q>0 sub-cubes)

A single scalar threshold, calibrated to detect rotation-dominated sub-cubes, then
transferred to a held-out flow (chance = 0.50):

| scalar | source | in-sample accuracy | transfer accuracy |
|---|---|--:|--:|
| localization | ITD | 0.99 | 0.17 |
| orientation_dispersion | ITD | 0.98 | 0.50 |
| intensity | ITD | 0.78 | 0.50 |
| enstrophy | baseline | 0.78 | 0.50 |
| swirl mean | baseline | 0.78 | 0.50 |

**H10: not supported.** In-sample, ITD `localization` and `orientation_dispersion`
detect rotation-dominated sub-cubes almost perfectly — but **no single threshold
transfers**: transfer accuracy collapses to chance, and `localization` even
*anti-transfers* (0.17, below chance). Established scalars transfer no better. A fixed
universal threshold does not exist across these flows; thresholds are flow-dependent.
This corroborates the H11 finding (channel scales differ by regime) and the flow
-dependent-threshold direction of the spec.

## Consolidated verdicts

| hypothesis | verdict |
|---|---|
| H8 conditional superiority | supported within tested scope |
| H9 component universality | **not supported** |
| H10 single-threshold transfer | **not supported** |
| H13 generalization to unseen flows | partially supported |

## Limitations

Nine local flows, three families, `24³` resolution, under-resolved turbulence, one
classifier family, linear transfer models. Leave-one-family-out with three families
is a small, high-variance test (each fold trains on two families). The negative H9/H10
results are strong *for this catalogue*; a larger, external, better-resolved set could
move them, and confirming them there is the correct next step, not asserting
universality now. Nothing here certifies or de-certifies any ITD component.
