# ITD Simulator — Model Status

Current published snapshot: ITD V29.17.

- Previous modular components remain unchanged.
- Two material-deformation-orchestration functions (`interpolate_interval_series_to_nodes`, `simulate_material_deformation`) moved to `itd_v29_core/material_deformation.py`.
- The historical public API remains available through direct re-export from `itd_v29.py`.
- The main numerical summary is bitwise identical to ITD V29.16.
- The applicable historical validator suite (`validate_release_v10.py`) and the main simulator passed. A large number of historical validators (see the certification report) import predecessor monolith modules that were never part of this repository's Git history and are therefore excluded as not applicable, documented individually alongside the pre-existing `validate_bounded_cubic_v27.py` exclusion.
- The detailed certification report is available in `itd_v29_results/v29_17_material_deformation_certification.md`.
- Only `main` remains as a raw definition in `itd_v29.py`, pending V29.18.

These results are relative to the declared test suites, numerical oracles, and experimental configurations. They do not constitute a universal proof of correctness.
