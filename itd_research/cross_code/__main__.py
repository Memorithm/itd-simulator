"""CLI: ``python -m itd_research.cross_code {validate,run,campaign} --output DIR``.

``validate`` / ``run`` execute the Mission 5 same-physics cross-code study (H29):
compare Taylor-Green integral trajectories through the pseudo-spectral and
finite-difference codes, then train a leakage-safe predictor on the spectral code and
evaluate it on the finite-difference code, including the decisive established-vs-
established+ITD added-value test. ``campaign`` runs the Mission 6 *competent-baseline*
cross-code campaign (H37-H42): it selects a fair normalization on development folds only,
then evaluates ITD against that competent established baseline on the holdout, in both
directions. The holdout source is never used for feature/threshold selection. ``validate``
is a tiny CI form.
"""

from __future__ import annotations

import argparse
import math

from itd_research.cross_code.comparison import (
    compare_taylorgreen,
    simulate_taylorgreen_fd_raw,
)
from itd_research.cross_code.transfer import run_competent_campaign
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


def _finite(value: object) -> object:
    """Coerce non-finite floats to ``None`` so the strict JSON writer accepts them."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _finite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_finite(item) for item in value]
    return value


def _run_h29(arguments: argparse.Namespace, quick: bool) -> int:
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
    write_json(directory, "cross_code.json", _finite(report), overwrite=True)

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


def _run_campaign(arguments: argparse.Namespace, quick: bool) -> int:
    result = run_competent_campaign(quick=quick, horizon=arguments.horizon)
    report = {
        "environment": environment_metadata(),
        "quick": quick,
        "evidence_class": "cross-code competent-baseline (H37-H42; two in-repo numerical methods)",
        "hypotheses": {
            "H38": "ITD beats a COMPETENT (dev-selected, normalized) established baseline",
            "H39": "competent+ITD beats competent-only by >=0.02 with CI excluding 0",
        },
        "campaign": result.as_dict(),
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "cross_code_competent.json", _finite(report), overwrite=True)

    print(f"competent campaign  selected_normalization={result.competent_method_selected}")
    print("  dev established AUC by method (selection uses dev folds only):")
    for method, auc in result.dev_established_auc_by_method.items():
        marker = " <- selected" if method == result.competent_method_selected else ""
        shown = "nan" if auc is None or (isinstance(auc, float) and math.isnan(auc)) else f"{auc:.3f}"
        print(f"    {method:16s} {shown}{marker}")
    print("  HOLDOUT (evaluated once) -- competent baseline vs ITD, both directions:")
    for d in result.holdout_directions:
        print(f"    {d.direction:16s} est_raw={d.established_raw_auc:.3f} "
              f"est_competent={d.established_competent_auc:.3f}"
              f"{'(>chance)' if d.competent_above_chance else '(<=chance)'} "
              f"itd_struct={d.itd_structural_auc:.3f} itd_full={d.itd_full_auc:.3f} "
              f"combined={d.combined_auc:.3f}")
        print(f"      H39 added value: diff={d.added_value_diff:+.3f} "
              f"[{d.added_value_ci_low:+.3f},{d.added_value_ci_high:+.3f}] -> {d.added_value_verdict}")
    print("  descriptive all-methods holdout grid (transparency; NOT used for the verdict):")
    for row in result.descriptive_holdout:
        print(f"    {row['direction']:16s} {row['normalization']:16s} "
              f"est={row['established_auc']:.3f} itd_struct={row['itd_structural_auc']:.3f} "
              f"itd_full={row['itd_full_auc']:.3f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.cross_code")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run", "campaign"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
        p.add_argument("--horizon", type=int, default=4)
        if name == "campaign":
            p.add_argument("--quick", action="store_true", help="tiny bounded form for CI")
    arguments = parser.parse_args(argv)

    if arguments.command == "campaign":
        return _run_campaign(arguments, quick=arguments.quick)
    return _run_h29(arguments, quick=arguments.command == "validate")


if __name__ == "__main__":
    raise SystemExit(main())
