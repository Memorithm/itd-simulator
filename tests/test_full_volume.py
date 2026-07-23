"""Tests for the full-volume ITD-3D benchmark (Mission 5, H35)."""

from __future__ import annotations

import numpy as np

from itd_research.full_volume.benchmark import (
    WORKLOADS,
    benchmark_volume,
    evaluate_full_volume,
)
from itd_research.validation_lab.candidates import channel_superset


def test_evaluate_full_volume_returns_all_channels_no_reduction() -> None:
    rng = np.random.default_rng(0)
    n = 16
    coords = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    u, v, w = (rng.normal(size=(n, n, n)) for _ in range(3))
    values = evaluate_full_volume(u, v, w, coords)
    # all 8 ITD-3D channels + 3 established diagnostics, computed over the whole volume
    for name in channel_superset():
        assert name in values and np.isfinite(values[name])
    for name in ("q_positive_fraction", "lambda2_negative_fraction", "swirl_mean"):
        assert name in values
    assert 0.0 <= values["q_positive_fraction"] <= 1.0


def test_benchmark_volume_reports_bounded_metrics() -> None:
    result = benchmark_volume("VOL-3D-XS", repeats=1)
    assert result.nodes == WORKLOADS["VOL-3D-XS"][0]
    assert result.p95_ms > 0.0
    assert result.peak_memory_mb > 0.0
    assert result.channels_evaluated == len(channel_superset()) + 3
