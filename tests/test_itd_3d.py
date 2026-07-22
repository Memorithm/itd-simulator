"""Analytical validation of the experimental 3D ITD candidate channels."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.diagnostics_3d import analytical_fields as af
from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d


def test_rigid_rotation_channels() -> None:
    grid = af.finite_grid_3d(17, -2.0, 2.0)
    u, v, w = af.linear_velocity(af.rigid_rotation_gradient(1.3), grid)
    result = evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "finite")
    assert result.intensity == pytest.approx((2 * 1.3) ** 2, abs=1e-9)
    assert result.heterogeneity == pytest.approx(0.0, abs=1e-9)
    assert result.localization == pytest.approx(0.0, abs=1e-9)
    assert result.roughness == pytest.approx(0.0, abs=1e-9)
    assert result.orientation_dispersion == pytest.approx(0.0, abs=1e-9)
    assert result.helicity_mean == pytest.approx(0.0, abs=1e-9)
    assert result.stretching_rate == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("axial_strain", [0.3, 0.6])
def test_burgers_stretching_rate_equals_axial_strain(axial_strain: float) -> None:
    grid = af.finite_grid_3d(65, -3.0, 3.0)
    u, v, w = af.burgers_vortex(grid, 2.0, 0.5, axial_strain)
    result = evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "finite")
    assert result.stretching_rate == pytest.approx(axial_strain, abs=1e-3)


def test_abc_flow_is_maximally_helical() -> None:
    grid = af.periodic_grid_3d(24, 2.0 * np.pi)
    u, v, w = af.abc_flow(grid, 1.0, 1.0, 1.0)
    result = evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "periodic")
    # Beltrami flow: vorticity equals velocity, so normalized helicity is 1.
    assert result.normalized_helicity == pytest.approx(1.0, abs=1e-9)


def test_orientation_dispersion_separates_tube_from_antiparallel() -> None:
    grid = af.finite_grid_3d(33, -3.0, 3.0)
    u, v, w = af.vortex_tube(grid, 2.0, 0.5, axis="z")
    single = evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "finite")
    assert single.orientation_dispersion < 0.05  # one orientation

    def tube(sign: float, cx: float) -> tuple[np.ndarray, np.ndarray]:
        dx = grid.xx - cx
        r2 = dx**2 + grid.yy**2
        with np.errstate(divide="ignore", invalid="ignore"):
            factor = -np.expm1(-r2 / 0.5**2) / r2
        factor = np.where(r2 > 0.0, factor, 1.0 / 0.5**2)
        swirl = sign * (2.0 / (2.0 * np.pi)) * factor
        return -swirl * grid.yy, swirl * dx

    ua, va = tube(1.0, -1.0)
    ub, vb = tube(-1.0, 1.0)
    antiparallel = evaluate_itd3d(
        ua + ub, va + vb, np.zeros_like(ua), grid.x, grid.y, grid.z, "finite"
    )
    assert antiparallel.orientation_dispersion > 0.5


def test_magnitude_channels_are_amplitude_invariant() -> None:
    grid = af.periodic_grid_3d(24, 2.0 * np.pi)
    u, v, w = af.taylor_green_3d(grid, 1.0, 1.0)
    low = evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "periodic")
    high = evaluate_itd3d(7.0 * u, 7.0 * v, 7.0 * w, grid.x, grid.y, grid.z, "periodic")
    assert high.heterogeneity == pytest.approx(low.heterogeneity, rel=1e-10)
    assert high.localization == pytest.approx(low.localization, rel=1e-10)
    assert high.roughness == pytest.approx(low.roughness, rel=1e-10)
    assert high.orientation_dispersion == pytest.approx(low.orientation_dispersion, rel=1e-10)
    assert high.intensity == pytest.approx(49.0 * low.intensity, rel=1e-10)


def test_zero_field_gives_zero_channels() -> None:
    grid = af.finite_grid_3d(5, -1.0, 1.0)
    zero = np.zeros(grid.shape)
    result = evaluate_itd3d(zero, zero, zero, grid.x, grid.y, grid.z, "finite")
    assert result.as_dict() == {key: 0.0 for key in result.as_dict()}


def test_invalid_parameters_rejected() -> None:
    grid = af.finite_grid_3d(5, -1.0, 1.0)
    u, v, w = af.linear_velocity(af.rigid_rotation_gradient(1.0), grid)
    with pytest.raises(ValueError):
        evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "finite", characteristic_length=-1.0)
    with pytest.raises(ValueError):
        evaluate_itd3d(u, v, w, grid.x, grid.y, grid.z, "unknown")
