# Mission 4 dataset inventory (hard external predictive validation)

Status: **research/provenance document**. Not a certified revision; does not modify
`ITD V29.18`. Extends `NEW_DATASET_INVENTORY.md` and `datasets/registry.json` with the
Mission 4 triage. **No large third-party data is committed; no checksum is
fabricated;** candidates not integrated carry no results.

## Environment reality (why most externals are blocked here)

This container has **no network download in CI**, **no OpenFOAM/Nek5000**, and lacks
`h5py`/`netCDF4`/`vtk`. GB-scale external DNS/PIV cannot be fetched, verified, or
processed in this session. The Mission 4 predictive results therefore rest on
**local-solver held-out** evidence (perturbed, jittered, degraded, grouped-by-seed)
plus the **one committed external PIV field** (biofilm) as an OOD control. External
datasets below are triaged honestly; integrating them is a **manual-workflow**,
network-enabled task, not a CI task.

## Evidence-class triage

`integrated` · `integration-ready` · `metadata-only` · `blocked-by-{network,size,
licence,authentication,format,tooling,missing-ground-truth}` · `rejected`.

## Priority candidates found (real, not integrated here)

| candidate | flow class | ground truth | class in this env | why |
|---|---|---|---|---|
| Cylinder wake **Re=3900**, Eulerian+Lagrangian DNS (purpose-built for PIV/PTV validation; time-resolved 3D velocity + 2D snapshots + pressure) | bluff-body wake / shedding | pressure/force + shedding frequency; core tracks | **integration-ready / blocked-by-{network,size}** | real 3D time-resolved velocity with independent labels — ideal for H17/H24, but large and needs manual download + conversion |
| JHTDB `isotropic1024`, `channel`, `transition_bl` (already in `datasets/registry.json`) | HIT / channel / transition | known event times, γ(x) | **metadata-only / blocked-by-{network,authentication}** | queried, not committed; needs the JHTDB token and network |
| JHTDB additional flows (rotating, MHD, mixing layer) | varied 3D DNS | solver event times | **integration-ready (same path)** | reachable via the existing `fetch_jhtdb_cutout` path when network is available |
| International PIV Challenge cases | canonical PIV | published references | **metadata-only / blocked-by-{licence,format}** | manual download, licence check, coordinate/units mapping |
| biofilm PIV mean boundary layer (Zenodo 1175014) | shear-dominated BL | none (mean field) | **integrated (control)** | committed excerpt; used as the OOD/negative example |

## What each priority class would test (if integrated)

* **Cylinder wake Re=3900** → H17 (shedding-onset prediction with independent
  lift/force labels), H24 (time-resolved PIV/PTV with core tracks), H19/H20
  (cross-solver / cross-source transfer). This is the single highest-value external
  target and is `integration-ready` behind a manual, network-enabled workflow.
* **JHTDB extra flows** → H13/H19/H20 breadth (already have the fetch path).
* **PIV Challenge** → H24 on canonical benchmark PIV.

## Explicit gaps (stated, not hidden)

* **No strongly-vortical, time-resolved, independently-annotated PIV integrated** →
  H24 is **blocked** (the committed biofilm field is a shear-dominated mean, a
  control, not a vortex-event dataset).
* **No second external institution/source integrated** → H20 (cross-institution
  transfer) is **blocked** (one external source only).
* **No external finite-volume solver run** → H19 external-FV transfer **blocked**;
  the achievable cross-solver evidence is 2D `spectral_ns` ↔ 3D `spectral3d`.

## Rules (unchanged)

Large raw data never committed; `redistribution_allowed=false` entries downloaded by
the user and checksum-verified; synthetic/local-solver fields are **never** presented
as external empirical validation; every integrated dataset keeps full provenance.

## Sources consulted

- Cylinder-wake Re=3900 Eulerian+Lagrangian DNS dataset (built for PIV/PTV
  assessment): https://pmc.ncbi.nlm.nih.gov/articles/PMC8713130/
- JHTDB: https://turbulence.pha.jhu.edu/ (entries in `datasets/registry.json`)
- biofilm PIV: Zenodo record 1175014 (CC-BY-4.0), already integrated.
