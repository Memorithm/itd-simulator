# Cylinder-wake Re=3900 — manual integration workflow

Status: **manual, network-enabled workflow** (NOT run in CI). This directory documents
how to integrate the highest-priority external target from the Mission 4/5 inventory.
It is **blocked-by-{network,size}** in this offline environment; no dataset is committed
and no result is produced here. Provenance metadata is in
`itd_research/external_validation/cylinder_re3900/metadata.py`.

## Why this dataset

A time-resolved cylinder-wake DNS at Re≈3900 with Eulerian **and** Lagrangian fields,
pressure, and force coefficients — purpose-built for PIV/PTV validation. Its independent
labels (lift/drag zero-crossings, shedding phase, published Strouhal frequency, pressure
minima, core tracks) are all **ITD-independent**, which is exactly what H27/H24/H28 need.

## Steps (to run locally, off CI)

1. **Locate & verify** the authoritative record (start from the source URL in the
   metadata module). Confirm DOI, authors, licence, and **redistribution conditions**
   before downloading. Do not proceed if redistribution is disallowed.
2. **Download** into a scratch directory (never into the repo). The full time-resolved
   3D set is GB-scale — prefer the 2D snapshot subset first.
3. **Checksum** every downloaded file (SHA-256) and record it in a
   `source_manifest.json`.
4. **Inspect** variables, dimensions, cadence, coordinate system, and units; write an
   `inspect_report.json`.
5. **Convert** a **small subset** to the internal typed field model
   (`itd_research.io`), writing `conversion_manifest.json`, `units.json`,
   `mask_summary.json`, and `checksum.json`. Never commit the raw or oversized data.
6. **Subset** deterministically (fixed frame indices / spatial crop) so development does
   not require the whole dataset; commit only a **tiny, legally-redistributable** CI
   fixture, clearly labelled as a fixture (not scientific external evidence).
7. **Label** events from lift/drag/pressure/published tracks — never from ITD — and
   record label provenance and uncertainty.
8. **Evaluate** with the leakage-safe grouped protocol
   (`docs/research/MISSION5_GENUINE_EXTERNAL_CROSS_CODE_SPEC.md`), reporting the
   established-vs-established+ITD added value on this external holdout.

## Guarantees

CI never runs this workflow, never downloads, and never depends on third-party
availability. Anything committed from here is a tiny fixture with full provenance, kept
distinct from scientific external evidence.
