# ITD Simulator — Model Status

Current published snapshot: ITD V29.13.

- Previous modular components remain unchanged.
- Five spatial and boundary operators moved to `itd_v29_core/spatial_operators.py`.
- The historical public API remains available through direct re-export from `itd_v29.py`.
- The extracted functions cover boundary-mode validation, numerical vorticity, scalar gradients, bounded projection, and spatial means.
- The main numerical summary is bitwise identical to ITD V29.12.
- Fifteen applicable validation suites passed.
- The detailed certification report is available in `itd_v29_results/v29_13_spatial_operators_certification.txt`.

These results are relative to the declared test suites, numerical oracles, and experimental configurations. They do not constitute a universal proof of correctness.
