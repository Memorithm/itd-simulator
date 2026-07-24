"""External sequence ingestion for Mission 8 (reuses the Mission 7 safety machinery).

Mission 7's ``itd_research.mission7.ingestion`` already implements safe loading of
``.npz`` velocity-field sequences with checksums and the security/resource limits the
Mission 8 preregistration also requires (path traversal is impossible with ``np.load``,
no pickle, size/frame/grid-cell caps, non-finite rejection, timestamp-order and duplicate
checks). Mission 8 re-uses it rather than re-implementing ingestion, and adds the tuple
view the structural/baseline/event modules consume.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.mission7.ingestion import (
    Frame,
    IngestionLimits,
    SequenceProvenance,
    load_field_sequence,
)

FloatArray: TypeAlias = NDArray[np.float64]

FrameTuple = tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]

__all__ = ["Frame", "IngestionLimits", "SequenceProvenance", "load_field_sequence", "load_sequence_as_tuples"]


def load_sequence_as_tuples(
    directory: str | Path, *, source_id: str, pattern: str = "frame_*.npz",
    limits: IngestionLimits | None = None,
) -> tuple[list[FrameTuple], SequenceProvenance]:
    """Load a sequence and return ``(time, u, v, w, x, y, z)`` tuples plus provenance."""
    frames, provenance = load_field_sequence(directory, source_id=source_id, pattern=pattern, limits=limits)
    tuples: list[FrameTuple] = [(fr.time, fr.u, fr.v, fr.w, fr.x, fr.y, fr.z) for fr in frames]
    return tuples, provenance
