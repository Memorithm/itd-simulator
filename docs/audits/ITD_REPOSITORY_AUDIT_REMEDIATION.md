# ITD repository audit remediation

Audit and remediation date: 2026-07-19

- Repository: `https://github.com/Memorithm/itd-simulator`
- Working clone: `/root/itd-simulator-publish`
- Branch: `audit/v29-repository-hardening`
- Scientific model: **ITD V29.18**
- Software source version: **0.2.0**

## Outcome

All technical remediation findings were implemented without changing the
certified V29.18 summary. In the declared CPython 3.12 / NumPy 2.5.1 reference
environment, the generated `itd_v29_results/summary.csv` remains byte-for-byte
equal to the tracked reference with SHA-256
`119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b`.

The sole unresolved owner decision is the software licence. No licence was
invented, no `LICENSE` was added, and package licence metadata remains absent.

## Initial repository state

The supplied `/root/itd-simulator` path was not the project Git checkout; it was
an untracked development directory under an unrelated empty `/root/.git`. To
avoid endangering that unrelated state, work continued in the explicitly
provided publication clone `/root/itd-simulator-publish`.

The publication clone was clean but ten commits behind. It was fetched and
fast-forwarded without rewriting history:

- initial local `main`: `988aed2`;
- audited `origin/main`: `05ba06df462e8dfc39b7a00f89b52e097fa2f3b1`;
- audit branch point: `05ba06df462e8dfc39b7a00f89b52e097fa2f3b1`;
- current scientific tag `v29.18` commit:
  `4896cac9f312e0008ecf5c78058f9e1508a392f2`;
- published software tag `v0.1.1` commit:
  `478f812f5abb1ea9c6e9be3e04a623d7d11d2b8e`.

Inventory found the modular `itd_v29_core/` implementation, thin V29 facade,
V10 and many numbered historical scripts, result/certification documents,
`oracle_harness.py`, a partial `MANIFEST.sha256`, and one V10-only GitHub
Release. It found no packaging metadata, pytest suite, workflow, licence,
governance files, or current V29-first validation entry point.

The public `0.1.1` GitHub Release contains
`itd-simulator-0.1.1.tar.gz` and its checksum asset. The downloaded archive
verified as
`af323367f804853ebf980e0805d2127714b7f5971abb3d0848d375b4931ba00e`
and contains V10 material, not V29. There is no public V29.18 GitHub Release
artifact.

## Baseline evidence before modification

With the repository's exact declared NumPy 2.5.1, SciPy 1.18.0, and Matplotlib
3.11.0 pins on CPython 3.12.3:

- the tracked V29.18 summary reproduced exactly;
- the oracle generated 260 lines / 50,203 bytes before its contract header was
  expanded;
- the only runnable general historical release validator was
  `validate_release_v10.py`, which exercises the separate V10 implementation;
- `import itd_v29` initialized Matplotlib and selected a backend;
- the old `run_validation.sh` compiled and ran only V10 files;
- the README simultaneously advertised software 0.1.1, model 29.18 elsewhere,
  and a V10 run command;
- the manifest's listed digests were valid but its scope was incomplete and
  contained duplicate paths.

A global, unpinned environment produced a last-bit summary difference, while
the declared pins reproduced the certified file exactly. This established that
dependency/environment scoping must remain part of every numerical claim.

## Finding-by-finding remediation

