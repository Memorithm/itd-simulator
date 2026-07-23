"""CLI: ``python -m itd_research.cross_code {validate,run} --output DIR``.

Runs the same-physics cross-code study (H29): compares Taylor-Green integral
trajectories through the pseudo-spectral and finite-difference codes, then trains a
leakage-safe predictor on the spectral code (development) and evaluates it on the
finite-difference code (final holdout) -- including the decisive established-vs-
established+ITD added-value test on the cross-code holdout. ``validate`` is a tiny CI
form. The holdout source is never used for feature/threshold selection.
"""

from __future__ import annotations

import argparse

from itd_research.cross_code.comparison import (
    compare_taylorgreen,
    simulate_taylorgreen_fd_raw,
)
from itd_research.hard_prediction.evaluation import (
    added_value,
    build_labeled,
    cross_solver_auc,
    evaluate_feature_set,
)
from itd_research.hard_prediction.flows import (
    ESTABLISHED_FEATURES,
    ITD_FEATURES,
    features_from_raw,
    simulate_taylorgreen_raw,
)
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)

_AUG = tuple(ESTABLISHED_FEATURES) + tuple(ITD_FEATURES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.cross_code")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
        p.add_argument("--horizon", type=int, default=4)
    arguments = parser.parse_args(argv)
    quick = arguments.command == "validate"

    nodes = 16 if quick else 24
    spec_kwargs = {"nodes": nodes, "steps": 700, "record_every": 50} if quick else {}
    fd_kwargs = {"nodes": nodes, "steps": 500, "record_every": 40} if quick else {}
    dev_seeds = (10, 11, 12) if quick else (10, 11, 12, 13, 14, 15)
    holdout_seeds = (90, 91, 92) if quick else (90, 91, 92, 93, 94, 95)

    comparison = compare_taylorgreen(nodes=nodes, physical_time=3.0 if quick else 6.4)

    dev = build_labeled(
        [features_from_raw(simulate_taylorgreen_raw(s, **spec_kwargs)) for s in dev_seeds],
        arguments.horizon,
    )
    holdout = build_labeled(
        [features_from_raw(simulate_taylorgreen_fd_raw(s, **fd_kwargs)) for s in holdout_seeds],
        arguments.horizon,
    )

    bootstrap = 200 if quick else 2000
    metrics = {}
    if dev and holdout:
        for name, feats in (("established", tuple(ESTABLISHED_FEATURES)), ("itd", tuple(ITD_FEATURES)),
                            ("established+itd", _AUG)):
            metrics[name] = evaluate_feature_set(dev, holdout, name, feats, bootstrap=bootstrap).as_dict()
        value = added_value(dev, holdout, tuple(ESTABLISHED_FEATURES), _AUG,
                            margin=0.02, bootstrap=bootstrap).as_dict()
        transfer_auc = cross_solver_auc(dev, holdout, _AUG)
    else:
        value = {"verdict": "inconclusive"}
        transfer_auc = float("nan")

    report = {
        "environment": environment_metadata(),
        "quick": quick,
        "evidence_class": "cross-code (two in-repo numerical methods; NOT cross-institution)",
        "integral_comparison": {
            "energy_trajectory_correlation": comparison.energy_trajectory_correlation,
            "enstrophy_trajectory_correlation": comparison.enstrophy_trajectory_correlation,
            "spectral_event_time": comparison.spectral_event_time,
            "fd_event_time": comparison.fd_event_time,
            "enstrophy_peak_time_rel_error": comparison.enstrophy_peak_time_rel_error,
        },
        "n_dev_events": len(dev),
        "n_holdout_events": len(holdout),
        "cross_code_transfer_auc": transfer_auc,
        "feature_set_metrics": metrics,
        "h29_added_value": value,
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "cross_code.json", report, overwrite=True)

    print(f"cross_code[taylorgreen] energy_corr={comparison.energy_trajectory_correlation:.3f} "
          f"enstrophy_corr={comparison.enstrophy_trajectory_correlation:.3f} "
          f"event_rel_err={comparison.enstrophy_peak_time_rel_error}")
    print(f"  events dev(spectral)={len(dev)} holdout(FD)={len(holdout)} transfer AUC={transfer_auc:.3f}")
    for name, m in metrics.items():
        print(f"  {name:16s} AUC={m['auc']:.3f} [{m['auc_ci_low']:.3f},{m['auc_ci_high']:.3f}]")
    if "auc_base" in value:
        print(f"  H29 added value: base={value['auc_base']:.3f} aug={value['auc_augmented']:.3f} "
              f"diff={value['diff_mean']:+.3f} [{value['diff_ci_low']:+.3f},{value['diff_ci_high']:+.3f}] "
              f"-> {value['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
