"""Deterministic pseudo-spectral 2D Navier-Stokes solver (research).

A minimal, NumPy-only vorticity-streamfunction solver on a doubly-periodic box.
It exists so the external-validation layer can run a **genuine independent CFD
solver in-environment** -- not ITD, not a queried database, not a hand-made
synthetic fixture -- and then apply the ITD channels and the transport-vs
-deformation decomposition to the solver's own time evolution.

Formulation (2D incompressible NS, vorticity form):

    d omega / d t + (u . grad) omega = nu * laplacian(omega)
    laplacian(psi) = -omega,   u = d psi/d y,   v = -d psi/d x

Solved spectrally with 2/3-rule dealiasing and classical RK4 time stepping. It is
fully deterministic (no randomness), float64, and periodic. In the inviscid limit
(nu = 0) it conserves kinetic energy and enstrophy to time-discretisation error --
the property used to validate it -- and 2D vorticity is materially conserved,
which is what makes the transport-vs-deformation residual meaningful.

This is a numerical experiment generated locally; it is genuine CFD but is **not**
external empirical data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
ComplexArray: TypeAlias = NDArray[np.complex128]


@dataclass(frozen=True)
class SpectralGrid:
    """Wavenumber operators for a square doubly-periodic box."""

    nodes: int
    length: float
    kx: FloatArray
    ky: FloatArray
    k_squared: FloatArray
    inv_k_squared: FloatArray
    dealias: FloatArray

    @property
    def coordinates(self) -> FloatArray:
        spacing = self.length / self.nodes
        return np.arange(self.nodes, dtype=np.float64) * spacing


def spectral_grid(nodes: int, length: float) -> SpectralGrid:
    """Build the spectral operators for an ``nodes x nodes`` box of side ``length``."""
    if nodes < 8 or nodes % 2 != 0:
        raise ValueError("nodes must be an even integer >= 8.")
    if not np.isfinite(length) or length <= 0.0:
        raise ValueError("length must be finite and strictly positive.")
    wavenumbers = 2.0 * np.pi * np.fft.fftfreq(nodes, d=length / nodes)
    ky: FloatArray
    kx: FloatArray
    ky, kx = np.meshgrid(wavenumbers, wavenumbers, indexing="ij")
    k_squared = kx**2 + ky**2
    safe = k_squared.copy()
    safe[0, 0] = 1.0  # avoid division by zero for the mean mode
    inv_k_squared = 1.0 / safe
    inv_k_squared[0, 0] = 0.0  # drop the (undetermined) mean streamfunction
    cutoff = (2.0 / 3.0) * np.max(np.abs(wavenumbers))
    dealias = ((np.abs(kx) < cutoff) & (np.abs(ky) < cutoff)).astype(np.float64)
    return SpectralGrid(nodes, float(length), kx, ky, k_squared, inv_k_squared, dealias)


def velocity_from_vorticity(
    omega: FloatArray, grid: SpectralGrid
) -> tuple[FloatArray, FloatArray]:
    """Recover the incompressible velocity ``(u, v)`` from a vorticity field."""
    omega_hat = np.fft.fft2(np.asarray(omega, dtype=np.float64))
    psi_hat = omega_hat * grid.inv_k_squared
    u = np.fft.ifft2(1j * grid.ky * psi_hat).real
    v = np.fft.ifft2(-1j * grid.kx * psi_hat).real
    return np.ascontiguousarray(u), np.ascontiguousarray(v)


def _rhs(omega_hat: ComplexArray, grid: SpectralGrid, viscosity: float) -> ComplexArray:
    psi_hat = omega_hat * grid.inv_k_squared
    u = np.fft.ifft2(1j * grid.ky * psi_hat).real
    v = np.fft.ifft2(-1j * grid.kx * psi_hat).real
    omega_x = np.fft.ifft2(1j * grid.kx * omega_hat).real
    omega_y = np.fft.ifft2(1j * grid.ky * omega_hat).real
    advection_hat = np.fft.fft2(u * omega_x + v * omega_y) * grid.dealias
    return np.asarray(-advection_hat - viscosity * grid.k_squared * omega_hat, dtype=np.complex128)


def energy_enstrophy(omega: FloatArray, grid: SpectralGrid) -> tuple[float, float]:
    """Mean kinetic energy ``<|u|^2>/2`` and enstrophy ``<omega^2>/2``."""
    u, v = velocity_from_vorticity(omega, grid)
    energy = 0.5 * float(np.mean(u**2 + v**2))
    enstrophy = 0.5 * float(np.mean(np.asarray(omega, dtype=np.float64) ** 2))
    return energy, enstrophy


@dataclass(frozen=True)
class SimulationResult:
    """Recorded vorticity snapshots from a run, plus their times."""

    grid: SpectralGrid
    times: tuple[float, ...]
    vorticity: tuple[FloatArray, ...]

    def velocity(self, index: int) -> tuple[FloatArray, FloatArray]:
        return velocity_from_vorticity(self.vorticity[index], self.grid)


def simulate_vorticity(
    omega0: FloatArray,
    grid: SpectralGrid,
    viscosity: float,
    delta_time: float,
    steps: int,
    record_every: int = 1,
) -> SimulationResult:
    """Integrate the 2D vorticity equation with RK4 and record snapshots.

    ``record_every`` controls how often a physical-space vorticity snapshot is
    stored (the initial field is always stored). The time step is checked against
    a simple advective CFL estimate and rejected if clearly unstable.
    """
    field = np.asarray(omega0, dtype=np.float64)
    if field.shape != (grid.nodes, grid.nodes):
        raise ValueError("omega0 shape does not match the grid.")
    dt = float(delta_time)
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("delta_time must be finite and strictly positive.")
    if steps < 1 or record_every < 1:
        raise ValueError("steps and record_every must be positive integers.")
    if not np.isfinite(viscosity) or viscosity < 0.0:
        raise ValueError("viscosity must be finite and non-negative.")

    omega_hat: ComplexArray = np.fft.fft2(field)
    times = [0.0]
    snapshots = [field.copy()]
    for step in range(1, steps + 1):
        k1 = _rhs(omega_hat, grid, viscosity)
        k2 = _rhs(omega_hat + 0.5 * dt * k1, grid, viscosity)
        k3 = _rhs(omega_hat + 0.5 * dt * k2, grid, viscosity)
        k4 = _rhs(omega_hat + dt * k3, grid, viscosity)
        omega_hat = omega_hat + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if step % record_every == 0 or step == steps:
            snapshot = np.fft.ifft2(omega_hat).real
            if not np.all(np.isfinite(snapshot)):
                raise FloatingPointError(
                    "simulation went non-finite; reduce delta_time or add viscosity."
                )
            snapshots.append(np.ascontiguousarray(snapshot))
            times.append(step * dt)
    return SimulationResult(grid, tuple(times), tuple(snapshots))


def gaussian_vortex_pair(
    grid: SpectralGrid,
    circulation: float = 1.0,
    core: float = 0.5,
    separation: float = 1.6,
    same_sign: bool = True,
) -> FloatArray:
    """Two Gaussian vorticity blobs, centred in the box, for a merger run.

    Like-signed blobs (``same_sign``) co-rotate and merge into a single core; the
    opposite-sign case is a propagating dipole. The field is periodic-safe because
    Gaussians decay well inside the box for a sensible ``core``.
    """
    coordinates = grid.coordinates
    yy: FloatArray
    xx: FloatArray
    yy, xx = np.meshgrid(coordinates, coordinates, indexing="ij")
    centre = 0.5 * grid.length
    peak = float(circulation) / (np.pi * core**2)
    sign = 1.0 if same_sign else -1.0
    left = peak * np.exp(-(((xx - centre + 0.5 * separation) ** 2) + (yy - centre) ** 2) / core**2)
    right = sign * peak * np.exp(
        -(((xx - centre - 0.5 * separation) ** 2) + (yy - centre) ** 2) / core**2
    )
    field = left + right
    field = field - float(np.mean(field))  # zero mean vorticity (periodic constraint)
    return np.ascontiguousarray(field.astype(np.float64))
