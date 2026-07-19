#!/usr/bin/env python3
"""Reject prohibited automated-authorship trailers in new commit messages."""

from __future__ import annotations

import argparse
import re
import subprocess

EXPECTED_IDENTITY = "Tarek Zekriti <194770978+CHECKUPAUTO@users.noreply.github.com>"
FORBIDDEN = re.compile(
    r"(?im)^(?:"
    r"co-authored-by:\s*(?:claude|anthropic)\b|"
    r"claude-session:|"
    r"generated-by:|"
    r"assisted-by:"
    r")"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision_range", help="Git revision or range to inspect")
    parser.add_argument(
        "--require-identity",
        action="store_true",
        help="also require Tarek Zekriti as author and committer",
    )
    arguments = parser.parse_args()
    result = subprocess.run(
        [
            "git",
            "log",
            "--format=%H%x00%an <%ae>%x00%cn <%ce>%x00%B%x00",
            arguments.revision_range,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    records = result.stdout.split("\0")
    failures: list[str] = []
    for index in range(0, len(records) - 3, 4):
        commit = records[index].strip()
        author = records[index + 1]
        committer = records[index + 2]
        message = records[index + 3]
        if commit and FORBIDDEN.search(message):
            failures.append(f"{commit}: forbidden trailer")
        if arguments.require_identity and commit:
            if author != EXPECTED_IDENTITY:
                failures.append(f"{commit}: author is {author!r}")
            if committer != EXPECTED_IDENTITY:
                failures.append(f"{commit}: committer is {committer!r}")
    if failures:
        raise SystemExit("commit-message policy failed: " + "; ".join(failures))
    print(f"commit-message policy passed for {arguments.revision_range}")


if __name__ == "__main__":
    main()
