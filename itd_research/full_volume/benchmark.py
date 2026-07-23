"""Full-volume ITD-3D evaluation and latency/memory benchmark (research, H35).

``evaluate_full_volume`` computes, over the entire 3D grid, the ITD-3D channel superset
and the established velocity-gradient diagnostics (Q, lambda_2, swirling strength) --
explicitly NOT reduced to a plane. ``benchmark_volume`` measures p50/p95/p99 latency,
peak traced memory, and throughput per declared workload. A workload "meets" its
envelope only if p95 is within the declared budget on the measured node.
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d import (
    lambda2,
    q_criterion,
    swirling_strength,
    velocity_gradient_3d,
)
from itd_research.validation_lab.candidates import channel_superset, evaluate_channels

FloatArray: TypeAlias = NDArray[np.float64]

# name -> (nodes, budget_ms). VOL-3D-L (128^3) is declared batch/offline (no p95 budget).
WORKLOADS: dict[str, tuple[int, float]] = {
    "VOL-3D-XS": (32, 250.0),
    "VOL-3D-S": (48, 1200.0),
    "VOL-3D-M": (64, 4000.0),
}


def evaluate_full_volume(
    u: FloatArray, v: FloatArray, w: FloatArray, coords: FloatArray
) -> dict[str, float]:
    """Compute ALL ITD-3D channels + established diagnostics over the whole volume."""
    itd = evaluate_channels(u, v, w, coords, coords, coords, "finite")
    gradient = velocity_gradient_3d(u, v, w, coords, coords, coords, "finite")
    established = {
        "q_positive_fraction": float(np.mean(q_criterion(gradient) > 0.0)),
        "lambda2_negative_fraction": float(np.mean(lambda2(gradient) < 0.0)),
        "swirl_mean": float(np.mean(swirling_strength(gradient))),
    }
    return {**{name: itd[name] for name in channel_superset()}, **established}


@dataclass(frozen=True)
class VolumeResult:
    name: str
    nodes: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    peak_memory_mb: float
    throughput_hz: float
    budget_ms: float
    meets_budget: bool
    channels_evaluated: int

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name, "nodes": self.nodes, "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms, "p99_ms": self.p99_ms, "max_ms": self.max_ms,
            "peak_memory_mb": self.peak_memory_mb, "throughput_hz": self.throughput_hz,
            "budget_ms": self.budget_ms, "meets_budget": self.meets_budget,
            "channels_evaluated": self.channels_evaluated,
        }


def _field(nodes: int, seed: int) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    rng = np.random.default_rng(seed)
    coords = np.linspace(0.0, 2.0 * np.pi, nodes, endpoint=False)
    return (rng.normal(size=(nodes, nodes, nodes)), rng.normal(size=(nodes, nodes, nodes)),
            rng.normal(size=(nodes, nodes, nodes)), coords)


def benchmark_volume(name: str, *, repeats: int = 5) -> VolumeResult:
    """Benchmark full-volume ITD-3D for a declared workload."""
    nodes, budget = WORKLOADS[name]
    u, v, w, coords = _field(nodes, 0)
    sample = evaluate_full_volume(u, v, w, coords)  # warm-up + channel count
    tracemalloc.start()
    times: list[float] = []
    for i in range(1, repeats + 1):
        u, v, w, coords = _field(nodes, i)
        t = time.perf_counter()
        evaluate_full_volume(u, v, w, coords)
        times.append((time.perf_counter() - t) * 1e3)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    arr = np.asarray(times)
    p50, p95, p99 = (float(np.percentile(arr, q)) for q in (50, 95, 99))
    return VolumeResult(
        name, nodes, p50, p95, p99, float(arr.max()), peak / 1e6,
        float(1000.0 / max(p50, 1e-9)), budget, bool(p95 <= budget), len(sample),
    )
