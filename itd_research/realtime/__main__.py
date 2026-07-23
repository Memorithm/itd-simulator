"""CLI: ``python -m itd_research.realtime bench --output DIR``.

Benchmarks the declared ITD workload classes and writes a latency report. Prints
which classes meet their declared p95 budget. Timings are hardware-dependent and
recorded with the environment; this measures feasibility, it does not guarantee it.
"""

from __future__ import annotations

import argparse

from itd_research.realtime.benchmarks import WORKLOADS, benchmark_workload
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.realtime")
    sub = parser.add_subparsers(dest="command", required=True)
    bench = sub.add_parser("bench", help="benchmark declared workload classes")
    bench.add_argument("--output", required=True)
    bench.add_argument("--repeats", type=int, default=30)
    bench.add_argument("--only", default=None, help="benchmark a single class (e.g. RT-3D-S)")
    arguments = parser.parse_args(argv)

    names = [arguments.only] if arguments.only else list(WORKLOADS)
    results = [benchmark_workload(name, repeats=arguments.repeats).as_dict() for name in names]
    directory = prepare_output_directory(arguments.output)
    write_json(
        directory,
        "realtime_benchmarks.json",
        {"environment": environment_metadata(), "workloads": results},
        overwrite=True,
    )
    for result in results:
        status = "MEETS" if result["meets_budget"] else "MISSES"
        print(
            f"{result['name']}: p50={result['p50_ms']:.1f}ms p95={result['p95_ms']:.1f}ms "
            f"p99={result['p99_ms']:.1f}ms budget={result['budget_ms']:.0f}ms -> {status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
