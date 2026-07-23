# Cylinder Re≈3900 ingestion report (H49) — cylinder blocked; JHTDB integrated instead

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Does not modify
`ITD V29.18`.

## Cylinder Re≈3900 — **blocked** (honest)

The authoritative time-resolved cylinder-wake DNS remains a GB-scale record behind a
publication; no manageable, redistribution-clear file was fetchable this session. Its
Mission 6 workflow contract, provenance metadata and evidence ladder remain in place
(`itd_research/external_validation/cylinder_re3900/`,
`tools/datasets/cylinder_re3900/`). Achieved evidence level for the cylinder: **E0**
(metadata verified) — no raw file obtained. No checksum was fabricated; no result asserted.

## What was ingested instead (H49 **supported** via real data)

Because the session had network, two genuinely external sources were downloaded and
**checksum-verified**, satisfying H49 with real data:

- **JHTDB isotropic1024coarse** (Johns Hopkins DNS). A 16³ Eulerian cutout was fetched at
  16 and 48 consecutive times via the public GetVelocity service. Every frame carries a
  SHA-256 recorded in `repro/mission7/source_manifest.jhtdb.json`. The ingestion path
  (`itd_research.mission7.ingestion`) enforces the preregistered limits and rejects
  non-finite values, non-monotone coordinates, timestamp disorder and duplicate frames.
  Evidence level **E5** (short sequence converted) and beyond.
- **biofilm PIV** (Zenodo 1175014, CC-BY-4.0). Downloaded and verified against its pinned
  SHA-256 (`107ba492…`). A time-averaged shear control (see
  `SECOND_EXTERNAL_SOURCE_REPORT.md`).

## Security and resource limits (offline-tested)

`IngestionLimits` caps raw file size, grid cells, frame count and variable count. Unit
tests (`tests/test_mission7.py`) exercise the rejections: non-finite values, non-monotone
coordinates, duplicate frames, and the frame/grid-cell caps. Normal CI never touches the
network; it runs the pipeline on a synthetic fixture only.

**Verdict: H49 supported** on genuine external data (JHTDB + biofilm); the cylinder Re≈3900
target specifically remains **blocked**.
