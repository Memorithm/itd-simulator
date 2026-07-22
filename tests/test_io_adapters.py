"""Tests for the external-field ingestion adapters and provenance layer."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from itd_research.diagnostics_3d import analytical_fields as af
from itd_research.io import (
    DatasetProvenance,
    FieldData2D,
    FieldData3D,
    FieldMetadata,
    load_registry,
    read_csv_field_2d,
    read_npz_field_3d,
    read_piv_csv_2d,
    read_vtk_structured,
    sha256_of,
    verify_checksum,
    write_csv_field_2d,
    write_npz_field_3d,
    write_vtk_structured_points_3d,
)

META = FieldMetadata(source="test", length_unit="m", velocity_unit="m/s")
_FIXTURES = Path(__file__).parent / "fixtures" / "external"
_REGISTRY = Path(__file__).resolve().parents[1] / "datasets" / "registry.json"


def _field2d() -> FieldData2D:
    x = np.linspace(0.0, 1.0, 5)
    y = np.linspace(0.0, 1.0, 4)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    return FieldData2D(x=x, y=y, u=np.sin(xx), v=np.cos(yy), metadata=META)


def test_csv_round_trip_2d(tmp_path: Path) -> None:
    field = _field2d()
    path = tmp_path / "f.csv"
    write_csv_field_2d(path, field)
    loaded = read_csv_field_2d(path, META)
    assert np.allclose(loaded.u, field.u)
    assert np.allclose(loaded.v, field.v)
    assert loaded.shape == field.shape


def test_csv_missing_column_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("x,y,u\n0,0,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_csv_field_2d(path, META)


def test_csv_non_structured_grid_rejected(tmp_path: Path) -> None:
    path = tmp_path / "scatter.csv"
    path.write_text("x,y,u,v\n0,0,1,1\n1,0,1,1\n0.5,1,1,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_csv_field_2d(path, META)


def test_npz_and_vtk_round_trip_3d(tmp_path: Path) -> None:
    grid = af.finite_grid_3d(4, -1.0, 1.0)
    u, v, w = af.linear_velocity(af.rigid_rotation_gradient(1.0), grid)
    field = FieldData3D(x=grid.x, y=grid.y, z=grid.z, u=u, v=v, w=w, metadata=META)
    npz_path = tmp_path / "f.npz"
    vtk_path = tmp_path / "f.vtk"
    write_npz_field_3d(npz_path, field)
    write_vtk_structured_points_3d(vtk_path, field)
    from_npz = read_npz_field_3d(npz_path, META)
    from_vtk = read_vtk_structured(vtk_path, META)
    assert np.allclose(from_npz.w, w)
    assert isinstance(from_vtk, FieldData3D)
    assert np.allclose(from_vtk.u, u) and np.allclose(from_vtk.v, v)


def test_adapters_reject_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.csv"
    write_csv_field_2d(real, _field2d())
    link = tmp_path / "link.csv"
    os.symlink(real, link)
    with pytest.raises(ValueError):
        read_csv_field_2d(link, META)


def test_piv_strict_masks_invalid_vectors() -> None:
    field, report = read_piv_csv_2d(_FIXTURES / "piv_small.csv", META, mode="strict")
    assert report.n_invalid == 2
    assert report.n_interpolated == 0
    assert report.n_masked == 2
    assert field.mask is not None and not field.mask.all()


def test_piv_repair_fills_and_reports() -> None:
    field, report = read_piv_csv_2d(_FIXTURES / "piv_small.csv", META, mode="repair")
    assert report.n_invalid == 2
    assert report.n_interpolated == 2
    assert report.method == "jacobi_neighbour_average"
    assert field.valid_fraction == 1.0  # all filled in this small case


def test_piv_rejects_bad_mode() -> None:
    with pytest.raises(ValueError):
        read_piv_csv_2d(_FIXTURES / "piv_small.csv", META, mode="magic")


def test_committed_fixtures_load() -> None:
    field2d = read_csv_field_2d(_FIXTURES / "field2d_small.csv", META)
    assert field2d.shape == (4, 5)
    field3d = read_npz_field_3d(_FIXTURES / "field3d_small.npz", META)
    assert field3d.shape == (4, 4, 4)
    vtk_field = read_vtk_structured(_FIXTURES / "field3d_small.vtk", META)
    assert isinstance(vtk_field, FieldData3D)


def test_registry_loads_and_is_valid() -> None:
    registry = load_registry(_REGISTRY)
    assert "synthetic_piv_small" in registry
    for entry in registry.values():
        assert isinstance(entry, DatasetProvenance)
        assert entry.licence
        assert entry.dimensionality in ("2D", "3D")


def test_checksum_verification(tmp_path: Path) -> None:
    path = tmp_path / "data.bin"
    path.write_bytes(b"itd")
    digest = sha256_of(path)
    verify_checksum(path, digest)
    with pytest.raises(ValueError):
        verify_checksum(path, "0" * 64)