| # | Finding | Severity | Exact correction | Principal files |
|---:|---|---|---|---|
| 1 | README/version mismatch | High | Separated software `0.2.0` from scientific `ITD V29.18`, made V29 the default, and labelled 0.1.1/V10 as the latest historical published release | `README.md`, `VERSION`, `MODEL_REVISION`, `MODEL_STATUS.md`, `CHANGELOG.md` |
| 2 | Official validation was V10-only | Critical | Replaced the default with strict V29 compilation, pytest, architecture, deterministic process, full simulator summary, manifest, oracle, and cleanliness checks; V10 is optional and explicitly V10-only | `run_validation.sh`, `tools/check_v29_summary.py`, `tools/deterministic_smoke.py` |
| 3 | No GitHub Actions CI | High | Added push/PR CI for Python 3.11, 3.12, and 3.13 with pinned actions, deterministic variables, locked install, compile/lint/type/validation/audit/cleanliness/policy checks, and failure artifacts | `.github/workflows/ci.yml` |
| 4 | No focused current test suite | High | Added 56 deterministic tests spanning analytical invariants, malformed input, material/periodic geometry, simulation, public API identity/architecture, oracle, and independent processes | `tests/` |
| 5 | Weak Python-to-Rust oracle workflow | High | Added reviewed fixture, tolerant structural `--check`, exclusive default output, explicit atomic `--force`, symlink refusal, revision/layout headers, and snapshot-versus-proof contract | `oracle_harness.py`, `tests/fixtures/oracle_data.rs`, `docs/rust_oracle_contract.md` |
| 6 | No modern packaging | Medium | Added setuptools `pyproject.toml`, package namespace, module/console commands, Python range, dependencies, author, and build manifest without disrupting `import itd_v29` | `pyproject.toml`, `MANIFEST.in`, `itd_simulator/` |
| 7 | Numerical import forced plotting backend | Medium | Deferred Matplotlib/backend imports to plotting `main()` functions; numerical import no longer initializes plotting | `itd_v29_core/entrypoint.py`, `compare_scenarios.py`, `itd_v29.py` |
| 8 | Public API was implicit | High | Added explicit stable/advanced/legacy categories and `__all__`; retained direct object identities and zero facade function definitions | `itd_v29.py`, `itd_simulator/__init__.py`, `tests/test_public_api.py` |
| 9 | Dependency reproduction was ambiguous | High | Added compatible project ranges and exact interpreter-aware runtime/development lock files with an update workflow and explicit no-hash limitation | `pyproject.toml`, `requirements.txt`, `requirements.lock`, `requirements-dev.lock`, `docs/reproducibility.md` |
| 10 | No lint/static policy | Medium | Configured Ruff correctness/import/modernization checks with frozen historical exclusions and incremental mypy for new tools; no scientific expression formatter was imposed | `pyproject.toml`, CI |
| 11 | Scientific/architecture documentation incomplete | High | Documented intensity, five raw/bounded components, dimensions, boundaries, time integration, material/Eulerian distinction, multiscale scaling, frames, interpolation, limitations, and non-universality | `docs/scientific_definition.md`, `docs/numerical_methods.md`, `docs/architecture.md` |
| 12 | Governance/citation absent | Medium | Added single-maintainer contribution rules, security process, changelog, and CFF citation naming only Tarek Zekriti; omitted a code of conduct because external code contributions are not yet accepted | `CONTRIBUTING.md`, `SECURITY.md`, `CITATION.cff`, `CHANGELOG.md` |
| 13 | No licence selected | Critical legal decision | Preserved all-rights-unclear status and prepared an option/consequence comparison; no licence text or metadata was fabricated | `docs/license_decision.md` |
| 14 | Release hash lacked context | High | Verified the real V10 asset and replaced the isolated hash with artifact/tag/commit/manifest context; explicitly records that no V29 release asset exists | `README.md`, `docs/release_integrity.md` |
| 15 | Future prohibited trailers not enforced | Medium | Added new-range checks for the named forbidden trailers and exact Tarek Zekriti author/committer identity; historical commits are untouched | `tools/check_commit_messages.py`, CI, `CONTRIBUTING.md` |
| 16 | Input/security robustness gaps | High | Added finite/shape/mesh/callable/length/time/period checks, correct float conversion, output protections, deterministic thread policy, and explicit entrypoint resource responsibility | core modules, oracle, tests, `SECURITY.md`, `docs/security_performance_audit.md` |
| 17 | Performance had not been measured | Medium | Profiled first, removed plotting import cost, reprofiled numerical work, and rejected unjustified numerical rewrites because core runtime was unchanged | plotting boundary changes, `docs/security_performance_audit.md` |

