"""Competent established structural/topological baselines (Mission 8, section 10).

Every quantity here is a standard vortex-identification or region-tracking diagnostic --
none is ITD. ``BASELINE_COMPETENT_COMBINED`` is the primary comparison partner: the
preregistered H62 test is whether adding ``ITD_STRUCTURAL`` beats it.
"""

from __future__ import annotations

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
from itd_research.mission8.statistics import temporal_rate
from itd_research.mission8.vortex_regions import centroid_distance, detect_regions

FloatArray: TypeAlias = NDArray[np.float64]

BASELINE_MAGNITUDE: tuple[str, ...] = ("enstrophy", "vorticity_rms")
BASELINE_STRUCTURAL: tuple[str, ...] = (
    "q_positive_fraction", "lambda2_negative_fraction", "swirl_mean", "region_count",
)
BASELINE_CORE_TRACKING: tuple[str, ...] = (
    "mean_region_volume", "region_volume_std", "centroid_displacement_rate",
)
BASELINE_TEMPORAL: tuple[str, ...] = ("d_region_count_dt", "d_q_positive_fraction_dt")
BASELINE_COMPETENT_COMBINED: tuple[str, ...] = (
    BASELINE_MAGNITUDE + BASELINE_STRUCTURAL + BASELINE_CORE_TRACKING + BASELINE_TEMPORAL
)


@dataclass(frozen=True)
class BaselineTrajectory:
    """Per-frame established-diagnostic time series (never ITD)."""

    times: list[float]
    channels: dict[str, list[float]]

    def as_dict(self) -> dict[str, object]:
        return {"times": self.times, "channels": self.channels}

    def matrix(self, names: tuple[str, ...]) -> FloatArray:
        return np.column_stack([np.asarray(self.channels[n], dtype=np.float64) for n in names])


def _per_frame_baseline(
    u: FloatArray, v: FloatArray, w: FloatArray, x: FloatArray, y: FloatArray, z: FloatArray,
    prev_centroid: tuple[float, float, float] | None, dt: float, min_cells: int,
) -> tuple[dict[str, float], tuple[float, float, float] | None]:
    grad = velocity_gradient_3d(u, v, w, x, y, z, "finite")
    omega = np.stack([grad[..., 2, 1] - grad[..., 1, 2], grad[..., 0, 2] - grad[..., 2, 0],
                      grad[..., 1, 0] - grad[..., 0, 1]], axis=-1)
    enstrophy = 0.5 * float(np.mean(np.sum(omega**2, axis=-1)))
    vorticity_rms = float(np.sqrt(max(2.0 * enstrophy, 0.0)))
    q = q_criterion(grad)
    l2 = lambda2(grad)
    swirl = swirling_strength(grad)
    _, regions = detect_regions(q, threshold=0.0, comparison="greater", min_cells=min_cells)
    region_count = len(regions)
    centroid: tuple[float, float, float] | None
    if regions:
        volumes = np.array([r.volume_cells for r in regions], dtype=np.float64)
        mean_volume = float(np.mean(volumes))
        volume_std = float(np.std(volumes))
        largest = max(regions, key=lambda r: r.volume_cells)
        centroid = largest.centroid
    else:
        mean_volume = 0.0
        volume_std = 0.0
        centroid = prev_centroid
    if prev_centroid is not None and centroid is not None:
        displacement_rate = centroid_distance(prev_centroid, centroid) / max(dt, 1e-12)
    else:
        displacement_rate = 0.0
    values = {
        "enstrophy": enstrophy,
        "vorticity_rms": vorticity_rms,
        "q_positive_fraction": float(np.mean(q > 0.0)),
        "lambda2_negative_fraction": float(np.mean(l2 < 0.0)),
        "swirl_mean": float(np.mean(swirl)),
        "region_count": float(region_count),
        "mean_region_volume": mean_volume,
        "region_volume_std": volume_std,
        "centroid_displacement_rate": displacement_rate,
    }
    return values, centroid


def compute_baseline_trajectory(
    frames: list[tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]],
    *, min_cells: int = 8,
) -> BaselineTrajectory:
    """Compute per-frame established baseline channels, including temporal-rate channels."""
    static_names = BASELINE_MAGNITUDE + BASELINE_STRUCTURAL + BASELINE_CORE_TRACKING
    channels: dict[str, list[float]] = {name: [] for name in static_names}
    times: list[float] = []
    prev_centroid: tuple[float, float, float] | None = None
    prev_time: float | None = None
    for time, u, v, w, x, y, z in frames:
        dt = (time - prev_time) if prev_time is not None else 1.0
        values, prev_centroid = _per_frame_baseline(u, v, w, x, y, z, prev_centroid, dt, min_cells)
        for name in static_names:
            channels[name].append(values[name])
        times.append(time)
        prev_time = time
    channels["d_region_count_dt"] = temporal_rate(channels["region_count"], times)
    channels["d_q_positive_fraction_dt"] = temporal_rate(channels["q_positive_fraction"], times)
    return BaselineTrajectory(times=times, channels=channels)
