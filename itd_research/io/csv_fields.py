"""Deterministic CSV vector-grid ingestion and writing (research, NumPy only).

The supported CSV layout is one row per structured-grid node with a header line.
2D: ``x,y,u,v`` (optional ``pressure``, ``mask``). 3D: ``x,y,z,u,v,w`` (optional
``pressure``, ``mask``). Rows may be in any order; the structured grid is
reconstructed from the unique sorted coordinates and every node must appear
exactly once. ``mask`` uses 1 for valid and 0 for invalid.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from itd_research.io.field_data import (
    BoolArray,
    FieldData2D,
    FieldData3D,
    FieldMetadata,
    FloatArray,
)

DEFAULT_MAX_BYTES = 256 * 1024 * 1024


def _read_table(path: str | Path, max_bytes: int) -> tuple[list[str], np.ndarray]:
    file_path = Path(path)
    if file_path.is_symlink():
        raise ValueError(f"refusing to read a symlink: {file_path}")
    size = file_path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"file exceeds the {max_bytes}-byte limit: {size} bytes.")
    text = file_path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip() != ""]
    if len(lines) < 2:
        raise ValueError("CSV must contain a header and at least one data row.")
    header = [name.strip().lower() for name in lines[0].split(",")]
    rows = np.array(
        [[float(cell) for cell in line.split(",")] for line in lines[1:]],
        dtype=np.float64,
    )
    if rows.shape[1] != len(header):
        raise ValueError("CSV data columns do not match the header width.")
    return header, rows


def _column(header: list[str], rows: np.ndarray, name: str) -> FloatArray:
    if name not in header:
        raise ValueError(f"CSV is missing required column {name!r}.")
    return np.ascontiguousarray(rows[:, header.index(name)], dtype=np.float64)


def _reconstruct_axis(values: FloatArray, name: str) -> tuple[FloatArray, np.ndarray]:
    unique = np.unique(values)
    index = np.asarray(np.searchsorted(unique, values), dtype=np.intp)
    if not np.array_equal(unique[index], values):
        raise ValueError(f"{name} values do not lie on a structured grid.")
    return unique.astype(np.float64), index


def _fill_grid(
    index_tuple: tuple[np.ndarray, ...],
    shape: tuple[int, ...],
    columns: dict[str, FloatArray],
) -> dict[str, FloatArray]:
    filled: np.ndarray = np.zeros(shape, dtype=bool)
    filled[index_tuple] = True
    if not np.all(filled):
        raise ValueError("CSV does not cover every structured-grid node exactly once.")
    result: dict[str, FloatArray] = {}
    for name, values in columns.items():
        grid: FloatArray = np.empty(shape, dtype=np.float64)
        grid[index_tuple] = values
        result[name] = grid
    return result


def _mask_from_column(mask_values: FloatArray) -> BoolArray:
    if not np.all(np.isin(mask_values, (0.0, 1.0))):
        raise ValueError("mask column must contain only 0 or 1.")
    return mask_values > 0.5


def read_csv_field_2d(
    path: str | Path,
    metadata: FieldMetadata,
    time: float | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FieldData2D:
    """Read a 2D structured velocity field from a ``x,y,u,v[,pressure,mask]`` CSV."""
    header, rows = _read_table(path, max_bytes)
    x_axis, ix = _reconstruct_axis(_column(header, rows, "x"), "x")
    y_axis, iy = _reconstruct_axis(_column(header, rows, "y"), "y")
    shape = (y_axis.size, x_axis.size)
    columns = {"u": _column(header, rows, "u"), "v": _column(header, rows, "v")}
    if "pressure" in header:
        columns["pressure"] = _column(header, rows, "pressure")
    mask: BoolArray | None = None
    if "mask" in header:
        mask_grid = _fill_grid((iy, ix), shape, {"mask": _column(header, rows, "mask")})
        mask = _mask_from_column(mask_grid["mask"].ravel()).reshape(shape)
    grids = _fill_grid((iy, ix), shape, columns)
    return FieldData2D(
        x=x_axis,
        y=y_axis,
        u=grids["u"],
        v=grids["v"],
        metadata=metadata,
        time=time,
        pressure=grids.get("pressure"),
        mask=mask,
    )


def read_csv_field_3d(
    path: str | Path,
    metadata: FieldMetadata,
    time: float | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FieldData3D:
    """Read a 3D structured field from a ``x,y,z,u,v,w[,pressure,mask]`` CSV."""
    header, rows = _read_table(path, max_bytes)
    x_axis, ix = _reconstruct_axis(_column(header, rows, "x"), "x")
    y_axis, iy = _reconstruct_axis(_column(header, rows, "y"), "y")
    z_axis, iz = _reconstruct_axis(_column(header, rows, "z"), "z")
    shape = (z_axis.size, y_axis.size, x_axis.size)
    columns = {
        "u": _column(header, rows, "u"),
        "v": _column(header, rows, "v"),
        "w": _column(header, rows, "w"),
    }
    if "pressure" in header:
        columns["pressure"] = _column(header, rows, "pressure")
    mask: BoolArray | None = None
    if "mask" in header:
        mask_grid = _fill_grid(
            (iz, iy, ix), shape, {"mask": _column(header, rows, "mask")}
        )
        mask = _mask_from_column(mask_grid["mask"].ravel()).reshape(shape)
    grids = _fill_grid((iz, iy, ix), shape, columns)
    return FieldData3D(
        x=x_axis,
        y=y_axis,
        z=z_axis,
        u=grids["u"],
        v=grids["v"],
        w=grids["w"],
        metadata=metadata,
        time=time,
        pressure=grids.get("pressure"),
        mask=mask,
    )


def write_csv_field_2d(path: str | Path, field: FieldData2D) -> None:
    """Write a 2D field to the canonical CSV layout (mainly for test fixtures)."""
    columns = ["x", "y", "u", "v"]
    if field.pressure is not None:
        columns.append("pressure")
    if field.mask is not None:
        columns.append("mask")
    lines = [",".join(columns)]
    for j in range(field.y.size):
        for i in range(field.x.size):
            row = [repr(float(field.x[i])), repr(float(field.y[j])),
                   repr(float(field.u[j, i])), repr(float(field.v[j, i]))]
            if field.pressure is not None:
                row.append(repr(float(field.pressure[j, i])))
            if field.mask is not None:
                row.append("1" if bool(field.mask[j, i]) else "0")
            lines.append(",".join(row))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
