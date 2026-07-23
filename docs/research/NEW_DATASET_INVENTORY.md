# External dataset inventory (DNS / CFD / PIV / tomographic-PIV)

Status: **research/provenance document**. Not a certified revision; does not modify
`ITD V29.18`. Authoritative machine-readable provenance is `datasets/registry.json`
(+ `docs/research/DATASET_PROVENANCE.md`); this inventory adds the **evidence-class
triage** the spec requires and the shortlist of candidates for broadening external
validation. **No large third-party data is committed; no checksum is fabricated;**
candidates not yet integrated carry no results.

## Evidence classes

`integrated` · `integration-ready` · `metadata-only` · `blocked by
{licence,authentication,size,missing-velocity-field}` · `rejected as scientifically
unsuitable`. CI never touches the network; only small legally-redistributable excerpts
with checksums are committed.

## Currently in the registry

| id | dim | class | note |
|---|---|---|---|
| `biofilm_piv_boundary_layer` | 2D | **integrated** | real PIV mean field (Zenodo 1175014, CC-BY-4.0); excerpt committed + checksummed; used for H5/H14 |
| `jhtdb_isotropic1024` | 3D | **integrated** (queried) | real DNS point queries (public token); raw not committed per JHTDB terms; H6/H13 |
| `jhtdb_channel` | 3D | **integrated** (queried) | real anisotropic DNS; near-wall vs core orientation; H6 |
| `jhtdb_transition_bl` | 3D | **integrated** (queried) | real transitional DNS; H2 transition + γ(x) |
| `turbine_wake_2d_synthetic` | 2D | **rejected as unsuitable** (for tensor diagnostics) | single scalar component only; no v, no coordinates — cannot form the velocity-gradient tensor |
| `piv_challenge_candidate` | 2D | **metadata-only** | International PIV Challenge; needs manual download + checksum |
| `synthetic_piv_small` | 2D | **integrated** (CI fixture) | synthetic; never external empirical validation |

## Shortlist to broaden coverage (candidates, not yet integrated)

Each is a real public source; status reflects what is missing to reach `integrated`.
None has results here — the point is an honest queue, not a claim.

| target flow family | candidate source | class | what is needed |
|---|---|---|---|
| additional 3D DNS regimes (rotating, MHD, mixing layer) | JHTDB further datasets | integration-ready | same query path as the integrated JHTDB sets; add registry entries + checksums |
| instantaneous PIV coherent structures | biofilm 4000-frame instantaneous set (Zenodo 1175014) | blocked by size | 22 GB; not downloaded; needed for instantaneous H14/H2 on measured data |
| **tomographic / volumetric PIV** (3D vortex regions) | published tomographic-PIV datasets | blocked by {licence, authentication} | a redistributable volumetric u,v,w field; none integrated — the 3D-candidate PIV agreement is untested on measured volumetric data |
| canonical benchmark PIV | International PIV Challenge cases | metadata-only | manual download, licence check, checksum, coordinate/units mapping |
| external OpenFOAM-class CFD | user-provided VTK/OpenFOAM case | integration-ready | the `io.vtk`/`io.openfoam` adapters exist; needs a governed case file |

## Gaps this inventory makes explicit

* **No integrated tomographic/volumetric PIV** — the single most important gap for the
  3D candidate; it is `blocked`, not silently absent.
* **No instantaneous measured PIV** — only a time-averaged mean is integrated.
* **No locally-run heavy external CFD** — the in-environment solver is a minimal
  pseudo-spectral code; external DNS is queried, not solved here.

## Rules (unchanged from the spec)

Large raw data is never committed; entries with `redistribution_allowed=false` are
downloaded by the user and checksum-verified (`itd_research.io.verify_checksum`);
synthetic fields are for code verification/CI only and are **never** presented as
external empirical validation; every integrated dataset keeps full provenance
(source, DOI, licence, retrieval date, checksum).
