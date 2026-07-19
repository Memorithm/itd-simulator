from __future__ import annotations

import numpy as np
import pytest

from itd_v29_core.structural_metrics import structural_metrics


def test_zero_field_has_zero_signature() -> None:
    metrics = structural_metrics(np.zeros((5, 6)), 0.5, None, None)
    assert metrics == {
        "heterogeneity": 0.0,
        "localization": 0.0,
        "roughness": 0.0,
        "sign_mixing": 0.0,
        "temporal_deformation": 0.0,
        "structure_score": 0.0,
    }


def test_constant_nonzero_field_has_zero_spatial_signature() -> None:
    omega = np.full((5, 7), 2.0)
    metrics = structural_metrics(omega, 0.25, None, None)
    assert metrics["heterogeneity"] == pytest.approx(0.0, abs=1.0e-15)
    assert metrics["localization"] == pytest.approx(0.0, abs=1.0e-15)
    assert metrics["roughness"] == 0.0
    assert metrics["sign_mixing"] == 0.0


def test_identical_consecutive_fields_have_zero_temporal_deformation() -> None:
    omega = np.arange(30, dtype=np.float64).reshape(5, 6) - 10.0
    metrics = structural_metrics(omega, 0.2, omega.copy(), 0.125)
    assert metrics["temporal_deformation"] == 0.0


@pytest.mark.parametrize("delta_time", [0.0, -1.0, np.nan, np.inf])
def test_invalid_time_intervals_are_rejected(delta_time: float) -> None:
    omega = np.ones((4, 4))
    with pytest.raises(ValueError):
        structural_metrics(omega, 1.0, omega, delta_time)


def test_previous_field_and_interval_must_be_supplied_together() -> None:
    omega = np.ones((4, 4))
    with pytest.raises(ValueError):
        structural_metrics(omega, 1.0, omega, None)
    with pytest.raises(ValueError):
        structural_metrics(omega, 1.0, None, 1.0)


@pytest.mark.parametrize(
    "omega", [np.ones((2, 3)), np.ones((3, 3, 1)), np.empty((0, 0))]
)
def test_invalid_shapes_are_rejected(omega: np.ndarray) -> None:
    with pytest.raises(ValueError):
        structural_metrics(omega, 1.0, None, None)


def test_nonfinite_current_and_previous_fields_are_rejected() -> None:
    omega = np.ones((4, 4))
    bad = omega.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError):
        structural_metrics(bad, 1.0, None, None)
    with pytest.raises(ValueError):
        structural_metrics(omega, 1.0, bad, 1.0)
