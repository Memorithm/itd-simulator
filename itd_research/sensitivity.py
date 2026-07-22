"""Deterministic sensitivity and invariance study for the post-V29 research phase.

Each study varies one factor and records how the raw five-component signature,
the intensity, and the dimensionless temporal-deformation candidates respond.
Results are long-format rows (study, case, parameter, value, metric, value) plus
a structured summary of the key findings (linearity, invariance, ranking
changes). All randomness is seeded; all arithmetic is float64.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research import analytical_cases as ac
from itd_research.signature import evaluate_signature
from itd_research.temporal_scaling import (
    TemporalScaleDefinition,
    raw_temporal_deformation,
    scale_temporal_deformation,
)
from itd_v29_core.spatial_operators import (
    bounded,
    numerical_vorticity_with_boundary,
    spatial_mean,
)
from itd_v29_core.structural_metrics import structural_metrics

FloatArray: TypeAlias = NDArray[np.float64]

SENSITIVITY_COLUMNS = ("study", "case", "parameter", "parameter_value", "metric", "value")


@dataclass(frozen=True)
class _Row:
    study: str
    case: str
    parameter: str
    parameter_value: float
    metric: str
    value: float

    def as_list(self) -> list[object]:
        return [
            self.study,
            self.case,
            self.parameter,
            self.parameter_value,
            self.metric,
            self.value,
        ]


def _signature_rows(
    study: str,
    case: str,
    parameter: str,
    parameter_value: float,
    vx: FloatArray,
    vy: FloatArray,
    spacing: object,
    boundary_mode: str,
) -> list[_Row]:
    signature = evaluate_signature(vx, vy, spacing, boundary_mode)
    metrics = {
        "intensity": signature.intensity,
        "heterogeneity": signature.heterogeneity,
        "localization": signature.localization,
        "roughness": signature.roughness,
        "sign_mixing": signature.sign_mixing,
    }
    return [
        _Row(study, case, parameter, parameter_value, name, value)
        for name, value in metrics.items()
    ]


def _spatial_resolution(sizes: Sequence[int]) -> list[_Row]:
    rows: list[_Row] = []
    period = 2.0 * np.pi
    for size in sizes:
        grid = ac.periodic_grid(size, period)
        vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
        rows.extend(
            _signature_rows(
                "spatial_resolution", "taylor_green", "nodes", float(size),
                vx, vy, grid.spacing, "periodic",
            )
        )
    for size in (33, 65, 129):
        grid = ac.finite_grid(size, -3.0, 3.0)
        vx, vy = ac.lamb_oseen(grid.x, grid.y, 2.0, 0.5)
        rows.extend(
            _signature_rows(
                "spatial_resolution", "lamb_oseen", "nodes", float(size),
                vx, vy, grid.spacing, "finite",
            )
        )
    return rows


def _temporal_resolution() -> tuple[list[_Row], dict[str, object]]:
    """Raw temporal deformation and D* versus the sampling timestep."""
    amplitude, wavenumber, background = 1.0, 1.0, 0.4
    period = 2.0 * np.pi / wavenumber
    grid = ac.periodic_grid(64, period)

    def vorticity_at(t: float) -> FloatArray:
        phase = wavenumber * (grid.x - background * t)
        vx = background + amplitude * np.sin(phase) * np.cos(wavenumber * grid.y)
        vy = -amplitude * np.cos(phase) * np.sin(wavenumber * grid.y)
        return numerical_vorticity_with_boundary(vx, vy, grid.spacing, "periodic")

    base_time = 1.0
    omega0 = vorticity_at(base_time)
    definition = TemporalScaleDefinition.from_observation_duration(0.0, 2.0, time_unit="s")
    rows: list[_Row] = []
    raw_values: list[float] = []
    for dt in (0.4, 0.2, 0.1, 0.05, 0.025):
        omega1 = vorticity_at(base_time + dt)
        raw = raw_temporal_deformation(omega0, omega1, grid.spacing, dt, "periodic")
        scaled = scale_temporal_deformation(raw, definition)
        raw_values.append(raw)
        rows.append(_Row("temporal_resolution", "translated_vortex", "dt", dt, "raw_rate", raw))
        rows.append(
            _Row(
                "temporal_resolution", "translated_vortex", "dt", dt,
                "dimensionless_observation_duration", scaled.dimensionless_deformation,
            )
        )
    summary: dict[str, object] = {
        "raw_rate_limit_estimate": raw_values[-1],
        "raw_rate_change_ratio_coarse_to_fine": (
            raw_values[0] / raw_values[-1] if raw_values[-1] != 0.0 else None
        ),
        "note": (
            "The raw rate is a finite-time-difference approximation of the "
            "instantaneous rate and converges as dt decreases."
        ),
    }
    return rows, summary


def _time_unit_conversion() -> tuple[list[_Row], dict[str, object]]:
    """Seconds vs milliseconds; raw rate scales as 1/c, D* is invariant."""
    conversion = 1000.0
    period = 2.0 * np.pi
    grid = ac.periodic_grid(64, period)
    vx0, vy0 = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    omega0 = numerical_vorticity_with_boundary(vx0, vy0, grid.spacing, "periodic")
    vx1, vy1 = ac.taylor_green(grid.x, grid.y, 1.15, 1.0)
    omega1 = numerical_vorticity_with_boundary(vx1, vy1, grid.spacing, "periodic")

    dt_seconds = 0.25
    dt_millis = dt_seconds * conversion
    raw_seconds = raw_temporal_deformation(omega0, omega1, grid.spacing, dt_seconds, "periodic")
    raw_millis = raw_temporal_deformation(omega0, omega1, grid.spacing, dt_millis, "periodic")

    policies = {
        "external": (
            TemporalScaleDefinition.from_external(2.0, time_unit="s"),
            TemporalScaleDefinition.from_external(2.0 * conversion, time_unit="ms"),
        ),
        "observation_duration": (
            TemporalScaleDefinition.from_observation_duration(0.0, 2.0, time_unit="s"),
            TemporalScaleDefinition.from_observation_duration(0.0, 2.0 * conversion, time_unit="ms"),
        ),
        "turnover": (
            TemporalScaleDefinition.from_turnover(1.5, 0.75, time_unit="s"),
            TemporalScaleDefinition.from_turnover(1.5, 0.75 / conversion, time_unit="ms"),
        ),
        "vorticity_timescale": (
            TemporalScaleDefinition.from_vorticity_timescale(2.0, time_unit="s"),
            TemporalScaleDefinition.from_vorticity_timescale(2.0 / conversion, time_unit="ms"),
        ),
    }

    rows: list[_Row] = []
    residuals: dict[str, float] = {}
    for name, (def_s, def_ms) in policies.items():
        d_seconds = scale_temporal_deformation(raw_seconds, def_s).dimensionless_deformation
        d_millis = scale_temporal_deformation(raw_millis, def_ms).dimensionless_deformation
        residuals[name] = abs(d_seconds - d_millis)
        rows.append(_Row("time_unit", name, "unit_seconds", 1.0, "dimensionless", d_seconds))
        rows.append(_Row("time_unit", name, "unit_milliseconds", conversion, "dimensionless", d_millis))
    rows.append(_Row("time_unit", "raw", "unit_seconds", 1.0, "raw_rate", raw_seconds))
    rows.append(_Row("time_unit", "raw", "unit_milliseconds", conversion, "raw_rate", raw_millis))

    summary: dict[str, object] = {
        "raw_rate_scaling_residual": abs(raw_millis - raw_seconds / conversion),
        "max_dimensionless_residual": max(residuals.values()),
        "per_policy_residual": residuals,
        "note": (
            "Raw rate transforms as 1/c between second and millisecond units; "
            "every dimensionless candidate is invariant under consistent "
            "conversion."
        ),
    }
    return rows, summary


def _structural_length() -> tuple[list[_Row], dict[str, object]]:
    """Raw roughness is linear in the structural length; the bounded map is not."""
    grid = ac.finite_grid(65, -3.0, 3.0)
    vx, vy = ac.lamb_oseen(grid.x, grid.y, 2.0, 0.5)
    omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "finite")
    rows: list[_Row] = []
    slopes: list[float] = []
    for ell in (0.25, 0.5, 1.0, 2.0):
        metrics = structural_metrics(
            omega, grid.spacing, None, None, structural_length=ell, boundary_mode="finite"
        )
        raw = float(metrics["roughness"])
        rows.append(_Row("structural_length", "lamb_oseen", "ell_s", ell, "raw_roughness", raw))
        rows.append(_Row("structural_length", "lamb_oseen", "ell_s", ell, "bounded_roughness", bounded(raw)))
        slopes.append(raw / ell)
    summary: dict[str, object] = {
        "raw_roughness_slope_spread": float(max(slopes) - min(slopes)),
        "note": (
            "raw_roughness / ell_s is constant (linear law); bounded roughness "
            "x/(1+x) saturates and is nonlinear in ell_s."
        ),
    }
    return rows, summary


def _curvature_length() -> tuple[list[_Row], dict[str, object]]:
    """Intensity depends exponentially on the curvature length via exp(lc^2 R)."""
    grid = ac.finite_grid(65, -2.0, 2.0)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.5)
    curvature = np.exp(-(grid.x**2 + grid.y**2)).astype(np.float64)
    rows: list[_Row] = []
    intensities: list[float] = []
    for lc in (0.0, 0.5, 1.0, 1.5, 2.0):
        signature = evaluate_signature(
            vx, vy, grid.spacing, "finite",
            curvature=curvature, characteristic_length=lc,
        )
        rows.append(_Row("curvature_length", "taylor_green", "ell_c", lc, "intensity", signature.intensity))
        intensities.append(signature.intensity)
    summary: dict[str, object] = {
        "intensity_amplification_ratio": (
            intensities[-1] / intensities[0] if intensities[0] > 0.0 else None
        ),
        "note": (
            "The curvature weight exp(lc^2 R) grows exponentially with lc^2; "
            "large lc can amplify intensity and is rejected if it overflows the "
            "finite range."
        ),
    }
    return rows, summary


def _boundary_mode() -> tuple[list[_Row], dict[str, object]]:
    """Convention sensitivity: the same periodic sample under both operators."""
    period = 2.0 * np.pi
    grid = ac.periodic_grid(64, period)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    rows: list[_Row] = []
    differences: dict[str, float] = {}
    periodic_sig = evaluate_signature(vx, vy, grid.spacing, "periodic")
    finite_sig = evaluate_signature(vx, vy, grid.spacing, "finite")
    for name in ("intensity", "heterogeneity", "localization", "roughness", "sign_mixing"):
        periodic_value = getattr(periodic_sig, name)
        finite_value = getattr(finite_sig, name)
        rows.append(_Row("boundary_mode", "taylor_green", "mode_periodic", 0.0, name, periodic_value))
        rows.append(_Row("boundary_mode", "taylor_green", "mode_finite", 1.0, name, finite_value))
        differences[name] = abs(periodic_value - finite_value)
    summary: dict[str, object] = {
        "max_absolute_difference": max(differences.values()),
        "note": (
            "The periodic and finite operators encode different domain "
            "conventions; the difference quantifies convention sensitivity, not "
            "a physical change in the flow."
        ),
    }
    return rows, summary


def _noise(seed: int = 12345) -> tuple[list[_Row], dict[str, object]]:
    """Seeded additive vorticity noise; robustness of derived components."""
    grid = ac.finite_grid(65, -3.0, 3.0)
    vx, vy = ac.lamb_oseen(grid.x, grid.y, 2.0, 0.5)
    omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "finite")
    rms = float(np.sqrt(max(spatial_mean(omega**2, grid.spacing, "finite"), 0.0)))
    rng = np.random.default_rng(seed)
    base = rng.standard_normal(omega.shape)
    reference = structural_metrics(omega, grid.spacing, None, None, boundary_mode="finite")
    rows: list[_Row] = []
    max_delta: dict[str, float] = {}
    for amplitude in (0.0, 0.01, 0.05, 0.1):
        perturbed = omega + amplitude * rms * base
        metrics = structural_metrics(perturbed, grid.spacing, None, None, boundary_mode="finite")
        for name in ("heterogeneity", "localization", "roughness", "sign_mixing"):
            value = float(metrics[name])
            rows.append(_Row("noise", "lamb_oseen", "relative_amplitude", amplitude, name, value))
            delta = abs(value - float(reference[name]))
            max_delta[name] = max(max_delta.get(name, 0.0), delta)
    summary: dict[str, object] = {
        "seed": seed,
        "max_component_delta": max_delta,
        "note": (
            "Deterministic seeded synthetic noise is a robustness probe, not "
            "empirical validation. Roughness is the most noise-sensitive "
            "component because it differentiates the field."
        ),
    }
    return rows, summary


def _scalar_weights() -> tuple[list[_Row], dict[str, object]]:
    """Different weight vectors can reorder cases by their scalar score."""
    grid_p = ac.periodic_grid(64, 2.0 * np.pi)
    grid_f = ac.finite_grid(65, -3.0, 3.0)
    fields = {
        "taylor_green": (ac.taylor_green(grid_p.x, grid_p.y, 1.0, 1.0), grid_p, "periodic"),
        "lamb_oseen": (ac.lamb_oseen(grid_f.x, grid_f.y, 2.0, 0.5), grid_f, "finite"),
        "counter_rotating_pair": (
            ac.counter_rotating_pair(grid_f.x, grid_f.y, 2.0, 0.5, 2.0), grid_f, "finite",
        ),
    }
    weight_vectors = {
        "equal": (1.0, 1.0, 1.0, 1.0, 1.0),
        "localization_heavy": (1.0, 5.0, 1.0, 1.0, 1.0),
        "sign_mixing_heavy": (1.0, 1.0, 1.0, 5.0, 1.0),
    }
    rows: list[_Row] = []
    rankings: dict[str, list[str]] = {}
    for weight_name, weights in weight_vectors.items():
        scores: dict[str, float] = {}
        for case_name, ((vx, vy), grid, mode) in fields.items():
            omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, mode)
            metrics = structural_metrics(
                omega, grid.spacing, None, None,
                structural_weights=weights, boundary_mode=mode,
            )
            score = float(metrics["structure_score"])
            scores[case_name] = score
            rows.append(_Row("scalar_weights", case_name, weight_name, 0.0, "structure_score", score))
        rankings[weight_name] = sorted(scores, key=lambda name: scores[name], reverse=True)
    summary: dict[str, object] = {
        "rankings": rankings,
        "ranking_changes_with_weights": len({tuple(order) for order in rankings.values()}) > 1,
        "note": (
            "Because the scalar score is a weighted bounded aggregation, the "
            "ranking of cases can change with the weights; the raw five-component "
            "vector must remain the primary reported structural result."
        ),
    }
    return rows, summary


def run_sensitivity(spatial_sizes: Sequence[int] = (16, 32, 64, 128)) -> dict[str, Any]:
    """Run every sensitivity study and return rows plus structured summaries."""
    rows: list[_Row] = []
    summaries: dict[str, object] = {}

    rows.extend(_spatial_resolution(spatial_sizes))

    for key, (study_rows, summary) in {
        "temporal_resolution": _temporal_resolution(),
        "time_unit_conversion": _time_unit_conversion(),
        "structural_length": _structural_length(),
        "curvature_length": _curvature_length(),
        "boundary_mode": _boundary_mode(),
        "noise": _noise(),
        "scalar_weights": _scalar_weights(),
    }.items():
        rows.extend(study_rows)
        summaries[key] = summary

    return {
        "columns": list(SENSITIVITY_COLUMNS),
        "rows": [row.as_list() for row in rows],
        "summaries": summaries,
    }
