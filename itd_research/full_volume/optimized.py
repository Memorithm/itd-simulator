"""Selective, shared-gradient full-volume evaluation (research, Mission 6, H48).

The Mission 5 :func:`evaluate_full_volume` computes the velocity-gradient tensor twice --
once inside the ITD-3D channel kernel and once for the established Q / lambda2 / swirl
diagnostics. This module computes it **once** and shares it, and lets a caller request
only a **profile** subset of channels. The optimization must be numerically identical to
the reference (same operators, same reductions) -- it removes duplicate work, never
changes a value; :func:`verify_equivalence` checks that against the authoritative path.

Experimental research; does not modify ``ITD V29.18``. The certified core is untouched;
only research diagnostics are reused.
"""

from __future__ import annotations

import time
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
from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d
from itd_research.full_volume.benchmark import WORKLOADS, evaluate_full_volume
from itd_research.validation_lab.candidates import channel_superset

FloatArray: TypeAlias = NDArray[np.float64]

# Selective channel profiles (names must exist in the superset or the established set).
_ESTABLISHED = ("q_positive_fraction", "lambda2_negative_fraction", "swirl_mean")
PROFILES: dict[str, tuple[str, ...]] = {
    "merger": ("localization", "heterogeneity", "roughness", "intensity"),
    "stretching": ("orientation_dispersion", "helicity_mean", "stretching_rate", "q_positive_fraction"),
    "full": channel_superset() + _ESTABLISHED,
}


def profile_channels(profile: str) -> tuple[str, ...]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; choose from {tuple(PROFILES)}")
    return PROFILES[profile]


def evaluate_full_volume_optimized(
    u: FloatArray, v: FloatArray, w: FloatArray, coords: FloatArray, *, profile: str = "full"
) -> dict[str, float]:
    """Full-volume channels with the velocity gradient computed once and shared.

    The velocity-gradient tensor is evaluated a single time and passed to both the ITD-3D
    kernel (via its ``gradient=`` fast path) and the established diagnostics. Only the
    requested ``profile`` channels are returned. The ITD kernel still evaluates its fused
    channel set internally, so the realized saving is the shared gradient (and any skipped
    established diagnostics), not per-channel pruning -- stated honestly rather than
    over-claimed.
    """
    channels = profile_channels(profile)
    gradient = velocity_gradient_3d(u, v, w, coords, coords, coords, "finite")
    itd = evaluate_itd3d(u, v, w, coords, coords, coords, "finite", gradient=gradient).as_dict()
    values: dict[str, float] = {name: float(itd[name]) for name in channel_superset()}
    if any(name in _ESTABLISHED for name in channels):
        if "q_positive_fraction" in channels:
            values["q_positive_fraction"] = float(np.mean(q_criterion(gradient) > 0.0))
        if "lambda2_negative_fraction" in channels:
            values["lambda2_negative_fraction"] = float(np.mean(lambda2(gradient) < 0.0))
        if "swirl_mean" in channels:
            values["swirl_mean"] = float(np.mean(swirling_strength(gradient)))
    return {name: values[name] for name in channels}


@dataclass(frozen=True)
class EquivalenceReport:
    """Per-channel agreement between the optimized and reference full-volume outputs."""

    nodes: int
    max_abs_diff: float
    max_rel_diff: float
    level: str
    channels: int

    def as_dict(self) -> dict[str, object]:
        return {
            "nodes": self.nodes, "max_abs_diff": self.max_abs_diff,
            "max_rel_diff": self.max_rel_diff, "level": self.level, "channels": self.channels,
        }


def _classify(max_abs: float, max_rel: float) -> str:
    if max_abs == 0.0:
        return "bitwise_equal"
    if max_abs <= 1e-9:
        return "absolute_tolerance"
    if max_rel <= 1e-9:
        return "relative_tolerance"
    return "not_equivalent"


def _field(nodes: int, seed: int) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    rng = np.random.default_rng(seed)
    coords = np.linspace(0.0, 2.0 * np.pi, nodes, endpoint=False)
    shape = (nodes, nodes, nodes)
    return rng.normal(size=shape), rng.normal(size=shape), rng.normal(size=shape), coords


def verify_equivalence(nodes: int = 24, seed: int = 0) -> EquivalenceReport:
    """Optimized 'full' profile must equal the reference full-volume evaluation."""
    u, v, w, coords = _field(nodes, seed)
    reference = evaluate_full_volume(u, v, w, coords)
    optimized = evaluate_full_volume_optimized(u, v, w, coords, profile="full")
    max_abs = 0.0
    max_rel = 0.0
    for name, ref_value in reference.items():
        opt_value = optimized[name]
        abs_diff = abs(opt_value - ref_value)
        rel_diff = abs_diff / max(abs(ref_value), 1e-30)
        max_abs = max(max_abs, abs_diff)
        max_rel = max(max_rel, rel_diff)
    return EquivalenceReport(nodes, max_abs, max_rel, _classify(max_abs, max_rel), len(reference))


@dataclass(frozen=True)
class OptimizationResult:
    """Reference vs optimized latency for one workload, with equivalence."""

    name: str
    nodes: int
    reference_p95_ms: float
    optimized_p95_ms: float
    speedup: float
    equivalence_level: str
    max_rel_diff: float

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name, "nodes": self.nodes,
            "reference_p95_ms": self.reference_p95_ms, "optimized_p95_ms": self.optimized_p95_ms,
            "speedup": self.speedup, "equivalence_level": self.equivalence_level,
            "max_rel_diff": self.max_rel_diff,
        }


def _p95(times: list[float]) -> float:
    return float(np.percentile(np.asarray(times), 95))


def benchmark_optimization(name: str, *, repeats: int = 5, profile: str = "full") -> OptimizationResult:
    """Measure reference vs shared-gradient p95 latency and confirm equivalence."""
    nodes = WORKLOADS[name][0]
    u, v, w, coords = _field(nodes, 0)
    evaluate_full_volume(u, v, w, coords)  # warm-up
    evaluate_full_volume_optimized(u, v, w, coords, profile=profile)
    ref_times: list[float] = []
    opt_times: list[float] = []
    for i in range(1, repeats + 1):
        u, v, w, coords = _field(nodes, i)
        t = time.perf_counter()
        evaluate_full_volume(u, v, w, coords)
        ref_times.append((time.perf_counter() - t) * 1e3)
        t = time.perf_counter()
        evaluate_full_volume_optimized(u, v, w, coords, profile=profile)
        opt_times.append((time.perf_counter() - t) * 1e3)
    equivalence = verify_equivalence(nodes=min(nodes, 24), seed=99)
    ref_p95, opt_p95 = _p95(ref_times), _p95(opt_times)
    return OptimizationResult(
        name=name, nodes=nodes, reference_p95_ms=ref_p95, optimized_p95_ms=opt_p95,
        speedup=ref_p95 / max(opt_p95, 1e-9),
        equivalence_level=equivalence.level, max_rel_diff=equivalence.max_rel_diff,
    )
