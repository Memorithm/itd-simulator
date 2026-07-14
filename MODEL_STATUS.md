# ITD Simulator — Model Status

Current published snapshot: ITD V29.11.

- Previous modular components remain unchanged.
- Galilean and time-dependent translating-frame transformations moved to `itd_v29_core/reference_frames.py`.
- Eleven historical public functions remain available from `itd_v29` through direct re-export.
- The main numerical summary remains bit-for-bit identical to V29.10.
- Galilean objectivity validation V23 passed.
- Accelerating translating-frame validation V24 passed.
- Local transformation laws and frame-composition laws passed their declared numerical oracles.
- Material and semi-Lagrangian objectivity checks passed their declared convergence studies.
- The published snapshot is source-clean and contains no Python bytecode cache.
- Validation is relative to the declared suites, numerical oracles and resolution studies.
