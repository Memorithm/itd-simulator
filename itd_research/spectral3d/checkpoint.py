"""Deterministic, safe checkpoint/restart for the 3D solver (research).

Checkpoints are stored as ``.npz`` (no pickle) with the velocity field, the
simulation state, the spectral/solver configuration, the repository commit, and a
SHA-256 checksum of the velocity payload. Loading verifies the checksum and rebuilds
the grid, so a run can be restarted bit-for-bit.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d.grids import SpectralGrid3D, spectral_grid_3d

FloatArray: TypeAlias = NDArray[np.float64]

_MAX_BYTES = 2 * 1024 * 1024 * 1024


def _velocity_checksum(u: FloatArray, v: FloatArray, w: FloatArray) -> str:
    digest = hashlib.sha256()
    for component in (u, v, w):
        digest.update(np.ascontiguousarray(component, dtype=np.float64).tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class Checkpoint:
    """A restored checkpoint: velocity field, grid, and metadata."""

    velocity: tuple[FloatArray, FloatArray, FloatArray]
    grid: SpectralGrid3D
    time: float
    delta_time: float
    viscosity: float
    seed: int
    commit: str


def save_checkpoint(
    path: str | Path,
    velocity: tuple[FloatArray, FloatArray, FloatArray],
    grid: SpectralGrid3D,
    time: float,
    delta_time: float,
    viscosity: float,
    seed: int = 0,
    commit: str = "unknown",
) -> str:
    """Write a checkpoint and return the velocity checksum."""
    u, v, w = (np.ascontiguousarray(c, dtype=np.float64) for c in velocity)
    checksum = _velocity_checksum(u, v, w)
    np.savez(
        Path(path),
        u=u,
        v=v,
        w=w,
        nodes=np.int64(grid.nodes),
        length=np.float64(grid.length),
        time=np.float64(time),
        delta_time=np.float64(delta_time),
        viscosity=np.float64(viscosity),
        seed=np.int64(seed),
        commit=np.array(str(commit)),
        checksum=np.array(checksum),
        solver_version=np.array("spectral3d/1"),
    )
    return checksum


def load_checkpoint(path: str | Path) -> Checkpoint:
    """Load and verify a checkpoint (rejects symlinks, oversized files, bad checksum)."""
    file_path = Path(path)
    if file_path.is_symlink():
        raise ValueError(f"refusing to read a symlink: {file_path}")
    if file_path.stat().st_size > _MAX_BYTES:
        raise ValueError("checkpoint exceeds the size limit.")
    with np.load(file_path, allow_pickle=False) as archive:
        u = np.asarray(archive["u"], dtype=np.float64)
        v = np.asarray(archive["v"], dtype=np.float64)
        w = np.asarray(archive["w"], dtype=np.float64)
        nodes = int(archive["nodes"])
        length = float(archive["length"])
        time = float(archive["time"])
        delta_time = float(archive["delta_time"])
        viscosity = float(archive["viscosity"])
        seed = int(archive["seed"])
        commit = str(archive["commit"])
        stored_checksum = str(archive["checksum"])
    if _velocity_checksum(u, v, w) != stored_checksum:
        raise ValueError("checkpoint velocity checksum mismatch.")
    grid = spectral_grid_3d(nodes, length)
    return Checkpoint((u, v, w), grid, time, delta_time, viscosity, seed, commit)
