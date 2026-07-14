# ITD Simulator — Model Status

Current published snapshot: ITD V29.9.

- Constants, temporal geometry, spatial geometry, geometric transforms and spatial scaling remain modularized.
- Multi-scale grid validation and profile derivation moved to `itd_v29_core/multiscale_structure.py`.
- `simulate_multiscale` remains temporarily in `itd_v29.py` because it depends on the main simulation routine.
- Historical public imports remain available from `itd_v29`.
- The main V29.8 numerical summary remains identical bit for bit.
- V18 multi-scale validation and V19 numerical-certification validation passed.
- The published snapshot is source-clean and contains no Python bytecode cache.
- Certification is relative to the declared validation suites and numerical oracles.
