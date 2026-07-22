# ITD Simulator

Deterministic research simulator for curvature-weighted rotational intensity
and a five-component structural signature.

| Version dimension | Value |
|---|---|
| Software version in this source tree | `0.2.0` |
| Scientific model revision | `ITD V29.18` |
| Latest published GitHub software release | `0.1.1` (legacy V10) |

Software versions describe packaging and repository releases. Scientific model
revisions describe the numerical model. They are intentionally independent:
software `0.2.0` packages the unchanged scientific model `ITD V29.18`.

## Install

Python 3.11, 3.12, and 3.13 are tested. The exact resolved validation
environment is recorded in `requirements-dev.lock`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
```

## Run

Either current entry point runs V29.18:

```bash
python itd_v29.py
python -m itd_simulator
```

The command writes CSV summaries and plots beneath `itd_v29_results/` in the
current directory. Importing `itd_v29` alone does not initialize Matplotlib or
select a plotting backend.

`itd_v10.py` and `validate_release_v10.py` remain historical V10 material. They
do not certify V29.18.

## Validate

```bash
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
ruff check .
pytest -q
./run_validation.sh
```

The default validation compiles the current facade, package, core, tools, and
tests; runs the V29.18 pytest suite and dependency analyser; checks independent
process determinism; executes the full V29 simulator; verifies the public
manifest; generates the Rust oracle in a temporary file; compares it with the
reviewed fixture; and proves tracked files were not changed. The optional
`./run_validation.sh --legacy-v10` adds the separately labelled V10 validator.

## Model outputs

The two primary outputs are:

1. time-averaged curvature-weighted rotational intensity;
2. a five-component structural signature comprising heterogeneity,
   localization, roughness, sign mixing, and temporal deformation.

An explicitly weighted scalar structural score and an intensity/structure
coupling are experimental aggregations. They are not universal quantities.
Definitions and numerical conventions are in
[`docs/scientific_definition.md`](docs/scientific_definition.md) and
[`docs/numerical_methods.md`](docs/numerical_methods.md).

## Public API

`itd_v29.py` is a compatibility facade containing direct re-exports and no
scientific function definitions. Its explicit `__all__` separates stable,
advanced, and legacy compatibility names. The implementation is in
`itd_v29_core/`; `import itd_v29` remains supported. The packaged namespace
`itd_simulator` re-exports the same objects.

## Post-V29 research namespace

`itd_research/` is an isolated research namespace layered on top of the
certified, immutable `ITD V29.18` baseline. It studies a dimensionless
reformulation of temporal deformation, provides analytical/manufactured
benchmarks, established-diagnostic comparisons, convergence and sensitivity
runners, and hand-derived analytical oracles. It never modifies V29.18, is never
imported by `itd_v29_core`, and importing it does not initialize Matplotlib.

It is **not** a certified scientific revision; `MODEL_REVISION` remains
`ITD V29.18`. Run the deterministic research suite into an explicit directory:

```bash
python -m itd_research --quick --output /tmp/itd-research-quick
python -m itd_research --full  --output /tmp/itd-research-full
```

The specification, oracle derivations, and results are in
[`docs/research/`](docs/research/).

## Release integrity

The previously unexplained SHA-256 belongs specifically to the public V10
software `0.1.1` archive:

| Scientific revision | Software | Tag | Artifact | SHA-256 |
|---|---:|---|---|---|
| V10 | 0.1.1 | `v0.1.1` | `itd-simulator-0.1.1.tar.gz` | `af323367f804853ebf980e0805d2127714b7f5971abb3d0848d375b4931ba00e` |
| ITD V29.18 | 0.2.0 source | pending review | no public artifact | not applicable |

The full commit, manifest, and publication status are recorded in
[`docs/release_integrity.md`](docs/release_integrity.md). No V29.18 software
archive is claimed to exist.

## Scientific and legal status

This repository is an experimental mathematical and numerical research
prototype. Its results are relative to the declared algorithms, validators,
fixtures, tolerances, inputs, and execution environments. They do not establish
ITD as a validated physical observable, a universal complexity measure, an
entropy, or a replacement for Shannon information or established measures.

No software licence has been selected. Public visibility does not itself grant
permission to copy, modify, redistribute, or commercially reuse the source.
The owner decision and consequences are summarized in
[`docs/license_decision.md`](docs/license_decision.md).
