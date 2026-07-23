"""Real-time and streaming ITD evaluation (research, H15).

A CPU NumPy reference for streaming field evaluation with bounded memory,
deterministic frame ordering, missing/duplicate/out-of-order detection, an
incremental temporal channel, and latency benchmarks for declared workload
classes. Part of the isolated ``itd_research`` namespace; never modifies the
certified V29.18 core; imports no plotting library at import time; no network
access. "Real-time" is only claimed against a declared deadline with measured
p95/p99 latency.
"""

from __future__ import annotations

from itd_research.realtime.benchmarks import WORKLOADS, LatencyStats, benchmark_workload
from itd_research.realtime.streaming import FrameStream, StreamState

__all__ = (
    "FrameStream",
    "StreamState",
    "WORKLOADS",
    "LatencyStats",
    "benchmark_workload",
)
