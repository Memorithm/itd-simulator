"""Typed, immutable field-data model for external velocity fields (research).

This model represents 2D and 3D velocity fields ingested from external CFD or
PIV sources. It is deliberately decoupled from any file format (OpenFOAM, VTK,
PIV, HDF5): adapters produce these objects. It is part of the isolated
``itd_research`` namespace and never modifies the certified V29.18 core.

Conventions match :mod:`itd_research.diagnostics_3d.operators`: 2D arrays are
``(ny, nx)`` (axis 0 = y, axis 1 = x); 3D arrays are ``(nz, ny, nx)`` (axis 0 =
z, axis 1 = y, axis 2 = x). Coordinates are explicit strictly increasing 1D
arrays and are never inferred.

Mask policy
-----------
A boolean ``mask`` (``True`` = valid) marks the only locations where NaN/inf are
permitted (invalid PIV vectors). Where no mask is supplied, every value must be
finite. Repaired/interpolated values are never hidden: adapters report how many
vectors were original, invalid, interpolated, or masked.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]


@dataclass(frozen=True)
class FieldMetadata:
    """Immutable units and convention record attached to a field.

    ``extra`` holds additional provenance as a tuple of ``(key, value)`` string
    pairs so the metadata stays hashable and immutable.
    """

    source: str
    length_unit: str
    velocity_unit: str
    time_unit: str = "unspecified"
    coordinate_convention: str = "zyx"
    boundary_mode: str = "unknown"
    extra: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict[str, object]:
        record: dict[str, object] = {
            "source": self.source,
            "length_unit": self.length_unit,
            "velocity_unit": self.velocity_unit,
            "time_unit": self.time_unit,
            "coordinate_convention": self.coordinate_convention,
            "boundary_mode": self.boundary_mode,
            "extra": {key: value for key, value in self.extra},
        }
        return record


def _validate_axis(coordinates: object, name: str) -> FloatArray:
    if isinstance(coordinates, (str, bytes)):
        raise ValueError(f"{name} coordinates must be a numeric sequence.")
    array = np.array(np.asarray(coordinates, dtype=np.float64), copy=True)
    if array.ndim != 1:
        raise ValueError(f"{name} coordinates must be one-dimensional.")
    if array.size < 3:
        raise ValueError(f"{name} axis must contain at least three coordinates.")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} coordinates contain a non-finite value.")
    differences = np.diff(array)
    if not np.all(differences > 0.0):
        raise ValueError(f"{name} coordinates must be strictly increasing.")
    array.setflags(write=False)
    return array


def _validate_component(
    values: object,
    name: str,
    shape: tuple[int, ...],
    mask: BoolArray | None,
    require_units: bool,
) -> FloatArray:
    del require_units
    array = np.array(np.asarray(values, dtype=np.float64), copy=True)
    if array.shape != shape:
        raise ValueError(f"{name} has shape {array.shape}, expected {shape}.")
    if mask is None:
        if not np.all(np.isfinite(array)):
            raise ValueError(
                f"{name} contains a non-finite value and no mask was provided."
            )
    else:
        if not np.all(np.isfinite(array[mask])):
            raise ValueError(f"{name} has a non-finite value at a valid (unmasked) node.")
    array.setflags(write=False)
    return array


def _validate_mask(mask: object, shape: tuple[int, ...]) -> BoolArray:
    array = np.array(np.asarray(mask, dtype=bool), copy=True)
    if array.shape != shape:
        raise ValueError(f"mask has shape {array.shape}, expected {shape}.")
    if not bool(np.any(array)):
        raise ValueError("mask marks every node invalid; no usable data.")
    array.setflags(write=False)
    return array


def _validate_time(time: float | None) -> float | None:
    if time is None:
        return None
    value = float(time)
    if not np.isfinite(value):
        raise ValueError("time must be finite when supplied.")
    return value


@dataclass(frozen=True)
class FieldData2D:
    """An immutable, validated 2D velocity field on a structured grid."""

    x: FloatArray
    y: FloatArray
    u: FloatArray
    v: FloatArray
    metadata: FieldMetadata
    time: float | None = None
    pressure: FloatArray | None = None
    mask: BoolArray | None = None
    scalars: tuple[tuple[str, FloatArray], ...] = field(default=())

    def __post_init__(self) -> None:
        x = _validate_axis(self.x, "x")
        y = _validate_axis(self.y, "y")
        shape = (y.size, x.size)
        mask = None if self.mask is None else _validate_mask(self.mask, shape)
        u = _validate_component(self.u, "u", shape, mask, True)
        v = _validate_component(self.v, "v", shape, mask, True)
        pressure = (
            None
            if self.pressure is None
            else _validate_component(self.pressure, "pressure", shape, mask, False)
        )
        scalars = tuple(
            (str(name), _validate_component(values, str(name), shape, mask, False))
            for name, values in self.scalars
        )
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "u", u)
        object.__setattr__(self, "v", v)
        object.__setattr__(self, "pressure", pressure)
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "scalars", scalars)
        object.__setattr__(self, "time", _validate_time(self.time))

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.size, self.x.size)

    @property
    def valid_fraction(self) -> float:
        if self.mask is None:
            return 1.0
        return float(np.count_nonzero(self.mask)) / float(self.mask.size)


@dataclass(frozen=True)
class FieldData3D:
    """An immutable, validated 3D velocity field on a structured grid."""

    x: FloatArray
    y: FloatArray
    z: FloatArray
    u: FloatArray
    v: FloatArray
    w: FloatArray
    metadata: FieldMetadata
    time: float | None = None
    pressure: FloatArray | None = None
    mask: BoolArray | None = None
    scalars: tuple[tuple[str, FloatArray], ...] = field(default=())

    def __post_init__(self) -> None:
        x = _validate_axis(self.x, "x")
        y = _validate_axis(self.y, "y")
        z = _validate_axis(self.z, "z")
        shape = (z.size, y.size, x.size)
        mask = None if self.mask is None else _validate_mask(self.mask, shape)
        u = _validate_component(self.u, "u", shape, mask, True)
        v = _validate_component(self.v, "v", shape, mask, True)
        w = _validate_component(self.w, "w", shape, mask, True)
        pressure = (
            None
            if self.pressure is None
            else _validate_component(self.pressure, "pressure", shape, mask, False)
        )
        scalars = tuple(
            (str(name), _validate_component(values, str(name), shape, mask, False))
            for name, values in self.scalars
        )
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "z", z)
        object.__setattr__(self, "u", u)
        object.__setattr__(self, "v", v)
        object.__setattr__(self, "w", w)
        object.__setattr__(self, "pressure", pressure)
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "scalars", scalars)
        object.__setattr__(self, "time", _validate_time(self.time))

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.z.size, self.y.size, self.x.size)

    @property
    def valid_fraction(self) -> float:
        if self.mask is None:
            return 1.0
        return float(np.count_nonzero(self.mask)) / float(self.mask.size)


def is_uniform(coordinates: FloatArray, relative_tolerance: float = 1.0e-9) -> bool:
    """Return whether 1D coordinates are uniformly spaced within a tolerance."""
    differences = np.diff(np.asarray(coordinates, dtype=np.float64))
    mean = float(np.mean(differences))
    if mean == 0.0:
        return False
    return bool(np.all(np.abs(differences - mean) <= relative_tolerance * abs(mean)))


def metadata_from_mapping(mapping: Mapping[str, object]) -> FieldMetadata:
    """Build :class:`FieldMetadata` from a mapping, requiring units to be present."""
    for required in ("source", "length_unit", "velocity_unit"):
        if required not in mapping:
            raise ValueError(f"metadata is missing required key {required!r}.")
    known = {
        "source",
        "length_unit",
        "velocity_unit",
        "time_unit",
        "coordinate_convention",
        "boundary_mode",
    }
    extra = tuple(
        (str(key), str(value))
        for key, value in sorted(mapping.items())
        if key not in known
    )
    return FieldMetadata(
        source=str(mapping["source"]),
        length_unit=str(mapping["length_unit"]),
        velocity_unit=str(mapping["velocity_unit"]),
        time_unit=str(mapping.get("time_unit", "unspecified")),
        coordinate_convention=str(mapping.get("coordinate_convention", "zyx")),
        boundary_mode=str(mapping.get("boundary_mode", "unknown")),
        extra=extra,
    )
