# Security, robustness, and performance audit

Audit date: 2026-07-19. Scope: public V29 facade/core, command entry points,
oracle generation, validation tooling, dependencies, and reduced representative
simulation. Environment: Linux 6.8.12-tegra aarch64, CPython 3.12.3, NumPy
2.5.1, SciPy 1.18.0, Matplotlib 3.11.0.

## Robustness findings and corrections

| Area | Initial risk | Correction / disposition |
|---|---|---|
| NaN and infinity | High: some early zero-field branches could bypass previous-field/time checks | Current/previous vorticity, velocities, curvature, coordinates, transport stages, transforms, geometry, weights, lengths, spacings, and time grids are validated as finite where required |
| Shapes and empty/small axes | High: mesh/field assumptions were not uniformly enforced | Meshes must be matching Cartesian 2D arrays; current operators require at least three points per direction; cubic transport requires four; engine field outputs must match the mesh |
| Coordinate monotonicity | High for derivatives/interpolation | Rectilinear and periodic axes must be finite and strictly increasing; periodic/uniform transforms additionally verify uniform spacing |
| Spacing and duration | High for division and derivatives | Negative/zero/non-finite spacing and nonpositive/non-finite intervals are rejected; time samples must be strictly increasing |
| Dtype conversion | Medium | Numerical inputs are deliberately converted to `float64`; integer arrays therefore enter floating algorithms without in-place integer truncation. This conversion is documented. Complex-valued fields are outside the real-valued API contract |
| Curvature exponential | High for overflow | Non-finite curvature is rejected and the computed exponential weight must remain finite |
| Output replacement | Medium | Oracle generation uses exclusive creation by default, refuses symbolic-link destinations, and requires explicit `--force` for atomic replacement. Main report generation intentionally replaces its fixed, documented output filenames in the selected working directory |
| Path traversal | Medium for fixture tools | The oracle accepts a path explicitly chosen by the local caller, never creates parent directories, and refuses symlink writes. It is not a network-service path sandbox; an embedding service must restrict destinations itself |
| Global plotting state | Medium | Matplotlib and `Agg` backend selection moved to plotting entry-point execution. Importing `itd_v29` does not initialize Matplotlib |
| Thread nondeterminism | Medium | Validation and CI set Python hash and numerical-library thread controls explicitly |
| Resource exhaustion | Context dependent | No arbitrary grid cap was added to the mathematical core. Network/service entry points must impose configurable memory, CPU, output, and timeout quotas |
| Commit provenance | Repository integrity | CI checks new ranges for prohibited automated-authorship trailers and requires the declared Tarek Zekriti author/committer identity |

The main plotting command has deterministic, fixed output names and overwrites
them on rerun; this is preserved command behavior and is clearly documented.
Run from a temporary directory when existing reports must not be replaced.

## Dependency audit

Command:

```bash
pip-audit -r requirements-dev.lock --progress-spinner off
```

Result on 2026-07-19: **No known vulnerabilities found**. This is a
time-bounded query against the vulnerability data available to `pip-audit`
2.10.1, not a guarantee that the dependency set has no undisclosed issue.

GitHub private vulnerability reporting, Dependabot security updates, secret
scanning, and push protection were observed disabled at audit time. Source
policy is supplied in `SECURITY.md`; enabling repository-host settings remains
an owner/administrator decision.

## Performance method

Optimization was considered only after measurement. Import timing used seven
fresh child processes and the same locked interpreter. The pre-change tree was
exported from commit `05ba06df462e8dfc39b7a00f89b52e097fa2f3b1`; the current
tree was measured with identical assertions.

| Probe | Before | After | Interpretation |
|---|---:|---:|---|
| Median `import itd_v29`, 7 processes | 0.468020 s | 0.130679 s | 72.1% lower wall time after deferring Matplotlib; before loaded Matplotlib, after does not |
| Reduced 41×41 grid, 41 times, multi-vortex cProfile total | 0.028 s | 0.028 s | Core numerical path unchanged within measurement resolution |
| Reduced scenario steady-state median, 7 runs (current) | not used as a cross-tree claim | 0.020264 s | Reference for future audits |

The reduced scenario reported intensity `0.6001624039770418`, structure
`0.5912061532148405`, and coupled diagnostic `0.9543438405799598`.

The current cProfile recorded 20,269 calls in 0.028 s. Dominant cumulative
locations were `structural_metrics` (0.014 s), `spatial_mean` (0.009 s), the
multi-vortex field (0.005 s), trapezoidal quadrature (0.005 s), and gradients
(0.005 s). These are clear vectorized NumPy operations. No opaque loop rewrite,
cached interpolation-plan change, or numerical reordering was justified by the
profile, so none was made.

## Remaining risks

- Exact dependency versions are pinned but distribution hashes are not.
- Binary64 last bits may vary across CPUs, operating systems, and library
  builds; cross-environment claims remain tolerance-based.
- The core intentionally permits caller-sized allocations.
- Python callables passed as model fields are trusted executable code.
- The temporal deformation aggregation is time-unit-sensitive unless callers
  nondimensionalize time.
- No licence or external-contribution agreement has been selected.
- Host-level private vulnerability reporting and security automation require an
  owner setting change outside this source branch.
