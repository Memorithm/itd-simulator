"""CLI: ``python -m itd_research.product bench --output DIR``.

Builds a reference pipeline and measures the complete end-to-end per-frame latency for
the declared workloads (H26). Prints which workloads meet their declared p95 budget.
Timings are hardware-dependent feasibility measurements, not guarantees.
"""

from __future__ import annotations

import argparse

from itd_research.product.pipeline import (
    _WORKLOADS,
    benchmark_end_to_end,
    build_reference_pipeline,
)
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.product")
    sub = parser.add_subparsers(dest="command", required=True)
    bench = sub.add_parser("bench", help="end-to-end latency benchmark (H26)")
    bench.add_argument("--output", required=True)
    bench.add_argument("--repeats", type=int, default=30)
    bench.add_argument("--only", default=None)
    arguments = parser.parse_args(argv)

    pipeline = build_reference_pipeline(quick=True)
    names = [arguments.only] if arguments.only else list(_WORKLOADS)
    results = [benchmark_end_to_end(pipeline, name, repeats=arguments.repeats) for name in names]

    directory = prepare_output_directory(arguments.output)
    write_json(
        directory, "end_to_end_realtime.json",
        {"environment": environment_metadata(), "workloads": [r.as_dict() for r in results]},
        overwrite=True,
    )
    for r in results:
        status = "MEETS" if r.meets_budget else "MISSES"
        print(f"{r.name}: size={r.size} p50={r.p50_ms:.1f} p95={r.p95_ms:.1f} p99={r.p99_ms:.1f} "
              f"budget={r.budget_ms:.0f}ms -> {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
