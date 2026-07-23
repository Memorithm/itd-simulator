# Cylinder Re=3900 integration report (Mission 5, H27)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **external-DNS** (attempted). Provenance:
`itd_research.external_validation.cylinder_re3900.metadata`; workflow:
`tools/datasets/cylinder_re3900/README.md`.

## Question (H27)

Does ITD predict an independently-labelled event in an **external** CFD/DNS/PIV dataset?

## Integration attempt

The highest-priority external target (Mission 4 inventory) is a time-resolved
cylinder-wake DNS at Re≈3900 with Eulerian + Lagrangian fields, pressure, and force
coefficients — purpose-built for PIV/PTV validation, with **ITD-independent** labels
(lift/drag zero-crossings, shedding phase, published Strouhal frequency, pressure
minima, core tracks). Its provenance is recorded and a full manual integration workflow
is documented.

## H27 classification: **blocked-by-{network,size}**

Integration is **not** completed in this environment:

* CI has **no network download**; the full time-resolved 3D dataset is **GB-scale** and
  is not committed;
* no OpenFOAM/Nek5000 is available to regenerate an equivalent case locally.

No external event was processed, so H27 **cannot be evaluated** and is recorded as
blocked — not supported or not-supported. The DOI is marked *unverified* in the metadata
pending confirmation at the source record; no fabricated checksum or result is recorded.

## What integration would enable (documented)

Following `tools/datasets/cylinder_re3900/README.md` (locate/verify → download →
checksum → inspect → convert a small subset → subset → label from lift/pressure →
evaluate with the leakage-safe grouped protocol) would enable H27 (external prediction),
H24/H32 (annotated vortical PIV/PTV), and H28 (external incremental value against a
competent baseline) — the tests that are otherwise blocked. This is the single
highest-value next step and requires a network-enabled, off-CI run.

## Limitations

No external data integrated; this report records the attempt, the provenance, the
workflow, and the honest blockage.
