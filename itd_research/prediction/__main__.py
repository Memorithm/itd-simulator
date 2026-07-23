"""CLI: ``python -m itd_research.prediction run --output DIR [--quick]``.

Simulates the vortex-merger ensemble, runs the leakage-safe prediction evaluation
(H7), writes a JSON report, and prints the per-feature-set AUC table plus the H7
verdict. ``--quick`` uses a tiny ensemble for CI; it exercises the pipeline and is
**not** a scientific result (too few events for a verdict).
"""

from __future__ import annotations

import argparse

from itd_research.prediction.ensemble import (
    ITD_CHANNELS,
    default_ensemble,
    quick_ensemble,
    simulate_merger_run,
)
from itd_research.prediction.evaluation import classify_h7, evaluate_all
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.prediction")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run the merger-prediction study (H7)")
    run.add_argument("--output", required=True)
    run.add_argument("--quick", action="store_true", help="tiny CI ensemble (not a result)")
    run.add_argument("--horizon", type=int, default=4, help="primary imminent-merger horizon (frames)")
    run.add_argument(
        "--horizons", default="2,3,4,6", help="comma-separated horizons for the sensitivity table"
    )
    arguments = parser.parse_args(argv)

    configs = quick_ensemble() if arguments.quick else default_ensemble()
    if arguments.quick:
        runs = tuple(
            simulate_merger_run(cfg, nodes=48, steps=1100, record_every=55, min_cells=8)
            for cfg in configs
        )
    else:
        runs = tuple(simulate_merger_run(cfg) for cfg in configs)

    horizons = sorted({arguments.horizon, *(int(h) for h in arguments.horizons.split(","))})
    sensitivity: list[dict[str, object]] = []
    primary_metrics = None
    for horizon in horizons:
        metrics, n_events = evaluate_all(runs, horizon_frames=horizon)
        verdict, rationale = classify_h7(metrics, n_events)
        sensitivity.append(
            {
                "horizon_frames": horizon,
                "n_events": n_events,
                "verdict": verdict,
                "feature_sets": [m.as_dict() for m in metrics],
            }
        )
        if horizon == arguments.horizon:
            primary_metrics = (metrics, n_events, verdict, rationale)

    assert primary_metrics is not None
    metrics, n_events, verdict, rationale = primary_metrics

    seconds_per_frame = runs[0].times[1] - runs[0].times[0] if runs[0].times else 0.0
    report = {
        "environment": environment_metadata(),
        "quick": arguments.quick,
        "horizon_frames": arguments.horizon,
        "seconds_per_frame": seconds_per_frame,
        "itd_channels": list(ITD_CHANNELS),
        "n_runs": len(runs),
        "n_events": n_events,
        "runs": [
            {**run.config.as_dict(), "event_frame": run.event_frame, "event_time": run.event_time}
            for run in runs
        ],
        "feature_sets": [m.as_dict() for m in metrics],
        "horizon_sensitivity": sensitivity,
        "h7_verdict": verdict,
        "h7_rationale": rationale,
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "prediction.json", report, overwrite=True)

    print(f"prediction (H7): {n_events} labelled events across {len(runs)} runs "
          f"(primary horizon {arguments.horizon} frames)")
    print(f"{'feature_set':22s} {'AUC':>6} {'CI':>15} {'lead(t)':>8} {'miss':>6} {'FA':>6}")
    for m in metrics:
        print(
            f"{m.name:22s} {m.pooled_auc:6.3f} "
            f"[{m.auc_ci_low:5.3f},{m.auc_ci_high:5.3f}] "
            f"{m.median_lead_time:8.2f} {m.missed_event_rate:6.2f} {m.false_alarm_rate:6.2f}"
        )
    print("horizon sensitivity (verdict):")
    for entry in sensitivity:
        print(f"  H={entry['horizon_frames']}: {entry['verdict']}")
    print(f"H7 verdict (primary): {verdict} -- {rationale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
