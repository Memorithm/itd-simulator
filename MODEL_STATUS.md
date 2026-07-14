# ITD Simulator — Model Status

Current published snapshot: ITD V29.10.

- Previous modular components remain unchanged.
- Numerical certification and convergence analysis moved to `itd_v29_core/numerical_certification.py`.
- Eleven historical public functions remain available from `itd_v29` through direct re-export.
- Richardson extrapolation and single-scale and multi-scale triplet analysis are modularized.
- Decoupled spatial-temporal error-budget combination and summary functions are modularized.
- The main numerical summary remains bit-for-bit identical to V29.9.
- V19, V20, V20.1 and V20.1 summary-semantics validations passed.
- V19 deterministic CSV and JSON reports remain bit-for-bit identical to V29.9.
- The published snapshot is source-clean and contains no Python bytecode cache.
- Certification is relative to the declared validation suites, resolution studies and numerical oracles.
