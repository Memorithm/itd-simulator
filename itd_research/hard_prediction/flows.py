"""Seed-keyed hard held-out runs and a common 2D feature space (research, Mission 4).

Each run is a distinct simulation keyed by an integer seed (parameter jitter + a small
seeded initial perturbation), so grouped splits isolate whole simulations. Two solver
families:

* **2D merger** (``spectral_ns``): perturbed co-rotating pair; the event is the
  ITD-independent core-count 2->1 transition.
* **3D Taylor-Green** (``spectral3d``): perturbed Taylor-Green; the event is the
  ITD-independent frame of maximum enstrophy-production rate (a weak, under-resolved
  breakdown). Features are taken on the z-midplane -- the same 2D feature space as the
  merger and what a planar PIV sees (also the H22 partial-observation view).

Simulation is separated from feature extraction: ``simulate_*_raw`` stores the 2D
velocity snapshots, and ``features_from_raw`` extracts the ITD + established feature
matrix, optionally under a :class:`DegradationSpec`, so one simulation can be scored
at many difficulty levels without re-integrating.
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
from itd_research.hard_prediction.degradation import DegradationSpec
from itd_research.prediction.events import core_count_series, detect_merger_frame
from itd_research.signature import evaluate_signature
from itd_research.spectral3d import (
    SpectralGrid3D,
    mean_enstrophy,
    simulate,
    spectral_grid_3d,
    taylor_green_velocity,
)
from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]

ITD_FEATURES: tuple[str, ...] = (
    "intensity", "heterogeneity", "localization", "roughness",
    "sign_mixing", "temporal_deformation", "structure_score",
)
ESTABLISHED_FEATURES: tuple[str, ...] = (
    "enstrophy", "palinstrophy", "vorticity_rms", "vorticity_flatness",
    "q_positive_fraction", "swirl_mean",
)
ALL_FEATURES: tuple[str, ...] = ITD_FEATURES + ESTABLISHED_FEATURES


def _repair(u: FloatArray, v: FloatArray, valid: BoolArray | None) -> tuple[FloatArray, FloatArray]:
    """Fill invalid vectors by a few Jacobi neighbour-average passes (repaired mode)."""
    if valid is None or bool(np.all(valid)):
        return u, v
    u, v = u.copy(), v.copy()
    for field_array in (u, v):
        field_array[~valid] = float(np.mean(field_array[valid])) if np.any(valid) else 0.0
    for _ in range(20):
        for field_array in (u, v):
            padded = np.pad(field_array, 1, mode="edge")
            avg = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]) / 4.0
            field_array[~valid] = avg[~valid]
    return u, v


def _established_2d(u: FloatArray, v: FloatArray, spacing: float) -> dict[str, float]:
    diagnostics = established_diagnostics(u, v, spacing, "finite")
    du_dx = np.gradient(u, spacing, axis=1)
    du_dy = np.gradient(u, spacing, axis=0)
    dv_dx = np.gradient(v, spacing, axis=1)
    dv_dy = np.gradient(v, spacing, axis=0)
    vort = dv_dx - du_dy
    normal = du_dx - dv_dy
    shear = dv_dx + du_dy
    okubo = normal**2 + shear**2 - vort**2  # W<0 => rotation-dominated
    det = du_dx * dv_dy - du_dy * dv_dx
    trace = du_dx + dv_dy
    swirl = np.sqrt(np.maximum(4.0 * det - trace**2, 0.0)) / 2.0
    return {
        "enstrophy": float(diagnostics["enstrophy"]),
        "palinstrophy": float(diagnostics["palinstrophy"]),
        "vorticity_rms": float(diagnostics["vorticity_rms"]),
        "vorticity_flatness": float(diagnostics["vorticity_flatness"]),
        "q_positive_fraction": float(np.mean(okubo < 0.0)),
        "swirl_mean": float(np.mean(swirl)),
    }


def extract_features_2d(
    u: FloatArray,
    v: FloatArray,
    spacing: float,
    *,
    previous_omega: FloatArray | None = None,
    delta_time: float | None = None,
    valid: BoolArray | None = None,
) -> dict[str, float]:
    """ITD full signature + locked established diagnostics on one 2D field."""
    u, v = _repair(u, v, valid)
    signature = evaluate_signature(
        u, v, spacing, "finite", previous_omega=previous_omega, delta_time=delta_time
    )
    values = {name: getattr(signature, name) for name in ITD_FEATURES}
    values.update(_established_2d(u, v, spacing))
    return values


@dataclass(frozen=True)
class RawRun:
    """Stored 2D velocity snapshots for one simulation, with its ITD-independent event."""

    seed: int
    family: str
    spacing: float
    times: tuple[float, ...]
    event_frame: int | None
    velocities: tuple[tuple[FloatArray, FloatArray], ...]


@dataclass(frozen=True)
class HardRun:
    """A feature-extracted run: seed, per-frame feature matrix, times, and the event."""

    seed: int
    family: str
    times: tuple[float, ...]
    event_frame: int | None
    features: dict[str, FloatArray] = field(default_factory=dict)

    def event_time(self) -> float | None:
        return None if self.event_frame is None else self.times[self.event_frame]


def _seeded_perturbation(grid_nodes: int, seed: int, amplitude: float) -> FloatArray:
    """A small low-wavenumber real perturbation field (seeded, zero-mean)."""
    rng = np.random.default_rng(seed)
    field_hat: NDArray[np.complex128] = np.zeros((grid_nodes, grid_nodes), dtype=np.complex128)
    for _ in range(6):
        kx, ky = int(rng.integers(1, 4)), int(rng.integers(1, 4))
        phase = rng.uniform(0.0, 2.0 * np.pi)
        field_hat[ky, kx] += amplitude * np.exp(1j * phase)
    field = np.fft.ifft2(field_hat).real
    return np.ascontiguousarray(field - field.mean())


def simulate_merger_raw(seed: int, nodes: int = 80, steps: int = 2800, record_every: int = 140) -> RawRun:
    """A perturbed, parameter-jittered 2D merger keyed by ``seed`` (harder than M3)."""
    rng = np.random.default_rng(seed)
    separation = 1.2 + float(rng.uniform(-0.05, 0.05))
    circulation = float(rng.uniform(1.0, 1.9))
    viscosity = float(rng.uniform(0.002, 0.004))
    length = 2.0 * np.pi
    grid = spectral_grid(nodes, length)
    spacing = length / nodes
    omega0 = gaussian_vortex_pair(grid, circulation=circulation, core=0.5, separation=separation, same_sign=True)
    omega0 = omega0 + 0.15 * _seeded_perturbation(nodes, seed, amplitude=float(np.max(np.abs(omega0))))
    omega0 = np.ascontiguousarray(omega0 - omega0.mean())
    result = simulate_vorticity(omega0, grid, viscosity, 0.002, steps, record_every)
    counts = core_count_series(result.vorticity, fraction=0.6, min_cells=20)
    event = detect_merger_frame(counts)
    velocities = tuple(velocity_from_vorticity(omega, grid) for omega in result.vorticity)
    return RawRun(seed, "merger2d", spacing, result.times, event, velocities)


def _enstrophy_production_event(velocities: tuple, grid: SpectralGrid3D) -> int | None:
    values = [float(mean_enstrophy(u, v, w, grid)) for (u, v, w) in velocities]
    if len(values) < 3:
        return None
    event = int(np.argmax(np.gradient(np.asarray(values))))
    return event if 0 < event < len(values) - 1 else None


def simulate_taylorgreen_raw(seed: int, nodes: int = 24, steps: int = 1600, record_every: int = 64) -> RawRun:
    """A perturbed 3D Taylor-Green breakdown keyed by ``seed``; midplane 2D snapshots."""
    grid = spectral_grid_3d(nodes)
    u0, v0, w0 = taylor_green_velocity(grid)
    rng = np.random.default_rng(seed)
    amp = 0.05 * float(np.sqrt(np.mean(u0**2)))
    u0 = np.ascontiguousarray(u0 + amp * _seeded_perturbation(nodes, seed, amplitude=1.0)[None, :, :])
    viscosity = float(rng.uniform(0.015, 0.025))
    result = simulate((u0, v0, w0), grid, viscosity, 0.004, steps, record_every)
    event = _enstrophy_production_event(result.velocity, grid)
    spacing = float(grid.coordinates[1] - grid.coordinates[0])
    mid = nodes // 2
    velocities = tuple(
        (np.ascontiguousarray(u[mid]), np.ascontiguousarray(v[mid])) for (u, v, _w) in result.velocity
    )
    times = tuple(float(i) for i in range(len(result.velocity)))
    return RawRun(seed, "taylorgreen3d", spacing, times, event, velocities)


def features_from_raw(raw: RawRun, spec: DegradationSpec | None = None) -> HardRun:
    """Extract the ITD + established feature matrix, optionally under a degradation."""
    coords = np.arange(raw.velocities[0][0].shape[1], dtype=np.float64) * raw.spacing
    coords_y = np.arange(raw.velocities[0][0].shape[0], dtype=np.float64) * raw.spacing
    per_frame: list[dict[str, float]] = []
    previous_omega: FloatArray | None = None
    previous_time: float | None = None
    for index, (u, v) in enumerate(raw.velocities):
        valid: BoolArray | None = None
        spacing = raw.spacing
        if spec is not None:
            degraded = spec.apply(u, v, coords, coords_y, seed=raw.seed * 1000 + index)
            u, v, valid = degraded.u, degraded.v, degraded.valid
            spacing = raw.spacing * spec.downsample_factor
        dt = None if previous_time is None else raw.times[index] - previous_time
        per_frame.append(
            extract_features_2d(u, v, spacing, previous_omega=previous_omega, delta_time=dt, valid=valid)
        )
        u_rep, v_rep = _repair(u, v, valid)
        previous_omega = numerical_vorticity_with_boundary(u_rep, v_rep, spacing, "finite")
        previous_time = raw.times[index]
    features = {name: np.array([f[name] for f in per_frame], dtype=np.float64) for name in ALL_FEATURES}
    return HardRun(raw.seed, raw.family, raw.times, raw.event_frame, features)


def hard_merger_run(seed: int, spec: DegradationSpec | None = None, **kwargs: int) -> HardRun:
    """Convenience: simulate a 2D merger and extract features (optionally degraded)."""
    return features_from_raw(simulate_merger_raw(seed, **kwargs), spec)


def hard_taylorgreen_run(seed: int, spec: DegradationSpec | None = None, **kwargs: int) -> HardRun:
    """Convenience: simulate a 3D Taylor-Green and extract midplane features."""
    return features_from_raw(simulate_taylorgreen_raw(seed, **kwargs), spec)
