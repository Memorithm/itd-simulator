"""Tests for the explicit temporal-scaling research API."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.temporal_scaling import (
    TemporalScaleDefinition,
    TemporalScalePolicy,
    raw_temporal_deformation,
    scale_temporal_deformation,
    temporal_deformation_from_fields,
)
from itd_v29_core.structural_metrics import structural_metrics


def _fields(seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    previous = rng.standard_normal((9, 11))
    current = previous + 0.1 * rng.standard_normal((9, 11))
    return previous, current


def test_raw_rate_matches_v29_structural_metrics_exactly() -> None:
    previous, current = _fields()
    spacing, dt = 0.2, 0.25
    mine = raw_temporal_deformation(previous, current, spacing, dt, "finite")
    reference = structural_metrics(current, spacing, previous, dt, boundary_mode="finite")
    assert mine == reference["temporal_deformation"]


def test_raw_rate_scales_inversely_with_time_unit() -> None:
    previous, current = _fields()
    spacing = 0.2
    conversion = 1000.0
    raw_seconds = raw_temporal_deformation(previous, current, spacing, 0.25, "finite")
    raw_millis = raw_temporal_deformation(previous, current, spacing, 0.25 * conversion, "finite")
    assert raw_millis == pytest.approx(raw_seconds / conversion, rel=1e-13)


@pytest.mark.parametrize(
    "definition_pair",
    [
        (
            TemporalScaleDefinition.from_external(2.0),
            TemporalScaleDefinition.from_external(2.0 * 1000.0),
        ),
        (
            TemporalScaleDefinition.from_observation_duration(0.0, 2.0),
            TemporalScaleDefinition.from_observation_duration(0.0, 2.0 * 1000.0),
        ),
        (
            TemporalScaleDefinition.from_turnover(1.5, 0.75),
            TemporalScaleDefinition.from_turnover(1.5, 0.75 / 1000.0),
        ),
        (
            TemporalScaleDefinition.from_vorticity_timescale(2.0),
            TemporalScaleDefinition.from_vorticity_timescale(2.0 / 1000.0),
        ),
    ],
)
def test_dimensionless_value_is_unit_invariant(
    definition_pair: tuple[TemporalScaleDefinition, TemporalScaleDefinition],
) -> None:
    previous, current = _fields()
    spacing = 0.2
    conversion = 1000.0
    raw_seconds = raw_temporal_deformation(previous, current, spacing, 0.25, "finite")
    raw_millis = raw_temporal_deformation(previous, current, spacing, 0.25 * conversion, "finite")
    def_s, def_ms = definition_pair
    d_s = scale_temporal_deformation(raw_seconds, def_s).dimensionless_deformation
    d_ms = scale_temporal_deformation(raw_millis, def_ms).dimensionless_deformation
    assert d_ms == pytest.approx(d_s, rel=1e-12, abs=1e-15)


def test_identical_fields_give_zero_raw_and_dimensionless() -> None:
    previous, _ = _fields()
    result = temporal_deformation_from_fields(
        previous, previous.copy(), 0.2, 0.25,
        TemporalScaleDefinition.from_external(3.0),
    )
    assert result.raw_rate == 0.0
    assert result.dimensionless_deformation == 0.0
    assert any("zero" in warning for warning in result.warnings)


def test_zero_vorticity_reference_returns_zero_rate() -> None:
    zeros = np.zeros((5, 5))
    assert raw_temporal_deformation(zeros, zeros, 0.5, 0.1, "finite") == 0.0


@pytest.mark.parametrize("bad_tau", [0.0, -1.0, np.nan, np.inf])
def test_invalid_characteristic_time_rejected(bad_tau: float) -> None:
    with pytest.raises(ValueError):
        scale_temporal_deformation(1.0, TemporalScaleDefinition.from_external(bad_tau))


def test_missing_policy_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        TemporalScaleDefinition(policy=TemporalScalePolicy.TURNOVER).resolve()
    with pytest.raises(ValueError):
        TemporalScaleDefinition(policy=TemporalScalePolicy.VORTICITY_TIMESCALE).resolve()


@pytest.mark.parametrize("bad_rate", [-1.0, np.nan, np.inf])
def test_invalid_raw_rate_rejected(bad_rate: float) -> None:
    with pytest.raises(ValueError):
        scale_temporal_deformation(bad_rate, TemporalScaleDefinition.from_external(1.0))


@pytest.mark.parametrize("bad_dt", [0.0, -1.0, np.nan, np.inf])
def test_invalid_delta_time_rejected(bad_dt: float) -> None:
    previous, current = _fields()
    with pytest.raises(ValueError):
        raw_temporal_deformation(previous, current, 0.2, bad_dt, "finite")


def test_nonfinite_fields_rejected() -> None:
    previous, current = _fields()
    bad = current.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError):
        raw_temporal_deformation(previous, bad, 0.2, 0.25, "finite")


def test_mismatched_shapes_rejected() -> None:
    with pytest.raises(ValueError):
        raw_temporal_deformation(np.zeros((5, 5)), np.zeros((5, 6)), 0.2, 0.25, "finite")


def test_self_referential_definition_warns() -> None:
    definition = TemporalScaleDefinition.from_vorticity_timescale(
        2.0, self_referential=True
    )
    result = scale_temporal_deformation(1.0, definition)
    assert any("circular" in warning for warning in result.warnings)


def test_result_is_deterministic_and_serialisable() -> None:
    previous, current = _fields()
    definition = TemporalScaleDefinition.from_observation_duration(0.0, 4.0, time_unit="s")
    first = temporal_deformation_from_fields(previous, current, 0.2, 0.25, definition)
    second = temporal_deformation_from_fields(previous, current, 0.2, 0.25, definition)
    assert first.as_dict() == second.as_dict()
    assert first.as_dict()["policy"] == "observation_duration"
    assert first.as_dict()["time_unit"] == "s"
