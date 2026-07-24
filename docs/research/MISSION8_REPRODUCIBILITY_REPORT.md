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
(`nodes=24`) synthetic oracle in ~10-30 seconds, deterministically. Two consecutive runs
produce identical output (`tests/test_mission8.py::
test_run_fixture_campaign_is_deterministic_across_runs`, NaN-aware comparison). This is
CODE-VERIFICATION only, explicitly labelled `"synthetic-code-verification (NOT external
evidence)"` in every fixture-campaign report — never mixed with, or presented as, the
real JHTDB results above.

## What is NOT reproducible without network access

All real-data numbers in this mission's reports depend on the fetched JHTDB
isotropic1024coarse and mhd1024 cutouts (`docs/research/MISSION8_DATASET_INVENTORY.md`),
which are not committed to the repository (per the established pattern from Missions
6/7) and must be re-fetched via the manual dataset-acquisition workflow to reproduce
byte-for-byte. The ingestion/checksum/provenance machinery (Mission 7's, reused
unchanged) guarantees that a re-fetch of the same JHTDB cutout coordinates reproduces the
same frames.

## Test coverage this mission

40 tests in `tests/test_mission8.py` + 13 in `tests/test_mission8_oracles.py` (53 total),
plus all 18 Mission 8 modules added to `tests/test_research_boundaries.py`'s import-safety
and one-way-dependency checks (117 boundary tests total, all passing). All 53 Mission-8-
specific tests pass; the full repository test suite and `run_validation.sh` were run
before any commit (see `MISSION8_FINAL_REPORT.md`).
