"""CLI: ``python -m itd_research.generalization run --output DIR [--nodes N]``.

Runs the leakage-safe cross-flow transfer studies (H8/H9/H10/H13) on the
deterministic 3D flow catalogue and writes a JSON report plus the per-hypothesis
verdicts. Invariants checked: the sub-cube count is reproducible and the
leave-one-family-out component fits are genuinely evaluated on a held-out family.
Findings (including the negative ones) are reported, not asserted.
"""

from __future__ import annotations

import argparse

from itd_research.generalization.transfer import (
    classify_h9,
    classify_h10,
    classify_h13,
    component_transfer,
    family_generalization,
    sample_generalization,
    threshold_transfer,
)
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)
from itd_research.validation_lab.flows import lab_flows

_TARGETS = ("q_positive_fraction", "enstrophy", "swirl_mean")
_THRESHOLD_FEATURES = (
    ("itd", "intensity"),
    ("itd", "localization"),
    ("itd", "orientation_dispersion"),
    ("baseline", "enstrophy"),
    ("baseline", "swirl_mean"),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.generalization")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run cross-flow transfer studies (H8/H9/H10/H13)")
    run.add_argument("--output", required=True)
    run.add_argument("--nodes", type=int, default=24)
    run.add_argument("--subcubes", type=int, default=3)
    arguments = parser.parse_args(argv)

    flows = lab_flows(nodes=arguments.nodes)
    samples = sample_generalization(flows, subcubes_per_axis=arguments.subcubes)

    generalization = family_generalization(samples)
    components = [component_transfer(samples, target) for target in _TARGETS]
    thresholds = [threshold_transfer(samples, feature, source) for source, feature in _THRESHOLD_FEATURES]

    h13 = classify_h13(generalization)
    h9 = classify_h9(components)
    h10 = classify_h10(thresholds)

    report = {
        "environment": environment_metadata(),
        "n_flows": len(flows),
        "n_samples": int(samples.itd_matrix.shape[0]),
        "families": sorted(set(samples.family_labels)),
        "h13_family_generalization": generalization.as_dict(),
        "h9_component_transfer": [c.as_dict() for c in components],
        "h10_threshold_transfer": [t.as_dict() for t in thresholds],
        "verdicts": {
            "H13": {"verdict": h13[0], "rationale": h13[1]},
            "H9": {"verdict": h9[0], "rationale": h9[1]},
            "H10": {"verdict": h10[0], "rationale": h10[1]},
        },
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "generalization.json", report, overwrite=True)

    expected = len(flows) * arguments.subcubes**3
    failures: list[str] = []
    if int(samples.itd_matrix.shape[0]) != expected:
        failures.append("sub-cube count not reproducible")
    if len(generalization.itd_per_family_recall) < 2:
        failures.append("fewer than two families; transfer study ill-posed")

    print(f"generalization: {report['n_samples']} sub-cubes across {len(flows)} flows")
    print(f"  H13 family generalization: ITD={generalization.itd_balanced_accuracy:.3f} "
          f"baseline={generalization.baseline_balanced_accuracy:.3f} -> {h13[0]}")
    print(f"  H9  component transfer:    -> {h9[0]}")
    print(f"  H10 threshold transfer:    -> {h10[0]}")
    if failures:
        print("generalization invariants FAILED:")
        for message in failures:
            print(f"  - {message}")
        return 1
    print("generalization invariants PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
