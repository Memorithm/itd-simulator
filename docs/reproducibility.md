# Reproducibility

## Declared environment

The current validation targets CPython 3.11, 3.12, and 3.13 on Linux. The
scientific reference environment used to confirm the tracked V29.18 summary is
CPython 3.12, NumPy 2.5.1, SciPy 1.18.0, and Matplotlib 3.11.0. Python 3.11 uses
NumPy 2.3.5 and SciPy 1.17.1 because the newer releases require Python 3.12.

Every deterministic run sets:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
```

The thread limits prevent uncontrolled parallel reductions. They do not imply
bitwise equivalence across operating systems, CPUs, Python versions, or math
libraries.

## Dependency files

- `pyproject.toml` declares compatible runtime ranges and development extras.
- `requirements.lock` pins the resolved runtime and validation environment,
  with interpreter markers where compatibility differs.
- `requirements-dev.lock` adds exact test, lint, build, type-check, and audit
  tool versions.
- `requirements.txt` remains a compatibility include of `requirements.lock`.

These lock files pin versions but do not yet record distribution hashes.
Therefore they prevent silent version drift but do not provide byte-level
distribution provenance. Adding cross-platform generated hash locks is a future
hardening option; it must include every supported interpreter/platform wheel
and a documented resolver rather than a partial hash set.

## Creating the environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip==26.1.2
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
python -m pip check
```

## Validation sequence

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

python -m compileall -q .
pytest -q
ruff check .
./run_validation.sh
python itd_v29.py
python oracle_harness.py /tmp/oracle_data.rs
python oracle_harness.py --check tests/fixtures/oracle_data.rs
python tools/check_manifest.py
```

Run report-producing commands from a temporary working directory if the Git
checkout must remain byte-for-byte clean. `run_validation.sh` already does so
and compares tracked status before and after.

## Updating dependencies

1. Read upstream Python and wheel compatibility metadata for every direct
   scientific dependency.
2. Resolve and test all three supported Python versions in clean environments.
3. Update direct and transitive pins in both lock files together.
4. Run `python -m pip check` and `pip-audit -r requirements-dev.lock`.
5. Run the complete deterministic validation and compare the V29 summary and
   Rust oracle. Never change expected scientific values merely to accommodate a
   dependency update.
6. Record environment changes and any last-bit differences in `CHANGELOG.md`
   and the relevant audit/certification report.

## What is and is not certified

The tracked full-size summary is compared exactly in the NumPy 2.5.1 reference
environment and within `rtol=1e-13`, `atol=1e-14` elsewhere. The Rust fixture
comparison uses structural equality plus `rtol=1e-12`, `atol=1e-12` for float
literals. Independent-process reduced scenarios must be byte-identical inside
one environment.

These are bounded software contracts. They are not proof that the numerical
model is physically valid, universally invariant, or independent of all
floating-point environments.
