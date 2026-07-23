# PIV validation expansion report (H14)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Builds on `EXTERNAL_CFD_PIV_VALIDATION_REPORT.md` §3 (biofilm PIV, Zenodo 1175014,
CC-BY-4.0). Reproduce the new region-conditioned agreement with:

```
python -c "import numpy as np; from itd_research.external_validation.piv_agreement \
import region_conditioned_agreement, classify_h14; \
d=np.load('tests/fixtures/external/biofilm_piv_excerpt.npz'); \
a=region_conditioned_agreement(d['u'],d['v'],d['x'],d['y']); \
print(a.as_dict()); print(classify_h14(a))"
```

## Question (H14, falsifiable)

Does PIV **strongly validate ITD in every vortex region**? Reframed: on measured PIV
velocities, does ITD's local rotational intensity (`ω²`) agree with an *independent*
rotation-strength diagnostic (2D swirling strength `λ_ci`) — and does that agreement
hold **whole-field** or only **inside genuinely rotational regions** (Okubo-Weiss
`W < 0`, an ITD-independent label)?

## Result on measured PIV (biofilm boundary-layer excerpt, 2400 nodes)

| quantity | value | reading |
|---|--:|---|
| rotation fraction (`W<0`) | 0.48 | roughly half the excerpt is rotation-dominated |
| **whole-field** Spearman(`ω²`, `λ_ci`) | **−0.11** | essentially no agreement across the field |
| **rotation-region** Spearman(`ω²`, `λ_ci`) | **+0.45** | moderate agreement *inside* vortices |
| Jaccard(top-20% `ω²`, `W<0`) | 0.16 | high-intensity nodes are mostly *not* rotational |

## H14 classification: **partially supported**

The claim "PIV strongly validates ITD in every vortex region" is **not supported**:

* **Whole-field, ITD intensity and rotation strength are uncorrelated** (Spearman
  −0.11), and the top-intensity region overlaps the rotation region at only
  Jaccard 0.16. On real shear-driven data, high `ω²` lands predominantly on **shear**,
  not rotation — ITD's vorticity basis counts shear as intensity (the exact effect the
  analytical "simple shear" case and §3 of the external report predict).
* **Inside genuine rotation regions**, ITD intensity *does* moderately track rotation
  strength (Spearman +0.45). So PIV **partially validates** ITD where rotation actually
  exists, while **refuting** the "every region / strongly" version of the claim.

The honest, scoped statement: *on the one integrated PIV field, ITD intensity agrees
moderately with independent rotation strength conditioned on vortical regions, and not
at all whole-field; ITD is complementary to — not a validator-confirmed replica of —
rotation-based identification (H5), and shear contamination is real and measurable.*

## What is blocked (evidence-limited, stated not hidden)

| aspect | status |
|---|---|
| instantaneous coherent structures | **blocked** — only the time-averaged mean and this excerpt are integrated; the 4000 instantaneous fields (22 GB) are not downloaded |
| volumetric / **tomographic PIV** (3D vortex regions) | **blocked by unavailable evidence** — no tomographic-PIV dataset is integrated in the authoritative path; the 3D candidate's PIV agreement is untested on measured volumetric data |
| multiple independent PIV facilities | **blocked** — one facility/flow; generalization across PIV sources is unestablished |

These are recorded in the dataset inventory (`NEW_DATASET_INVENTORY.md`) as
integration-ready or blocked candidates, with no fabricated results.

## Limitations

One measured field (a small committed excerpt of a single time-averaged boundary
layer), 2D, single facility; swirling strength and Okubo-Weiss are themselves
diagnostics, not ground truth. The moderate in-region agreement is an association on
one snapshot, not a causal or cross-facility claim. Nothing here certifies ITD against
PIV; it quantifies where measured PIV does and does not agree with ITD intensity, and
finds the "every region" claim false while the "inside vortices, moderately" claim
holds on this field.
