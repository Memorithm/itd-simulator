"""CLI: ``python -m itd_research.profiles {validate,run} --output DIR``.

Runs the event-profile stability study (H34): compares Taylor-Green channel importance
across the pseudo-spectral and finite-difference codes, and lists the declared profile
registry. ``validate`` is a tiny CI form.
"""

from __future__ import annotations

import argparse

from itd_research.profiles.registry import REGISTRY
from itd_research.profiles.stability import run_stability_study
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.profiles")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)
    quick = arguments.command == "validate"

    stability = run_stability_study(quick=quick)
    report = {
        "environment": environment_metadata(),
        "quick": quick,
        "registry": {pid: profile.as_dict() for pid, profile in REGISTRY.items()},
        "h34_stability": stability.as_dict(),
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "profiles.json", report, overwrite=True)

    print(f"profiles: {len(REGISTRY)} declared "
          f"({', '.join(REGISTRY)})")
    print(f"  H34 stability (spectral vs FD Taylor-Green): rank_corr={stability.rank_correlation:.3f} "
          f"top3_overlap={stability.top3_overlap:.2f} -> {stability.verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
