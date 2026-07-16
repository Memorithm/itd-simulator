# ITD V29 — Rapport final de modularisation (V29.14 → V29.18)

- Généré le : `2026-07-16`
- Portée : conclusion de la série de modularisation de `itd_v29.py`,
  V29.14 à V29.18.

## 1. Graphe final des modules

```
itd_v29_core/constants.py            (V29.4)   — aucune dépendance interne
itd_v29_core/time_geometry.py        (V29.5)   — constants
itd_v29_core/spatial_geometry.py     (V29.6)   — constants
itd_v29_core/geometric_transforms.py (V29.7)   — spatial_geometry
itd_v29_core/spatial_scaling.py      (V29.8)   — spatial_geometry
itd_v29_core/multiscale_structure.py (V29.9)   — constants
itd_v29_core/numerical_certification.py (V29.10) — constants
itd_v29_core/reference_frames.py     (V29.11)  — spatial_geometry, geometric_transforms
itd_v29_core/periodic_transport.py   (V29.12)  — constants, spatial_geometry
itd_v29_core/spatial_operators.py    (V29.13)  — constants, spatial_geometry
itd_v29_core/material_interval.py    (V29.14)  — constants, spatial_geometry, spatial_operators
itd_v29_core/structural_metrics.py   (V29.15)  — constants, spatial_geometry, spatial_operators
itd_v29_core/simulation_engine.py    (V29.16)  — constants, spatial_geometry, spatial_operators,
                                                  multiscale_structure, periodic_transport,
                                                  structural_metrics (V29.15), time_geometry,
                                                  compare_scenarios, typing, numpy
itd_v29_core/material_deformation.py (V29.17)  — constants, spatial_geometry, spatial_operators,
                                                  time_geometry, material_interval (V29.14),
                                                  simulation_engine (V29.16),
                                                  compare_scenarios, typing, numpy
itd_v29_core/entrypoint.py           (V29.18)  — constants, simulation_engine (V29.16),
                                                  compare_scenarios, matplotlib, numpy, pathlib

itd_v29.py                                     — thin facade: direct imports + re-exports of
                                                  every module above, plus
                                                  `if __name__ == "__main__": main()`
```

No `itd_v29_core` module imports `itd_v29` at any point in this graph
(verified by grep across `itd_v29_core/*.py` after every release). The
dependency direction is strictly layered: `simulation_engine` (V29.16)
depends on `structural_metrics` (V29.15), never the reverse;
`material_deformation` (V29.17) depends on both `material_interval`
(V29.14) and `simulation_engine` (V29.16), never the reverse;
`entrypoint` (V29.18) depends on `simulation_engine` only. This was
confirmed by an explicit dependency audit (see `V29_16_STATUS.md`)
using the fixed lexical analyser before any V29.16 extraction was
attempted, and no circular import, inverted dependency, or forced
regrouping was needed — the provisional plan was correct as originally
proposed.

## 2. The compatibility facade

`itd_v29.py` is 232 lines and contains **zero function or class
definitions** (verified via `ast.walk` — 0 `FunctionDef`/
`AsyncFunctionDef` nodes remain). It consists of:

- the `#!/usr/bin/env python3` shebang and `from __future__ import annotations`;
- `matplotlib.use("Agg")` (a runtime backend-selection statement, not
  scientific logic);
- grouped direct imports from `compare_scenarios` and every
  `itd_v29_core.*` module, re-exporting the full historical public API
  by direct object identity (verified after every release via
  `getattr(itd_v29, name) is getattr(extracted_module, name)`);
- `if __name__ == "__main__": main()`.

No scientific algorithm, numerical computation, or duplicated logic
remains in the facade. This is the only executable logic left in
`itd_v29.py`.

## 3. Archives, file counts, and manifest SHA-256

All archives live under `archives/` in the working tree (internal,
`.gitignore`d, never published — see §6 for why). Each is read-only
after creation and contains its own internal `MANIFEST.sha256`
(verified entry-by-entry at creation time).

