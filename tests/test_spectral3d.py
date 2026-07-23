"""Validation of the deterministic pseudo-spectral 3D Navier-Stokes solver (Gate A)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.spectral3d import (
    abc_flow_velocity,
    corotating_tubes,
    curl,
    divergence,
    isotropic_seed,
    kinetic_energy,
    laplacian_vector,
    project_solenoidal,
    simulate,
    spectral_grid_3d,
    taylor_green_velocity,
    vorticity_budget,
)
from itd_research.spectral3d.grids import spectral_grid_3d as make_grid
from itd_research.spectral3d.operators import gradient_scalar


def test_grid_rejects_bad_size() -> None:
    with pytest.raises(ValueError):
        spectral_grid_3d(15)
    with pytest.raises(ValueError):
        spectral_grid_3d(4)
    with pytest.raises(ValueError):
        spectral_grid_3d(16, 0.0)


def test_derivative_sign_each_direction() -> None:
    grid = spectral_grid_3d(16)
    xx, yy, zz = grid.mesh()
    fx, fy, fz = gradient_scalar(np.sin(xx), grid)
    assert np.allclose(fx, np.cos(xx), atol=1e-12)
    assert np.allclose(fy, 0.0, atol=1e-12) and np.allclose(fz, 0.0, atol=1e-12)
    fx, fy, fz = gradient_scalar(np.sin(2.0 * yy), grid)
    assert np.allclose(fy, 2.0 * np.cos(2.0 * yy), atol=1e-12)
    assert np.allclose(fx, 0.0, atol=1e-12) and np.allclose(fz, 0.0, atol=1e-12)
    fx, fy, fz = gradient_scalar(np.cos(3.0 * zz), grid)
    assert np.allclose(fz, -3.0 * np.sin(3.0 * zz), atol=1e-12)
    assert np.allclose(fx, 0.0, atol=1e-12) and np.allclose(fy, 0.0, atol=1e-12)


def test_laplacian_known() -> None:
    grid = spectral_grid_3d(16)
    xx, yy, zz = grid.mesh()
    field = np.sin(xx) * np.cos(2.0 * yy)
    lu, _, _ = laplacian_vector(field, np.zeros_like(field), np.zeros_like(field), grid)
    assert np.allclose(lu, -(1.0 + 4.0) * field, atol=1e-11)


def test_abc_curl_equals_velocity() -> None:
    grid = spectral_grid_3d(16)
    u, v, w = abc_flow_velocity(grid)
    cx, cy, cz = curl(u, v, w, grid)
    assert np.allclose(cx, u, atol=1e-11)
    assert np.allclose(cy, v, atol=1e-11)
    assert np.allclose(cz, w, atol=1e-11)


def test_taylor_green_is_divergence_free() -> None:
    grid = spectral_grid_3d(16)
    u, v, w = taylor_green_velocity(grid)
    assert np.max(np.abs(divergence(u, v, w, grid))) < 1e-11


def test_projection_properties() -> None:
    grid = spectral_grid_3d(16)
    u, v, w = isotropic_seed(grid, seed=1)
    up, vp, wp = project_solenoidal(u, v, w, grid)
    assert np.max(np.abs(divergence(up, vp, wp, grid))) < 1e-11
    # idempotent
    up2, vp2, wp2 = project_solenoidal(up, vp, wp, grid)
    assert np.allclose(up2, up, atol=1e-12)
    # a solenoidal field is unchanged
    tu, tv, tw = taylor_green_velocity(grid)
    su, sv, sw = project_solenoidal(tu, tv, tw, grid)
    assert np.allclose(su, tu, atol=1e-11)
    # a pure gradient is removed, and projection never adds energy
    xx, yy, _ = grid.mesh()
    gx, gy, gz = gradient_scalar(np.sin(xx) * np.cos(2.0 * yy), grid)
    rx, ry, rz = project_solenoidal(gx, gy, gz, grid)
    assert kinetic_energy(rx, ry, rz) < 1e-20
    assert kinetic_energy(up, vp, wp) <= kinetic_energy(u, v, w) + 1e-12


def test_dealias_mask_zeros_top_third() -> None:
    grid = spectral_grid_3d(24)
    # modes at |k| just above 2/3 * k_max must be masked out
    assert float(np.min(grid.dealias)) == 0.0
    assert float(np.max(grid.dealias)) == 1.0


def test_viscous_decay_single_mode() -> None:
    grid = spectral_grid_3d(16)
    _, yy, _ = grid.mesh()
    u = np.sin(yy)  # k=1, divergence-free (only x-component varying with y)
    zero = np.zeros_like(u)
    viscosity = 0.1
    result = simulate((u, zero, zero), grid, viscosity, 0.005, steps=200, record_every=200)
    amplitude = float(np.max(np.abs(result.velocity[-1][0])))
    expected = float(np.exp(-viscosity * 1.0 * result.times[-1]))
    assert abs(amplitude - expected) / expected < 1e-6


def test_inviscid_energy_conserved_and_enstrophy_grows() -> None:
    grid = spectral_grid_3d(32)
    result = simulate(taylor_green_velocity(grid), grid, 0.0, 0.004, steps=200, record_every=50)
    energy0 = result.energy[0]
    for energy in result.energy:
        assert abs(energy - energy0) / energy0 < 1e-10  # 3D energy conserved inviscibly
    # Taylor-Green stretches vorticity, so enstrophy grows (3D, not conserved)
    assert result.enstrophy[-1] > result.enstrophy[0] * 1.05
    # divergence stays at round-off throughout
    assert max(result.divergence_linf) < 1e-10


def test_vorticity_budget_closes() -> None:
    grid = spectral_grid_3d(32)
    viscosity = 0.01
    warmed = simulate(taylor_green_velocity(grid), grid, viscosity, 0.005, steps=200, record_every=200).velocity[-1]
    after = simulate(warmed, grid, viscosity, 0.002, steps=1, record_every=1).velocity[-1]
    budget = vorticity_budget(warmed, after, 0.002, grid, viscosity)
    # stretching is a leading-order term in 3D (not negligible vs advection)
    assert budget.stretching_rms > 0.3 * budget.advection_rms
    assert budget.closure_fraction < 0.05  # budget closes


def test_simulation_is_deterministic() -> None:
    grid = spectral_grid_3d(16)
    run_a = simulate(taylor_green_velocity(grid), grid, 0.01, 0.005, steps=40, record_every=40)
    run_b = simulate(taylor_green_velocity(grid), grid, 0.01, 0.005, steps=40, record_every=40)
    assert all(np.array_equal(a, b) for a, b in zip(run_a.velocity[-1], run_b.velocity[-1], strict=True))


def test_seeded_initial_condition_is_reproducible() -> None:
    grid = spectral_grid_3d(16)
    a = isotropic_seed(grid, seed=123)
    b = isotropic_seed(grid, seed=123)
    assert all(np.array_equal(x, y) for x, y in zip(a, b, strict=True))
    assert np.max(np.abs(divergence(*a, grid))) < 1e-11


def test_corotating_tubes_are_solenoidal() -> None:
    grid = spectral_grid_3d(24)
    u, v, w = corotating_tubes(grid, circulation=2.0, core=0.5, separation=1.5)
    assert np.max(np.abs(divergence(u, v, w, grid))) < 1e-10


def test_simulate_rejects_bad_parameters() -> None:
    grid = spectral_grid_3d(16)
    field = taylor_green_velocity(grid)
    with pytest.raises(ValueError):
        simulate(field, grid, 0.01, 0.0, steps=1)
    with pytest.raises(ValueError):
        simulate(field, grid, -1.0, 0.01, steps=1)
    with pytest.raises(ValueError):
        simulate((np.zeros((8, 8, 8)), np.zeros((8, 8, 8)), np.zeros((8, 8, 8))), grid, 0.0, 0.01, steps=1)


def test_high_cfl_is_rejected() -> None:
    grid = make_grid(16)
    fast = tuple(100.0 * c for c in taylor_green_velocity(grid))
    with pytest.raises(ValueError):
        simulate(fast, grid, 0.0, 0.5, steps=1)


def test_checkpoint_roundtrip_and_restart(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from itd_research.spectral3d.checkpoint import load_checkpoint, save_checkpoint

    grid = spectral_grid_3d(16)
    warmed = simulate(taylor_green_velocity(grid), grid, 0.01, 0.005, steps=20, record_every=20).velocity[-1]
    path = tmp_path / "ckpt.npz"
    save_checkpoint(path, warmed, grid, time=0.1, delta_time=0.005, viscosity=0.01)
    restored = load_checkpoint(path)
    assert restored.grid.nodes == 16
    assert all(np.array_equal(a, b) for a, b in zip(warmed, restored.velocity, strict=True))
    # restart is bit-for-bit identical to continuing in memory
    a = simulate(warmed, grid, 0.01, 0.005, steps=10, record_every=10).velocity[-1]
    b = simulate(restored.velocity, grid, 0.01, 0.005, steps=10, record_every=10).velocity[-1]
    assert all(np.array_equal(x, y) for x, y in zip(a, b, strict=True))


def test_checkpoint_detects_corruption(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from itd_research.spectral3d.checkpoint import load_checkpoint, save_checkpoint

    grid = spectral_grid_3d(16)
    field = taylor_green_velocity(grid)
    path = tmp_path / "ckpt.npz"
    save_checkpoint(path, field, grid, time=0.0, delta_time=0.005, viscosity=0.0)
    # tamper with the stored velocity so the checksum no longer matches
    with np.load(path, allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    data["u"] = data["u"] + 1.0
    np.savez(path, **data)
    with pytest.raises(ValueError):
        load_checkpoint(path)
