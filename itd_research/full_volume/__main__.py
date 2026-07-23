"""CLI: ``python -m itd_research.full_volume bench --output DIR``.

Benchmarks full-volume ITD-3D (no planar reduction) for the declared workloads (H35).
Timings are hardware-dependent feasibility measurements, not guarantees.
"""

from __future__ import annotations

import argparse

from itd_research.full_volume.benchmark import WORKLOADS, benchmark_volume
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.full_volume")
    sub = parser.add_subparsers(dest="command", required=True)
    bench = sub.add_parser("bench", help="full-volume ITD-3D benchmark (H35)")
    bench.add_argument("--output", required=True)
    bench.add_argument("--repeats", type=int, default=5)
    bench.add_argument("--only", default=None)
    arguments = parser.parse_args(argv)

    names = [arguments.only] if arguments.only else list(WORKLOADS)
    results = [benchmark_volume(name, repeats=arguments.repeats) for name in names]
    directory = prepare_output_directory(arguments.output)
    write_json(
        directory, "full_volume_3d.json",
        {"environment": environment_metadata(), "note": "full volume, no planar reduction",
         "workloads": [r.as_dict() for r in results]},
        overwrite=True,
    )
    for r in results:
        status = "MEETS" if r.meets_budget else "MISSES"
        print(f"{r.name}: {r.nodes}^3 channels={r.channels_evaluated} p50={r.p50_ms:.0f} "
              f"p95={r.p95_ms:.0f} p99={r.p99_ms:.0f}ms mem={r.peak_memory_mb:.0f}MB "
              f"budget={r.budget_ms:.0f}ms -> {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
