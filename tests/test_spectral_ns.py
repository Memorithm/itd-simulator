"""Validation of the deterministic pseudo-spectral 2D Navier-Stokes solver."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.external_validation.spectral_ns import (
    energy_enstrophy,
    gaussian_vortex_pair,
    simulate_vorticity,
    spectral_grid,
    velocity_from_vorticity,
)
from itd_research.external_validation.transport import transport_decomposition


def test_spectral_grid_rejects_bad_size() -> None:
    with pytest.raises(ValueError):
        spectral_grid(7, 2.0 * np.pi)  # odd
    with pytest.raises(ValueError):
        spectral_grid(4, 2.0 * np.pi)  # too small
    with pytest.raises(ValueError):
        spectral_grid(16, 0.0)  # bad length


def test_gaussian_vortex_pair_has_zero_mean() -> None:
    grid = spectral_grid(32, 2.0 * np.pi)
    field = gaussian_vortex_pair(grid, circulation=2.0, core=0.5, separation=1.5)
    assert field.shape == (32, 32)
    assert float(np.mean(field)) == pytest.approx(0.0, abs=1e-12)


def test_velocity_vorticity_roundtrip() -> None:
    grid = spectral_grid(48, 2.0 * np.pi)
    omega = gaussian_vortex_pair(grid, circulation=2.0, core=0.6, separation=1.6)
    u, v = velocity_from_vorticity(omega, grid)
    # recompute vorticity spectrally: omega = dv/dx - du/dy
    dv_dx = np.fft.ifft2(1j * grid.kx * np.fft.fft2(v)).real
    du_dy = np.fft.ifft2(1j * grid.ky * np.fft.fft2(u)).real
    assert np.allclose(dv_dx - du_dy, omega, atol=1e-10)


def test_inviscid_conserves_energy_and_enstrophy() -> None:
    grid = spectral_grid(64, 2.0 * np.pi)
    omega0 = gaussian_vortex_pair(grid, circulation=2.0, core=0.6, separation=1.8)
    result = simulate_vorticity(omega0, grid, viscosity=0.0, delta_time=0.002, steps=300, record_every=100)
    energy0, enstrophy0 = energy_enstrophy(result.vorticity[0], grid)
    for index in range(len(result.times)):
        energy, enstrophy = energy_enstrophy(result.vorticity[index], grid)
        assert energy == pytest.approx(energy0, rel=1e-9)
        assert enstrophy == pytest.approx(enstrophy0, rel=1e-9)


def test_viscosity_dissipates_enstrophy() -> None:
    grid = spectral_grid(64, 2.0 * np.pi)
    omega0 = gaussian_vortex_pair(grid, circulation=2.0, core=0.5, separation=1.5)
    result = simulate_vorticity(omega0, grid, viscosity=0.02, delta_time=0.002, steps=400, record_every=400)
    _, enstrophy0 = energy_enstrophy(result.vorticity[0], grid)
    _, enstrophy1 = energy_enstrophy(result.vorticity[-1], grid)
    assert enstrophy1 < enstrophy0  # 2D enstrophy decays under viscosity


def test_transport_residual_recovers_viscous_term() -> None:
    """On genuine NS dynamics the compensated residual equals nu*laplacian(omega)."""
    grid = spectral_grid(96, 2.0 * np.pi)
    x = grid.coordinates
    viscosity = 0.01
    omega0 = gaussian_vortex_pair(grid, circulation=3.0, core=0.5, separation=1.6)
    warmed = simulate_vorticity(omega0, grid, viscosity, 0.001, steps=400, record_every=400).vorticity[-1]
    delta_time = 0.001
    after = simulate_vorticity(warmed, grid, viscosity, delta_time, steps=1, record_every=1).vorticity[-1]
    u, v = velocity_from_vorticity(warmed, grid)
    decomposition = transport_decomposition(warmed, after, u, v, x, x, delta_time, "periodic")
    expected = viscosity * np.fft.ifft2(-grid.k_squared * np.fft.fft2(warmed)).real

    def rms(a: np.ndarray) -> float:
        return float(np.sqrt(np.mean(a**2)))

    # transport dominates the Eulerian change; the residual is the (small) material term
    assert decomposition.residual_fraction < 0.5
    # and that residual matches the exact viscous material derivative
    assert rms(decomposition.material_residual - expected) / rms(decomposition.material_residual) < 0.15


def test_simulate_rejects_bad_parameters() -> None:
    grid = spectral_grid(16, 2.0 * np.pi)
    good = gaussian_vortex_pair(grid)
    with pytest.raises(ValueError):
        simulate_vorticity(good, grid, viscosity=0.0, delta_time=0.0, steps=1)
    with pytest.raises(ValueError):
        simulate_vorticity(good, grid, viscosity=-1.0, delta_time=0.01, steps=1)
    with pytest.raises(ValueError):
        simulate_vorticity(np.zeros((8, 8)), grid, viscosity=0.0, delta_time=0.01, steps=1)
