from __future__ import annotations

import numpy as np

from itd_v29_core.periodic_transport import (
    periodic_backtrace,
    periodic_bilinear_sample_at_departures,
    periodic_cubic_local_bounded_sample_at_departures,
    periodic_cubic_local_sum_preserving_sample_at_departures,
    periodic_departure_bounds,
    precise_discrete_sum,
)


def periodic_grid() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.arange(8, dtype=np.float64) * 0.25
    y = np.arange(6, dtype=np.float64) * 0.4
    grid_x, grid_y = np.meshgrid(x, y, indexing="xy")
    field = np.sin(np.pi * grid_x) + 0.3 * np.cos(2.0 * np.pi * grid_y / 2.4)
    return x, y, grid_x, grid_y, field


def test_original_nodes_reproduce_node_values() -> None:
    x, y, grid_x, grid_y, field = periodic_grid()
    sampled = periodic_bilinear_sample_at_departures(field, x, y, grid_x, grid_y)
    np.testing.assert_allclose(sampled, field, rtol=0.0, atol=4.0e-16)


def test_full_period_translation_returns_original_field() -> None:
    x, y, _, _, field = periodic_grid()
    period_x = (x[1] - x[0]) * x.size
    period_y = (y[1] - y[0]) * y.size
    for interpolation in (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
        "cubic_local_sum_preserving_periodic",
    ):
        transported = periodic_backtrace(
            field,
            x,
            y,
            np.full_like(field, period_x),
            np.full_like(field, period_y),
            1.0,
            interpolation,
        )
        np.testing.assert_array_equal(transported, field)


def test_local_bounded_interpolation_stays_inside_declared_bounds() -> None:
    x, y, grid_x, grid_y, field = periodic_grid()
    sharp = field.copy()
    sharp[2, 3] += 5.0
    departure_x = grid_x + 0.37 * (x[1] - x[0])
    departure_y = grid_y - 0.41 * (y[1] - y[0])
    lower, upper = periodic_departure_bounds(sharp, x, y, departure_x, departure_y)
    bounded = periodic_cubic_local_bounded_sample_at_departures(
        sharp, x, y, departure_x, departure_y
    )
    tolerance = 1.0e-14
    assert np.all(bounded >= lower - tolerance)
    assert np.all(bounded <= upper + tolerance)


def test_sum_preserving_interpolation_preserves_discrete_sum() -> None:
    x, y, grid_x, grid_y, field = periodic_grid()
    departure_x = grid_x + 0.31 * (x[1] - x[0])
    departure_y = grid_y - 0.27 * (y[1] - y[0])
    result = periodic_cubic_local_sum_preserving_sample_at_departures(
        field, x, y, departure_x, departure_y
    )
    assert abs(precise_discrete_sum(result) - precise_discrete_sum(field)) <= 2.0e-14
