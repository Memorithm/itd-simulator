"""Safe NumPy ``.npz`` ingestion and writing (research).

Loading always uses ``allow_pickle=False`` so untrusted archives cannot execute
code. Expected arrays: 2D ``x, y, u, v`` (optional ``pressure``, ``mask``);
3D ``x, y, z, u, v, w`` (optional ``pressure``, ``mask``).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from itd_research.io.field_data import (
    BoolArray,
    FieldData2D,
    FieldData3D,
    FieldMetadata,
)

DEFAULT_MAX_BYTES = 512 * 1024 * 1024


def _open(path: str | Path, max_bytes: int) -> dict[str, np.ndarray]:
    file_path = Path(path)
    if file_path.is_symlink():
        raise ValueError(f"refusing to read a symlink: {file_path}")
    if file_path.stat().st_size > max_bytes:
        raise ValueError(f"file exceeds the {max_bytes}-byte limit.")
    with np.load(file_path, allow_pickle=False) as handle:
        return {key: np.asarray(handle[key]) for key in handle.files}


def _mask(arrays: dict[str, np.ndarray]) -> BoolArray | None:
    if "mask" not in arrays:
        return None
    return np.asarray(arrays["mask"], dtype=bool)


def read_npz_field_2d(
    path: str | Path,
    metadata: FieldMetadata,
    time: float | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FieldData2D:
    """Read a 2D field from an ``.npz`` archive with keys ``x, y, u, v``."""
    arrays = _open(path, max_bytes)
    return FieldData2D(
        x=arrays["x"],
        y=arrays["y"],
        u=arrays["u"],
        v=arrays["v"],
        metadata=metadata,
        time=time,
        pressure=arrays.get("pressure"),
        mask=_mask(arrays),
    )


def read_npz_field_3d(
    path: str | Path,
    metadata: FieldMetadata,
    time: float | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FieldData3D:
    """Read a 3D field from an ``.npz`` archive with keys ``x, y, z, u, v, w``."""
    arrays = _open(path, max_bytes)
    return FieldData3D(
        x=arrays["x"],
        y=arrays["y"],
        z=arrays["z"],
        u=arrays["u"],
        v=arrays["v"],
        w=arrays["w"],
        metadata=metadata,
        time=time,
        pressure=arrays.get("pressure"),
        mask=_mask(arrays),
    )


def write_npz_field_2d(path: str | Path, field: FieldData2D) -> None:
    """Write a 2D field to an ``.npz`` archive (mainly for test fixtures)."""
    arrays = {"x": field.x, "y": field.y, "u": field.u, "v": field.v}
    if field.pressure is not None:
        arrays["pressure"] = field.pressure
    if field.mask is not None:
        arrays["mask"] = field.mask
    np.savez(Path(path), **arrays)


def write_npz_field_3d(path: str | Path, field: FieldData3D) -> None:
    """Write a 3D field to an ``.npz`` archive (mainly for test fixtures)."""
    arrays = {
        "x": field.x,
        "y": field.y,
        "z": field.z,
        "u": field.u,
        "v": field.v,
        "w": field.w,
    }
    if field.pressure is not None:
        arrays["pressure"] = field.pressure
    if field.mask is not None:
        arrays["mask"] = field.mask
    np.savez(Path(path), **arrays)