## Source corrections

The compatibility facade now has zero `FunctionDef`/`AsyncFunctionDef` nodes,
111 unique deliberate exports, and direct identities with source modules. AST
tests prove no core module imports the facade. Numerical modules validate
matching real meshes, velocity/curvature output shapes, finite fields,
strictly-positive spacing and intervals, strictly-increasing axes/times,
orthogonal transforms, positive periods, and safe structural state pairing.

No expected V29 scientific value was edited. Input hardening and plotting
separation preserve valid V29.18 calculation order and outputs.

## Tests added

- `test_spatial_operators.py`: constant-field gradient, constant-velocity
  vorticity, finite/shape/spacing rejection, bounded-map input contract.
- `test_structural_metrics.py`: zero/constant/identical-field invariants,
  interval pairing, invalid shape and non-finite rejection.
- `test_periodic_transport.py`: node interpolation, full-period translation,
  local bounds, and discrete-sum preservation tolerance.
- `test_geometry.py`: identity, orthogonal norm, exact node map, axis and mesh
  validation.
- `test_material_deformation.py`: zero tendencies/rates, hand-derived interval
  interpolation, duration/shape/finite rejection.
- `test_simulation_engine.py`: hand-derived solid-rotation intensity of 4,
  zero-field outputs, callable/mesh/field-output failures.
- `test_public_api.py`: zero facade definitions, direct object identity,
  categorized API uniqueness, no reverse imports, no Matplotlib initialization.
- `test_oracle_harness.py`: committed fixture equivalence, mismatch detection,
  no implicit overwrite.
- `test_determinism.py`: byte-identical reduced results from two independent
  processes under the deterministic environment.

## Validation commands and results

