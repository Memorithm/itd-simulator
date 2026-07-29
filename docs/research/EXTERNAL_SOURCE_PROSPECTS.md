# External source prospects — dataset discovery record

Status: **infrastructure / dataset-discovery record**. Not a certified revision; does not
modify `ITD V29.18`. No hypothesis verdict is claimed or changed by this document.

Purpose: record what external-source searching has actually found, so a future mission acts
on it immediately instead of repeating the search. Written after the Mission 8 H65
follow-up, whose result exposed the limitation this record is meant to address.

## The limitation being tracked

Every external result in Missions 6–8 rests on **JHTDB**. Mission 8's H65 could therefore
only ever be a **within-institution cross-physics** test (isotropic hydrodynamic → forced
MHD, both Johns Hopkins) — never cross-institution generalization. That caveat is stated in
`CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT.md` and is not a flaw in the analysis; it is a
limit of the available data.

## Found: The Well (Polymathic AI / Flatiron Institute) — first credible cross-institution candidate

**The Well** (arXiv 2412.00568) is a collection of ~21 physics-simulation datasets on the
Hugging Face Hub under `polymathic-ai/`, **CC-BY-4.0**, generated at the **Flatiron
Institute** (Center for Computational Astrophysics / Center for Computational Mathematics)
and collaborating universities — an institution genuinely independent of Johns Hopkins.

This is the first source found across Missions 3–8 that could support a real
**cross-institution** transfer test.

### 3D, velocity-bearing → potentially usable with the existing Mission 8 pipeline

| dataset | grid | timesteps | fields | file size (test) |
|---|---|---|---|---|
| `polymathic-ai/MHD_64` | 64³ | 100 | density, **velocity**, magnetic field | ~734 MB / file |
| `polymathic-ai/MHD_256` | 256³ | 100 | same, higher resolution | larger |
| `polymathic-ai/turbulent_radiative_layer_3D` | 3D | — | velocity + thermodynamic | — |
| `polymathic-ai/supernova_explosion_64` / `_128` | 3D | — | velocity + thermodynamic | — |
| `polymathic-ai/turbulence_gravity_cooling` | 3D | — | velocity + thermodynamic | — |

`MHD_64` is the closest analogue to the existing sources: uniform cartesian grid, 3D,
time-resolved, explicit velocity vector field, 100 timesteps, 100 trajectories.

### 2D → NOT usable without new machinery

`shear_flow` (128×256, `u = (uₓ, u_y)`), `rayleigh_benard`, `turbulent_radiative_layer_2D`,
`euler_multi_quadrants_*`, `gray_scott_reaction_diffusion`, `active_matter`,
`viscoelastic_instability`, `planetswe`, `helmholtz_staircase`, `acoustic_scattering_*`.

`shear_flow` is superficially attractive — Kelvin–Helmholtz billows merge and split, which
is exactly Mission 8's `core_merger` / `core_split` event — but the **entire Mission 8
structural pipeline is 3D**: `velocity_gradient_3d`, `q_criterion`, `lambda2`,
`label_components_3d`, and every `ITD_3D_NONREDUNDANT` channel via `evaluate_itd3d`.
Embedding a 2D field as pseudo-3D (`w = 0`, no z-variation) makes the Q-criterion
degenerate and would be physically meaningless. Using 2D data requires a genuine 2D
structural pipeline, whose channels would **not** be comparable with the merged H61–H74
results.

## Blockers to resolve before any cross-institution claim

1. **Compressibility.** `MHD_64` is *compressible* MHD (∇·(ρv) = 0, not ∇·v = 0). Both
   JHTDB sources are incompressible. Q-criterion and λ₂ are conventionally derived under
   incompressibility, and Mission 8's ingestion physical validation
   (`itd_research.mission7.physics.validate_isotropic_dns`) checks a near-solenoidal
   velocity field — it would correctly flag this data. Whether the Q/λ₂ topology event is
   appropriate for compressible flow is a **real scientific question that must be settled
   before**, not after, any evaluation.
2. **Format.** The Well ships HDF5 with its own field grouping, not the `frame_*.npz`
   layout `itd_research.mission8.ingestion` consumes. A conversion adapter is required, and
   must preserve the `(nz, ny, nx)` axis convention — the axis-order failure mode Mission
   8's Oracle tests exist to catch.
3. **Scale.** ~734 MB per `MHD_64` test file; the full collection is ~15 TB. Any use must
   be a bounded, preregistered subset with published checksums, as in
   `repro/mission8h65/`.

## H72 (vortical PIV/PTV) — still blocked

This search did **not** unblock H72. The Well is **simulation** data; H72 asks whether ITD
structural channels agree with independently documented coherent-vortex evolution in
**time-resolved experimental PIV/PTV**. A simulation source, however independent the
institution, cannot answer an experimental-validation question.

Searches performed and their outcome are recorded in `STRONGLY_VORTICAL_PIV_M8_REPORT.md`
(VIVALDy: matches the criteria but no public repository located; Tomo-PIV/PTV vortex-ring
literature: papers without open data releases). H72 remains **blocked**, unchanged since
Mission 3.

## What this record does and does not claim

It records a **candidate**, not a result. No data from The Well has been fetched, ingested,
validated or evaluated. No hypothesis verdict changes. Acting on this record requires its
own preregistration — fixing the dataset, subset, event definition, compressibility
decision and decision rule **before** any evaluation, exactly as
`configs/mission8h65/preregistered_protocol.toml` did.
