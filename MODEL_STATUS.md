# ITD Simulator — Model Status

Current scientific model revision: ITD V29.18.

Current source-tree software version: 0.2.0. The latest published GitHub
software release remains the legacy V10 release 0.1.1; no V29.18 software
archive is claimed until a reviewed release is published.

- Previous modular components remain unchanged.
- `main` moved to `itd_v29_core/entrypoint.py`. This concludes the V29 modularization series (V29.14–V29.18).
- `itd_v29.py` contains zero function definitions: it is a thin compatibility facade of direct imports, direct re-exports, and `if __name__ == "__main__": main()`.
- The historical public API remains available through direct re-export from `itd_v29.py`.
- The main numerical summary is bitwise identical to ITD V29.17 (and, transitively, to every certified release back to V29.13).
- The focused V29.18 pytest suite, architectural checks, deterministic smoke
  process, main simulator summary, public manifest, and Rust oracle contract are
  the current validation path. `validate_release_v10.py` is V10-only historical
  material and is not evidence for V29.18.
- No `itd_v29_core` module imports the `itd_v29` facade.
- The detailed certification report is available in `itd_v29_results/v29_18_entrypoint_certification.md`.

These results are relative to the declared test suites, analytical cases,
implementation-generated oracle fixture, tolerances, dependencies, and
experimental configurations. They do not constitute a universal proof of
correctness or physical validity.
