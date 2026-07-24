"""ITD-independent 3D vortex-region detection and tracking (Mission 8, sections 9/11/12).

Connected components of an established scalar field (Q-criterion > 0, or lambda2 < 0) on a
3D grid, found by a deterministic 6-connectivity flood fill -- the same style as the
certified-adjacent 2D labeller in ``itd_research.prediction.events`` extended to 3D and to
BOTH merge and split. ITD never participates: the mask, the labelling and the tracking use
only an established scalar field. This module also provides the transparent region-level
metrics (IoU, Dice, centroid distance, Hausdorff-like max nearest distance) Mission 8 needs
for localization evaluation, and a lightweight frame-to-frame region tracker used to define
core_merger / core_split events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.mission8.schema import FrameRegions, RegionRecord

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]
IntArray: TypeAlias = NDArray[np.int64]

_NEIGHBORS_6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def label_components_3d(mask: BoolArray, *, periodic: bool = False) -> tuple[IntArray, list[int]]:
    """Deterministic 6-connectivity connected components of a 3D boolean mask.

    ``periodic=False`` (default) treats the array as a bounded box: a structure that
    touches the array edge stops there. ``periodic=True`` treats each axis as wrapping
    (a torus), so a structure straddling e.g. index 0 / index N-1 is correctly seen as one
    component -- the physically correct choice for a field sampled on a genuinely periodic
    full simulation domain, but WRONG for an arbitrary sub-window cutout of a larger
    periodic domain (its own edges are not physical periodic boundaries; e.g. a JHTDB
    cutout box). Callers must match this flag to the same convention used for the
    field's derivatives (``velocity_gradient_3d``'s ``boundary_mode``).

    Returns the integer label field (0 = background) and component sizes in label order.
    A raster scan seeds components; an explicit stack does the flood fill (no recursion, no
    hashing), so results are bit-reproducible regardless of platform.
    """
    if mask.ndim != 3:
        raise ValueError("mask must be a 3D array.")
    nz, ny, nx = mask.shape
    labels: IntArray = np.zeros((nz, ny, nx), dtype=np.int64)
    sizes: list[int] = []
    current = 0
    for z0 in range(nz):
        for y0 in range(ny):
            for x0 in range(nx):
                if not mask[z0, y0, x0] or labels[z0, y0, x0] != 0:
                    continue
                current += 1
                size = 0
                stack = [(z0, y0, x0)]
                labels[z0, y0, x0] = current
                while stack:
                    z, y, x = stack.pop()
                    size += 1
                    for dz, dy, dx_ in _NEIGHBORS_6:
                        zz, yy, xx = z + dz, y + dy, x + dx_
                        if periodic:
                            zz, yy, xx = zz % nz, yy % ny, xx % nx
                        elif not (0 <= zz < nz and 0 <= yy < ny and 0 <= xx < nx):
                            continue
                        if mask[zz, yy, xx] and labels[zz, yy, xx] == 0:
                            labels[zz, yy, xx] = current
                            stack.append((zz, yy, xx))
                sizes.append(size)
    return labels, sizes


def region_records(labels: IntArray, sizes: list[int], min_cells: int) -> tuple[RegionRecord, ...]:
    """Regions at/above ``min_cells``, with cell-index centroids (deterministic order).

    The centroid is a plain arithmetic mean of cell indices, which is only meaningful for
    a component that does NOT wrap across a periodic boundary (a wrapping component's
    naive index mean lands near the middle of the domain, not at the true center of mass).
    Volume and count are unaffected; callers needing a centroid for a periodic-wrapping
    component should treat it as approximate.
    """
    records: list[RegionRecord] = []
    for label in range(1, len(sizes) + 1):
        if sizes[label - 1] < min_cells:
            continue
        zz, yy, xx = np.nonzero(labels == label)
        centroid = (float(np.mean(zz)), float(np.mean(yy)), float(np.mean(xx)))
        records.append(RegionRecord(label=label, volume_cells=int(sizes[label - 1]), centroid=centroid))
    return tuple(records)


def background_noise_threshold(scalar_field: FloatArray, rel: float = 1e-6) -> float:
    """A small positive threshold scaled to the field's own magnitude.

    An exact ``> 0.0`` threshold is the textbook Q/lambda2-criterion convention, but on a
    field with a large near-exactly-zero background (e.g. an isolated manufactured vortex
    surrounded by quiescent fluid) floating-point round-off can flip a scattered background
    cell to either sign; through periodic connectivity those scattered cells can chain into
    one spurious giant "region". Established diagnostics on genuinely turbulent data (where
    the field is nowhere near exactly zero almost everywhere) are not affected in practice;
    this threshold is for exactly the quiescent-background manufactured-fixture case.
    """
    return rel * float(np.max(np.abs(scalar_field)))


def detect_regions(scalar_field: FloatArray, *, threshold: float = 0.0,
                    comparison: str = "greater", min_cells: int = 8,
                    periodic: bool = False) -> tuple[IntArray, tuple[RegionRecord, ...]]:
    """Connected regions of an established scalar field crossing a threshold.

    ``comparison="greater"`` selects ``scalar_field > threshold`` (e.g. Q-criterion > 0);
    ``comparison="less"`` selects ``scalar_field < threshold`` (e.g. lambda2 < 0).
    ``periodic`` must match the boundary convention used to compute ``scalar_field``'s
    derivatives (see :func:`label_components_3d`).
    """
    if comparison == "greater":
        mask: BoolArray = scalar_field > threshold
    elif comparison == "less":
        mask = scalar_field < threshold
    else:
        raise ValueError("comparison must be 'greater' or 'less'.")
    labels, sizes = label_components_3d(mask, periodic=periodic)
    return labels, region_records(labels, sizes, min_cells)


def frame_regions(scalar_field: FloatArray, frame_index: int, time: float, *,
                   threshold: float = 0.0, comparison: str = "greater",
                   min_cells: int = 8, periodic: bool = False) -> FrameRegions:
    """Convenience wrapper returning a :class:`FrameRegions` for one snapshot."""
    _, records = detect_regions(scalar_field, threshold=threshold, comparison=comparison,
                                 min_cells=min_cells, periodic=periodic)
    return FrameRegions(frame_index=frame_index, time=time, regions=records)


# --- Region-level metrics (Mission 8 section 11) --------------------------------------------

def iou(mask_a: BoolArray, mask_b: BoolArray) -> float:
    """Intersection-over-union of two boolean region masks."""
    inter = int(np.sum(mask_a & mask_b))
    union = int(np.sum(mask_a | mask_b))
    return float(inter / union) if union else float("nan")


def dice(mask_a: BoolArray, mask_b: BoolArray) -> float:
    """Dice coefficient of two boolean region masks."""
    inter = int(np.sum(mask_a & mask_b))
    denom = int(np.sum(mask_a)) + int(np.sum(mask_b))
    return float(2.0 * inter / denom) if denom else float("nan")


def centroid_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))


def max_nearest_distance(mask_a: BoolArray, mask_b: BoolArray) -> float:
    """A Hausdorff-like directed max-nearest-cell distance, symmetrised.

    O(n_a * n_b) on cell coordinates; only used on the tiny manufactured/oracle fields and
    on downsampled region masks, never on a raw full-resolution external volume.
    """
    pa = np.argwhere(mask_a).astype(np.float64)
    pb = np.argwhere(mask_b).astype(np.float64)
    if pa.size == 0 or pb.size == 0:
        return float("nan")

    def directed(p: FloatArray, q: FloatArray) -> float:
        d = np.sqrt(np.sum((p[:, None, :] - q[None, :, :]) ** 2, axis=-1))
        return float(np.max(np.min(d, axis=1)))

    return float(max(directed(pa, pb), directed(pb, pa)))


# --- Frame-to-frame tracking + topology events (Mission 8 section 9) ------------------------

@dataclass(frozen=True)
class TopologyEvent:
    """A detected core-count change event (candidate for schema.StructuralEvent)."""

    event_type: str    # "core_merger" | "core_split"
    frame_index: int
    from_count: int
    to_count: int


def core_count_series(scalar_fields: list[FloatArray], *, threshold: float = 0.0,
                       comparison: str = "greater", min_cells: int = 8,
                       periodic: bool = False) -> list[int]:
    """Region count per frame (an ITD-independent structural time series)."""
    counts = []
    for field_ in scalar_fields:
        _, records = detect_regions(field_, threshold=threshold, comparison=comparison,
                                     min_cells=min_cells, periodic=periodic)
        counts.append(len(records))
    return counts


def detect_topology_events(counts: list[int], *, persistence: int = 2) -> list[TopologyEvent]:
    """First frames where the region count changes and PERSISTS for ``persistence`` frames.

    Mirrors the certified-adjacent 2D merger detector's persistence rule (a transient dip or
    spike is not an event), generalised to both directions (merger: count decreases; split:
    count increases) and to counts other than exactly one/two.

    Requires BOTH the post-change value to persist for ``persistence`` frames AND the
    pre-change value to have already been stable for ``persistence`` frames beforehand. The
    post-only check alone lets a single-frame blip that reverts (e.g. ``2,2,1,2,2``) pass:
    the dip itself is correctly rejected (it does not persist), but the "recovery" back to
    the original value then looks like a new, persistent change and fires a spurious event.
    Requiring a stable pre-history rejects that recovery too, since the frame just before it
    was itself still mid-transient.
    """
    events: list[TopologyEvent] = []
    i = 1
    n = len(counts)
    while i < n:
        if counts[i] != counts[i - 1]:
            post_window = counts[i:min(i + persistence, n)]
            post_ok = len(post_window) == min(persistence, n - i) and all(c == counts[i] for c in post_window)
            pre_window = counts[max(0, i - persistence):i]
            pre_ok = len(pre_window) == min(persistence, i) and all(c == counts[i - 1] for c in pre_window)
            if post_ok and pre_ok:
                event_type = "core_merger" if counts[i] < counts[i - 1] else "core_split"
                events.append(TopologyEvent(event_type, i, counts[i - 1], counts[i]))
        i += 1
    return events
