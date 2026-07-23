"""ITD-independent vortex-event labelling for the prediction study (research, H7).

The event time is defined by a criterion that never touches the ITD signature, so
using ITD to *predict* the event cannot leak the label. The criterion here is a
**vortex-core count** obtained from connected components of the strong-vorticity
mask ``|omega| > fraction * max|omega|`` (components below ``min_cells`` are
discarded as noise). A co-rotating like-signed vortex pair starts as two cores and
merges into one; the merger frame is the first frame that reaches, and keeps, a
single core.

The connected-component labeller is a small dependency-free 4-connectivity flood
fill so the module imports with NumPy alone (no SciPy at import time).
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]


def _label_components(mask: BoolArray) -> tuple[NDArray[np.int64], list[int]]:
    """4-connectivity connected components of a 2D boolean mask.

    Returns the integer label field (0 = background) and the list of component
    sizes in label order. Deterministic: a raster scan seeds components and an
    explicit stack does the flood fill, so no ordering depends on hashing.
    """
    rows, cols = mask.shape
    labels = np.zeros((rows, cols), dtype=np.int64)
    sizes: list[int] = []
    current = 0
    for r0 in range(rows):
        for c0 in range(cols):
            if not mask[r0, c0] or labels[r0, c0] != 0:
                continue
            current += 1
            size = 0
            stack = [(r0, c0)]
            labels[r0, c0] = current
            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols and mask[rr, cc] and labels[rr, cc] == 0:
                        labels[rr, cc] = current
                        stack.append((rr, cc))
            sizes.append(size)
    return labels, sizes


def count_vortex_cores(
    omega: FloatArray, fraction: float = 0.6, min_cells: int = 20
) -> int:
    """Number of strong-vorticity cores in a 2D vorticity field.

    A cell belongs to a core if ``|omega|`` exceeds ``fraction`` of the field
    maximum; connected components smaller than ``min_cells`` are dropped as noise.
    This is an ITD-independent structural count used only to *define* events.
    """
    field = np.abs(np.asarray(omega, dtype=np.float64))
    if field.ndim != 2:
        raise ValueError("omega must be a 2D vorticity field.")
    peak = float(np.max(field))
    if peak <= 0.0:
        return 0
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must lie strictly between 0 and 1.")
    mask: BoolArray = field > fraction * peak
    _, sizes = _label_components(mask)
    return int(sum(1 for size in sizes if size >= min_cells))


def core_count_series(
    vorticity: tuple[FloatArray, ...], fraction: float = 0.6, min_cells: int = 20
) -> tuple[int, ...]:
    """Vortex-core count for each snapshot in a sequence."""
    return tuple(count_vortex_cores(w, fraction, min_cells) for w in vorticity)


def detect_merger_frame(core_counts: tuple[int, ...]) -> int | None:
    """First frame index that reaches, and keeps, a single core after having >=2.

    Returns ``None`` if the sequence never settles to a persistent single core
    preceded by a multi-core phase (no clean merger detected). Persistence is
    required so a transient count dip is not mistaken for the merger.
    """
    counts = list(core_counts)
    n = len(counts)
    saw_multiple = False
    for i in range(n):
        if counts[i] >= 2:
            saw_multiple = True
        if saw_multiple and counts[i] == 1 and all(c == 1 for c in counts[i:]):
            return i
    return None
