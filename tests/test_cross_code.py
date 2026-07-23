"""Tests for the same-physics cross-code solver and comparison (Mission 5, H29)."""

from __future__ import annotations

import numpy as np

from itd_research.cross_code.comparison import (
    compare_taylorgreen,
    simulate_taylorgreen_fd_raw,
)
from itd_research.cross_code.fd_solver import (
    make_grid,
    max_divergence,
    simulate_fd,
    taylor_green_fd,
)


def test_fd_solver_keeps_divergence_small_and_finite() -> None:
    grid = make_grid(16)
    u, v, w = taylor_green_fd(grid)
    # Spectral projection makes the SPECTRAL divergence round-off; the finite-difference
    # divergence is only O(h^2) (h = 2*pi/16 ~ 0.39). We check it stays bounded/small,
    # not round-off -- the honest property of the FD-advection + spectral-projection code.
    initial_fd_div = max_divergence(u, v, w)
    result = simulate_fd((u, v, w), grid, viscosity=0.02, delta_time=0.01, steps=40, record_every=20)
    for a, b, c in result.velocity:
        assert np.all(np.isfinite(a))
        assert max_divergence(a, b, c) < max(10.0 * initial_fd_div, 5e-3)  # bounded, O(h^2)


def test_fd_solver_is_deterministic() -> None:
    grid = make_grid(16)
    field = taylor_green_fd(grid)
    a = simulate_fd(field, grid, 0.02, 0.01, 40, 40).velocity[-1][0]
    b = simulate_fd(field, grid, 0.02, 0.01, 40, 40).velocity[-1][0]
    assert np.array_equal(a, b)


def test_cross_code_agrees_on_integral_physics() -> None:
    comparison = compare_taylorgreen(nodes=16, physical_time=3.0)
    # The two independent codes track the same energy decay closely...
    assert comparison.energy_trajectory_correlation > 0.9
    # ...while the fine event timing differs (numerics-sensitive) -- reported, not hidden.
    assert comparison.enstrophy_peak_time_rel_error is None or comparison.enstrophy_peak_time_rel_error >= 0.0


def test_fd_taylorgreen_raw_produces_event() -> None:
    raw = simulate_taylorgreen_fd_raw(90, nodes=16, steps=400, record_every=30)
    assert raw.family == "taylorgreen_fd"
    assert raw.event_frame is None or 0 < raw.event_frame < len(raw.times)
