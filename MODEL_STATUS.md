# ITD Simulator — Model Status

Current published snapshot: ITD V29.15.

- Previous modular components remain unchanged.
- Two structural-signature functions moved to `itd_v29_core/structural_metrics.py`.
- The historical public API remains available through direct re-export from `itd_v29.py`.
- The main numerical summary is bitwise identical to ITD V29.14.
- The applicable historical validator suite (`validate_release_v10.py`) and the main simulator passed. A large number of historical validators (see the certification report) import predecessor monolith modules that were never part of this repository's Git history and are therefore excluded as not applicable, documented individually alongside the pre-existing `validate_bounded_cubic_v27.py` exclusion.
- The detailed certification report is available in `itd_v29_results/v29_15_structural_metrics_certification.md`.

These results are relative to the declared test suites, numerical oracles, and experimental configurations. They do not constitute a universal proof of correctness.
