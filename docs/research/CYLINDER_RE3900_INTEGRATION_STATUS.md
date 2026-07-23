# Cylinder Re=3900 integration status (H46) — blocked-in-CI

Status: **research status report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **external-DNS** — **blocked** in this environment.

## Honest status

Integration of the time-resolved Re≈3900 cylinder-wake dataset is **attempted** through a
manual, network-enabled, checksum-verified workflow and is **blocked-in-CI**: this
environment has **no network** and the full time-resolved set is GB-scale. No dataset is
downloaded, **no checksum is fabricated**, no raw/oversized data is committed, and **no
scientific result is asserted**. The blocked state is reported, not papered over.

## What is in the repository (offline, testable)

- **Provenance metadata** (`.../cylinder_re3900/metadata.py`): dataset id, source URL, the
  fields (Eulerian + Lagrangian, pressure, forces), and the ITD-**independent** event
  labels (lift/drag zero-crossings, shedding phase, published Strouhal frequency, pressure
  minima, core tracks). `integration_status = blocked-by-{network,size}`.
- **Integration contract** (`.../cylinder_re3900/integration.py`, Mission 6): the ordered
  workflow stages, the evidence-level ladder, and a **manifest schema validator** that
  runs offline against tiny synthetic fixtures. This lets a later offline run target a
  well-formed contract without the repo ever touching the network.
- **Manual workflow doc** (`tools/datasets/cylinder_re3900/README.md`): discover → verify
  → download → checksum → inspect → convert → subset → label → evaluate, with
  redistribution checked before any download and only tiny redistributable fixtures ever
  committed.

## Workflow stages and blocking point

`discover → download → verify → inspect → convert → subset → manifest → analyse`

- **Blocked at**: `download` (no network).
- **Evidence ladder** (none reached in CI): `ingestion_verified → diagnostic_comparison →
  temporal_event_analysis → predictive_development → locked_external_holdout`.
- **Reached level**: `None`.

## What a successful offline run would establish

Running the workflow on a network-enabled host would ingest a small verified subset, emit
schema-valid manifests, align frames to the independent force/pressure/shedding labels,
and run the leakage-safe grouped established-vs-established+ITD added-value test on a
frozen external holdout — the first genuinely external (cross-institution) evidence for
ITD. In this environment that remains **blocked**, and is reported as such.

**Verdict: H46 blocked** (attempted; contract + provenance in place; no fabricated
evidence).
