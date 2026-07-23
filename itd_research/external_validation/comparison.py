"""Deterministic region-overlap and correlation metrics (research).

Established diagnostics (Q, swirling strength, Okubo-Weiss) are **local** scalar
fields; ITD components are **global** aggregates. To compare them fairly this
module reduces each local field to a region (a boolean mask) or to a rank/linear
correlation, and measures agreement between regions and between fields:

* :func:`threshold_region` turns a scalar field into a boolean region by sign or
  by quantile, honouring an optional validity mask;
* :func:`region_overlap` reports Jaccard, Dice, and containment between regions;
* :func:`connected_components` counts and sizes connected regions (4- or
  8-connectivity) with a deterministic flood fill;
* :func:`pearson_correlation` / :func:`spearman_correlation` correlate two fields
  over their valid nodes, returning ``None`` when a field is (near-)constant so
  the coefficient is undefined rather than a spurious number.

Everything is NumPy-only and deterministic. No metric asserts that ITD or any
established diagnostic is superior; they quantify where the two views agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]

_VARIANCE_FLOOR = 1.0e-24


def _as_field(field: object, name: str) -> FloatArray:
    array = np.asarray(field, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a 2D array.")
    return array


def _valid_mask(shape: tuple[int, ...], mask: object | None) -> BoolArray:
    if mask is None:
        return np.ones(shape, dtype=bool)
    array = np.asarray(mask, dtype=bool)
    if array.shape != shape:
        raise ValueError("mask shape does not match the field shape.")
    return array


def threshold_region(
    field: object,
    *,
    sign: str | None = None,
    quantile: float | None = None,
    absolute: bool = False,
    mask: object | None = None,
) -> BoolArray:
    """Reduce a scalar field to a boolean region.

    Exactly one selection rule must be given:

    * ``sign="positive"`` / ``"negative"`` selects ``field > 0`` / ``field < 0``
      (e.g. the Q-criterion or Okubo-Weiss vortex convention);
    * ``quantile=q`` (0 < q < 1) selects nodes at or above the ``q``-quantile of
      the field (or of ``|field|`` when ``absolute`` is set), computed over valid
      nodes only.

    Invalid (masked-out) nodes are never selected.
    """
    array = _as_field(field, "field")
    valid = _valid_mask(array.shape, mask)
    if (sign is None) == (quantile is None):
        raise ValueError("provide exactly one of sign= or quantile=.")

    if sign is not None:
        if sign == "positive":
            region = array > 0.0
        elif sign == "negative":
            region = array < 0.0
        else:
            raise ValueError("sign must be 'positive' or 'negative'.")
        return np.asarray(region & valid, dtype=bool)

    q = float(quantile)  # type: ignore[arg-type]
    if not (0.0 < q < 1.0):
        raise ValueError("quantile must lie strictly between 0 and 1.")
    values = np.abs(array) if absolute else array
    finite_valid = valid & np.isfinite(values)
    if not bool(np.any(finite_valid)):
        return np.zeros(array.shape, dtype=bool)
    threshold = float(np.quantile(values[finite_valid], q))
    return np.asarray((values >= threshold) & finite_valid, dtype=bool)


@dataclass(frozen=True)
class RegionOverlap:
    """Set-overlap metrics between two boolean regions of equal shape."""

    jaccard: float
    dice: float
    a_fraction: float
    b_fraction: float
    intersection_fraction: float
    a_in_b: float
    b_in_a: float

    def as_dict(self) -> dict[str, float]:
        return {
            "jaccard": self.jaccard,
            "dice": self.dice,
            "a_fraction": self.a_fraction,
            "b_fraction": self.b_fraction,
            "intersection_fraction": self.intersection_fraction,
            "a_in_b": self.a_in_b,
            "b_in_a": self.b_in_a,
        }


def region_overlap(a: object, b: object) -> RegionOverlap:
    """Jaccard, Dice, and containment between two boolean regions."""
    a_mask = np.asarray(a, dtype=bool)
    b_mask = np.asarray(b, dtype=bool)
    if a_mask.shape != b_mask.shape:
        raise ValueError("regions must share a shape.")
    total = float(a_mask.size)
    a_count = float(np.count_nonzero(a_mask))
    b_count = float(np.count_nonzero(b_mask))
    inter = float(np.count_nonzero(a_mask & b_mask))
    union = a_count + b_count - inter
    jaccard = inter / union if union > 0.0 else 0.0
    dice = (2.0 * inter) / (a_count + b_count) if (a_count + b_count) > 0.0 else 0.0
    return RegionOverlap(
        jaccard=jaccard,
        dice=dice,
        a_fraction=a_count / total,
        b_fraction=b_count / total,
        intersection_fraction=inter / total,
        a_in_b=inter / a_count if a_count > 0.0 else 0.0,
        b_in_a=inter / b_count if b_count > 0.0 else 0.0,
    )


def connected_components(
    mask: object, connectivity: int = 4
) -> tuple[int, tuple[int, ...]]:
    """Count connected regions in a boolean mask via a deterministic flood fill.

    Returns ``(n_components, sizes)`` with ``sizes`` sorted descending. Scanning
    proceeds in row-major order so the labelling is fully deterministic.
    """
    region = np.asarray(mask, dtype=bool)
    if region.ndim != 2:
        raise ValueError("mask must be 2D.")
    neighbours: tuple[tuple[int, int], ...]
    if connectivity == 4:
        neighbours = ((-1, 0), (1, 0), (0, -1), (0, 1))
    elif connectivity == 8:
        neighbours = (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        )
    else:
        raise ValueError("connectivity must be 4 or 8.")

    ny, nx = region.shape
    seen = np.zeros(region.shape, dtype=bool)
    sizes: list[int] = []
    for i0 in range(ny):
        for j0 in range(nx):
            if not region[i0, j0] or seen[i0, j0]:
                continue
            size = 0
            stack = [(i0, j0)]
            seen[i0, j0] = True
            while stack:
                i, j = stack.pop()
                size += 1
                for di, dj in neighbours:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < ny and 0 <= jj < nx and region[ii, jj] and not seen[ii, jj]:
                        seen[ii, jj] = True
                        stack.append((ii, jj))
            sizes.append(size)
    sizes.sort(reverse=True)
    return len(sizes), tuple(sizes)


def _paired_valid(a: FloatArray, b: FloatArray, mask: object | None) -> tuple[FloatArray, FloatArray]:
    if a.shape != b.shape:
        raise ValueError("fields must share a shape.")
    valid = _valid_mask(a.shape, mask) & np.isfinite(a) & np.isfinite(b)
    return a[valid], b[valid]


def pearson_correlation(a: object, b: object, mask: object | None = None) -> float | None:
    """Pearson correlation over valid nodes; ``None`` if a field is constant."""
    fa = _as_field(a, "a")
    fb = _as_field(b, "b")
    xa, xb = _paired_valid(fa, fb, mask)
    if xa.size < 2:
        return None
    xa = xa - xa.mean()
    xb = xb - xb.mean()
    va = float(np.dot(xa, xa))
    vb = float(np.dot(xb, xb))
    if va <= _VARIANCE_FLOOR or vb <= _VARIANCE_FLOOR:
        return None
    return float(np.dot(xa, xb) / np.sqrt(va * vb))


def _rankdata_average(values: FloatArray) -> FloatArray:
    """Average-tie ranks (the standard Spearman ranking), NumPy-only."""
    flat = np.asarray(values, dtype=np.float64).ravel()
    sorter = np.argsort(flat, kind="mergesort")
    inverse: NDArray[np.intp] = np.empty(flat.size, dtype=np.intp)
    inverse[sorter] = np.arange(flat.size, dtype=np.intp)
    ordered = flat[sorter]
    is_new = np.ones(flat.size, dtype=bool)
    is_new[1:] = ordered[1:] != ordered[:-1]
    dense = np.cumsum(is_new)[inverse]
    boundaries = np.concatenate(
        (np.flatnonzero(is_new).astype(np.float64), np.array([float(flat.size)]))
    )
    return np.asarray(0.5 * (boundaries[dense - 1] + boundaries[dense] + 1.0), dtype=np.float64)


def spearman_correlation(a: object, b: object, mask: object | None = None) -> float | None:
    """Spearman rank correlation over valid nodes; ``None`` if undefined."""
    fa = _as_field(a, "a")
    fb = _as_field(b, "b")
    xa, xb = _paired_valid(fa, fb, mask)
    if xa.size < 2:
        return None
    ranked_a = _rankdata_average(xa).reshape(1, -1)
    ranked_b = _rankdata_average(xb).reshape(1, -1)
    return pearson_correlation(ranked_a, ranked_b)


def compare_scalar_fields(
    a: object, b: object, mask: object | None = None
) -> dict[str, float | None]:
    """Pearson and Spearman correlation between two scalar fields."""
    return {
        "pearson": pearson_correlation(a, b, mask),
        "spearman": spearman_correlation(a, b, mask),
    }
