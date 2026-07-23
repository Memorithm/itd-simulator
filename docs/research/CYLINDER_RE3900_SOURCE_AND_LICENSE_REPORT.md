# External source and licence report

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Does not modify
`ITD V29.18`.

## Cylinder Re≈3900 — source verified, data **blocked**

The Mission 6 metadata pointed at a published time-resolved cylinder-wake record
(PMC8713130). Verified this session: the authoritative record is a **publication** whose
associated full time-resolved dataset is **GB-scale** and not exposed as a single
manageable, redistribution-clear file reachable here. Classic small cylinder-wake snapshot
mirrors (dmdbook, PyDMD, databook) returned 403/404. **Status: blocked** — no raw file
obtained, **no checksum fabricated**, no redistribution assumed.

## JHTDB isotropic1024coarse — Johns Hopkins Turbulence Database

- **Institution**: Johns Hopkins University. **Access**: public `GetVelocity` SOAP service.
- **Token**: `edu.jhu.pha.turbulence.testing-201406` (public testing token; small queries).
- **Licence / terms**: JHTDB terms of use and citation policy
  (https://turbulence.pha.jhu.edu). Raw cutouts are **not** committed; they are regenerated
  by `tools/datasets/fetch_jhtdb_cutout.py`. **Retrieved**: 2026-07-23. Per-frame SHA-256 in
  `repro/mission7/source_manifest.jhtdb.json`.

## biofilm PIV — Zenodo record 1175014

- **Institution**: United States Naval Academy / University of Virginia.
- **DOI**: 10.5281/zenodo.1175014. **Licence**: **CC-BY-4.0** (redistribution permitted).
- **SHA-256**: `107ba49251eb28d454696157791e963ef2829bec2d714920b45f9519862d37b3` (verified).
- **Nature**: 2D **time-averaged** boundary-layer PIV (mean + Reynolds stresses). A
  shear-dominated **control**, never coherent-vortex validation.

All three provenance records carry institution, access method, licence and (where obtained)
checksums. The cylinder entry honestly records the blocked status.