| Version | Archive path | Files | Archive `MANIFEST.sha256` |
|---|---|---|---|
| V29.14 (reference, reconstructed — see §6) | `archives/v29_14_material_interval_modularized` | 135 | `8f925d8054fad6ccc9de1d3d99c3e42094caa5a1af00e6cfe47b25b1fd229b80` |
| V29.15 | `archives/v29_15_structural_metrics_modularized` | 137 | `f6f0ff7e804cfc376bf0a9df82cfb31a5658b7334bffa8d940a58a6ac61e1518` |
| V29.16 | `archives/v29_16_simulation_engine_modularized` | 141 | `fe7fecf8b5509df7e9b638325a93ae80452f4545cf709ed28d6d7600b6c421e7` |
| V29.17 | `archives/v29_17_material_deformation_modularized` | 144 | `8b5a547dbae82071bd74d545b9b33fa1f79144eec113549ba79f12cb9ded34c3` |
| V29.18 | `archives/v29_18_entrypoint_modularized` | 147 | `eac78dd8958b9a1255014f98a3849965a6421de8042d2ef9871b74bf08dcf0d2` |

Per-release module and facade hashes (also recorded in each
version-specific certification report):

| Version | `itd_v29.py` SHA-256 | New module SHA-256 | `summary.csv` SHA-256 |
|---|---|---|---|
| V29.14 | `fc0deb7a0c9e2ca9d14504760c8fc1dedc9cb8e2033a8446cb07187c55f840e7` | `itd_v29_core/material_interval.py`: `06468e0c0f23a2de8d71e17f8382527a4c56dcb58d11ebf57bdb7987536c1b83` | `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b` |
| V29.15 | `be4afb06f2adf0e6405a3b746c6dc715808a3ecb773edf531d846523447c72e0` | `itd_v29_core/structural_metrics.py`: `573f52b9aca8a99583cd10f710cb9dd329d3c29950e731c17ddedc8c12f45bf5` | `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b` |
| V29.16 | `579d76c6b1f94cfeca9420d201181b1365fd5ef7d06e576cf3afdb239ac0ee84` | `itd_v29_core/simulation_engine.py`: `d611ee0f6ee21d36ce7a551dba7548e1b1f389dc1bfec3756f6d23de44512375` | `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b` |
| V29.17 | `9868d795ed77916fcfe8ca6326e041e15cc0bb99841bab4c9e302aefdc1ba3a0` | `itd_v29_core/material_deformation.py`: `21540507edc0ecceed847b699004eb3f70d3a3bfff329e56603c66135dfcef32` | `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b` |
| V29.18 | `624320698c9bc8fa4b65ef160e75bbe6591bf14f43ea2ceca50123361746246f` | `itd_v29_core/entrypoint.py`: `7e76257f161d1d643e5808f2793db6ecd4a3a3cbd8a9bfd678db0c6f4be5494e` | `119b4db845a504facc6f024dc37efe5e5544197802fd219227d32bb38246254b` |

**`summary.csv` is bitwise identical (`119b4db8…46254b`) through every
release from V29.14 through V29.18** — the same hash documented as
certified for V29.13/V29.14. The three scenario values remain exactly:

- `calme_irrotationnel`: intensity `4.6790906362952044e-32`, structure `0.0`, coupled `4.6790906362952044e-32`
- `vortex_coherent`: intensity `4.347614838943572`, structure `0.023259157148216747`, coupled `4.439409432678483`
- `multi_vortex_complexe`: intensity `0.6156393846646117`, structure `0.5926115146458905`, coupled `0.9798227221918314`

## 4. Validation results

For every release (V29.15–V29.18), the applicable suite was:

- `validate_release_v10.py` (imports `itd_v10`, unrelated to the V29
  modularization but structurally runnable) — **PASSED** every time;
- `MAIN` (`itd_v29.py` end-to-end) — **PASSED** every time.

