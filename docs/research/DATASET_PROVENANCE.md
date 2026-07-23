# Dataset provenance

Status: **research provenance record**. Not a certified revision; does not modify
`ITD V29.18`. Machine-readable source of truth: `datasets/registry.json` (loaded
and validated by `itd_research.io.load_registry`). Large third-party data is
**not** committed; download scripts verify checksums, and only a small legally
redistributable excerpt is committed as a fixture.

## Rules applied

* Every external dataset records source, authors, URL/DOI, licence, version,
  SHA-256, retrieval date, format, units, coordinate convention, and uncertainty
  information.
* `redistribution_allowed` is set explicitly per entry. Data is committed only
  when the licence permits redistribution, and only as a small excerpt with
  attribution.
* Downloads use `tools/datasets/fetch_dataset.py` (checksum-verified, no
  credentials, never auto-run in CI). MATLAB v5 conversion uses
  `tools/datasets/convert_mat_piv.py` (SciPy used **only** in this optional
  user-run tool; the `itd_research` package stays NumPy-only).
* `.npz` loading always uses `allow_pickle=False`. Python `pickle` is never used
  for external data.

## Datasets

### `biofilm_piv_boundary_layer` — used as external empirical evidence

* **Title:** Biofilm flow data — time-averaged PIV velocity field of a turbulent
  boundary layer (`velocity_fields.mat`).
* **Authors:** Murphy, Barros, Schultz, Flack, Steppe, Reidenbach.
* **DOI:** 10.5281/zenodo.1175014 · **Licence:** CC-BY-4.0 (redistribution
  permitted with attribution).
* **SHA-256 (source `.mat`):**
  `107ba49251eb28d454696157791e963ef2829bec2d714920b45f9519862d37b3`.
* **Variables:** `U`, `V` (m/s), `x`, `y` (mm), turbulence statistics.
* **Grid:** `239 x 410`, uniform `dx = dy = 0.1765 mm`, `y` increasing from the
  wall; ~5.7 % invalid vectors (NaN), handled by the mask policy.
* **Preparation (reproducible):**
  ```
  python tools/datasets/fetch_dataset.py --id biofilm_piv_boundary_layer --output <dir>
  python tools/datasets/convert_mat_piv.py \
      --input <dir>/biofilm_piv_boundary_layer --output biofilm_full.npz \
      --u-var u_means_msec --v-var v_means_msec --x-var x_mm --y-var y_mm \
      --length-scale 1e-3 --length-unit m --velocity-unit m/s
  ```
* **Committed excerpt:** `tests/fixtures/external/biofilm_piv_excerpt.npz`
  (`40 x 60`, SHA-256
  `9d3753e18e2c6789868c829f4cf8e01a6d14356959d7a132752d0afd968c37ca`; a
  fully-valid interior crop, rows 15:95, cols 160:280, stride 2, rescaled to
  metres). Attribution and the exact transformations are in
  `tests/fixtures/external/ATTRIBUTION.md` (CC-BY-4.0 requirement).

### `turbine_wake_2d_synthetic` — registered, out of scope for the vector comparison

* **Title:** Synthetic two-dimensional wind-turbine wake field
  (`Wake_2D_Smooth.npy`). **Author:** Lengyel. **DOI:** 10.5281/zenodo.20607774 ·
  **Licence:** CC-BY-4.0.
* **SHA-256:**
  `f0cd5067524fd490e70ef787efff3b47ce82317793ab580ddff1d92d95bd8fe9`.
* **Why not used for the comparison:** the file is a **single scalar** field
  (streamwise velocity `U` only, `351 x 1001`, no `v` component and no
  coordinates). Vortex-identification diagnostics need the full velocity-gradient
  tensor, so a scalar field cannot drive the ITD-vs-Q/swirling comparison. It is
  recorded as a verified, redistributable external field for ingestion/provenance
  completeness and is honestly out of scope for the vector-field study.

### `jhtdb_isotropic1024` — used as external 3D empirical evidence

* **Title:** JHU Turbulence Database, forced isotropic turbulence DNS
  (`isotropic1024coarse`). **DOI:** 10.1080/14685240802376389.
* **Licence:** open for research use under the JHTDB terms and citation policy;
  `redistribution_allowed=false`, so the raw DNS is **not committed**.
* **Retrieved here:** a `32^3` block of native grid nodes at origin
  `(200, 300, 400)`, spacing `2pi/1024`, `t=0`, via the `GetVelocity` SOAP point
  query with the public testing token, using
  `tools/datasets/fetch_jhtdb_cutout.py` (standard-library `urllib` only — no
  SOAP/HDF5 dependency).
* **SHA-256 (retrieved `.npz`):**
  `74b81f6d27da64b55cdeb132c0500c9deab01133989a8663c6599c19b9d67186`
  (component rms 0.5524).
* **Use:** the 3D ITD candidate vs Q/lambda_2/swirling comparison
  (`ITD_3D_CANDIDATE_REPORT.md` §4). Reproduce with the fetch tool and verify the
  checksum; CI itself uses only the analytical 3D oracles (no network).

### `piv_challenge_candidate` — download recipe

PIV Challenge reference cases kept as a verified download recipe for additional
2D validation. `redistribution_allowed=false`: fetch from the portal under its
terms, then checksum-verify.

### `synthetic_piv_small` — CI fixture only

Tiny project-generated PIV grid used solely to exercise the masking adapter in
CI. **Synthetic; never external empirical validation.**

## Environment note

The development environment has no OpenFOAM/VTK/HDF5. CFD cases in the spec are
represented by deterministic **synthetic** analogues in
`itd_research.external_validation.synthetic_flows`, clearly labelled and never
presented as solver output or empirical data. The one genuinely external,
empirical dataset processed here is the biofilm PIV field above.
