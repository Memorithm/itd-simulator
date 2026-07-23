"""Same-physics cross-code comparison of Taylor-Green (research, Mission 5, H29).

Runs the *same* Taylor-Green physics through the pseudo-spectral `spectral3d` code and
the independent finite-difference `fd_solver`, and compares them by **integral / phase
metrics and event times**, never pointwise (the grids/methods differ). Also exposes a
finite-difference Taylor-Green run in the `hard_prediction` RawRun format so the
existing leakage-safe predictor can be trained on one code and tested on the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.cross_code.fd_solver import make_grid, simulate_fd, taylor_green_fd
from itd_research.hard_prediction.flows import RawRun
from itd_research.spectral3d import (
    kinetic_energy,
    mean_enstrophy,
    simulate,
    spectral_grid_3d,
    taylor_green_velocity,
)

FloatArray: TypeAlias = NDArray[np.float64]


def _perturb(nodes: int, seed: int, amplitude: float) -> FloatArray:
    rng = np.random.default_rng(seed)
    field_hat: NDArray[np.complex128] = np.zeros((nodes, nodes), dtype=np.complex128)
    for _ in range(6):
        kx, ky = int(rng.integers(1, 4)), int(rng.integers(1, 4))
        field_hat[ky, kx] += amplitude * np.exp(1j * rng.uniform(0.0, 2.0 * np.pi))
    field = np.fft.ifft2(field_hat).real
    return np.ascontiguousarray(field - field.mean())


def _enstrophy_peak(values: list[float]) -> int | None:
    if len(values) < 3:
        return None
    event = int(np.argmax(np.gradient(np.asarray(values))))
    return event if 0 < event < len(values) - 1 else None


def simulate_taylorgreen_fd_raw(
    seed: int, nodes: int = 24, steps: int = 1000, record_every: int = 40
) -> RawRun:
    """A perturbed finite-difference Taylor-Green run in RawRun form (midplane 2D)."""
    grid = make_grid(nodes)
    u0, v0, w0 = taylor_green_fd(grid)
    rng = np.random.default_rng(seed)
    amp = 0.05 * float(np.sqrt(np.mean(u0**2)))
    u0 = np.ascontiguousarray(u0 + amp * _perturb(nodes, seed, 1.0)[None, :, :])
    viscosity = float(rng.uniform(0.015, 0.025))
    result = simulate_fd((u0, v0, w0), grid, viscosity, 0.01, steps, record_every)
    ens = [mean_enstrophy(a, b, c, grid) for (a, b, c) in result.velocity]
    event = _enstrophy_peak(ens)
    spacing = float(grid.coordinates[1] - grid.coordinates[0])
    mid = nodes // 2
    velocities = tuple(
        (np.ascontiguousarray(u[mid]), np.ascontiguousarray(v[mid])) for (u, v, _w) in result.velocity
    )
    times = tuple(float(i) for i in range(len(result.velocity)))
    return RawRun(seed, "taylorgreen_fd", spacing, times, event, velocities)


@dataclass(frozen=True)
class CrossCodeComparison:
    """Integral-metric comparison of the same physics through two codes."""

    spectral_energy: tuple[float, ...]
    fd_energy: tuple[float, ...]
    spectral_enstrophy: tuple[float, ...]
    fd_enstrophy: tuple[float, ...]
    spectral_event_time: float | None
    fd_event_time: float | None
    energy_trajectory_correlation: float
    enstrophy_trajectory_correlation: float
    enstrophy_peak_time_rel_error: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "spectral_energy": list(self.spectral_energy),
            "fd_energy": list(self.fd_energy),
            "spectral_enstrophy": list(self.spectral_enstrophy),
            "fd_enstrophy": list(self.fd_enstrophy),
            "spectral_event_time": self.spectral_event_time,
            "fd_event_time": self.fd_event_time,
            "energy_trajectory_correlation": self.energy_trajectory_correlation,
            "enstrophy_trajectory_correlation": self.enstrophy_trajectory_correlation,
            "enstrophy_peak_time_rel_error": self.enstrophy_peak_time_rel_error,
        }


def _resample(values: list[float], n: int) -> FloatArray:
    """Resample a trajectory onto ``n`` points of normalized time [0, 1]."""
    source = np.linspace(0.0, 1.0, len(values))
    target = np.linspace(0.0, 1.0, n)
    return np.interp(target, source, np.asarray(values, dtype=np.float64))


def _corr(a: FloatArray, b: FloatArray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    denom = float(np.sqrt(np.sum(a**2) * np.sum(b**2)))
    return float(np.sum(a * b) / denom) if denom > 0 else float("nan")


def compare_taylorgreen(
    nodes: int = 24, viscosity: float = 0.02, physical_time: float = 6.4
) -> CrossCodeComparison:
    """Run Taylor-Green through both codes and compare integral trajectories + events."""
    grid_s = spectral_grid_3d(nodes)
    us, vs, ws = taylor_green_velocity(grid_s)
    dt_s = 0.004
    steps_s = int(round(physical_time / dt_s))
    res_s = simulate(
        (us, vs, ws), grid_s, viscosity, dt_s, steps_s, max(steps_s // 24, 1)
    )
    energy_s = [kinetic_energy(a, b, c) for (a, b, c) in res_s.velocity]
    enstrophy_s = [mean_enstrophy(a, b, c, grid_s) for (a, b, c) in res_s.velocity]

    grid_f = make_grid(nodes)
    uf, vf, wf = taylor_green_fd(grid_f)
    dt_f = 0.01
    steps_f = int(round(physical_time / dt_f))
    res_f = simulate_fd((uf, vf, wf), grid_f, viscosity, dt_f, steps_f, max(steps_f // 24, 1))
    energy_f = [kinetic_energy(a, b, c) for (a, b, c) in res_f.velocity]
    enstrophy_f = [mean_enstrophy(a, b, c, grid_f) for (a, b, c) in res_f.velocity]

    n = 24
    energy_corr = _corr(_resample(energy_s, n), _resample(energy_f, n))
    enstrophy_corr = _corr(_resample(enstrophy_s, n), _resample(enstrophy_f, n))

    peak_s = _enstrophy_peak(enstrophy_s)
    peak_f = _enstrophy_peak(enstrophy_f)
    event_time_s = None if peak_s is None else float(res_s.times[peak_s])
    event_time_f = None if peak_f is None else float(res_f.times[peak_f])
    if event_time_s and event_time_f and event_time_s > 0:
        peak_rel_error: float | None = abs(event_time_f - event_time_s) / event_time_s
    else:
        peak_rel_error = None

    return CrossCodeComparison(
        spectral_energy=tuple(energy_s), fd_energy=tuple(energy_f),
        spectral_enstrophy=tuple(enstrophy_s), fd_enstrophy=tuple(enstrophy_f),
        spectral_event_time=event_time_s, fd_event_time=event_time_f,
        energy_trajectory_correlation=energy_corr,
        enstrophy_trajectory_correlation=enstrophy_corr,
        enstrophy_peak_time_rel_error=peak_rel_error,
    )
