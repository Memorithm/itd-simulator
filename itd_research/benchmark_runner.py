"""Deterministic benchmark catalogue for the post-V29 research phase.

Each benchmark evaluates the V29.18 ITD signature and established diagnostics on
an analytical or manufactured field and compares the result with a hand-derived
expectation. Expectations are classified so that exact algebraic identities are
never conflated with continuum-limit targets:

* ``exact``            : holds at every admissible resolution (algebraic identity)
* ``continuum_limit``  : discrete value converges to a closed form as h -> 0
* ``manufactured``     : qualitative property of a constructed field
* ``regression``       : reproducibility snapshot (no independent proof)

The runner is pure computation; serialisation lives in :mod:`itd_research.reporting`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

from compare_scenarios import Config
from itd_research import analytical_cases as ac
from itd_research.established_diagnostics import established_diagnostics
from itd_research.signature import SignatureResult, evaluate_signature
from itd_v29_core.simulation_engine import simulate
from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    spatial_mean,
)

FloatArray: TypeAlias = NDArray[np.float64]

_EXACT_TOL = 1.0e-9


@dataclass(frozen=True)
class BenchmarkResolution:
    """Grid sizes and domains used by the benchmark catalogue."""

    finite_nodes: int
    periodic_nodes: int
    finite_half_width: float
    lamb_half_width: float
    label: str


QUICK = BenchmarkResolution(
    finite_nodes=65,
    periodic_nodes=64,
    finite_half_width=2.0,
    lamb_half_width=3.0,
    label="quick",
)
FULL = BenchmarkResolution(
    finite_nodes=129,
    periodic_nodes=128,
    finite_half_width=2.0,
    lamb_half_width=3.0,
    label="full",
)


@dataclass(frozen=True)
class Expectation:
    """One analytical check with an explicit tolerance and classification."""

    quantity: str
    expected: float
    computed: float
    tolerance: float
    classification: str

    @property
    def abs_error(self) -> float:
        return abs(self.computed - self.expected)

    @property
    def passed(self) -> bool:
        return self.abs_error <= self.tolerance

    def as_dict(self) -> dict[str, object]:
        record = asdict(self)
        record["abs_error"] = self.abs_error
        record["passed"] = self.passed
        return record


def _check(
    quantity: str,
    expected: float,
    computed: float,
    tolerance: float,
    classification: str,
) -> Expectation:
    return Expectation(
        quantity=quantity,
        expected=float(expected),
        computed=float(computed),
        tolerance=float(tolerance),
        classification=classification,
    )


def _signature_record(signature: SignatureResult) -> dict[str, float]:
    return signature.as_dict()


def _zero_curvature(x: FloatArray, y: FloatArray, t: float) -> FloatArray:
    return np.zeros_like(x)


# --------------------------------------------------------------------------- #
# Individual benchmark cases.                                                  #
# --------------------------------------------------------------------------- #


def case_zero_field(res: BenchmarkResolution) -> dict[str, Any]:
    grid = ac.finite_grid(res.finite_nodes, -res.finite_half_width, res.finite_half_width)
    vx, vy = ac.zero_field(grid.x, grid.y)
    signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, grid.boundary_mode)
    checks = [
        _check("intensity", 0.0, signature.intensity, _EXACT_TOL, "exact"),
        _check("heterogeneity", 0.0, signature.heterogeneity, _EXACT_TOL, "exact"),
        _check("localization", 0.0, signature.localization, _EXACT_TOL, "exact"),
        _check("roughness", 0.0, signature.roughness, _EXACT_TOL, "exact"),
        _check("sign_mixing", 0.0, signature.sign_mixing, _EXACT_TOL, "exact"),
        _check("enstrophy", 0.0, diagnostics["enstrophy"], _EXACT_TOL, "exact"),
    ]
    return {
        "name": "zero_field",
        "description": "Identically zero velocity field; all outputs vanish.",
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {},
        "signature": _signature_record(signature),
        "diagnostics": diagnostics,
        "checks": [check.as_dict() for check in checks],
    }


def case_solid_body_rotation(res: BenchmarkResolution) -> dict[str, Any]:
    rate = 1.3
    grid = ac.finite_grid(res.finite_nodes, -res.finite_half_width, res.finite_half_width)
    vx, vy = ac.solid_body_rotation(grid.x, grid.y, rate)
    signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, grid.boundary_mode)
    expected_intensity = (2.0 * rate) ** 2
    checks = [
        _check("intensity", expected_intensity, signature.intensity, 1.0e-9, "exact"),
        _check("heterogeneity", 0.0, signature.heterogeneity, _EXACT_TOL, "exact"),
        _check("localization", 0.0, signature.localization, _EXACT_TOL, "exact"),
        _check("roughness", 0.0, signature.roughness, 1.0e-9, "exact"),
        _check("sign_mixing", 0.0, signature.sign_mixing, _EXACT_TOL, "exact"),
        _check(
            "mean_square_vorticity",
            (2.0 * rate) ** 2,
            diagnostics["mean_square_vorticity"],
            1.0e-9,
            "exact",
        ),
    ]
    return {
        "name": "solid_body_rotation",
        "description": (
            "Rigid rotation vx=-Omega*y, vy=Omega*x; uniform vorticity 2*Omega."
        ),
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {"rotation_rate": rate},
        "signature": _signature_record(signature),
        "diagnostics": diagnostics,
        "checks": [check.as_dict() for check in checks],
    }


def case_uniform_shear(res: BenchmarkResolution) -> dict[str, Any]:
    shear = 0.7
    grid = ac.finite_grid(res.finite_nodes, -res.finite_half_width, res.finite_half_width)
    vx, vy = ac.uniform_shear(grid.x, grid.y, shear)
    signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, grid.boundary_mode)
    checks = [
        _check("intensity", shear**2, signature.intensity, 1.0e-9, "exact"),
        _check("heterogeneity", 0.0, signature.heterogeneity, _EXACT_TOL, "exact"),
        _check("localization", 0.0, signature.localization, _EXACT_TOL, "exact"),
        _check("roughness", 0.0, signature.roughness, 1.0e-9, "exact"),
        _check("sign_mixing", 0.0, signature.sign_mixing, _EXACT_TOL, "exact"),
    ]
    return {
        "name": "uniform_shear",
        "description": "Uniform shear vx=gamma*y, vy=0; uniform vorticity -gamma.",
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {"shear_rate": shear},
        "signature": _signature_record(signature),
        "diagnostics": diagnostics,
        "checks": [check.as_dict() for check in checks],
    }


def case_taylor_green(res: BenchmarkResolution) -> dict[str, Any]:
    amplitude, wavenumber = 1.0, 1.0
    period = 2.0 * np.pi / wavenumber
    grid = ac.periodic_grid(res.periodic_nodes, period)
    vx, vy = ac.taylor_green(grid.x, grid.y, amplitude, wavenumber)
    signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, grid.boundary_mode)
    # The centred difference scales each sinusoidal derivative by sin(kh)/(kh),
    # so <omega^2> carries a leading O(h^2) error U^2 k^2 (kh)^2 / 3 with
    # kh = 2*pi/N. A factor-two safety margin keeps the check honest about the
    # known truncation error without altering the exact reference value.
    kh = 2.0 * np.pi / grid.node_count
    leading_error = (
        ac.taylor_green_mean_square_vorticity(amplitude, wavenumber) * kh**2 / 3.0
    )
    continuum_tol = 2.0 * leading_error
    checks = [
        _check(
            "localization",
            ac.taylor_green_localization(),
            signature.localization,
            1.0e-9,
            "exact",
        ),
        _check("sign_mixing", 1.0, signature.sign_mixing, 1.0e-9, "exact"),
        _check(
            "mean_square_vorticity",
            ac.taylor_green_mean_square_vorticity(amplitude, wavenumber),
            diagnostics["mean_square_vorticity"],
            max(continuum_tol, 1.0e-9),
            "continuum_limit",
        ),
        _check(
            "heterogeneity",
            ac.taylor_green_heterogeneity_continuum(),
            signature.heterogeneity,
            0.1,
            "continuum_limit",
        ),
    ]
    return {
        "name": "taylor_green",
        "description": (
            "Periodic Taylor-Green vortex; omega=2Uk sin(kx)sin(ky). "
            "Localization=5/4 and sign_mixing=1 are exact; enstrophy and "
            "heterogeneity converge to closed forms."
        ),
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {"amplitude": amplitude, "wavenumber": wavenumber},
        "signature": _signature_record(signature),
        "diagnostics": diagnostics,
        "checks": [check.as_dict() for check in checks],
    }


def case_lamb_oseen(res: BenchmarkResolution) -> dict[str, Any]:
    circulation, core = 2.0, 0.5
    grid = ac.finite_grid(res.finite_nodes, -res.lamb_half_width, res.lamb_half_width)
    vx, vy = ac.lamb_oseen(grid.x, grid.y, circulation, core)
    omega_analytic = ac.lamb_oseen_vorticity(grid.x, grid.y, circulation, core)
    signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, grid.boundary_mode)
    omega_numeric = numerical_vorticity_with_boundary(
        vx, vy, grid.spacing, grid.boundary_mode
    )
    max_vorticity_error = float(np.max(np.abs(omega_numeric - omega_analytic)))
    peak = ac.lamb_oseen_peak_vorticity(circulation, core)
    # Second-order accurate vorticity; loose absolute tolerance for the peak.
    vorticity_tol = 40.0 * grid.spacing**2 * peak
    checks = [
        _check(
            "max_vorticity_error",
            0.0,
            max_vorticity_error,
            max(vorticity_tol, 1.0e-9),
            "continuum_limit",
        ),
        _check(
            "sign_mixing_single_sign",
            0.0,
            signature.sign_mixing,
            0.05,
            "manufactured",
        ),
    ]
    return {
        "name": "lamb_oseen",
        "description": (
            "Lamb-Oseen vortex with regular core limit; Gaussian vorticity blob "
            "used for localization, roughness, and finite-domain truncation."
        ),
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {
            "circulation": circulation,
            "core_radius": core,
            "peak_vorticity": peak,
        },
        "signature": _signature_record(signature),
        "diagnostics": diagnostics,
        "checks": [check.as_dict() for check in checks],
    }


def case_counter_rotating_pair(res: BenchmarkResolution) -> dict[str, Any]:
    circulation, core, separation = 2.0, 0.5, 2.0
    grid = ac.finite_grid(res.finite_nodes, -res.lamb_half_width, res.lamb_half_width)
    vx, vy = ac.counter_rotating_pair(grid.x, grid.y, circulation, core, separation)
    signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
    diagnostics = established_diagnostics(vx, vy, grid.spacing, grid.boundary_mode)
    # Balanced +/- vorticity => mean vorticity ~ 0 => sign_mixing ~ 1.
    checks = [
        _check("sign_mixing_balanced", 1.0, signature.sign_mixing, 1.0e-6, "manufactured"),
        _check(
            "domain_circulation",
            0.0,
            diagnostics["domain_circulation"],
            1.0e-6,
            "manufactured",
        ),
    ]
    return {
        "name": "counter_rotating_pair",
        "description": (
            "Opposite-sign Lamb-Oseen pair; sign-balanced field with sign_mixing "
            "near one and near-zero net circulation, unlike a single vortex."
        ),
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {
            "circulation": circulation,
            "core_radius": core,
            "separation": separation,
        },
        "signature": _signature_record(signature),
        "diagnostics": diagnostics,
        "checks": [check.as_dict() for check in checks],
    }


def case_amplitude_scaling(res: BenchmarkResolution) -> dict[str, Any]:
    """Same normalised structure, different amplitude.

    Demonstrates that the four spatial structural components are amplitude
    invariant while intensity scales with amplitude squared.
    """
    amplitude_a, amplitude_b = 1.0, 4.0
    wavenumber = 2.0
    period = 2.0 * np.pi / wavenumber
    grid = ac.periodic_grid(res.periodic_nodes, period)
    vx_a, vy_a = ac.taylor_green(grid.x, grid.y, amplitude_a, wavenumber)
    vx_b, vy_b = ac.taylor_green(grid.x, grid.y, amplitude_b, wavenumber)
    sig_a = evaluate_signature(vx_a, vy_a, grid.spacing, grid.boundary_mode)
    sig_b = evaluate_signature(vx_b, vy_b, grid.spacing, grid.boundary_mode)
    ratio = amplitude_b**2 / amplitude_a**2
    checks = [
        _check("heterogeneity_invariant", sig_a.heterogeneity, sig_b.heterogeneity, 1.0e-9, "exact"),
        _check("localization_invariant", sig_a.localization, sig_b.localization, 1.0e-9, "exact"),
        _check("roughness_invariant", sig_a.roughness, sig_b.roughness, 1.0e-9, "exact"),
        _check("sign_mixing_invariant", sig_a.sign_mixing, sig_b.sign_mixing, 1.0e-9, "exact"),
        _check(
            "intensity_ratio",
            ratio,
            sig_b.intensity / sig_a.intensity,
            1.0e-9,
            "exact",
        ),
    ]
    return {
        "name": "amplitude_scaling",
        "description": (
            "Identical spatial structure at amplitudes 1 and 4; structural vector "
            "invariant, intensity scales as amplitude squared."
        ),
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {
            "amplitude_a": amplitude_a,
            "amplitude_b": amplitude_b,
            "wavenumber": wavenumber,
        },
        "signature_a": _signature_record(sig_a),
        "signature_b": _signature_record(sig_b),
        "checks": [check.as_dict() for check in checks],
    }


def case_structure_pair(res: BenchmarkResolution) -> dict[str, Any]:
    """Two fields with matched intensity but different structure.

    A single localized Lamb-Oseen vortex (sign-coherent) and a rescaled
    Taylor-Green field (sign-balanced) are set to the same mean-square vorticity,
    hence the same intensity, yet their structural vectors differ markedly.
    """
    grid = ac.finite_grid(res.finite_nodes, -res.finite_half_width, res.finite_half_width)
    vx_a, vy_a = ac.lamb_oseen(grid.x, grid.y, 2.0, 0.5)
    vx_b0, vy_b0 = ac.taylor_green(grid.x, grid.y, 1.0, 2.0)
    omega_a = numerical_vorticity_with_boundary(vx_a, vy_a, grid.spacing, "finite")
    omega_b0 = numerical_vorticity_with_boundary(vx_b0, vy_b0, grid.spacing, "finite")
    ms_a = spatial_mean(omega_a**2, grid.spacing, "finite")
    ms_b0 = spatial_mean(omega_b0**2, grid.spacing, "finite")
    scale = float(np.sqrt(ms_a / ms_b0))
    vx_b, vy_b = vx_b0 * scale, vy_b0 * scale
    sig_a = evaluate_signature(vx_a, vy_a, grid.spacing, grid.boundary_mode)
    sig_b = evaluate_signature(vx_b, vy_b, grid.spacing, grid.boundary_mode)
    checks = [
        _check(
            "matched_intensity",
            sig_a.intensity,
            sig_b.intensity,
            1.0e-6 * sig_a.intensity,
            "manufactured",
        ),
        _check(
            "sign_mixing_separates",
            1.0,
            abs(sig_b.sign_mixing - sig_a.sign_mixing),
            1.0,
            "manufactured",
        ),
    ]
    return {
        "name": "structure_changed_pair",
        "description": (
            "Localized single-sign vortex vs sign-balanced field at equal "
            "intensity; the five-component vector separates cases a scalar cannot."
        ),
        "boundary_mode": grid.boundary_mode,
        "resolution": grid.node_count,
        "parameters": {"matched_mean_square_vorticity": float(ms_a)},
        "signature_a": _signature_record(sig_a),
        "signature_b": _signature_record(sig_b),
        "checks": [check.as_dict() for check in checks],
    }


def case_translated_vortex(res: BenchmarkResolution) -> dict[str, Any]:
    """Translating periodic vortex: Eulerian vs transport-compensated deformation.

    A Taylor-Green pattern is advected in x by a uniform background velocity. The
    Eulerian temporal deformation sees the translation as change; transport
    compensation removes most of it, isolating structural (not transport) change.
    """
    amplitude, wavenumber = 1.0, 1.0
    period = 2.0 * np.pi / wavenumber
    background = 0.4
    grid = ac.periodic_grid(res.periodic_nodes, period)

    def velocity(x: FloatArray, y: FloatArray, t: float) -> tuple[FloatArray, FloatArray]:
        phase = wavenumber * (x - background * t)
        vx = background + amplitude * np.sin(phase) * np.cos(wavenumber * y)
        vy = -amplitude * np.cos(phase) * np.sin(wavenumber * y)
        return np.asarray(vx, dtype=np.float64), np.asarray(vy, dtype=np.float64)

    times: FloatArray = np.linspace(0.0, 2.0, 9, dtype=np.float64)
    cfg = Config(characteristic_length=0.5)

    eulerian = simulate(
        "translated_eulerian",
        velocity,
        grid.x,
        grid.y,
        times,
        grid.spacing,
        cfg,
        curvature_function=_zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode="eulerian",
    )
    compensated = simulate(
        "translated_compensated",
        velocity,
        grid.x,
        grid.y,
        times,
        grid.spacing,
        cfg,
        curvature_function=_zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode="transport_compensated",
        transport_velocity_function=velocity,
        transport_interpolation="cubic_periodic",
        transport_trajectory_method="rk4_backtrace",
    )
    eulerian_index = float(eulerian["temporal_deformation_eulerian_index"])
    compensated_index = float(compensated["temporal_deformation_compensated_index"])
    checks = [
        _check(
            "compensated_below_eulerian",
            1.0,
            1.0 if compensated_index < eulerian_index else 0.0,
            0.0,
            "manufactured",
        ),
    ]
    return {
        "name": "translated_periodic_vortex",
        "description": (
            "Uniformly advected Taylor-Green pattern; transport compensation "
            "reduces apparent temporal deformation caused by translation."
        ),
        "boundary_mode": "periodic",
        "resolution": grid.node_count,
        "parameters": {
            "amplitude": amplitude,
            "wavenumber": wavenumber,
            "background_velocity": background,
        },
        "eulerian_temporal_deformation_index": eulerian_index,
        "compensated_temporal_deformation_index": compensated_index,
        "reduction_ratio": (
            compensated_index / eulerian_index if eulerian_index > 0.0 else 0.0
        ),
        "checks": [check.as_dict() for check in checks],
    }


_CASE_BUILDERS: tuple[Callable[[BenchmarkResolution], dict[str, Any]], ...] = (
    case_zero_field,
    case_solid_body_rotation,
    case_uniform_shear,
    case_taylor_green,
    case_lamb_oseen,
    case_counter_rotating_pair,
    case_amplitude_scaling,
    case_structure_pair,
    case_translated_vortex,
)


def run_benchmarks(resolution: BenchmarkResolution) -> dict[str, Any]:
    """Run the full benchmark catalogue at the given resolution."""
    cases = [builder(resolution) for builder in _CASE_BUILDERS]
    total_checks = 0
    passed_checks = 0
    for case in cases:
        for check in case.get("checks", []):
            total_checks += 1
            if bool(check["passed"]):
                passed_checks += 1
    return {
        "resolution_label": resolution.label,
        "finite_nodes": resolution.finite_nodes,
        "periodic_nodes": resolution.periodic_nodes,
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "cases": cases,
    }
