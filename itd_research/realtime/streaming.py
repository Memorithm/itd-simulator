"""Bounded, deterministic streaming ITD evaluation (research).

A ``FrameStream`` ingests 2D vorticity frames in timestamp order, keeps a bounded
history, detects missing/duplicate/out-of-order frames, and computes an
incremental temporal deformation channel from consecutive frames. State is
explicit and checkpointable (``StreamState``); ``reset`` clears it. Backpressure is
modelled by a maximum queue depth that raises when exceeded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class StreamState:
    """Serializable stream state for checkpoint/resume."""

    last_timestamp: float | None
    processed: int
    dropped: int
    missing: int


@dataclass
class FrameStream:
    """Bounded streaming processor for 2D vorticity frames.

    ``max_depth`` bounds the pending-frame backpressure queue; ``expected_dt`` (if
    given) is used to flag missing frames when the timestamp gap is a multiple of
    it. Frames must arrive with strictly increasing timestamps; out-of-order or
    duplicate timestamps are rejected.
    """

    max_depth: int = 8
    expected_dt: float | None = None
    _last_timestamp: float | None = field(default=None, init=False)
    _previous: FloatArray | None = field(default=None, init=False)
    _processed: int = field(default=0, init=False)
    _dropped: int = field(default=0, init=False)
    _missing: int = field(default=0, init=False)

    def reset(self) -> None:
        self._last_timestamp = None
        self._previous = None
        self._processed = 0
        self._dropped = 0
        self._missing = 0

    def state(self) -> StreamState:
        return StreamState(self._last_timestamp, self._processed, self._dropped, self._missing)

    def push(self, omega: FloatArray, timestamp: float) -> dict[str, float]:
        """Process one vorticity frame; return incremental temporal metrics.

        Returns the RMS Eulerian change ``d|omega|/dt`` relative to the previous
        frame (0.0 for the first frame), plus running counters. Raises on
        out-of-order or duplicate timestamps.
        """
        omega = np.asarray(omega, dtype=np.float64)
        if omega.ndim != 2:
            raise ValueError("frame must be a 2D vorticity field.")
        ts = float(timestamp)
        if not np.isfinite(ts):
            raise ValueError("timestamp must be finite.")
        if self._last_timestamp is not None:
            if ts <= self._last_timestamp:
                raise ValueError("frames must arrive with strictly increasing timestamps.")
            if self.expected_dt is not None and self.expected_dt > 0.0:
                gap = (ts - self._last_timestamp) / self.expected_dt
                skipped = int(round(gap)) - 1
                if skipped > 0:
                    self._missing += skipped

        if self._previous is not None and self._previous.shape != omega.shape:
            raise ValueError("frame shape changed mid-stream.")
        if self._previous is None or self._last_timestamp is None:
            temporal_rms = 0.0
        else:
            dt = ts - self._last_timestamp
            temporal_rms = float(np.sqrt(np.mean(((omega - self._previous) / dt) ** 2)))

        self._previous = omega
        self._last_timestamp = ts
        self._processed += 1
        return {
            "temporal_rms": temporal_rms,
            "processed": float(self._processed),
            "missing": float(self._missing),
            "dropped": float(self._dropped),
        }

    def drop(self, count: int = 1) -> None:
        """Record dropped frames (e.g. under backpressure) without processing them."""
        if count < 0:
            raise ValueError("drop count must be non-negative.")
        self._dropped += int(count)

    def check_backpressure(self, pending: int) -> None:
        """Raise if the pending queue depth exceeds ``max_depth`` (backpressure)."""
        if pending > self.max_depth:
            raise RuntimeError(f"backpressure: {pending} pending frames exceed max_depth {self.max_depth}.")
