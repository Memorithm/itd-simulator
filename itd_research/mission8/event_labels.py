"""ITD-independent structural (topology-change) event labelling (Mission 8, section 9).

The primary label uses ONLY the established Q-criterion field (never ITD): a topology
event is a persistent change in the count of connected Q>0 regions -- a core merger
(count drops) or a core split (count rises). An alternative label from lambda2<0 regions
is computed for disagreement reporting; the Q-based label is preregistered as primary and
is never replaced after seeing ITD's score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d import lambda2, q_criterion, velocity_gradient_3d
from itd_research.mission8.schema import StructuralEvent
from itd_research.mission8.vortex_regions import (
    core_count_series,
    detect_topology_events,
)

FloatArray: TypeAlias = NDArray[np.float64]


def _scalar_fields(
    frames: list[tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]],
    *, field: str,
) -> list[FloatArray]:
    fields = []
    for _time, u, v, w, x, y, z in frames:
        grad = velocity_gradient_3d(u, v, w, x, y, z, "finite")
        fields.append(q_criterion(grad) if field == "q" else lambda2(grad))
    return fields


def label_structural_events(
    frames: list[tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]],
    *, source_id: str, min_cells: int = 8, persistence: int = 2,
) -> tuple[list[StructuralEvent], dict[str, object]]:
    """Primary Q-criterion topology events, plus a lambda2-based disagreement check.

    Returns the primary event list (Q-based, preregistered) and a diagnostic dict
    reporting the lambda2-based event frames/types for comparison. Disagreement is
    reported, never resolved in ITD's favour (ITD does not appear anywhere here).
    """
    times = [f[0] for f in frames]
    q_fields = _scalar_fields(frames, field="q")
    q_counts = core_count_series(q_fields, threshold=0.0, comparison="greater", min_cells=min_cells)
    q_events = detect_topology_events(q_counts, persistence=persistence)

    l2_fields = _scalar_fields(frames, field="lambda2")
    l2_counts = core_count_series(l2_fields, threshold=0.0, comparison="less", min_cells=min_cells)
    l2_events = detect_topology_events(l2_counts, persistence=persistence)

    primary: list[StructuralEvent] = []
    for i, event in enumerate(q_events):
        primary.append(StructuralEvent(
            event_id=f"{source_id}_q_{i}", event_type=event.event_type,
            event_time=float(times[event.frame_index]), event_frame=event.frame_index,
            event_uncertainty=float(persistence), label_source="established_Q_criterion",
            label_method="connected_components_persistence", source_file=source_id,
            source_index=event.frame_index, itd_independence=True,
        ))

    q_frames = {(e.frame_index, e.event_type) for e in q_events}
    l2_frames = {(e.frame_index, e.event_type) for e in l2_events}
    disagreement = {
        "q_region_counts": q_counts,
        "lambda2_region_counts": l2_counts,
        "q_events": [(e.frame_index, e.event_type) for e in q_events],
        "lambda2_events": [(e.frame_index, e.event_type) for e in l2_events],
        "agree": sorted(q_frames & l2_frames),
        "q_only": sorted(q_frames - l2_frames),
        "lambda2_only": sorted(l2_frames - q_frames),
    }
    return primary, disagreement


@dataclass(frozen=True)
class BinaryLabels:
    """Frame-level positive/negative labels derived from structural events (a horizon)."""

    labels: NDArray[np.int64]
    positive_frames: tuple[int, ...]


def labels_from_events(n_frames: int, events: list[StructuralEvent], *, horizon: int) -> BinaryLabels:
    """A frame is positive iff a structural event occurs within ``horizon`` frames ahead."""
    labels: NDArray[np.int64] = np.zeros(n_frames, dtype=np.int64)
    positive: set[int] = set()
    for event in events:
        for offset in range(horizon + 1):
            idx = event.event_frame - offset
            if 0 <= idx < n_frames:
                positive.add(idx)
    for idx in positive:
        labels[idx] = 1
    return BinaryLabels(labels=labels, positive_frames=tuple(sorted(positive)))
