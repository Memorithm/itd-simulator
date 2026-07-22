"""Verify the V29.18 implementation reproduces the hand-derived analytical oracles.

The oracle values in ``tests/fixtures/analytical_oracles.json`` are derived by
hand from the field definitions (see ``docs/research/ANALYTICAL_ORACLES.md``) and
are independent of the Python implementation. This test evaluates each oracle's
quantity with the implementation and checks it against the recorded value. It is
kept strictly separate from the implementation-generated Rust regression fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from itd_research import analytical_cases as ac
from itd_research.signature import evaluate_signature
from itd_research.temporal_scaling import raw_temporal_deformation
from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary

_FIXTURE = Path(__file__).parent / "fixtures" / "analytical_oracles.json"

_SIGNATURE_QUANTITIES = frozenset(
    {"intensity", "heterogeneity", "localization", "roughness", "sign_mixing"}
)


def _load() -> dict[str, object]:
    with _FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)


def _grid_from(domain: dict[str, object]) -> ac.Grid:
    if domain["kind"] == "finite":
        return ac.finite_grid(
            int(domain["nodes"]), float(domain["lower"]), float(domain["upper"])
        )
    return ac.periodic_grid(int(domain["nodes"]), float(domain["period"]))


def _evaluate(oracle: dict[str, object]) -> float:
    case = oracle["case"]
    quantity = oracle["quantity"]
    parameters = oracle["parameters"]
    grid = _grid_from(oracle["domain"])  # type: ignore[arg-type]

    if case == "zero_field":
        vx, vy = ac.zero_field(grid.x, grid.y)
        signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
        return float(getattr(signature, quantity))

    if case == "solid_body_rotation":
        vx, vy = ac.solid_body_rotation(grid.x, grid.y, parameters["rotation_rate"])
        signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
        return float(getattr(signature, quantity))

    if case == "uniform_shear":
        vx, vy = ac.uniform_shear(grid.x, grid.y, parameters["shear_rate"])
        signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
        return float(getattr(signature, quantity))

    if case == "taylor_green":
        vx, vy = ac.taylor_green(
            grid.x, grid.y, parameters["amplitude"], parameters["wavenumber"]
        )
        signature = evaluate_signature(vx, vy, grid.spacing, grid.boundary_mode)
        return float(getattr(signature, quantity))

    if case == "identical_fields":
        vx, vy = ac.taylor_green(
            grid.x, grid.y, parameters["amplitude"], parameters["wavenumber"]
        )
        omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "periodic")
        return raw_temporal_deformation(
            omega, omega.copy(), grid.spacing, parameters["delta_time"], "periodic"
        )

    if case == "full_period_translation":
        period = float(oracle["domain"]["period"])  # type: ignore[index]
        vx0, vy0 = ac.taylor_green(
            grid.x, grid.y, parameters["amplitude"], parameters["wavenumber"]
        )
        vx1, vy1 = ac.taylor_green(
            grid.x - period, grid.y, parameters["amplitude"], parameters["wavenumber"]
        )
        omega0 = numerical_vorticity_with_boundary(vx0, vy0, grid.spacing, "periodic")
        omega1 = numerical_vorticity_with_boundary(vx1, vy1, grid.spacing, "periodic")
        return raw_temporal_deformation(
            omega0, omega1, grid.spacing, parameters["delta_time"], "periodic"
        )

    if case == "amplitude_scaling":
        vx_a, vy_a = ac.taylor_green(
            grid.x, grid.y, parameters["amplitude_a"], parameters["wavenumber"]
        )
        vx_b, vy_b = ac.taylor_green(
            grid.x, grid.y, parameters["amplitude_b"], parameters["wavenumber"]
        )
        sig_a = evaluate_signature(vx_a, vy_a, grid.spacing, grid.boundary_mode)
        sig_b = evaluate_signature(vx_b, vy_b, grid.spacing, grid.boundary_mode)
        if quantity == "intensity_ratio":
            return sig_b.intensity / sig_a.intensity
        base = quantity.removesuffix("_delta")
        return abs(getattr(sig_b, base) - getattr(sig_a, base))

    raise AssertionError(f"unhandled oracle case: {case!r}")


def test_fixture_is_pure_hand_derived() -> None:
    data = _load()
    assert data["schema"] == "itd-analytical-oracles/1"
    assert data["model_baseline"] == "ITD V29.18"
    sources = {oracle["source"] for oracle in data["oracles"]}
    # This category file must never mix in implementation-generated snapshots.
    assert sources == {"hand_derived"}


def test_oracle_identifiers_are_unique() -> None:
    identifiers = [oracle["id"] for oracle in _load()["oracles"]]
    assert len(identifiers) == len(set(identifiers))


@pytest.mark.parametrize("oracle", _load()["oracles"], ids=lambda o: o["id"])
def test_implementation_reproduces_oracle(oracle: dict[str, object]) -> None:
    computed = _evaluate(oracle)
    expected = float(oracle["expected_value"])  # type: ignore[arg-type]
    tolerance = float(oracle["tolerance"])  # type: ignore[arg-type]
    assert abs(computed - expected) <= tolerance, (
        f"{oracle['id']}: computed={computed!r} expected={expected!r} "
        f"tol={tolerance!r}"
    )


def test_signature_quantities_are_known() -> None:
    for oracle in _load()["oracles"]:
        quantity = oracle["quantity"]
        case = oracle["case"]
        if case in {"zero_field", "solid_body_rotation", "uniform_shear", "taylor_green"}:
            assert quantity in _SIGNATURE_QUANTITIES


def test_no_nonfinite_expected_values() -> None:
    for oracle in _load()["oracles"]:
        assert np.isfinite(float(oracle["expected_value"]))
        assert float(oracle["tolerance"]) >= 0.0
