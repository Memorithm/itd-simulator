#!/usr/bin/env python3
"""Reproducibly fetch and verify an external dataset by registry id.

This script never runs during ordinary CI. It reads ``datasets/registry.json``,
downloads the dataset for a chosen id into an explicit output directory outside
the tracked tree, and verifies the SHA-256 recorded in the registry. It embeds no
credentials, refuses to overwrite by default, and fails with actionable
instructions when a dataset must be fetched manually (for example JHTDB or PIV
Challenge, whose terms require using their own portals).

Usage
-----
    python tools/datasets/fetch_dataset.py --id jhtdb_isotropic1024 \
        --output /tmp/itd-datasets

If the registry entry has a direct ``url`` and a non-empty ``sha256``, the file is
downloaded and verified. Otherwise the script prints the manual download
instructions from the registry and exits non-zero.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from itd_research.io.metadata import load_registry, verify_checksum  # noqa: E402

_MAX_BYTES = 8 * 1024 * 1024 * 1024


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, help="dataset id from the registry")
    parser.add_argument("--output", required=True, help="output directory (created)")
    parser.add_argument(
        "--registry",
        default=str(Path(__file__).resolve().parents[2] / "datasets" / "registry.json"),
    )
    parser.add_argument("--overwrite", action="store_true")
    arguments = parser.parse_args(argv)

    registry = load_registry(arguments.registry)
    if arguments.id not in registry:
        print(f"unknown dataset id: {arguments.id}", file=sys.stderr)
        print(f"available ids: {', '.join(sorted(registry))}", file=sys.stderr)
        return 2
    entry = registry[arguments.id]

    output_dir = Path(arguments.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not entry.url or not entry.sha256:
        print(f"[{entry.id}] manual download required (no direct url/sha256).")
        print(f"  title  : {entry.title}")
        print(f"  source : {entry.source}")
        print(f"  url    : {entry.url or 'see source'}")
        print(f"  doi    : {entry.doi or 'n/a'}")
        print(f"  licence: {entry.licence}")
        print(f"  method : {entry.download_method}")
        print(
            "  After downloading, record the sha256 in the registry and verify "
            "with itd_research.io.verify_checksum."
        )
        return 1

    target = output_dir / f"{entry.id}"
    if target.exists() and not arguments.overwrite:
        print(f"refusing to overwrite {target} (use --overwrite).", file=sys.stderr)
        return 1

    print(f"downloading {entry.url} -> {target}")
    request = urllib.request.Request(entry.url, headers={"User-Agent": "itd-research"})
    with urllib.request.urlopen(request) as response:  # noqa: S310 - explicit, user-run
        data = response.read(_MAX_BYTES + 1)
    if len(data) > _MAX_BYTES:
        print("download exceeds the size limit.", file=sys.stderr)
        return 1
    target.write_bytes(data)
    verify_checksum(target, entry.sha256)
    print(f"verified sha256 for {entry.id}: {entry.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
