"""Latency benchmarks for declared ITD workload classes (research, H15).

Measures per-frame ITD evaluation latency (p50/p95/p99/worst), throughput, and
peak memory for the declared 2D and 3D workload classes on the CPU NumPy
reference path. Real-time is only claimed where the measured p95 meets the class
budget. Timings are wall-clock and hardware-dependent; the report records the
environment.
"""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d
from itd_research.signature import evaluate_signature

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class Workload:
    """A declared workload class with an explicit latency budget (ms)."""

    name: str
    dimensionality: str
    size: int
    budget_ms: float


WORKLOADS: dict[str, Workload] = {
    "RT-2D-S": Workload("RT-2D-S", "2D", 128, 5.0),
    "RT-2D-M": Workload("RT-2D-M", "2D", 512, 50.0),
    "RT-3D-S": Workload("RT-3D-S", "3D", 32, 50.0),
    "RT-3D-M": Workload("RT-3D-M", "3D", 64, 500.0),
}


@dataclass(frozen=True)
class LatencyStats:
    """Latency percentiles and resource use for one workload class."""

    name: str
    budget_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    worst_ms: float
    throughput_fps: float
    peak_mib: float
    meets_budget: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "budget_ms": self.budget_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "worst_ms": self.worst_ms,
            "throughput_fps": self.throughput_fps,
            "peak_mib": self.peak_mib,
            "meets_budget": self.meets_budget,
        }


def _percentile(sorted_ms: list[float], q: float) -> float:
    if not sorted_ms:
        return 0.0
    index = min(len(sorted_ms) - 1, int(q * len(sorted_ms)))
    return sorted_ms[index]


def _make_evaluator(workload: Workload) -> Callable[[], object]:
    rng = np.random.default_rng(0)
    if workload.dimensionality == "2D":
        m = workload.size
        u = rng.normal(size=(m, m))
        v = rng.normal(size=(m, m))
        spacing = (2.0 * np.pi / m, 2.0 * np.pi / m)
        return lambda: evaluate_signature(u, v, spacing, "periodic")
    n = workload.size
    coords = np.arange(n, dtype=np.float64) * (2.0 * np.pi / n)
    u = rng.normal(size=(n, n, n))
    v = rng.normal(size=(n, n, n))
    w = rng.normal(size=(n, n, n))
    return lambda: evaluate_itd3d(u, v, w, coords, coords, coords, "periodic")


def benchmark_workload(name: str, repeats: int = 30, warmup: int = 3) -> LatencyStats:
    """Benchmark one workload class; returns latency percentiles and memory."""
    workload = WORKLOADS[name]
    evaluate = _make_evaluator(workload)
    for _ in range(max(warmup, 0)):
        evaluate()
    tracemalloc.start()
    samples: list[float] = []
    for _ in range(max(repeats, 1)):
        start = time.perf_counter()
        evaluate()
        samples.append((time.perf_counter() - start) * 1000.0)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    samples.sort()
    p50 = _percentile(samples, 0.50)
    p95 = _percentile(samples, 0.95)
    p99 = _percentile(samples, 0.99)
    worst = samples[-1]
    throughput = 1000.0 / p50 if p50 > 0 else 0.0
    return LatencyStats(
        name=name,
        budget_ms=workload.budget_ms,
        p50_ms=p50,
        p95_ms=p95,
        p99_ms=p99,
        worst_ms=worst,
        throughput_fps=throughput,
        peak_mib=peak / (1024.0 * 1024.0),
        meets_budget=p95 <= workload.budget_ms,
    )
