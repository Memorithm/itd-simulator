"""Tests for the benchmark, convergence, and sensitivity runners."""

from __future__ import annotations

import numpy as np

from itd_research.benchmark_runner import QUICK, run_benchmarks
from itd_research.convergence import (
    CONVERGENCE_COLUMNS,
    observed_order,
    run_convergence,
)
from itd_research.sensitivity import run_sensitivity


def test_benchmark_catalogue_all_checks_pass() -> None:
    results = run_benchmarks(QUICK)
    assert results["total_checks"] > 0
    assert results["passed_checks"] == results["total_checks"]
    names = {case["name"] for case in results["cases"]}
    assert {
        "zero_field",
        "solid_body_rotation",
        "uniform_shear",
        "taylor_green",
        "lamb_oseen",
        "counter_rotating_pair",
        "amplitude_scaling",
        "structure_changed_pair",
        "translated_periodic_vortex",
    } <= names


def test_benchmark_is_deterministic() -> None:
    first = run_benchmarks(QUICK)
    second = run_benchmarks(QUICK)
    assert first == second


def test_convergence_reports_second_order_for_taylor_green_enstrophy() -> None:
    result = run_convergence((17, 33, 65), (16, 32, 64, 128))
    assert list(result["columns"]) == list(CONVERGENCE_COLUMNS)
    order_index = CONVERGENCE_COLUMNS.index("observed_order")
    study_index = CONVERGENCE_COLUMNS.index("study")
    orders = [
        row[order_index]
        for row in result["rows"]
        if row[study_index] == "taylor_green_enstrophy" and row[order_index] != "n/a"
    ]
    assert orders, "expected at least one estimable order"
    assert orders[-1] == abs(orders[-1])  # positive
    assert 1.7 < float(orders[-1]) < 2.3


def test_convergence_does_not_report_order_for_exact_or_zero_reference() -> None:
    # Errors below the roundoff floor must not yield an order.
    assert observed_order(1e-18, 1e-19, 1.0, 0.5, reference_magnitude=1.0) is None
    # Non-decreasing error is outside the asymptotic regime.
    assert observed_order(1e-3, 2e-3, 1.0, 0.5, reference_magnitude=1.0) is None


def test_sensitivity_reports_unit_invariance_and_ranking_changes() -> None:
    result = run_sensitivity((16, 32, 64))
    summaries = result["summaries"]
    time_unit = summaries["time_unit_conversion"]
    assert time_unit["max_dimensionless_residual"] < 1e-9
    assert time_unit["raw_rate_scaling_residual"] < 1e-9
    structural = summaries["structural_length"]
    assert structural["raw_roughness_slope_spread"] < 1e-9
    weights = summaries["scalar_weights"]
    assert weights["ranking_changes_with_weights"] is True


def test_sensitivity_is_deterministic() -> None:
    first = run_sensitivity((16, 32))
    second = run_sensitivity((16, 32))
    assert first == second


def test_sensitivity_noise_summary_records_seed() -> None:
    result = run_sensitivity((16,))
    noise = result["summaries"]["noise"]
    assert noise["seed"] == 12345
    assert set(noise["max_component_delta"]) == {
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
    }
    assert all(np.isfinite(value) for value in noise["max_component_delta"].values())
