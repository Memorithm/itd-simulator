"""Deterministic, overwrite-safe result serialisation (post-V29 research).

This module contains no scientific computation and imports no plotting library.
It writes CSV and JSON artifacts atomically, refuses to clobber existing files
or follow symlinks unless overwrite is explicitly requested, keeps every
artifact inside a chosen output directory (guarding against path traversal), and
records environment and commit metadata so runs are auditable and reproducible.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

import numpy as np

_THREAD_ENV_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "PYTHONHASHSEED",
)


def environment_metadata() -> dict[str, object]:
    """Return a deterministic record of the execution environment.

    The commit SHA and dirty flag are read from Git when available; failures are
    recorded as ``"unknown"`` rather than raising, so reporting never depends on
    a working Git checkout.
    """
    commit = "unknown"
    dirty: object = "unknown"
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=no"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        dirty = bool(status.strip())
    except (OSError, subprocess.SubprocessError):
        commit = "unknown"
        dirty = "unknown"

    threads = {name: os.environ.get(name, "unset") for name in _THREAD_ENV_VARS}

    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy_version": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "git_commit": commit,
        "git_tree_dirty": dirty,
        "thread_environment": threads,
        "model_baseline": "ITD V29.18 (preserved)",
        "research_stage": "post-V29 dimensional-validation research candidate",
    }


def _jsonable(value: object) -> object:
    """Recursively coerce numpy scalars/arrays and mappings to JSON types."""
    if isinstance(value, (str, bool)) or value is None:
        return value
    if isinstance(value, (int,)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float is not serialisable: {value!r}")
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        coerced = float(value)
        if not math.isfinite(coerced):
            raise ValueError(f"non-finite float is not serialisable: {coerced!r}")
        return coerced
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in value}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    raise TypeError(f"Value of type {type(value)!r} is not JSON serialisable.")


def _resolve_within(directory: Path, name: str) -> Path:
    """Resolve ``name`` inside ``directory`` and reject escapes/symlinks."""
    base = directory.resolve()
    candidate = (base / name)
    resolved_parent = candidate.parent.resolve()
    if os.path.commonpath([str(base), str(resolved_parent)]) != str(base):
        raise ValueError(f"refusing to write outside output directory: {name!r}")
    if candidate.is_symlink():
        raise ValueError(f"refusing to write through a symlink: {name!r}")
    return candidate


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Write ``payload`` atomically via a temporary file in the same directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def prepare_output_directory(path: str | os.PathLike[str]) -> Path:
    """Create and return the output directory, rejecting symlink targets."""
    directory = Path(path)
    if directory.is_symlink():
        raise ValueError("output directory must not be a symlink.")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_json(
    directory: Path,
    name: str,
    data: object,
    *,
    overwrite: bool = False,
) -> Path:
    """Write ``data`` as deterministic, sorted JSON inside ``directory``."""
    target = _resolve_within(directory, name)
    if target.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {target}")
    text = json.dumps(
        _jsonable(data),
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    )
    _atomic_write_bytes(target, (text + "\n").encode("utf-8"))
    return target


def _format_cell(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (np.floating, float)):
        coerced = float(value)
        if not math.isfinite(coerced):
            raise ValueError(
                f"non-finite value not permitted in CSV cell: {coerced!r}"
            )
        return repr(coerced)
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    return str(value)


def write_csv(
    directory: Path,
    name: str,
    header: Sequence[str],
    rows: Iterable[Sequence[object]],
    *,
    overwrite: bool = False,
) -> Path:
    """Write ``rows`` as deterministic CSV with a fixed header and ``\\n`` endings.

    Finite floats are rendered with :func:`repr` for exact round-tripping;
    non-finite floats are rejected. Commas, double quotes, and any control
    character (including CR and LF) are rejected inside cells to keep the format
    unambiguous without a dialect dependency.
    """
    target = _resolve_within(directory, name)
    if target.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {target}")

    width = len(header)
    lines = [",".join(header)]
    for row in rows:
        if len(row) != width:
            raise ValueError("row width does not match the header width.")
        cells = [_format_cell(cell) for cell in row]
        for cell in cells:
            if "," in cell or '"' in cell or any(ord(ch) < 0x20 for ch in cell):
                raise ValueError(f"unsupported character in CSV cell: {cell!r}")
        lines.append(",".join(cells))
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    _atomic_write_bytes(target, payload)
    return target


def sha256_of(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(
    directory: Path,
    artifacts: Sequence[Path],
    metadata: Mapping[str, object],
    *,
    name: str = "manifest.json",
    overwrite: bool = False,
) -> Path:
    """Write a machine-readable manifest listing artifacts with SHA-256 digests."""
    base = directory.resolve()
    entries = []
    for artifact in sorted(artifacts, key=lambda item: item.name):
        relative = artifact.resolve().relative_to(base)
        entries.append(
            {
                "path": str(relative),
                "sha256": sha256_of(artifact),
                "bytes": artifact.stat().st_size,
            }
        )
    manifest = {
        "environment": dict(metadata),
        "artifacts": entries,
    }
    return write_json(directory, name, manifest, overwrite=overwrite)
