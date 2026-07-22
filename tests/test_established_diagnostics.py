"""Tests for the established comparison diagnostics."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research import analytical_cases as ac
from itd_research.established_diagnostics import (
    established_diagnostics,
    kinetic_energy_density,
    vorticity_diagnostics,
)
from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary


def test_zero_field_diagnostics_vanish() -> None:
    grid = ac.finite_grid(17, -1.0, 1.0)
    vx, vy = ac.zero_field(grid.x, grid.y)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, "finite")
    assert diagnostics["kinetic_energy_density"] == 0.0
    assert diagnostics["enstrophy"] == 0.0
    assert diagnostics["mean_square_vorticity"] == 0.0
    assert diagnostics["palinstrophy"] == 0.0


def test_solid_body_enstrophy_matches_analytic() -> None:
    grid = ac.finite_grid(65, -2.0, 2.0)
    vx, vy = ac.solid_body_rotation(grid.x, grid.y, 1.3)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, "finite")
    assert diagnostics["mean_square_vorticity"] == pytest.approx((2.0 * 1.3) ** 2, rel=1e-9)
    assert diagnostics["enstrophy"] == pytest.approx(0.5 * (2.0 * 1.3) ** 2, rel=1e-9)


def test_localization_reference_equals_flatness_minus_one() -> None:
    grid = ac.periodic_grid(64, 2.0 * np.pi)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "periodic")
    diagnostics = vorticity_diagnostics(omega, grid.spacing, "periodic")
    assert diagnostics["itd_localization_reference"] == pytest.approx(
        diagnostics["vorticity_flatness"] - 1.0
    )
    assert diagnostics["vorticity_excess_kurtosis"] == pytest.approx(
        diagnostics["vorticity_flatness"] - 3.0
    )


def test_counter_rotating_pair_has_near_zero_circulation() -> None:
    grid = ac.finite_grid(129, -3.0, 3.0)
    vx, vy = ac.counter_rotating_pair(grid.x, grid.y, 2.0, 0.5, 2.0)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, "finite")
    assert diagnostics["domain_circulation"] == pytest.approx(0.0, abs=1e-6)


def test_kinetic_energy_density_of_uniform_flow() -> None:
    grid = ac.finite_grid(17, -1.0, 1.0)
    vx = np.full(grid.shape, 3.0)
    vy = np.full(grid.shape, 4.0)
    energy = kinetic_energy_density(vx, vy, grid.spacing, "finite")
    assert energy == pytest.approx(0.5 * (9.0 + 16.0))


def test_nonfinite_inputs_rejected() -> None:
    grid = ac.finite_grid(9, -1.0, 1.0)
    bad = np.zeros(grid.shape)
    bad[0, 0] = np.inf
    with pytest.raises(ValueError):
        vorticity_diagnostics(bad, grid.spacing, "finite")
    with pytest.raises(ValueError):
        established_diagnostics(bad, np.zeros(grid.shape), grid.spacing, "finite")
