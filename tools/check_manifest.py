#!/usr/bin/env python3
"""Create or verify the repository's complete SHA-256 public manifest."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path, PurePosixPath

MANIFEST_NAME = "MANIFEST.sha256"
ENTRY = re.compile(r"^([0-9a-f]{64})  (.+)$")


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return sorted(path for path in paths if path and path != MANIFEST_NAME)


def validate_relative_path(text: str) -> str:
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe manifest path: {text!r}")
    if str(path) != text or "\\" in text:
        raise ValueError(f"non-canonical manifest path: {text!r}")
    return text


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_manifest(root: Path, paths: list[str]) -> str:
    lines: list[str] = []
    for relative in paths:
        validate_relative_path(relative)
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"manifest target must be a regular file: {relative}")
        lines.append(f"{digest_file(path)}  {relative}")
    return "\n".join(lines) + "\n"


def verify_manifest(root: Path, manifest: Path) -> None:
    entries: dict[str, str] = {}
    lines = manifest.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        match = ENTRY.fullmatch(line)
        if match is None:
            raise ValueError(f"malformed manifest line {line_number}")
        digest, relative = match.groups()
        validate_relative_path(relative)
        if relative in entries:
            raise ValueError(f"duplicate manifest path: {relative}")
        entries[relative] = digest

    expected_paths = tracked_paths(root)
    if list(entries) != expected_paths:
        missing = sorted(set(expected_paths) - set(entries))
        extra = sorted(set(entries) - set(expected_paths))
        raise ValueError(f"manifest scope mismatch; missing={missing}, extra={extra}")
    expected_text = render_manifest(root, expected_paths)
    actual_text = manifest.read_text(encoding="utf-8")
    if actual_text != expected_text:
        raise ValueError("manifest digest mismatch or non-canonical ordering")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="explicitly rewrite MANIFEST.sha256 from the Git index",
    )
    arguments = parser.parse_args()
    root = repository_root()
    manifest = root / MANIFEST_NAME
    if arguments.update:
        manifest.write_text(
            render_manifest(root, tracked_paths(root)),
            encoding="utf-8",
            newline="\n",
        )
        print(f"updated {manifest}")
        return
    verify_manifest(root, manifest)
    print(f"manifest verified: {len(tracked_paths(root))} tracked files")


if __name__ == "__main__":
    main()
