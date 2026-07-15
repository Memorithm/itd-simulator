# ITD Simulator — Model Status

Current published snapshot: ITD V29.12.

- Previous modular components remain unchanged.
- The periodic transport subsystem moved to `itd_v29_core/periodic_transport.py`.
- Twenty-seven periodic transport functions remain available through direct public re-export from `itd_v29.py`.
- The main numerical summary is bitwise identical to ITD V29.11.
- Thirteen applicable validation suites passed.
- `validate_bounded_cubic_v27.py` is retained as a historical validator for the deprecated `cubic_bounded_periodic` mode and is not applicable to the current local bounded API.
- Exact cubic-sum preservation is validated by `cubic_local_sum_preserving_periodic`.
- The detailed certification report is available in `itd_v29_results/v29_12_periodic_transport_certification.txt`.

These results are relative to the declared test suites, numerical oracles, and experimental configurations. They do not constitute a universal proof of correctness.
