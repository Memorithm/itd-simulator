"""Minimal legacy VTK ASCII reader/writer for structured velocity fields (research).

Only the legacy ASCII ``STRUCTURED_POINTS`` and ``RECTILINEAR_GRID`` datasets with
a ``POINT_DATA`` ``VECTORS`` array are supported. This is a deliberately narrow,
dependency-free reader (no VTK/HDF5 library). Binary VTK, unstructured grids, and
XML ``.vtu`` are out of scope; add a pinned, justified dependency if those are
needed. VTK point ordering is x-fastest, then y, then z.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from itd_research.io.field_data import (
    FieldData2D,
    FieldData3D,
    FieldMetadata,
    FloatArray,
)

DEFAULT_MAX_BYTES = 256 * 1024 * 1024


def _tokens(path: str | Path, max_bytes: int) -> list[str]:
    file_path = Path(path)
    if file_path.is_symlink():
        raise ValueError(f"refusing to read a symlink: {file_path}")
    if file_path.stat().st_size > max_bytes:
        raise ValueError(f"file exceeds the {max_bytes}-byte limit.")
    text = file_path.read_text(encoding="utf-8")
    if "ASCII" not in text:
        raise ValueError("only legacy ASCII VTK is supported.")
    return text.split()


def _read_dimensions(tokens: list[str]) -> tuple[int, int, int, int]:
    index = tokens.index("DIMENSIONS")
    nx, ny, nz = (int(tokens[index + 1]), int(tokens[index + 2]), int(tokens[index + 3]))
    return nx, ny, nz, index + 4


def _axis_from_coordinates(tokens: list[str], key: str, count: int) -> FloatArray:
    index = tokens.index(key)
    values = [float(tokens[index + 2 + i]) for i in range(count)]
    return np.array(values, dtype=np.float64)


def _read_vectors(tokens: list[str], total: int) -> FloatArray:
    index = tokens.index("VECTORS")
    # tokens: VECTORS name dtype, then 3*total floats
    start = index + 3
    values = np.array(
        [float(token) for token in tokens[start : start + 3 * total]], dtype=np.float64
    )
    if values.size != 3 * total:
        raise ValueError("VECTORS data does not match POINT_DATA count.")
    return values.reshape(total, 3)


def _read_structured(tokens: list[str]) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    nx, ny, nz, _ = _read_dimensions(tokens)
    total = nx * ny * nz
    if "STRUCTURED_POINTS" in tokens:
        origin_index = tokens.index("ORIGIN")
        spacing_index = tokens.index("SPACING")
        origin = [float(tokens[origin_index + 1 + i]) for i in range(3)]
        spacing = [float(tokens[spacing_index + 1 + i]) for i in range(3)]
        x = origin[0] + spacing[0] * np.arange(nx, dtype=np.float64)
        y = origin[1] + spacing[1] * np.arange(ny, dtype=np.float64)
        z = origin[2] + spacing[2] * np.arange(nz, dtype=np.float64)
    elif "RECTILINEAR_GRID" in tokens:
        x = _axis_from_coordinates(tokens, "X_COORDINATES", nx)
        y = _axis_from_coordinates(tokens, "Y_COORDINATES", ny)
        z = _axis_from_coordinates(tokens, "Z_COORDINATES", nz)
    else:
        raise ValueError("only STRUCTURED_POINTS or RECTILINEAR_GRID are supported.")
    vectors = _read_vectors(tokens, total)  # x-fastest ordering
    return x, y, z, vectors.reshape(nz, ny, nx, 3)


def read_vtk_structured(
    path: str | Path,
    metadata: FieldMetadata,
    time: float | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FieldData2D | FieldData3D:
    """Read a structured legacy-ASCII VTK velocity field (2D if a singleton axis)."""
    tokens = _tokens(path, max_bytes)
    x, y, z, vectors = _read_structured(tokens)
    u = vectors[..., 0]
    v = vectors[..., 1]
    w = vectors[..., 2]
    if z.size == 1:
        return FieldData2D(
            x=x, y=y, u=u[0], v=v[0], metadata=metadata, time=time
        )
    return FieldData3D(
        x=x, y=y, z=z, u=u, v=v, w=w, metadata=metadata, time=time
    )


def write_vtk_structured_points_3d(path: str | Path, field: FieldData3D) -> None:
    """Write a 3D field as legacy ASCII VTK STRUCTURED_POINTS (uniform grid only).

    Requires uniform spacing on each axis (raises otherwise). Mainly used to
    produce small deterministic test fixtures.
    """
    from itd_research.io.field_data import is_uniform

    for axis, name in ((field.x, "x"), (field.y, "y"), (field.z, "z")):
        if not is_uniform(axis):
            raise ValueError(f"{name} axis must be uniform for STRUCTURED_POINTS.")
    nx, ny, nz = field.x.size, field.y.size, field.z.size
    dx = float(field.x[1] - field.x[0])
    dy = float(field.y[1] - field.y[0])
    dz = float(field.z[1] - field.z[0])
    lines = [
        "# vtk DataFile Version 3.0",
        "itd_research structured field",
        "ASCII",
        "DATASET STRUCTURED_POINTS",
        f"DIMENSIONS {nx} {ny} {nz}",
        f"ORIGIN {float(field.x[0])!r} {float(field.y[0])!r} {float(field.z[0])!r}",
        f"SPACING {dx!r} {dy!r} {dz!r}",
        f"POINT_DATA {nx * ny * nz}",
        "VECTORS velocity double",
    ]
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                lines.append(
                    f"{float(field.u[k, j, i])!r} "
                    f"{float(field.v[k, j, i])!r} "
                    f"{float(field.w[k, j, i])!r}"
                )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
