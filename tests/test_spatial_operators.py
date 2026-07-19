from __future__ import annotations

import numpy as np
import pytest

from itd_v29_core.spatial_operators import (
    bounded,
    numerical_vorticity_with_boundary,
    scalar_gradient_with_boundary,
)


@pytest.mark.parametrize("boundary_mode", ["finite", "periodic"])
def test_constant_scalar_field_has_zero_gradient(boundary_mode: str) -> None:
    field = np.full((7, 9), 3.25)
    gradient_y, gradient_x = scalar_gradient_with_boundary(
        field, (0.2, 0.4), boundary_mode
    )
    np.testing.assert_array_equal(gradient_x, 0.0)
    np.testing.assert_array_equal(gradient_y, 0.0)


@pytest.mark.parametrize("boundary_mode", ["finite", "periodic"])
def test_constant_velocity_has_zero_vorticity(boundary_mode: str) -> None:
    vx = np.full((6, 8), -2.0)
    vy = np.full((6, 8), 5.0)
    omega = numerical_vorticity_with_boundary(vx, vy, 0.25, boundary_mode)
    np.testing.assert_array_equal(omega, 0.0)


@pytest.mark.parametrize(
    ("field", "spacing"),
    [
        (np.zeros((2, 4)), 1.0),
        (np.zeros((3, 4)), 0.0),
        (np.zeros((3, 4)), -1.0),
        (np.array([[0.0, 1.0, 2.0]] * 3), [0.0, 1.0, 0.5, 2.0]),
    ],
)
def test_gradient_rejects_invalid_grid(field: np.ndarray, spacing: object) -> None:
    with pytest.raises(ValueError):
        scalar_gradient_with_boundary(field, spacing)


def test_vorticity_rejects_shapes_and_nonfinite_values() -> None:
    with pytest.raises(ValueError):
        numerical_vorticity_with_boundary(np.zeros((3, 3)), np.zeros((3, 4)), 1.0)
    field = np.zeros((3, 3))
    field[1, 1] = np.inf
    with pytest.raises(ValueError):
        numerical_vorticity_with_boundary(field, np.zeros_like(field), 1.0)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf, "not-a-number"])
def test_bounded_rejects_nonfinite_or_non_numeric_input(value: object) -> None:
    with pytest.raises(ValueError):
        bounded(value)
