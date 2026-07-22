# Changelog

All notable repository and software changes are documented here. Scientific
model revisions and software package versions are separate dimensions.

## [0.2.0] - Unreleased

Scientific model revision: **ITD V29.18** (numerical behavior preserved).

### Added

- isolated `itd_research/` namespace for a post-V29 dimensional-validation
  research candidate: an explicit temporal-scale API (`external`,
  `observation_duration`, `turnover`, `vorticity_timescale` policies) that
  preserves the V29.18 raw temporal rate exactly and adds a dimensionless
  candidate `D* = tau_ref * D`; a deterministic analytical benchmark catalogue;
  established fluid-dynamics comparison diagnostics; grid-convergence and
  sensitivity/invariance runners; a `python -m itd_research` command with
  quick/full modes, overwrite-safe atomic CSV/JSON output, and a manifest;
- hand-derived analytical oracles (`tests/fixtures/analytical_oracles.json`) in
  a category strictly separate from the implementation-generated Rust snapshot;
- research documentation under `docs/research/` (specification, analytical
  oracle derivations, and the dimensional-validation report);
- focused research test suite and CI/validation coverage of the research quick
  suite (V29.18 behaviour unchanged);
- installable package metadata, `python -m itd_simulator`, and console entry
  point while retaining `import itd_v29`;
- focused analytical, API, oracle, robustness, and determinism pytest suite;
- V29-first defensive validation script and Python 3.11–3.13 GitHub Actions CI;
- exact dependency lock files, Ruff checks, incremental mypy checks, and
  dependency auditing;
- explicit public API categories and complete manifest verification;
- scientific, numerical, architecture, reproducibility, Rust oracle, licence,
  integrity, security/performance, governance, citation, and audit documents;
- non-destructive oracle check/regeneration workflow and commit-message policy.

### Changed

- separated software version `0.2.0` from scientific model revision
  `ITD V29.18`;
- made V29 the default run and validation target; V10 is explicitly historical;
- deferred Matplotlib imports and backend selection to plotting entry points;
- strengthened validation of meshes, shapes, finite values, intervals,
  transforms, interpolation inputs, and simulator callables.

### Fixed

- removed inconsistent V10 run instructions and contextualized the V10 archive
  SHA-256;
- replaced incomplete/duplicated manifest scope with a canonical full tracked
  file manifest;
- clarified that Python-generated Rust fixtures are regression references, not
  independent proofs.

## [0.1.1]

Published legacy V10 software release. Its public archive is documented in
`docs/release_integrity.md`.
