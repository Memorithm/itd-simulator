"""Command-line research runner: ``python -m itd_research``.

Executes the deterministic benchmark, convergence, and sensitivity studies into
an explicitly chosen output directory, writing CSV and JSON artifacts plus a
machine-readable manifest with environment and commit metadata. It refuses to
overwrite existing artifacts unless ``--overwrite`` is given and never writes
outside the selected directory, so it cannot modify tracked repository files
during ordinary validation.

    python -m itd_research --quick --output /tmp/itd-research-quick
    python -m itd_research --full  --output /tmp/itd-research-full  --plots
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from itd_research import benchmark_runner
from itd_research.convergence import run_convergence
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_csv,
    write_json,
    write_manifest,
)
from itd_research.sensitivity import run_sensitivity


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="itd_research",
        description="Deterministic post-V29 dimensional-validation research runner.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="explicitly selected output directory (created if absent).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--quick",
        action="store_true",
        help="reduced deterministic suite suitable for CI (default).",
    )
    mode.add_argument(
        "--full",
        action="store_true",
        help="complete resolution sweep for local scientific runs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="allow overwriting existing artifacts in the output directory.",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="also render PNG figures through the plotting boundary.",
    )
    return parser.parse_args(argv)


def _benchmark_summary_rows(benchmarks: dict[str, Any]) -> list[list[object]]:
    rows: list[list[object]] = []
    for case in benchmarks["cases"]:
        name = str(case["name"])
        for check in case.get("checks", []):
            rows.append(
                [
                    name,
                    check["quantity"],
                    check["classification"],
                    check["expected"],
                    check["computed"],
                    check["abs_error"],
                    check["tolerance"],
                    check["passed"],
                ]
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    full = bool(arguments.full)
    overwrite = bool(arguments.overwrite)

    directory = prepare_output_directory(arguments.output)
    metadata = environment_metadata()

    resolution = benchmark_runner.FULL if full else benchmark_runner.QUICK
    finite_sizes: tuple[int, ...]
    periodic_sizes: tuple[int, ...]
    spatial_sizes: tuple[int, ...]
    if full:
        finite_sizes = (17, 33, 65, 129)
        periodic_sizes = (16, 32, 64, 128)
        spatial_sizes = (16, 32, 64, 128)
    else:
        finite_sizes = (17, 33, 65)
        periodic_sizes = (16, 32, 64)
        spatial_sizes = (16, 32, 64)

    benchmarks = benchmark_runner.run_benchmarks(resolution)
    convergence = run_convergence(finite_sizes, periodic_sizes)
    sensitivity = run_sensitivity(spatial_sizes)

    artifacts: list[Path] = []
    artifacts.append(write_json(directory, "benchmarks.json", benchmarks, overwrite=overwrite))
    artifacts.append(write_json(directory, "convergence.json", convergence, overwrite=overwrite))
    artifacts.append(write_json(directory, "sensitivity.json", sensitivity, overwrite=overwrite))

    artifacts.append(
        write_csv(
            directory,
            "benchmarks_checks.csv",
            (
                "case", "quantity", "classification", "expected",
                "computed", "abs_error", "tolerance", "passed",
            ),
            _benchmark_summary_rows(benchmarks),
            overwrite=overwrite,
        )
    )
    artifacts.append(
        write_csv(
            directory,
            "convergence.csv",
            convergence["columns"],
            convergence["rows"],
            overwrite=overwrite,
        )
    )
    artifacts.append(
        write_csv(
            directory,
            "sensitivity.csv",
            sensitivity["columns"],
            sensitivity["rows"],
            overwrite=overwrite,
        )
    )

    if arguments.plots:
        from itd_research.plotting import render_plots

        artifacts.extend(render_plots(convergence, sensitivity, directory))

    manifest_path = write_manifest(directory, artifacts, metadata, overwrite=overwrite)

    passed = int(benchmarks["passed_checks"])
    total = int(benchmarks["total_checks"])
    print(f"mode: {'full' if full else 'quick'}")
    print(f"output: {directory.resolve()}")
    print(f"benchmark checks passed: {passed}/{total}")
    print(f"artifacts written: {len(artifacts)} (+ manifest {manifest_path.name})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
