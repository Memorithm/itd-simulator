# Mission 8 reproduction bundle

Lets an independent user reproduce the Mission 8 structural/topological results. It never
commits third-party raw data; it commits **provenance and checksums** plus the exact
commands to regenerate the data legally from its authoritative source.

## ⚠️ Read this before interpreting the offline run

The offline fixture campaign prints verdicts like:

```
mission8 validate: h61=supported within tested scope h62=supported within tested scope ...
```

**These are NOT the mission's findings — they are the opposite of them.** The offline
fixture is a *manufactured* two-vortex merger oracle: a clean, noise-free, unambiguous
event that is trivially predictable by design, so ITD "succeeds" on it. Its only purpose
is to prove the code path runs deterministically end to end. Every result JSON it produces
is tagged `"evidence_class": "synthetic-code-verification (NOT external evidence)"`.

The actual scientific result comes from the **real JHTDB data** (steps 4-7 below) and is a
clean negative:

| | established | ITD-only | augmented | added value |
|---|---|---|---|---|
| real external holdout | 0.519 | **0.246** (below chance) | 0.344 | **−0.168**, CI [−0.175, −0.153] |

H61 and H62 are **not supported** on real data. See
`docs/research/EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md` and
`docs/research/MISSION8_FINAL_REPORT.md`.

## Contents

| file | purpose |
|---|---|
| `environment.txt` | Python / NumPy / Rust versions used |
| `commands.sh` | end-to-end driver (offline steps 1-3; network steps 4-7) |
| `expected_checksums.txt` | canonical digests of the offline fixture results (determinism proof) |
| `source_manifest.jhtdb.json` | provenance + per-frame SHA-256 for all six real sequences (152 frames) |

## Offline reproduction (no network — this is what CI runs, `run_validation.sh` step 27)

```bash
PYTHONHASHSEED=0 PYTHONPATH=$PWD \
  python -m itd_research.mission8 validate --config configs/mission8/ci.toml --output /tmp/m8
```

Then check the canonical digests against `expected_checksums.txt` (step 3 of
`commands.sh`). `tests/test_mission8.py` asserts these same digests, so the published
checksums cannot silently drift from the code.

### What "deterministic" means precisely here

The digest is computed by `itd_research.mission8.campaign.canonical_result_digest`, which
strips the fields declared in `NONDETERMINISTIC_FIELDS`: the `environment` block and the
three **wall-clock timings** (`full_p95_ms`, `profile_p95_ms`, `speedup`) produced by the
H74 profile benchmark. Those genuinely vary between runs and between machines.

Everything else — every verdict, AUC, correlation, CI bound and statistic — is required to
be **bit-identical**, and `test_full_validation_is_deterministic_except_for_wall_clock_timings`
asserts both directions: identical after stripping, and *actually differing* before it, so
the strip-set cannot be quietly widened to mask a real determinism defect.

## Network reproduction (needs outbound HTTPS; never runs in CI)

Run `bash repro/mission8/commands.sh` and follow the printed network steps. Six sequences
(152 frames total) regenerate via `tools/datasets/fetch_jhtdb_cutout.py`; verify them
against `source_manifest.jhtdb.json`.

The primary evaluation uses the **locked** split (`evaluations_allowed = 1` in the
preregistration): development `iso_run1`, `iso_run2`; holdout `iso_topo`, `iso_run3`.

## Data provenance and licences

- **JHTDB isotropic1024coarse** and **JHTDB mhd1024** — Johns Hopkins Turbulence Database.
  Respect the JHTDB terms of use and citation policy (https://turbulence.pha.jhu.edu). The
  public testing token permits small queries. Raw cutouts are **not** committed.
- Both sources are JHTDB, so any cross-source result is **within-institution
  cross-physics** (isotropic hydrodynamic → forced MHD), never a cross-institution claim —
  see `docs/research/CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT.md`.

## Known reproduction caveats

- The two MHD sequences contain **zero** qualifying topology events under the corrected
  event definition, so H65 is inconclusive by event scarcity, not by transfer failure.
  A re-fetch reproduces that same absence.
- The event detector was corrected mid-mission (a transient one-frame blip previously fired
  a spurious event on recovery). All numbers here are post-fix; pre-fix numbers appear only
  in `docs/research/MISSION8_REPRODUCIBILITY_REPORT.md`'s before/after table.
