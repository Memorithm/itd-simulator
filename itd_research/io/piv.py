"""PIV vector-grid ingestion with masks and honest gap repair (research).

PIV data commonly contains invalid (spurious/missing) vectors. This adapter reads
a ``x,y,u,v,valid`` CSV and supports two modes:

* ``strict`` — invalid vectors are masked out; no interpolation is performed;
* ``repair`` — invalid vectors are filled by a deterministic iterative
  neighbour average, and the number of interpolated vectors is reported.

Interpolated values are never presented as measured data: a
:class:`PivRepairReport` records original, invalid, interpolated, and masked
counts and the interpolation method/parameters, and the returned field keeps a
mask distinguishing filled from unfilled nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from itd_research.io.field_data import FieldData2D, FieldMetadata, FloatArray

DEFAULT_MAX_BYTES = 256 * 1024 * 1024
VALID_MODES = ("strict", "repair")


@dataclass(frozen=True)
class PivRepairReport:
    """Accounting for a PIV ingestion pass."""

    mode: str
    n_original: int
    n_invalid: int
    n_interpolated: int
    n_masked: int
    method: str
    parameters: tuple[tuple[str, float], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "n_original": self.n_original,
            "n_invalid": self.n_invalid,
            "n_interpolated": self.n_interpolated,
            "n_masked": self.n_masked,
            "method": self.method,
            "parameters": {key: value for key, value in self.parameters},
        }


def _neighbour_average_fill(
    field: FloatArray, valid: np.ndarray, iterations: int
) -> tuple[FloatArray, np.ndarray]:
    """Deterministic Jacobi neighbour-average fill of invalid nodes.

    Returns the filled field and the boolean mask of nodes that are finite after
    filling (originally valid or successfully interpolated).
    """
    filled = np.where(valid, field, 0.0).astype(np.float64)
    known = valid.copy()
    for _ in range(iterations):
        if np.all(known):
            break
        up = np.roll(filled, 1, axis=0)
        down = np.roll(filled, -1, axis=0)
        left = np.roll(filled, 1, axis=1)
        right = np.roll(filled, -1, axis=1)
        known_up = np.roll(known, 1, axis=0)
        known_down = np.roll(known, -1, axis=0)
        known_left = np.roll(known, 1, axis=1)
        known_right = np.roll(known, -1, axis=1)
        # Do not wrap across boundaries: zero the rolled-in edge contributions.
        known_up[0, :] = False
        known_down[-1, :] = False
        known_left[:, 0] = False
        known_right[:, -1] = False
        neighbour_count = (
            known_up.astype(np.float64)
            + known_down
            + known_left
            + known_right
        )
        neighbour_sum = (
            np.where(known_up, up, 0.0)
            + np.where(known_down, down, 0.0)
            + np.where(known_left, left, 0.0)
            + np.where(known_right, right, 0.0)
        )
        fillable = (~known) & (neighbour_count > 0.0)
        filled = np.where(
            fillable, neighbour_sum / np.maximum(neighbour_count, 1.0), filled
        )
        known = known | fillable
    return filled, known


def read_piv_csv_2d(
    path: str | Path,
    metadata: FieldMetadata,
    mode: str = "strict",
    time: float | None = None,
    repair_iterations: int = 32,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> tuple[FieldData2D, PivRepairReport]:
    """Read a PIV ``x,y,u,v,valid`` CSV in ``strict`` or ``repair`` mode."""
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}.")
    from itd_research.io.csv_fields import _column, _read_table, _reconstruct_axis

    header, rows = _read_table(path, max_bytes)
    x_axis, ix = _reconstruct_axis(_column(header, rows, "x"), "x")
    y_axis, iy = _reconstruct_axis(_column(header, rows, "y"), "y")
    shape = (y_axis.size, x_axis.size)

    valid_column = "valid" if "valid" in header else "mask"
    valid_values = _column(header, rows, valid_column)
    if not np.all(np.isin(valid_values, (0.0, 1.0))):
        raise ValueError("valid/mask column must contain only 0 or 1.")

    def scatter(name: str) -> FloatArray:
        grid = np.zeros(shape, dtype=np.float64)
        grid[iy, ix] = _column(header, rows, name)
        return grid

    valid = np.zeros(shape, dtype=bool)
    valid[iy, ix] = valid_values > 0.5
    u = scatter("u")
    v = scatter("v")

    n_original = int(valid.size)
    n_invalid = int(np.count_nonzero(~valid))

    if mode == "strict":
        # Invalid nodes become NaN and are excluded via the mask.
        u = np.where(valid, u, np.nan)
        v = np.where(valid, v, np.nan)
        final_mask = valid
        report = PivRepairReport(
            mode="strict",
            n_original=n_original,
            n_invalid=n_invalid,
            n_interpolated=0,
            n_masked=n_invalid,
            method="none",
            parameters=(),
        )
    else:
        u, known_u = _neighbour_average_fill(u, valid, repair_iterations)
        v, known_v = _neighbour_average_fill(v, valid, repair_iterations)
        final_mask = known_u & known_v
        n_interpolated = int(np.count_nonzero(final_mask & ~valid))
        n_masked = int(np.count_nonzero(~final_mask))
        u = np.where(final_mask, u, np.nan)
        v = np.where(final_mask, v, np.nan)
        report = PivRepairReport(
            mode="repair",
            n_original=n_original,
            n_invalid=n_invalid,
            n_interpolated=n_interpolated,
            n_masked=n_masked,
            method="jacobi_neighbour_average",
            parameters=(("repair_iterations", float(repair_iterations)),),
        )

    field = FieldData2D(
        x=x_axis,
        y=y_axis,
        u=u,
        v=v,
        metadata=metadata,
        time=time,
        mask=final_mask if n_invalid > 0 else None,
    )
    return field, report
