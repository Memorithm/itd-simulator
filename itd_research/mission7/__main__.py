"""CLI: ``python -m itd_research.mission7 {validate,run} ...``.

``validate`` runs the OFFLINE synthetic fixture campaign (no network) for bounded CI.
``run --data DIR`` runs the campaign on a directory of already-downloaded external
``frame_*.npz`` files (e.g. a JHTDB cutout sequence). No network access occurs in either
mode -- acquisition is a separate manual step (``tools/datasets/fetch_jhtdb_cutout.py``).
"""

from __future__ import annotations

import argparse
import math

from itd_research.mission7.campaign import run_external_campaign, run_fixture_campaign
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def _finite(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_finite(v) for v in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.mission7")
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="offline synthetic-fixture campaign (CI)")
    v.add_argument("--output", required=True)
    v.add_argument("--config", default=None, help="accepted for parity; ignored (offline)")
    r = sub.add_parser("run", help="campaign on a downloaded external sequence")
    r.add_argument("--output", required=True)
    r.add_argument("--data", required=True, help="directory of external frame_*.npz files")
    r.add_argument("--source-id", default="external_sequence")
    arguments = parser.parse_args(argv)

    if arguments.command == "validate":
        result = run_fixture_campaign()
    else:
        result = run_external_campaign(arguments.data, source_id=arguments.source_id)

    report = {
        "environment": environment_metadata(),
        "central_question": "Does ITD provide reproducible structural/diagnostic/predictive "
        "information on genuinely external fluid-dynamics data?",
        "campaign": result.as_dict(),
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "mission7_external.json", _finite(report), overwrite=True)

    phys = result.physics
    pred = result.prediction
    comp = result.complementarity
    tag = "SYNTHETIC FIXTURE (not external evidence)" if result.is_synthetic_fixture else "EXTERNAL"
    print(f"mission7 [{result.source_id}] {tag}  frames={result.provenance.n_frames} "
          f"grid={result.provenance.grid_shape}")
    print(f"  physics: divergence_rel={phys.divergence_relative:.4f} solenoidal={phys.solenoidal_ok} "
          f"urms={tuple(round(x,3) for x in phys.component_urms)} -> {phys.verdict}")
    print(f"  complementarity vs {comp.reference}: distinct ITD channels={comp.distinct_channels}")
    print(f"  prediction: est_auc={pred.auc_established:.3f} aug_auc={pred.auc_augmented:.3f} "
          f"added={pred.added_value:+.3f} -> {pred.verdict}")
    print(f"    ({pred.note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
