"""Deterministic vortex-merger ensemble and per-frame features (research, H7).

Each run integrates a like-signed Gaussian vortex pair with the 2D pseudo-spectral
solver until the pair co-rotates and merges. Per recorded snapshot we extract two
disjoint feature groups from the *same* field:

* **ITD channels** -- the V29.18 signature (:func:`evaluate_signature`);
* **baselines** -- established scalar diagnostics (enstrophy, palinstrophy,
  vorticity RMS, flatness, mean gradient norm).

The merger frame is labelled by the ITD-independent vortex-core count, so the ITD
channels never see the label. Runs vary in separation, circulation and viscosity so
the event occurs at different times, which is what makes a *prediction* (rather than
a fixed-time detection) meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.established_diagnostics import established_diagnostics
from itd_research.external_validation.spectral_ns import (
    gaussian_vortex_pair,
    simulate_vorticity,
    spectral_grid,
    velocity_from_vorticity,
)
from itd_research.prediction.events import core_count_series, detect_merger_frame
from itd_research.signature import evaluate_signature
from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary

FloatArray: TypeAlias = NDArray[np.float64]

ITD_CHANNELS: tuple[str, ...] = (
    "intensity",
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
    "structure_score",
)
BASELINE_CHANNELS: tuple[str, ...] = (
    "enstrophy",
    "palinstrophy",
    "vorticity_rms",
    "vorticity_flatness",
    "mean_gradient_norm",
)


@dataclass(frozen=True)
class RunConfig:
    """One merger-run configuration."""

    run_id: str
    separation: float
    circulation: float
    viscosity: float
    core: float = 0.5

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "separation": self.separation,
            "circulation": self.circulation,
            "viscosity": self.viscosity,
            "core": self.core,
        }


@dataclass(frozen=True)
class MergerRun:
    """A completed run: times, per-frame features, and the ITD-independent event."""

    config: RunConfig
    times: tuple[float, ...]
    core_counts: tuple[int, ...]
    event_frame: int | None
    features: dict[str, FloatArray] = field(default_factory=dict)

    @property
    def event_time(self) -> float | None:
        if self.event_frame is None:
            return None
        return self.times[self.event_frame]

    def feature_matrix(self, channels: tuple[str, ...]) -> FloatArray:
        return np.column_stack([self.features[name] for name in channels])


def _frame_features(
    u: FloatArray,
    v: FloatArray,
    spacing: float,
    previous_omega: FloatArray | None,
    delta_time: float | None,
) -> dict[str, float]:
    signature = evaluate_signature(
        u, v, spacing, "finite", previous_omega=previous_omega, delta_time=delta_time
    )
    baselines = established_diagnostics(u, v, spacing, "finite")
    values = {name: getattr(signature, name) for name in ITD_CHANNELS}
    values.update({name: float(baselines[name]) for name in BASELINE_CHANNELS})
    return values


def simulate_merger_run(
    config: RunConfig,
    nodes: int = 80,
    length: float = 2.0 * np.pi,
    delta_time: float = 0.002,
    steps: int = 2800,
    record_every: int = 140,
    fraction: float = 0.6,
    min_cells: int = 20,
) -> MergerRun:
    """Integrate one merger run and extract per-frame ITD and baseline features."""
    grid = spectral_grid(nodes, length)
    spacing = length / nodes
    omega0 = gaussian_vortex_pair(
        grid,
        circulation=config.circulation,
        core=config.core,
        separation=config.separation,
        same_sign=True,
    )
    result = simulate_vorticity(omega0, grid, config.viscosity, delta_time, steps, record_every)

    core_counts = core_count_series(result.vorticity, fraction=fraction, min_cells=min_cells)
    event_frame = detect_merger_frame(core_counts)

    per_frame: list[dict[str, float]] = []
    previous_omega: FloatArray | None = None
    previous_time: float | None = None
    for index, omega in enumerate(result.vorticity):
        u, v = velocity_from_vorticity(omega, grid)
        dt = None if previous_time is None else result.times[index] - previous_time
        per_frame.append(_frame_features(u, v, spacing, previous_omega, dt))
        previous_omega = numerical_vorticity_with_boundary(u, v, spacing, "finite")
        previous_time = result.times[index]

    channels = ITD_CHANNELS + BASELINE_CHANNELS
    features = {
        name: np.array([frame[name] for frame in per_frame], dtype=np.float64)
        for name in channels
    }
    return MergerRun(
        config=config,
        times=result.times,
        core_counts=core_counts,
        event_frame=event_frame,
        features=features,
    )


def default_ensemble() -> tuple[RunConfig, ...]:
    """A varied merger ensemble at fixed initial geometry.

    Separation is held at 1.2 (a value that reliably merges with a healthy
    pre-event window); the rotation rate (circulation) and diffusion (viscosity)
    are varied so the merger occurs at different times and intensities. This is a
    real but bounded family -- one initial geometry, varied dynamics -- and the
    report says so.
    """
    separation = 1.2
    configs: list[RunConfig] = []
    for circulation in (1.0, 1.3, 1.6, 1.9):
        for viscosity in (0.002, 0.003, 0.004):
            run_id = f"circ{circulation:g}_nu{viscosity:g}"
            configs.append(RunConfig(run_id, separation, circulation, viscosity))
    return tuple(configs)


def quick_ensemble() -> tuple[RunConfig, ...]:
    """A tiny CI-sized ensemble (kept fast and deterministic).

    High viscosity so the under-resolved 48^3 runs still merge inside a short
    window; this exercises the pipeline and is not a scientific result.
    """
    return (
        RunConfig("circ1.4_nu0.006", 1.2, 1.4, 0.006),
        RunConfig("circ1.6_nu0.006", 1.2, 1.6, 0.006),
        RunConfig("circ1.8_nu0.006", 1.2, 1.8, 0.006),
    )
