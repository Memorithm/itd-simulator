# Mission 8 reproducibility report

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Determinism protocol

`PYTHONHASHSEED=0`, single-thread BLAS (`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=
MKL_NUM_THREADS=1`), float64 throughout, `numpy.random.default_rng(seed)` for every
stochastic step (bootstrap seed `6161` per the preregistration; noise/mask oracle seeds
fixed and documented in `fixtures.py`/`degradation.py`). Environment this session: Python
3.11.15, NumPy 2.3.5.

## A bug found, fixed, and reconciled before any report was written

`itd_research.mission8.vortex_regions.detect_topology_events`'s persistence rule only
checked that the **post**-change region count persisted, letting a one-frame count blip
that reverts fire a spurious event at the recovery point (see
`STRUCTURAL_EVENT_LABEL_REPORT.md` for the full mechanism and the regression test that
pins it: `tests/test_mission8.py::
test_detect_topology_events_requires_sustained_change_not_a_transient_blip`). The fix
requires the pre-change value to have also been stable for `persistence` frames.

**This changed the ground-truth event labels for every real sequence** (see the before/
after event counts below), which in turn changed the numbers in
`EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md`, `PARTIAL_OBSERVATION_STRUCTURAL_REPORT.md`,
`EXTERNAL_TOPOLOGY_VALIDATION_REPORT.md`, and `CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT.md`.
Per the preregistration's `evaluations_allowed = 1` rule, the primary holdout evaluation
was re-run **exactly once** on the corrected code, before any interpretive report was
drafted — this is a measurement-definition correction made in the same spirit as the
H61-verdict computation fix made earlier in this mission (see `prediction.py`'s history),
not a search for a more favorable result. The qualitative conclusion (ITD structural
channels do not add value, and actively hurt when combined) is **unchanged** by the fix;
only the specific AUC/added-value numbers moved.

| sequence | events before fix | events after fix |
|---|---|---|
| `iso_run1` | 5 | 2 |
| `iso_run2` | 4 | 1 |
| `iso_topo` | 4 | 1 |
| `iso_run3` | 2 | 0 |
| `mhd_topo` | not computed pre-fix | 0 |
| `mhd_topo_run2` | not computed pre-fix | 0 |

The 13 manufactured-oracle tests (`tests/test_mission8_oracles.py`) are **unaffected** by
the fix — the oracle sequences (B/C) use a clean step transition with no reverting blip,
so they never exercised the bug either way.

## What is reproducible offline (no network)

`python -m itd_research.mission8 validate --config configs/mission8/ci.toml --output ...`
runs the full module set (saturation screen + H61/H62, H64/H70/H71 descriptive checks,
H73 structural OOD, one profile benchmark) on a manufactured, resolution-honest
(`nodes=24`) synthetic oracle in ~10-30 seconds. This is CODE-VERIFICATION only,
explicitly labelled `"synthetic-code-verification (NOT external evidence)"` in every
fixture-campaign report — never mixed with, or presented as, the real JHTDB results above.
Its verdicts are *easier* than the real-data ones by construction (a clean manufactured
merger is trivially predictable), so they must never be quoted as findings; the
reproduction bundle's README states this prominently.

### Determinism, stated precisely (corrected)

An earlier draft of this report claimed "two consecutive runs produce identical output."
**That was too strong and is corrected here.** Building the reproduction bundle surfaced
the discrepancy: two consecutive full validations hash differently, because the H74
profile benchmark reports **wall-clock timings** (`full_p95_ms`, `profile_p95_ms`,
`speedup`), which legitimately vary run to run and machine to machine. The earlier claim
rested on `test_run_fixture_campaign_is_deterministic_across_runs`, which covers
`run_fixture_campaign` only — the primary campaign, which *is* fully deterministic — and
never exercised the benchmark-carrying full validation.

The precise, verified property is:

* **every scientific field is bit-identical** across runs — all verdicts, AUCs,
  correlations, CI bounds and statistics; and
* **only the three declared wall-clock fields differ**, plus the `environment` block.

This is enforced by `itd_research.mission8.campaign.canonical_result_digest`, whose
`NONDETERMINISTIC_FIELDS` set is the single shared definition used by both the pinned
checksums in `repro/mission8/expected_checksums.txt` and the tests, so the two cannot
drift apart. `test_full_validation_is_deterministic_except_for_wall_clock_timings` asserts
**both** directions — identical after stripping, and genuinely differing before it — so
the strip-set cannot later be widened to mask a real determinism defect, and
`test_published_reproducibility_digests_match_the_repro_bundle` fails if any code change
alters a scientific output without the published digest being deliberately re-pinned.

Canonical digests (this environment):

```
mission8_fixture_campaign.canonical   f75969f06f0dcaea057cfa1ac933e185ea490e1e286609a290e6bb1ad678757c
mission8_full_validation.canonical    7220974dd51c5389b6446137e8cef5aab09d2ab85f4c17ea3e7f803a44f5d324
```

## What is NOT reproducible without network access

All real-data numbers in this mission's reports depend on the fetched JHTDB
isotropic1024coarse and mhd1024 cutouts (`docs/research/MISSION8_DATASET_INVENTORY.md`),
which are not committed to the repository (per the established pattern from Missions
6/7) and must be re-fetched via the manual dataset-acquisition workflow to reproduce
byte-for-byte. The ingestion/checksum/provenance machinery (Mission 7's, reused
unchanged) guarantees that a re-fetch of the same JHTDB cutout coordinates reproduces the
same frames.

## Reproduction bundle

`repro/mission8/` follows the Mission 7 pattern: `README.md`, `commands.sh` (offline steps
1-3, network steps 4-7), `environment.txt`, `expected_checksums.txt` (the canonical
digests above), and `source_manifest.jhtdb.json` — provenance plus per-frame SHA-256 for
**all six real sequences (152 frames)**, so a re-fetch can be verified frame by frame. Raw
JHTDB data is not committed, per the repository's established practice.

## Test coverage this mission

29 tests in `tests/test_mission8.py` + 13 in `tests/test_mission8_oracles.py` — **42
Mission-8-specific tests**, all passing — plus all 18 Mission 8 modules added to
`tests/test_research_boundaries.py`'s import-safety and one-way-dependency checks. The
full repository suite and `run_validation.sh` were run before any commit (see
`MISSION8_FINAL_REPORT.md`).

*Correction:* an earlier draft of this report stated "40 tests in `tests/test_mission8.py`
+ 13 … (53 total)". That was a miscount — 40 was the *combined* total across both files
(27 + 13), not the count of the first file alone. The figures above are verified by
`pytest --collect-only` and include the two determinism/digest tests added with the
reproduction bundle (27 → 29).
