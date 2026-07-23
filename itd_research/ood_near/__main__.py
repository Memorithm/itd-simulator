"""CLI: ``python -m itd_research.ood_near {validate,run} --output DIR``.

Runs the near-OOD abstention campaign (H31): subtle shifts (untrained circulation,
viscosity, resolution) plus a far-OOD control, reporting OOD detection quality,
whether near-OOD flows stay predictable, and whether abstention reduces risk without
over-abstaining. ``validate`` is a tiny CI form.
"""

from __future__ import annotations

import argparse

from itd_research.ood_near.campaign import run_near_ood_campaign
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.ood_near")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
        p.add_argument("--quick", action="store_true")
    arguments = parser.parse_args(argv)
    quick = arguments.command == "validate" or arguments.quick

    result = run_near_ood_campaign(quick=quick)
    report = {"environment": environment_metadata(), "quick": quick, **result.as_dict()}
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "near_ood.json", report, overwrite=True)

    print("near-OOD mean scores:", {k: round(v, 2) for k, v in result.group_mean_scores.items()})
    print(f"  detection AUC near={result.detection_auc_near:.3f} far={result.detection_auc_far:.3f} "
          f"predictable-near AUC={result.predictable_near_auc:.3f}")
    s = result.selective
    print(f"  abstention: in-domain coverage={s['in_domain_coverage']:.2f} "
          f"selective_risk={s['selective_risk']:.3f} full_risk={s['full_risk']:.3f} "
          f"unnecessary_abstention={result.unnecessary_abstention_rate:.3f}")
    print(f"  H31 verdict: {result.h31_verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
