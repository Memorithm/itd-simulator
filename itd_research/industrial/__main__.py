"""CLI: ``python -m itd_research.industrial assess --output DIR``.

Writes the IRL maturity self-assessment and the named-standard gap analysis (H16),
and prints the achieved level. This reports a *maturity level and gaps only* -- it is
never a certification claim.
"""

from __future__ import annotations

import argparse

from itd_research.industrial.readiness import (
    IRL_SCALE,
    assess_readiness,
    standard_gaps,
)
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.industrial")
    sub = parser.add_subparsers(dest="command", required=True)
    assess = sub.add_parser("assess", help="write the IRL maturity + gap analysis")
    assess.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)

    assessment = assess_readiness()
    gaps = standard_gaps()
    report = {
        "environment": environment_metadata(),
        "irl_scale": [{"level": level, "label": label} for level, label in IRL_SCALE],
        "assessment": assessment.as_dict(),
        "standard_gaps": [gap.as_dict() for gap in gaps],
        "disclaimer": (
            "This is a maturity self-assessment, not a certification. Scientific "
            "validation does not satisfy any listed standard; every standard is 'not "
            "satisfied'."
        ),
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "industrial_readiness.json", report, overwrite=True)

    print(
        f"industrial readiness: IRL-{assessment.achieved_level} "
        f"({dict(IRL_SCALE)[assessment.achieved_level]})"
    )
    print(f"open gaps to the next rung: {len(assessment.next_gaps)}; "
          f"named standards not satisfied: {len(gaps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
