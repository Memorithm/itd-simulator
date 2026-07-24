# Mission 8 dataset inventory

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration `configs/mission8/preregistered_protocol.toml`
(SHA-256 `ddd64804b58b6661c22c5911f45832de7c0bc3afe2eed25de96d60ab40ec3206`), committed
before final external evaluation (`73adbdc`). Baseline commit `6480973` (Mission 7 merge).

## Secured datasets

| dataset | institution | evidence class | frames | independent units |
|---|---|---|---|---|
| **JHTDB isotropic1024coarse** (primary) | Johns Hopkins | external-DNS | `iso_topo` 40, `iso_run1/2/3` 24 each | **4 sequences** |
| **JHTDB mhd1024** (secondary) | Johns Hopkins | external-DNS | `mhd_topo` 24, `mhd_topo_run2` 16 | **2 sequences** |

Cutouts: 24³-cell sub-windows, `dt = 0.1`. Origins (chosen to sample distinct regions of
the same DNS field, never re-fetches of an identical window):

| sequence | origin (x, y, z) | frames |
|---|---|---|
| `iso_topo` | (100, 200, 300) | 40 |
| `iso_run1` | (500, 200, 300) | 24 |
| `iso_run2` | (100, 600, 300) | 24 |
| `iso_run3` | (100, 200, 700) | 24 |
| `mhd_topo` | (100, 200, 300) | 24 |
| `mhd_topo_run2` | (500, 200, 300) | 16 |

Every sequence downloaded, checksum-verified, and physically re-checked through
`itd_research.mission7.ingestion`/`itd_research.mission7.physics` (reused, not
reimplemented — see the preregistration §"physical_validation"). Ingestion safety
(non-finite rejection, duplicate-frame rejection, monotone-coordinate check, frame/grid-cell
caps) is Mission 7's already-tested machinery; Mission 8 adds only a tuple view
(`itd_research.mission8.ingestion.load_sequence_as_tuples`).

## Blocked / not integrated this mission

| target | status | reason |
|---|---|---|
| `cylinder_re3900` | blocked | not re-integrated this mission; Mission 6/7 already established it as a 2D/vortex-shedding source, not a 3D core-merger/split source matching this mission's event definition |
| `time_resolved_coherent_vortex_piv` | blocked | no open, downloadable, time-resolved, vortex-dominated PIV/PTV dataset secured — see `STRONGLY_VORTICAL_PIV_M8_REPORT.md` |
| `jhtdb_transition_bl` | blocked-by-format | JHTDB fetch tool returned HTTP 500 in node-index mode, consistent with a non-uniform wall-normal grid incompatible with the uniform-spacing fetch path used here; not retried further |

## Why two sources, not more

The preregistration's `evidence_ladder` requires at least one comparable second source
with full provenance. `mhd1024` is genuinely a second, independently-forced JHTDB dataset
(forced MHD turbulence vs. forced isotropic hydrodynamic turbulence) — but it is the
**same institution and access modality** as the primary source, so Mission 8 reports any
cross-source result as **within-institution cross-physics transfer**, never as
cross-institution generalization (see `CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT.md`).

## Dev/holdout split (locked before evaluation)

The preregistered `development_fraction=0.625`/`holdout_fraction=0.375`, applied to the 4
isotropic sequences, rounds to 2.5/1.5. **2 development / 2 holdout** was chosen — not
3/1 — specifically because a single holdout unit gives a degenerate (zero-variance)
grouped bootstrap. This choice was made as a preregistration-consistent *operationalization*
before any sequence was scored, not a post-hoc adjustment:

* development: `iso_run1`, `iso_run2`
* holdout: `iso_topo`, `iso_run3`

`evaluations_allowed = 1` per the preregistration: the numbers in
`EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md` are the single, locked holdout
evaluation on this split — not re-run after inspection, only re-derived once after a
detector bug fix made **before** any report was written (see
`MISSION8_REPRODUCIBILITY_REPORT.md`).

## Grid-resolution honesty note (offline CI fixture, not this dataset)

The offline CI fixture (`itd_research.mission8.fixtures.write_synthetic_sequence`) is a
manufactured, under-resolved oracle used only for bounded code-path exercise — it is never
mixed with, or presented as, the real JHTDB inventory above.
