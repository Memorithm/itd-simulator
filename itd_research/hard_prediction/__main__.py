"""CLI: ``python -m itd_research.hard_prediction {validate,run} --output DIR``.

``validate`` runs a tiny deterministic pipeline for CI (few seeds, low resolution) --
it exercises leakage-safe grouping and the added-value machinery and is NOT a result.
``run`` executes the preregistered study: locked development/holdout seeds, the H18
added-value test, and the H21/H22 degradation sweep, writing a JSON report and
per-hypothesis verdicts. The protocol hash is checked so the locked config is honoured.
"""

from __future__ import annotations

import argparse

from itd_research.hard_prediction.degradation import DegradationSpec
from itd_research.hard_prediction.evaluation import (
    added_value,
    build_labeled,
    evaluate_feature_set,
)
from itd_research.hard_prediction.flows import (
    ESTABLISHED_FEATURES,
    ITD_FEATURES,
    features_from_raw,
    simulate_merger_raw,
    simulate_taylorgreen_raw,
)
from itd_research.hard_prediction.protocol import load_protocol, protocol_sha256
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)

_AUGMENTED = tuple(ESTABLISHED_FEATURES) + tuple(ITD_FEATURES)

_SWEEP: tuple[DegradationSpec, ...] = (
    DegradationSpec("clean"),
    DegradationSpec("noise05", noise=0.05),
    DegradationSpec("noise10", noise=0.10),
    DegradationSpec("downsample2", downsample_factor=2),
    DegradationSpec("mask20", mask_fraction=0.20),
    DegradationSpec("central_crop", window="central_crop"),
    DegradationSpec("downstream_half", window="downstream_half"),
)


def _simulate(family: str, seeds: tuple[int, ...], quick: bool) -> list:
    raws = []
    for seed in seeds:
        if family == "taylorgreen":
            raws.append(simulate_taylorgreen_raw(seed, **({"nodes": 16, "steps": 700, "record_every": 50} if quick else {})))
        else:
            raws.append(simulate_merger_raw(seed, **({"nodes": 56, "steps": 2000, "record_every": 100} if quick else {})))
    return raws


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.hard_prediction")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
        p.add_argument("--config", default=None)
        p.add_argument("--family", default="merger", choices=["merger", "taylorgreen"])
        p.add_argument("--horizon", type=int, default=4)
    arguments = parser.parse_args(argv)
    quick = arguments.command == "validate"

    protocol = load_protocol(strict=not quick)
    dev_seeds: tuple[int, ...]
    holdout_seeds: tuple[int, ...]
    if quick:
        dev_seeds, holdout_seeds = (10, 11, 12), (90, 91, 92)
    else:
        dev_seeds = protocol.development_seeds
        holdout_seeds = protocol.final_holdout_seeds

    dev_raw = _simulate(arguments.family, dev_seeds, quick)
    holdout_raw = _simulate(arguments.family, holdout_seeds, quick)

    dev = build_labeled([features_from_raw(r) for r in dev_raw], arguments.horizon)
    holdout = build_labeled([features_from_raw(r) for r in holdout_raw], arguments.horizon)

    bootstrap = 200 if quick else 2000
    feature_sets = {
        "established": tuple(ESTABLISHED_FEATURES),
        "itd": tuple(ITD_FEATURES),
        "established+itd": _AUGMENTED,
    }
    metric_objs = {
        name: evaluate_feature_set(dev, holdout, name, names, bootstrap=bootstrap)
        for name, names in feature_sets.items()
    }
    metrics = {name: m.as_dict() for name, m in metric_objs.items()}
    value = added_value(
        dev, holdout, tuple(ESTABLISHED_FEATURES), _AUGMENTED,
        margin=protocol.added_value_margin, bootstrap=bootstrap,
    )

    # H21/H22 degradation sweep: train AND test at the SAME degradation level, so this
    # measures whether the signal survives the degradation (not distribution shift,
    # which is H23's concern). Both dev and holdout are degraded identically.
    sweep: list[dict[str, object]] = []
    specs = _SWEEP if not quick else (_SWEEP[0], _SWEEP[1], _SWEEP[3])
    for spec in specs:
        dev_deg = build_labeled([features_from_raw(r, spec) for r in dev_raw], arguments.horizon)
        deg = build_labeled([features_from_raw(r, spec) for r in holdout_raw], arguments.horizon)
        if not deg or not dev_deg:
            sweep.append({"degradation": spec.name, "auc": None, "n_events": 0})
            continue
        m = evaluate_feature_set(dev_deg, deg, spec.name, _AUGMENTED, bootstrap=bootstrap)
        sweep.append(
            {"degradation": spec.name, "auc": m.auc, "auc_ci_low": m.auc_ci_low, "n_events": len(deg)}
        )

    report = {
        "environment": environment_metadata(),
        "quick": quick,
        "protocol_sha256": protocol_sha256(),
        "matches_preregistration": protocol.matches_preregistration(),
        "family": arguments.family,
        "horizon_frames": arguments.horizon,
        "development_seeds": list(dev_seeds),
        "holdout_seeds": list(holdout_seeds),
        "n_dev_events": len(dev),
        "n_holdout_events": len(holdout),
        "feature_set_metrics": metrics,
        "h18_added_value": value.as_dict(),
        "degradation_sweep": sweep,
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "hard_prediction.json", report, overwrite=True)

    print(f"hard_prediction[{arguments.family}] protocol={protocol_sha256()[:12]} "
          f"match={protocol.matches_preregistration()} events dev={len(dev)} holdout={len(holdout)}")
    for name, m in metric_objs.items():
        print(f"  {name:16s} AUC={m.auc:.3f} [{m.auc_ci_low:.3f},{m.auc_ci_high:.3f}] PR-AUC={m.pr_auc:.3f}")
    print(f"  H18 added value: base={value.auc_base:.3f} aug={value.auc_augmented:.3f} "
          f"diff={value.diff_mean:+.3f} [{value.diff_ci_low:+.3f},{value.diff_ci_high:+.3f}] -> {value.verdict}")
    for s in sweep:
        auc = s["auc"]
        auc_text = f"{auc:.3f}" if isinstance(auc, float) else "None"
        print(f"  degrade {str(s['degradation']):16s} AUC={auc_text} (n={s['n_events']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