46 historical `validate_*.py` scripts are excluded as not applicable
(1 pre-existing exclusion + 45 discovered during the V29.15 audit).
See §6 and each certification report's "Exclusions historiques"
section for the full, individually-justified list.

## 5. Scientific certification reports

- `itd_v29_results/v29_14_material_interval_certification.md`
- `itd_v29_results/v29_15_structural_metrics_certification.md`
- `itd_v29_results/v29_16_simulation_engine_certification.md`
- `itd_v29_results/v29_17_material_deformation_certification.md`
- `itd_v29_results/v29_18_entrypoint_certification.md`
- `itd_v29_results/V29_SERIES_AUTOMATION_REPORT.md` (cumulative,
  merged from `itd_v29_results/v29_series_records.json` — never
  overwritten on a per-version run)
- `V29_14_STATUS.md`, `V29_15_STATUS.md`, `V29_16_STATUS.md`,
  `V29_17_STATUS.md`, `V29_18_STATUS.md`, `MODEL_STATUS.md`

## 6. Limitations and non-universal claims

- **Environment discontinuity.** The task that seeded this work
  described a prior local environment (`/root/itd-simulator`,
  `/root/itd-simulator-publish`, a certified V29.14 archive with
  manifest `ab99ee0c…`, and an existing `tools/finish_v29_series.py`)
  that does not exist in this session's container. That prior work
  was never committed/pushed and was lost when its container was
  reclaimed. Everything in this report was rebuilt from the last
  certified Git state (V29.13, later found to already include V29.14
  once the user pushed it from their own environment mid-session).
  The V29.14 archive referenced in §3 is a **reconstruction** made in
  this session from the certified V29.14 working tree (its per-file
  hashes for `itd_v29.py`, `material_interval.py`, and `summary.csv`
  match the originally-reported certified values exactly), not the
  original archive object — its overall manifest hash therefore
  differs from the originally-reported `ab99ee0c…` because it snapshots
  a different (superset) working tree.
- **Validator applicability.** 45 historical validators were found,
  during the V29.15 audit, to depend on predecessor monolith modules
  (`itd_v4` through `itd_v28`, `itd_v14_1`, `itd_v20_1`) that were
  never part of this repository's Git history (confirmed via
  `git log --all --diff-filter=A`). This is not an artifact of this
  container: no clone of this public repository can run them. They
  are excluded and documented individually, the same treatment
  already given to `validate_bounded_cubic_v27.py`. Only
  `validate_release_v10.py` and `MAIN` constitute the applicable
  suite for V29.15–V29.18.
- **Publishing mechanics.** Direct pushes to `main` and pushes of
  annotated tags are rejected (policy 403) from this session's Git
  proxy. All work was published via branch + pull request instead
  (`claude/itd-simulator-modularize-publish-pkysrn` → `main`), which
  is also what this session's own branch instructions specify.
  Annotated tags `v29.15`–`v29.18` were created locally for
  record-keeping but could not be pushed; they still need to be
  created against `main` by whoever has tag-push rights.
- **Scope of certification.** As stated in every certification
  report: these results are relative to the declared validator
  suite, numerical oracle, and experimental configuration. They are
  not a universal proof of correctness. `coupled_index` remains an
  experimental diagnostic, not a canonical scalar.
- **Non-certified diagnostic outputs.** The per-scenario time-series
  CSVs (`calme_irrotationnel.csv`, `vortex_coherent.csv`,
  `multi_vortex_complexe.csv`) show tiny (~1e-13–1e-16 relative)
  floating-point differences from what's currently committed,
  reproducible deterministically in this container's NumPy
  2.5.1/Python 3.12 environment. This is not a regression from any
  modularization step (identical before and after every extraction in
  this session) and does not affect `summary.csv`, which is the sole
  bitwise-identity contract and remains exactly reproduced. It was not
  investigated further as out of scope for this modularization task.
