"""Tests for the real-time streaming and benchmark reference (H15)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.realtime.benchmarks import WORKLOADS, benchmark_workload
from itd_research.realtime.streaming import FrameStream


def _frame(seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(size=(16, 16))


def test_stream_processes_ordered_frames() -> None:
    stream = FrameStream()
    m0 = stream.push(_frame(0), 0.0)
    assert m0["temporal_rms"] == 0.0  # first frame has no predecessor
    m1 = stream.push(_frame(1), 1.0)
    assert m1["temporal_rms"] > 0.0
    assert stream.state().processed == 2


def test_stream_rejects_out_of_order_and_duplicate() -> None:
    stream = FrameStream()
    stream.push(_frame(0), 1.0)
    with pytest.raises(ValueError):
        stream.push(_frame(1), 1.0)  # duplicate timestamp
    with pytest.raises(ValueError):
        stream.push(_frame(2), 0.5)  # out of order


def test_stream_detects_missing_frames() -> None:
    stream = FrameStream(expected_dt=1.0)
    stream.push(_frame(0), 0.0)
    stream.push(_frame(1), 3.0)  # skipped t=1,2 -> 2 missing
    assert stream.state().missing == 2


def test_stream_reset_and_dropped_and_shape_guard() -> None:
    stream = FrameStream()
    stream.push(_frame(0), 0.0)
    stream.drop(3)
    assert stream.state().dropped == 3
    with pytest.raises(ValueError):
        stream.push(np.zeros((8, 8)), 1.0)  # shape changed mid-stream
    stream.reset()
    assert stream.state().processed == 0 and stream.state().last_timestamp is None


def test_stream_backpressure() -> None:
    stream = FrameStream(max_depth=4)
    stream.check_backpressure(4)  # ok
    with pytest.raises(RuntimeError):
        stream.check_backpressure(5)


def test_benchmark_workload_returns_valid_stats() -> None:
    stats = benchmark_workload("RT-2D-S", repeats=5, warmup=1)
    assert stats.name == "RT-2D-S"
    assert 0.0 < stats.p50_ms <= stats.p95_ms <= stats.worst_ms
    assert stats.peak_mib > 0.0
    assert isinstance(stats.meets_budget, bool)
    assert set(WORKLOADS) == {"RT-2D-S", "RT-2D-M", "RT-3D-S", "RT-3D-M"}