Reference environment variables were:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONHASHSEED=0
OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
MKL_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
```

| Command | Result |
|---|---|
| `python -m compileall -q` over facade/package/core/tools/tests | Passed |
| `pytest -q` | **56 passed** |
| `ruff check .` | Passed, no findings |
| focused `mypy` tool checks | Passed, no findings |
| `tools/test_dependency_analyser.py` | **22 passed, 0 failed** |
| two independent `tools/deterministic_smoke.py` processes | Byte-identical |
| full `itd_v29.py` summary comparison | Exact; both files SHA-256 `119b4d…` |
| `tools/check_manifest.py` | Passed for 184 tracked files before this report was added; final count is regenerated below |
| oracle generation plus `--check` | Passed |
| `./run_validation.sh` | **ITD V29.18 validation: PASSED** |
| tracked status before/after validator | Identical |
| `python -m pip check` | Passed |
| package sdist/wheel build | Passed |

The complete integration log is preserved during execution at
`/tmp/itd-remediation-validation/run-validation.log`; CI provides durable
failure artifacts for remote runs.

## Dependency audit

`pip-audit 2.10.1 -r requirements-dev.lock --progress-spinner off` reported:

```text
No known vulnerabilities found
```

This result is time-bound to the advisory data available on 2026-07-19. Exact
versions are pinned, but distribution hashes are not yet recorded.

## Performance measurements

Platform: Linux aarch64, CPython 3.12.3. Seven independent import processes
gave a median of 0.468020 s at the audited base commit and 0.130679 s after lazy
plot imports, a 72.1% reduction. The prior import loaded Matplotlib; the current
import does not.

The representative 41×41, 41-time multi-vortex cProfile was 0.028 s both before
and after, with 20,269 calls in the current run. Current steady-state median
over seven runs was 0.020264 s. Dominant cumulative work was structural metrics
(0.014 s), spatial means (0.009 s), scenario field generation (0.005 s),
trapezoidal operations (0.005 s), and gradients (0.005 s). No numerical
optimization was made because the profile did not justify calculation-order or
clarity risk.

## Commits

Every commit has author and committer
`Tarek Zekriti <194770978+CHECKUPAUTO@users.noreply.github.com>` and contains no
automated-authorship trailer.

| SHA | Subject |
|---|---|
| `5ebbd46203444424e65f3aa63ef6450d11390b6c` | `docs: align software and scientific versions` |
| `14f3832af6f9c25bd42bf44a9d270cf351844afc` | `refactor: harden the V29 public numerical boundary` |
| `810938c6c9daf2bbbb6c992c8f0607481551a282` | `test: add V29 validation and oracle contracts` |
| `699108ebed34b0ad06912f374180d1c009f326c4` | `build: add packaging reproducibility and CI` |
| `1032cb97dad238de8afaeee7e49e8fcf486760a5` | `docs: define scientific and project governance contracts` |
| `81e278b2d7145b600e4c060ae0c0a5dc7e189c04` | `docs: record audit remediation and manifest` |
| `a86fcebd1ee28689b8bb386cb3f5faf5088429a0` | `ci: scope provenance and numerical checks` |
| `0278f7e92caa89180d7260660dcc9319e1af387c` | `ci: inspect pull request head commits only` |

The final publication-evidence update is necessarily this document's
containing commit, so its SHA cannot be embedded in its own content without
changing that SHA. The pull request head records it unambiguously.

## Pull request and publication status

Draft pull request: **[#9](https://github.com/Memorithm/itd-simulator/pull/9)**.

The first CI observation exposed two legitimate workflow-contract issues: an
all-zero `before` SHA on a new-branch push caused old public history to enter
the commit-policy range, and NumPy version alone was insufficient to infer
cross-architecture bitwise equality. A second PR-only observation showed that
GitHub checks out a synthetic merge commit. Commits `a86fceb` and `0278f7e`
scope first pushes to the default-branch merge base, inspect the actual PR head,
and make exact numerical comparison an explicit reference-environment opt-in.

Replacement GitHub Actions runs completed successfully:

- push run
  [`29695503764`](https://github.com/Memorithm/itd-simulator/actions/runs/29695503764):
  Python 3.11, 3.12, 3.13, dependency audit, cleanliness, and commit policy all
  passed;
- pull-request run
  [`29695505177`](https://github.com/Memorithm/itd-simulator/actions/runs/29695505177):
  the same complete matrix and policy passed.

The superseded failed runs remain visible as audit evidence; they were not
rerun or ignored without correction.

No tag or GitHub Release is created by this remediation. The 0.2.0 release
metadata, immutable asset hashes, and legal licence status are not yet all
owner-approved.

## Remaining risks

- No software licence or external contribution-rights policy is selected.
- Dependency versions are exact, but wheel/sdist hashes are not locked.
- Cross-platform binary64 results remain tolerance-scoped; bitwise stability is
  claimed only inside the same declared environment.
- Temporal deformation is time-unit-sensitive unless the caller
  nondimensionalizes time.
- The mathematical core intentionally has no arbitrary allocation cap; exposed
  services must configure their own quotas/timeouts.
- User-supplied Python field callables execute with process privileges.
- Main report generation intentionally replaces fixed documented output files
  in its working directory.
- GitHub private vulnerability reporting, Dependabot security updates, secret
  scanning, and push protection were observed disabled and require an owner
  repository-setting decision.
- Historical validators depending on absent predecessor monoliths remain
  provenance material, not executable V29 certification.

## Decisions requiring owner approval

1. **Licence (required):** choose Apache-2.0, MIT OR Apache-2.0,
   proprietary/all-rights-reserved, or a defined dual-licensing model. See
   `docs/license_decision.md`.
2. **Recommended host security settings:** enable private vulnerability
   reporting and decide whether to enable Dependabot and secret scanning.
3. **Release publication:** after merge and the licence decision, approve the
   exact 0.2.0 tag, artifacts, hashes, and release notes.

## Final repository status

All local technical checks pass, the canonical manifest covers 185 tracked
files, and the branch contains only intentional changes. The branch is pushed,
draft pull request #9 is open, and both replacement push and pull-request CI
runs are green. No tag, release asset, licence, or repository setting was
silently created or changed.
