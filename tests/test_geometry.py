from __future__ import annotations

import numpy as np
import pytest

from itd_v29_core.geometric_transforms import (
    BilinearTransformPlan,
    rotation_matrix,
    transform_coordinates,
    validate_uniform_axis_coordinates,
)
from itd_v29_core.spatial_geometry import RectilinearGeometry, validate_mesh_geometry


def test_identity_transform_preserves_coordinates() -> None:
    x, y = np.meshgrid(np.arange(4.0), np.arange(3.0), indexing="xy")
    transformed_x, transformed_y = transform_coordinates(x, y, np.eye(2))
    np.testing.assert_array_equal(transformed_x, x)
    np.testing.assert_array_equal(transformed_y, y)


def test_rotation_preserves_euclidean_norm() -> None:
    x = np.array([-2.0, -0.5, 1.25, 3.0])
    y = np.array([0.75, 4.0, -1.5, 2.0])
    transformed_x, transformed_y = transform_coordinates(x, y, rotation_matrix(0.73))
    np.testing.assert_allclose(
        transformed_x**2 + transformed_y**2,
        x**2 + y**2,
        rtol=2.0e-15,
        atol=2.0e-15,
    )


def test_identity_interpolation_reproduces_original_nodes() -> None:
    x = np.linspace(-1.0, 1.0, 6)
    y = np.linspace(-2.0, 2.0, 5)
    field = np.arange(30, dtype=np.float64).reshape(5, 6)
    plan = BilinearTransformPlan(x, y, np.eye(2))
    assert plan.uses_exact_node_map
    np.testing.assert_array_equal(plan.interpolate(field), field)


@pytest.mark.parametrize(
    "coordinates", [[0.0], [0.0, 1.0, 0.5], [0.0, np.nan, 2.0]]
)
def test_uniform_axis_rejects_short_nonmonotonic_or_nonfinite_data(
    coordinates: list[float],
) -> None:
    with pytest.raises(ValueError):
        validate_uniform_axis_coordinates(coordinates, "x")


def test_rectilinear_mesh_must_match_declared_coordinates() -> None:
    x_axis = np.array([0.0, 0.4, 1.1, 2.0])
    y_axis = np.array([-1.0, -0.2, 0.5])
    x, y = np.meshgrid(x_axis, y_axis, indexing="xy")
    geometry = RectilinearGeometry(x_axis, y_axis)
    validate_mesh_geometry(x, y, geometry)
    bad_x = x.copy()
    bad_x[1, 1] += 0.1
    with pytest.raises(ValueError):
        validate_mesh_geometry(bad_x, y, geometry)


def test_transform_rejects_shape_mismatch_and_nonfinite_coordinates() -> None:
    with pytest.raises(ValueError):
        transform_coordinates(np.zeros((2, 2)), np.zeros((3, 2)), np.eye(2))
    x = np.zeros((2, 2))
    x[0, 0] = np.inf
    with pytest.raises(ValueError):
        transform_coordinates(x, np.zeros_like(x), np.eye(2))
