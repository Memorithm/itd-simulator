from __future__ import annotations

import numpy as np
import pytest

from itd_v29_core.material_deformation import interpolate_interval_series_to_nodes
from itd_v29_core.material_interval import material_vorticity_interval


def test_identical_fields_and_zero_velocity_have_zero_deformation() -> None:
    omega = np.arange(30, dtype=np.float64).reshape(5, 6)
    zeros = np.zeros_like(omega)
    result = material_vorticity_interval(omega, omega, zeros, zeros, 0.25, 0.5)
    np.testing.assert_array_equal(result["temporal_tendency"], 0.0)
    np.testing.assert_array_equal(result["advective_tendency"], 0.0)
    np.testing.assert_array_equal(result["material_tendency"], 0.0)
    assert result["eulerian_rate"] == 0.0
    assert result["material_rate"] == 0.0


def test_interval_series_interpolation_has_declared_endpoint_behavior() -> None:
    times = np.array([0.0, 1.0, 3.0, 6.0])
    intervals = np.array([2.0, 4.0, 8.0])
    nodes = interpolate_interval_series_to_nodes(times, intervals)
    # Interval midpoints are 0.5, 2.0 and 4.5; linear interpolation gives
    # 2 + (1/3)(4 - 2) and 4 + (2/5)(8 - 4) at the interior nodes.
    expected = np.array([2.0, 8.0 / 3.0, 5.6, 8.0])
    np.testing.assert_allclose(nodes, expected, rtol=0.0, atol=1.0e-15)


@pytest.mark.parametrize("delta_time", [0.0, -0.1, np.nan, np.inf])
def test_material_interval_rejects_invalid_duration(delta_time: float) -> None:
    field = np.ones((4, 4))
    with pytest.raises(ValueError):
        material_vorticity_interval(field, field, field, field, 1.0, delta_time)


def test_material_interval_rejects_shapes_and_nonfinite_inputs() -> None:
    field = np.ones((4, 4))
    with pytest.raises(ValueError):
        material_vorticity_interval(field, field[:, :-1], field, field, 1.0, 1.0)
    bad = field.copy()
    bad[1, 1] = np.nan
    with pytest.raises(ValueError):
        material_vorticity_interval(field, bad, field, field, 1.0, 1.0)
