"""CLI: ``python -m itd_research.ood_shift {validate,run} --output DIR``.

Runs the shift-aware calibrated-abstention campaign (H43-H45): progressive shifts of
growing magnitude challenge an in-domain reference/predictor, and the per-axis severity
detector plus the three-state accept/reduce/abstain policy are compared against a global
Mahalanobis radius and binary abstention. ``validate`` is a tiny bounded CI form.
"""

from __future__ import annotations

import argparse

from itd_research.ood_shift.campaign import run_shift_campaign
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.ood_shift")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
        p.add_argument("--quick", action="store_true")
    arguments = parser.parse_args(argv)
    quick = arguments.command == "validate" or arguments.quick

    result = run_shift_campaign(quick=quick)
    report = {"environment": environment_metadata(), "quick": quick, **result.as_dict()}
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "shift_ood.json", report, overwrite=True)

    b = result.bands
    print(f"shift-aware OOD  bands: s_low={b['s_low']:.2f} s_high={b['s_high']:.2f} "
          f"global_thr={b['global_threshold']:.2f}")
    print("  H43 severity localization (rank-agreement with known shift level):")
    print(f"    per-axis mean={result.per_axis_separation['mean']:.3f} "
          f"global mean={result.global_separation['mean']:.3f} -> {result.h43_verdict}")
    print("  policies (per-frame utility; higher is better):")
    for name, outcome in result.policies.items():
        print(f"    {name:38s} util={outcome['utility']:+.3f} cover={outcome['coverage']:.2f} "
              f"false_conf={outcome['false_confidence']:.3f} "
              f"unnec_abst={outcome['unnecessary_abstention_rate']}")
    print(f"  H44 (three-state beats binary): {result.h44_verdict}")
    print(f"  H45 (unnecessary abstention << {result.m5_unnecessary_abstention}): {result.h45_verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
