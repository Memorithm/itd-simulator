"""Exact-oracle and convergence tests for the 3D velocity-gradient diagnostics."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.diagnostics_3d import analytical_fields as af
from itd_research.diagnostics_3d import operators as op
from itd_research.diagnostics_3d import velocity_gradient as vg


def _linear_gradient(matrix: np.ndarray) -> np.ndarray:
    grid = af.finite_grid_3d(9, -1.0, 1.0)
    u, v, w = af.linear_velocity(matrix, grid)
    return op.velocity_gradient_3d(u, v, w, grid.x, grid.y, grid.z, "finite")


def test_operator_recovers_constant_gradient_exactly() -> None:
    matrix = af.rotation_plus_strain_gradient(1.3, 0.7)
    recovered = _linear_gradient(matrix)
    assert np.allclose(recovered, matrix, atol=1e-12)


def test_rigid_rotation_diagnostics() -> None:
    omega = 1.3
    matrix = af.rigid_rotation_gradient(omega)
    assert float(vg.q_criterion(matrix)) == pytest.approx(omega**2, abs=1e-12)
    assert float(vg.lambda2(matrix)) == pytest.approx(-(omega**2), abs=1e-12)
    assert float(vg.swirling_strength(matrix)) == pytest.approx(omega, abs=1e-12)


def test_pure_strain_diagnostics() -> None:
    a = 0.7
    matrix = af.pure_strain_gradient(a)
    assert float(vg.q_criterion(matrix)) == pytest.approx(-(a**2), abs=1e-12)
    assert float(vg.lambda2(matrix)) == pytest.approx(a**2, abs=1e-12)
    assert float(vg.swirling_strength(matrix)) == pytest.approx(0.0, abs=1e-12)


def test_simple_shear_has_vorticity_but_no_swirl() -> None:
    """Critical case: nonzero vorticity yet zero Q, lambda2, and swirling."""
    gamma = 0.9
    matrix = af.simple_shear_gradient(gamma)
    assert float(vg.q_criterion(matrix)) == pytest.approx(0.0, abs=1e-12)
    assert float(vg.lambda2(matrix)) == pytest.approx(0.0, abs=1e-12)
    assert float(vg.swirling_strength(matrix)) == pytest.approx(0.0, abs=1e-12)
    recovered = _linear_gradient(matrix)
    vorticity_z = op.vorticity_3d_from_gradient(recovered)[..., 2]
    assert np.allclose(vorticity_z, -gamma, atol=1e-12)


def test_zero_field_diagnostics_vanish() -> None:
    matrix = np.zeros((3, 3))
    assert float(vg.q_criterion(matrix)) == 0.0
    assert float(vg.lambda2(matrix)) == 0.0
    assert float(vg.swirling_strength(matrix)) == 0.0


def test_rotation_plus_strain_swirl_matches_2x2_eigenvalue() -> None:
    omega, strain = 1.3, 0.7
    matrix = af.rotation_plus_strain_gradient(omega, strain)
    # In-plane block eigenvalues: +/- i*sqrt(omega^2 - strain^2).
    expected = np.sqrt(omega**2 - strain**2)
    assert float(vg.swirling_strength(matrix)) == pytest.approx(expected, abs=1e-12)


def test_swirl_axis_is_z_for_rotation_about_z() -> None:
    matrix = af.axisymmetric_stretch_rotation_gradient(1.3, 0.4)
    field = matrix[None, None, None, :, :]
    result = vg.swirling_strength_with_axis(field)
    assert bool(result["well_conditioned"][0, 0, 0])
    axis = result["axis"][0, 0, 0]
    assert abs(abs(axis[2]) - 1.0) < 1e-9  # swirl axis aligned with z


@pytest.mark.parametrize("gamma", [0.5, 1.5])
def test_okubo_weiss_signs(gamma: float) -> None:
    rotation = np.array([[0.0, -gamma], [gamma, 0.0]])
    strain = np.array([[gamma, 0.0], [0.0, -gamma]])
    assert float(vg.okubo_weiss_2d(rotation)) < 0.0  # rotation dominated
    assert float(vg.okubo_weiss_2d(strain)) > 0.0  # strain dominated


def test_burgers_vortex_vorticity_converges_second_order() -> None:
    errors = []
    spacings = []
    for nodes in (17, 33, 65):
        grid = af.finite_grid_3d(nodes, -3.0, 3.0)
        u, v, w = af.burgers_vortex(grid, 2.0, 0.5, 0.3)
        gradient = op.velocity_gradient_3d(u, v, w, grid.x, grid.y, grid.z, "finite")
        numeric = op.vorticity_3d_from_gradient(gradient)[..., 2]
        analytic = af.burgers_vortex_axial_vorticity(grid, 2.0, 0.5)
        errors.append(float(np.max(np.abs(numeric - analytic))))
        spacings.append(float(grid.x[1] - grid.x[0]))
    order = np.log(errors[0] / errors[-1]) / np.log(spacings[0] / spacings[-1])
    assert 1.7 < order < 2.3


def test_taylor_green_3d_is_incompressible() -> None:
    grid = af.periodic_grid_3d(32, 2.0 * np.pi)
    u, v, w = af.taylor_green_3d(grid, 1.0, 1.0)
    gradient = op.velocity_gradient_3d(u, v, w, grid.x, grid.y, grid.z, "periodic")
    divergence = gradient[..., 0, 0] + gradient[..., 1, 1] + gradient[..., 2, 2]
    assert float(np.max(np.abs(divergence))) < 1e-12


def test_periodic_derivative_of_sinusoid_second_order() -> None:
    errors = []
    spacings = []
    for nodes in (16, 32, 64):
        coords = np.arange(nodes) * (2.0 * np.pi / nodes)
        field = np.sin(coords)
        numeric = op.partial_derivative(field, coords, axis=0, boundary_mode="periodic")
        errors.append(float(np.max(np.abs(numeric - np.cos(coords)))))
        spacings.append(2.0 * np.pi / nodes)
    order = np.log(errors[0] / errors[-1]) / np.log(spacings[0] / spacings[-1])
    assert 1.8 < order < 2.2


def test_operators_reject_bad_inputs() -> None:
    grid = af.finite_grid_3d(5, -1.0, 1.0)
    u, v, w = af.linear_velocity(af.rigid_rotation_gradient(1.0), grid)
    bad = u.copy()
    bad[0, 0, 0] = np.inf
    with pytest.raises(ValueError):
        op.velocity_gradient_3d(bad, v, w, grid.x, grid.y, grid.z, "finite")
    with pytest.raises(ValueError):
        op.velocity_gradient_3d(u, v, w, grid.x, grid.y, grid.z, "unknown")
    with pytest.raises(ValueError):
        vg.lambda2(np.zeros((2, 2)))  # lambda2 needs 3x3


def test_diagnostics_reject_non_finite() -> None:
    bad = np.full((3, 3), np.nan)
    with pytest.raises(ValueError):
        vg.q_criterion(bad)
