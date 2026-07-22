"""Tests for the analytical/manufactured field catalogue."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research import analytical_cases as ac
from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    spatial_mean,
)


def test_finite_grid_is_endpoint_included() -> None:
    grid = ac.finite_grid(5, -1.0, 1.0)
    assert grid.boundary_mode == "finite"
    assert grid.x[0, 0] == -1.0 and grid.x[0, -1] == 1.0
    assert grid.spacing == pytest.approx(0.5)


def test_periodic_grid_is_endpoint_excluded() -> None:
    grid = ac.periodic_grid(4, 2.0)
    assert grid.boundary_mode == "periodic"
    assert grid.spacing == pytest.approx(0.5)
    assert grid.x[0, -1] == pytest.approx(1.5)  # last node is period - spacing


@pytest.mark.parametrize(
    "builder",
    [
        lambda: ac.finite_grid(2, -1.0, 1.0),
        lambda: ac.finite_grid(5, 1.0, -1.0),
        lambda: ac.periodic_grid(2, 1.0),
        lambda: ac.periodic_grid(5, 0.0),
    ],
)
def test_invalid_grids_rejected(builder) -> None:
    with pytest.raises(ValueError):
        builder()


def test_solid_body_rotation_has_uniform_analytic_vorticity() -> None:
    grid = ac.finite_grid(33, -2.0, 2.0)
    vx, vy = ac.solid_body_rotation(grid.x, grid.y, 1.5)
    omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "finite")
    assert np.allclose(omega, 2.0 * 1.5, atol=1e-12)


def test_uniform_shear_has_uniform_analytic_vorticity() -> None:
    grid = ac.finite_grid(33, -1.0, 1.0)
    vx, vy = ac.uniform_shear(grid.x, grid.y, 0.8)
    omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "finite")
    assert np.allclose(omega, -0.8, atol=1e-12)


def test_taylor_green_numeric_vorticity_matches_analytic_scaling() -> None:
    grid = ac.periodic_grid(64, 2.0 * np.pi)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    omega_numeric = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "periodic")
    omega_analytic = ac.taylor_green_vorticity(grid.x, grid.y, 1.0, 1.0)
    # Numeric vorticity is a uniform sinc-scaling of the analytic field.
    nonzero = np.abs(omega_analytic) > 1e-6
    ratio = omega_numeric[nonzero] / omega_analytic[nonzero]
    assert np.allclose(ratio, ratio.flat[0], atol=1e-12)


def test_taylor_green_closed_form_constants() -> None:
    assert ac.taylor_green_localization() == 1.25
    assert ac.taylor_green_mean_square_vorticity(2.0, 3.0) == pytest.approx(36.0)
    assert ac.taylor_green_heterogeneity_continuum() == pytest.approx(
        (np.pi**2 / 8.0) * np.sqrt(1.0 - 64.0 / np.pi**4)
    )


def test_lamb_oseen_has_regular_core_limit() -> None:
    grid = ac.finite_grid(65, -3.0, 3.0)
    vx, vy = ac.lamb_oseen(grid.x, grid.y, 2.0, 0.5)
    assert np.all(np.isfinite(vx)) and np.all(np.isfinite(vy))
    omega = ac.lamb_oseen_vorticity(grid.x, grid.y, 2.0, 0.5)
    centre = grid.node_count // 2
    assert omega[centre, centre] == pytest.approx(
        ac.lamb_oseen_peak_vorticity(2.0, 0.5), rel=1e-3
    )


def test_lamb_oseen_rejects_nonpositive_core() -> None:
    grid = ac.finite_grid(9, -1.0, 1.0)
    with pytest.raises(ValueError):
        ac.lamb_oseen(grid.x, grid.y, 1.0, 0.0)


def test_counter_rotating_pair_is_sign_balanced() -> None:
    grid = ac.finite_grid(65, -3.0, 3.0)
    vx, vy = ac.counter_rotating_pair(grid.x, grid.y, 2.0, 0.5, 2.0)
    omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "finite")
    assert spatial_mean(omega, grid.spacing, "finite") == pytest.approx(0.0, abs=1e-9)
    assert np.any(omega > 0.0) and np.any(omega < 0.0)


def test_fields_are_float64_and_deterministic() -> None:
    grid = ac.finite_grid(17, -1.0, 1.0)
    a = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    b = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    assert a[0].dtype == np.float64
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
