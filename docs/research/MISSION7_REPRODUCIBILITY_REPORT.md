# Mission 7 reproducibility report (H59)

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Does not modify
`ITD V29.18`.

## The reproduction bundle

`repro/mission7/` provides a complete public reproduction path that commits **no** third-
party raw data:

| artifact | content |
|---|---|
| `README.md` | offline + network reproduction instructions |
| `environment.txt` | Python 3.11.15, NumPy 2.3.5, Rust 1.94.1 (and the exact tool versions) |
| `commands.sh` | end-to-end driver: verify env → offline fixture → (network) fetch → run → compare |
| `expected_checksums.txt` | SHA-256 of the offline fixture campaign JSON |
| `source_manifest.jhtdb.json` | provenance + per-frame SHA-256 of the real JHTDB sequence |
| `small_public_subset_manifest.json` | exact command + checksums to regenerate the tiny subset |

## Offline determinism (verified)

The offline synthetic-fixture campaign
(`python -m itd_research.mission7 validate`) is **deterministic**: two independent
subprocess runs produced byte-identical campaign JSON (environment block excluded), pinned
in `expected_checksums.txt`. This runs in bounded CI (`run_validation.sh` step 26) with no
network.

## Network reproduction (documented, not committed)

The JHTDB short sequence and the biofilm PIV control are regenerated from their authoritative
sources with the exact commands in `commands.sh` / `README.md`; the fetched frame checksums
must match `source_manifest.jhtdb.json`. Raw data is never committed; where a source forbids
redistribution, only instructions and checksums are provided.

**Verdict: H59 supported** — an independent user can reproduce the offline result exactly
(checksum-matched) and the external result from the documented commands and public data.
Independent *replication on a second environment* is covered separately in
`INDEPENDENT_REPLICATION_REPORT.md`.
