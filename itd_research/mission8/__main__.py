"""CLI: ``python -m itd_research.mission8 {validate,run} ...``.

``validate`` runs the OFFLINE synthetic fixture validation (no network) -- the full
Mission 8 module set exercised on manufactured oracle sequences (H61/H62 primary test,
H64/H70/H71 descriptive checks, H73 structural OOD, one profile benchmark) -- for bounded
CI. ``run --data DIR --holdout DIR ...`` runs the primary campaign on already-downloaded
external ``frame_*.npz`` sequence directories. No network access occurs in either mode --
acquisition is a separate manual step (``tools/datasets/fetch_jhtdb_cutout.py``).
"""

from __future__ import annotations

import argparse
import math
from typing import Any

from itd_research.mission8.campaign import (
    run_full_fixture_validation,
    run_structural_campaign,
)
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
    parser = argparse.ArgumentParser(prog="itd_research.mission8")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="offline synthetic-fixture validation (CI)")
    v.add_argument("--output", required=True)
    v.add_argument("--config", default=None, help="accepted for parity; ignored (offline)")

    r = sub.add_parser("run", help="primary campaign on downloaded external sequences")
    r.add_argument("--output", required=True)
    r.add_argument("--dev", action="append", required=True, help="sequence_id=directory (repeatable)")
    r.add_argument("--holdout", action="append", required=True, help="sequence_id=directory (repeatable)")

    arguments = parser.parse_args(argv)
    directory = prepare_output_directory(arguments.output)

    if arguments.command == "validate":
        result: dict[str, Any] = run_full_fixture_validation()
        report = {
            "environment": environment_metadata(),
            "central_question": "Does the full Mission 8 structural/topological pipeline run "
            "deterministically end-to-end on a manufactured oracle (code verification only)?",
            "campaign": result,
        }
        write_json(directory, "mission8_fixture_validation.json", _finite(report), overwrite=True)
        primary = result["primary"]["primary_test"]
        print(f"mission8 validate: h61={primary['h61_verdict']} h62={primary['h62_verdict']} "
              f"h64={result['h64_topology_response']['verdict']} "
              f"h71={result['h71_channel_stability']['verdict']} "
              f"h73={result['h73_structural_ood']['verdict']}")
        return 0

    def _parse_pairs(items: list[str]) -> list[tuple[str, str]]:
        pairs = []
        for item in items:
            sid, _sep, path = item.partition("=")
            if not _sep:
                raise ValueError(f"expected sequence_id=directory, got {item!r}")
            pairs.append((sid, path))
        return pairs

    campaign = run_structural_campaign(
        _parse_pairs(arguments.dev), _parse_pairs(arguments.holdout), is_synthetic_fixture=False,
    )
    report = {
        "environment": environment_metadata(),
        "central_question": "Do existing non-magnitude ITD structural channels provide reproducible, "
        "transferable, incrementally useful information for external structural/topological vortex "
        "events beyond competent established structural diagnostics?",
        "campaign": campaign.as_dict(),
    }
    write_json(directory, "mission8_external.json", _finite(report), overwrite=True)
    primary_test = campaign.primary_test
    print(f"mission8 run: dev={campaign.dev_ids} holdout={campaign.holdout_ids}")
    print(f"  screening: {primary_test.screening.saturation_status} -> "
          f"selected_for_primary_test={primary_test.screening.selected_for_primary_test}")
    print(f"  established_auc={primary_test.holdout_auc_established:.3f} "
          f"itd_only_auc={primary_test.holdout_auc_itd_only:.3f} "
          f"augmented_auc={primary_test.holdout_auc_augmented:.3f}")
    print(f"  added_value={primary_test.added_value.diff_mean:+.3f} "
          f"[{primary_test.added_value.ci_low:+.3f}, {primary_test.added_value.ci_high:+.3f}] "
          f"-> h61={primary_test.h61_verdict} h62={primary_test.h62_verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
