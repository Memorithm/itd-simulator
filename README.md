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

## Research status: one line closed, AI laboratory open

The **Missions 3–8 fluid-diagnostic research line is CLOSED** — see
[`RESEARCH_CLOSURE.md`](RESEARCH_CLOSURE.md). It asked whether the existing ITD
channels provide diagnostic or predictive information about fluid-dynamic
structure that competent established diagnostics do not already capture. On the
external tests performed, the answer was negative; on the preregistered
unsaturated Mission 8 task, adding ITD's non-magnitude channels changed held-out
performance by **−0.168 (95 % CI [−0.175, −0.153])**.

That conclusion is intentionally preserved. It does **not** close distinct
questions about artificial intelligence or scientific machine learning. The
repository is now also an open experimental laboratory for falsifiable research
on representation value, auxiliary supervision, learned spatial and multiscale
structure, forecasting, anomaly/change detection, OOD and abstention, control,
compression/resource-aware AI, and later additional signal domains. The research
rules and ecosystem boundaries are defined in
[`docs/ai/AI_RESEARCH_CHARTER.md`](docs/ai/AI_RESEARCH_CHARTER.md).

The goal of the AI line is not to prove that ITD works. Every study must permit a
negative result and compare against competent established and learned controls.
`ITD V29.18` remains frozen unless a separate scientific-revision process ever
justifies changing it.

## Historical post-V29 fluid research namespace

`itd_research/` is an isolated research namespace layered on top of the
certified, immutable `ITD V29.18` baseline. Its Missions 3–8 material studies a
dimensionless reformulation of temporal deformation, analytical/manufactured
benchmarks, established-diagnostic comparisons, convergence and sensitivity,
and external validation. That fluid-diagnostic programme is historical evidence,
not an open backlog to rerun.

The infrastructure remains reusable: manufactured oracles, saturation screening,
grouped statistics, provenance/reproduction bundles, degradation tests, and OOD
machinery can support new hypotheses when their domain assumptions remain valid.
Future AI work must remain isolated from the certified core with the same one-way
dependency principle.

For the historical deterministic research suite:

```bash
python -m itd_research --quick --output /tmp/itd-research-quick
python -m itd_research --full  --output /tmp/itd-research-full
```

The historical specifications, oracle derivations, and results are in
[`docs/research/`](docs/research/).

## Ecosystem direction

ITD Simulator should reuse rather than duplicate validated scientific capabilities
from the wider ecosystem. SciRust is the preferred source of relevant scientific
algorithms when appropriate to a study. ElasticXxx is a natural downstream
research target for experiments about adaptive observation, representation,
precision, memory, model choice, and controlled resource decisions. These
relationships do not make ITD results automatically valid SciRust primitives or
ElasticXxx runtime policies; each integration requires its own evidence and
architectural review.

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

The source is dual-licensed: the **PolyForm Noncommercial License 1.0.0**
([`LICENSE`](LICENSE)) permits noncommercial and personal use, while **any
commercial use requires a separate written commercial licence** from the
copyright holder, Tarek Zekriti (zekrititarek@gmail.com). Public visibility does
not itself grant commercial rights. See [`LICENSING.md`](LICENSING.md) and the
consequences summary in [`docs/license_decision.md`](docs/license_decision.md).
