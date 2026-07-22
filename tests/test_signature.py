"""Tests for the single-snapshot ITD signature helper."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research import analytical_cases as ac
from itd_research.signature import evaluate_signature


def test_zero_field_signature_is_zero() -> None:
    grid = ac.finite_grid(17, -1.0, 1.0)
    vx, vy = ac.zero_field(grid.x, grid.y)
    signature = evaluate_signature(vx, vy, grid.spacing, "finite")
    assert signature.intensity == 0.0
    assert signature.component_vector() == (0.0, 0.0, 0.0, 0.0, 0.0)
    assert signature.structure_score == 0.0


def test_amplitude_invariance_of_structural_vector() -> None:
    grid = ac.periodic_grid(64, np.pi)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 2.0)
    low = evaluate_signature(vx, vy, grid.spacing, "periodic")
    high = evaluate_signature(37.0 * vx, 37.0 * vy, grid.spacing, "periodic")
    assert high.heterogeneity == pytest.approx(low.heterogeneity, rel=1e-12)
    assert high.localization == pytest.approx(low.localization, rel=1e-12)
    assert high.roughness == pytest.approx(low.roughness, rel=1e-12)
    assert high.sign_mixing == pytest.approx(low.sign_mixing, rel=1e-12)
    assert high.intensity == pytest.approx(37.0**2 * low.intensity, rel=1e-12)


def test_curvature_weight_scales_intensity() -> None:
    grid = ac.finite_grid(33, -2.0, 2.0)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.5)
    curvature = np.ones(grid.shape)
    without = evaluate_signature(vx, vy, grid.spacing, "finite")
    with_weight = evaluate_signature(
        vx, vy, grid.spacing, "finite", curvature=curvature, characteristic_length=1.0
    )
    assert with_weight.intensity == pytest.approx(np.e * without.intensity, rel=1e-9)


def test_nonfinite_curvature_rejected() -> None:
    grid = ac.finite_grid(9, -1.0, 1.0)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    curvature = np.zeros(grid.shape)
    curvature[0, 0] = np.nan
    with pytest.raises(ValueError):
        evaluate_signature(vx, vy, grid.spacing, "finite", curvature=curvature)


def test_negative_characteristic_length_rejected() -> None:
    grid = ac.finite_grid(9, -1.0, 1.0)
    vx, vy = ac.taylor_green(grid.x, grid.y, 1.0, 1.0)
    with pytest.raises(ValueError):
        evaluate_signature(vx, vy, grid.spacing, "finite", characteristic_length=-1.0)


def test_signature_is_deterministic() -> None:
    grid = ac.finite_grid(33, -2.0, 2.0)
    vx, vy = ac.lamb_oseen(grid.x, grid.y, 2.0, 0.5)
    first = evaluate_signature(vx, vy, grid.spacing, "finite")
    second = evaluate_signature(vx, vy, grid.spacing, "finite")
    assert first.as_dict() == second.as_dict()
