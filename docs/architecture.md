# Architecture

## Runtime layers

```text
itd_v29.py                    compatibility facade; direct re-exports only
itd_simulator/                package namespace and python -m entry point
itd_v29_core/                 current V29.18 numerical implementation
compare_scenarios.py          deterministic fields and shared configuration
itd_v29_core/entrypoint.py    plotting/report-producing command
oracle_harness.py             Python-to-Rust reference fixture generator
itd_research/                 isolated post-V29 research namespace (not V29.18)
tools/                        validation, manifest, policy, and smoke utilities
tests/                        focused analytical and regression validators
```

## Research namespace boundary

`itd_research/` depends on `itd_v29_core` (one-way); no core module imports
`itd_research`, enforced by an AST test. Its numerical modules import no plotting
library; only `itd_research/plotting.py` imports Matplotlib, and it does so
lazily inside `render_plots`. The research CLI (`python -m itd_research`) writes
only into an explicitly chosen output directory with overwrite-safe atomic
writes, so ordinary research runs never modify tracked files. It is a post-V29
research candidate, not a certified revision.

The facade contains no function definitions. Its `__all__` is composed from
`STABLE_PUBLIC_API`, `ADVANCED_PUBLIC_API`, and
`LEGACY_COMPATIBILITY_API`. Every imported function/class is the same object as
the implementation object; no wrapper or duplicate scientific implementation
is introduced. The `itd_simulator` package re-exports that facade so existing
`import itd_v29` users and packaged users share identities.

No module under `itd_v29_core` imports `itd_v29`. This direction is enforced by
AST tests and the dependency analyser.

## Plotting boundary

The numerical facade and core modules do not import Matplotlib during ordinary
import. `entrypoint.main()` selects the noninteractive `Agg` backend and imports
`matplotlib.pyplot` only when the plotting command runs. The legacy comparison
script follows the same lazy import rule. This avoids backend global state and
plotting import cost for library consumers while preserving command-line plots.

## API stability

Stable names cover the main simulator, geometry, core operators, structural
metrics, standard transformations, and declared constants. Advanced names
cover transport limiters, convergence analysis, multiscale tools, and material
diagnostics whose detailed numerical contract matters. Legacy compatibility
names retain historically documented configuration/field helpers and the
command `main`.

Names should move categories only with a changelog entry. Removal requires a
deprecation period unless a security or correctness issue makes continued use
unsafe. Internal names are not added to `__all__` merely because they are
imported by an implementation module.

## Historical material

`itd_v10.py`, `validate_release_v10.py`, and numbered historical validation
scripts are retained for provenance. Most numbered scripts targeted predecessor
monolith files that are absent from the published Git history. They are not
renamed, silently redirected, or treated as V29 certification.

## Packaging choice

The repository uses a low-risk root-layout package rather than moving the
scientific modules beneath `src/`. Setuptools packages `itd_simulator`,
`itd_v29_core`, and the compatibility modules. This avoids breaking
`import itd_v29` while providing `python -m itd_simulator` and the
`itd-simulator` console script.
