# ITD Simulator — Model Status

Current published snapshot: ITD V29.18.

- Previous modular components remain unchanged.
- `main` moved to `itd_v29_core/entrypoint.py`. This concludes the V29 modularization series (V29.14–V29.18).
- `itd_v29.py` contains zero function definitions: it is a thin compatibility facade of direct imports, direct re-exports, and `if __name__ == "__main__": main()`.
- The historical public API remains available through direct re-export from `itd_v29.py`.
- The main numerical summary is bitwise identical to ITD V29.17 (and, transitively, to every certified release back to V29.13).
- The applicable historical validator suite (`validate_release_v10.py`) and the main simulator passed. A large number of historical validators (see the certification reports) import predecessor monolith modules that were never part of this repository's Git history and are therefore excluded as not applicable, documented individually alongside the pre-existing `validate_bounded_cubic_v27.py` exclusion.
- No `itd_v29_core` module imports the `itd_v29` facade.
- The detailed certification report is available in `itd_v29_results/v29_18_entrypoint_certification.md`.

These results are relative to the declared test suites, numerical oracles, and experimental configurations. They do not constitute a universal proof of correctness.
