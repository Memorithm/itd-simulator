"""Tests for the typed, immutable external field-data model."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from itd_research.io.field_data import (
    FieldData2D,
    FieldData3D,
    FieldMetadata,
    is_uniform,
    metadata_from_mapping,
)

META = FieldMetadata(source="test", length_unit="m", velocity_unit="m/s")


def _field2d() -> FieldData2D:
    x = np.linspace(0.0, 1.0, 5)
    y = np.linspace(0.0, 2.0, 4)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    return FieldData2D(x=x, y=y, u=xx, v=-yy, metadata=META, time=0.5)


def test_valid_2d_field_and_shape() -> None:
    field = _field2d()
    assert field.shape == (4, 5)
    assert field.time == 0.5
    assert field.valid_fraction == 1.0


def test_field_is_immutable() -> None:
    field = _field2d()
    with pytest.raises((ValueError, RuntimeError)):
        field.u[0, 0] = 99.0  # arrays are read-only
    with pytest.raises(dataclasses.FrozenInstanceError):
        field.time = 1.0  # frozen dataclass


def test_valid_3d_field() -> None:
    x = np.linspace(-1.0, 1.0, 3)
    field = FieldData3D(
        x=x, y=x, z=x,
        u=np.zeros((3, 3, 3)), v=np.zeros((3, 3, 3)), w=np.ones((3, 3, 3)),
        metadata=META,
    )
    assert field.shape == (3, 3, 3)


@pytest.mark.parametrize(
    "coords",
    [np.array([0.0, 0.0, 1.0]), np.array([2.0, 1.0, 0.0]), np.array([0.0, 1.0])],
)
def test_bad_coordinates_rejected(coords: np.ndarray) -> None:
    with pytest.raises(ValueError):
        FieldData2D(
            x=coords, y=np.linspace(0, 1, 4),
            u=np.zeros((4, coords.size)), v=np.zeros((4, coords.size)), metadata=META,
        )


def test_shape_mismatch_rejected() -> None:
    with pytest.raises(ValueError):
        FieldData2D(
            x=np.linspace(0, 1, 5), y=np.linspace(0, 1, 4),
            u=np.zeros((4, 4)), v=np.zeros((4, 5)), metadata=META,
        )


def test_non_finite_without_mask_rejected() -> None:
    x = np.linspace(0, 1, 3)
    u = np.zeros((3, 3))
    u[0, 0] = np.nan
    with pytest.raises(ValueError):
        FieldData2D(x=x, y=x, u=u, v=np.zeros((3, 3)), metadata=META)


def test_non_finite_allowed_only_at_masked_nodes() -> None:
    x = np.linspace(0, 1, 3)
    u = np.zeros((3, 3))
    u[0, 0] = np.nan
    mask = np.ones((3, 3), dtype=bool)
    mask[0, 0] = False  # invalid node may hold NaN
    field = FieldData2D(x=x, y=x, u=u, v=np.zeros((3, 3)), metadata=META, mask=mask)
    assert field.valid_fraction == pytest.approx(8.0 / 9.0)
    # A NaN at a *valid* node must be rejected.
    mask[0, 0] = True
    with pytest.raises(ValueError):
        FieldData2D(x=x, y=x, u=u, v=np.zeros((3, 3)), metadata=META, mask=mask)


def test_metadata_requires_units() -> None:
    with pytest.raises(ValueError):
        metadata_from_mapping({"source": "s"})
    meta = metadata_from_mapping(
        {"source": "s", "length_unit": "m", "velocity_unit": "m/s", "reynolds": "100"}
    )
    assert meta.as_dict()["extra"] == {"reynolds": "100"}


def test_is_uniform() -> None:
    assert is_uniform(np.linspace(0.0, 1.0, 11))
    assert not is_uniform(np.array([0.0, 0.1, 0.5, 1.0]))
