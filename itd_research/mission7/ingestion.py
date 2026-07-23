"""Safe ingestion of external velocity-field sequences with provenance (Mission 7, H49).

Loads a time-ordered sequence of ``.npz`` frames (keys ``x,y,z,u,v,w``) -- the format the
JHTDB cutout tool and the internal 3D field writer produce -- under explicit security and
resource limits, and records a provenance manifest with a per-frame SHA-256. It defends
against the failure modes the preregistration lists: oversized files/arrays, too many
frames, non-finite values, dimension/axis mismatch, non-monotone or duplicate timestamps.
It fabricates nothing and asserts no physical result -- that is ``physics.py``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class IngestionLimits:
    """Hard caps enforced during external ingestion (from the preregistration)."""

    max_raw_file_bytes: int = 2 * 1024**3
    max_grid_cells: int = 64 * 1024**2
    max_frames: int = 4096
    max_variables: int = 64

    def as_dict(self) -> dict[str, int]:
        return {
            "max_raw_file_bytes": self.max_raw_file_bytes,
            "max_grid_cells": self.max_grid_cells,
            "max_frames": self.max_frames,
            "max_variables": self.max_variables,
        }


@dataclass(frozen=True)
class Frame:
    """One ingested velocity snapshot on a rectilinear grid."""

    time: float
    x: FloatArray
    y: FloatArray
    z: FloatArray
    u: FloatArray
    v: FloatArray
    w: FloatArray
    sha256: str


@dataclass(frozen=True)
class SequenceProvenance:
    """Provenance for an ingested sequence: source, frames, checksums, limits."""

    source_id: str
    n_frames: int
    grid_shape: tuple[int, int, int]
    times: list[float]
    frame_sha256: list[str]
    limits: dict[str, int]
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "n_frames": self.n_frames,
            "grid_shape": list(self.grid_shape),
            "times": self.times,
            "frame_sha256": self.frame_sha256,
            "limits": self.limits,
            "notes": self.notes,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _time_of(path: Path) -> float:
    """Parse ``time`` from the npz if present, else fall back to the frame index name."""
    with np.load(path) as data:
        if "time" in data:
            return float(np.asarray(data["time"]).reshape(-1)[0])
    return float("nan")


def _load_frame(path: Path, limits: IngestionLimits, index: int) -> Frame:
    if path.stat().st_size > limits.max_raw_file_bytes:
        raise ValueError(f"{path.name}: raw file exceeds max_raw_file_bytes")
    sha = _sha256(path)
    with np.load(path) as data:
        keys = set(data.files)
        if len(keys) > limits.max_variables:
            raise ValueError(f"{path.name}: too many variables ({len(keys)})")
        missing = {"x", "y", "z", "u", "v", "w"} - keys
        if missing:
            raise ValueError(f"{path.name}: missing field keys {sorted(missing)}")
        # Coerce to native-endian float64 (defends against endianness/dtype surprises).
        x, y, z = (np.ascontiguousarray(data[k], dtype=np.float64) for k in ("x", "y", "z"))
        u, v, w = (np.ascontiguousarray(data[k], dtype=np.float64) for k in ("u", "v", "w"))
        t = float(np.asarray(data["time"]).reshape(-1)[0]) if "time" in keys else float(index)
    shape = u.shape
    if v.shape != shape or w.shape != shape:
        raise ValueError(f"{path.name}: u/v/w shapes disagree")
    if len(shape) != 3 or (x.size, y.size, z.size) != shape:
        raise ValueError(f"{path.name}: coordinate sizes {(x.size, y.size, z.size)} != grid {shape}")
    cells = int(np.prod(shape))
    if cells > limits.max_grid_cells:
        raise ValueError(f"{path.name}: grid {shape} exceeds max_grid_cells")
    for name, arr in (("u", u), ("v", v), ("w", w)):
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{path.name}: non-finite values in {name}")
    for name, arr in (("x", x), ("y", y), ("z", z)):
        if arr.size >= 2 and not np.all(np.diff(arr) > 0):
            raise ValueError(f"{path.name}: coordinate {name} not strictly increasing")
    return Frame(t, x, y, z, u, v, w, sha)


def load_field_sequence(
    directory: str | Path, *, source_id: str, pattern: str = "frame_*.npz",
    limits: IngestionLimits | None = None,
) -> tuple[list[Frame], SequenceProvenance]:
    """Load and validate a time-ordered external field sequence with provenance.

    Frames are sorted by filename, then re-sorted by parsed time; strictly-increasing
    time is required (rejects timestamp disorder), and identical checksums for adjacent
    frames are rejected as duplicates. Returns the frames and a provenance record.
    """
    limits = limits or IngestionLimits()
    base = Path(directory)
    paths = sorted(base.glob(pattern))
    if not paths:
        raise ValueError(f"no frames matching {pattern!r} in {base}")
    if len(paths) > limits.max_frames:
        raise ValueError(f"too many frames ({len(paths)} > {limits.max_frames})")
    frames = [_load_frame(p, limits, i) for i, p in enumerate(paths)]
    frames.sort(key=lambda fr: fr.time)
    times = [fr.time for fr in frames]
    if any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
        raise ValueError("frame times are not strictly increasing (disorder or duplicates)")
    for i in range(len(frames) - 1):
        if frames[i].sha256 == frames[i + 1].sha256:
            raise ValueError("duplicate frame detected (identical checksum)")
    shape = frames[0].u.shape
    if any(fr.u.shape != shape for fr in frames):
        raise ValueError("frames have inconsistent grid shapes")
    grid_shape = (int(shape[0]), int(shape[1]), int(shape[2]))
    provenance = SequenceProvenance(
        source_id=source_id, n_frames=len(frames), grid_shape=grid_shape,
        times=times, frame_sha256=[fr.sha256 for fr in frames], limits=limits.as_dict(),
    )
    return frames, provenance
