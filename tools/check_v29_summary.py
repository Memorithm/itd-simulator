#!/usr/bin/env python3
"""Compare a generated V29 summary with the certified tracked reference."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def read_summary(path: Path) -> tuple[list[str], dict[str, tuple[float, ...]]]:
    with path.open(newline="", encoding="utf-8") as summary_file:
        reader = csv.reader(summary_file)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError(f"empty summary: {path}") from error
        rows: dict[str, tuple[float, ...]] = {}
        for row_number, row in enumerate(reader, start=2):
            if len(row) != 4 or not row[0] or row[0] in rows:
                raise ValueError(f"invalid row {row_number} in {path}")
            try:
                values = tuple(float(value) for value in row[1:])
            except ValueError as error:
                raise ValueError(f"non-numeric row {row_number} in {path}") from error
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"non-finite row {row_number} in {path}")
            rows[row[0]] = values
    return header, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--rtol", type=float, default=1.0e-13)
    parser.add_argument("--atol", type=float, default=1.0e-14)
    parser.add_argument("--exact", action="store_true")
    arguments = parser.parse_args()

    reference_header, reference_rows = read_summary(arguments.reference)
    candidate_header, candidate_rows = read_summary(arguments.candidate)
    if candidate_header != reference_header:
        raise SystemExit("summary header differs from the certified reference")
    if candidate_rows.keys() != reference_rows.keys():
        raise SystemExit("summary scenarios or their ordering differ")

    for scenario, reference_values in reference_rows.items():
        candidate_values = candidate_rows[scenario]
        for column, (reference, candidate) in enumerate(
            zip(reference_values, candidate_values, strict=True), start=2
        ):
            if arguments.exact:
                matches = candidate == reference
            else:
                matches = math.isclose(
                    candidate,
                    reference,
                    rel_tol=arguments.rtol,
                    abs_tol=arguments.atol,
                )
            if not matches:
                raise SystemExit(
                    f"summary mismatch: scenario={scenario}, column={column}, "
                    f"reference={reference!r}, candidate={candidate!r}"
                )
    mode = "exactly" if arguments.exact else "within declared tolerances"
    print(f"V29.18 summary matches {mode}")


if __name__ == "__main__":
    main()
