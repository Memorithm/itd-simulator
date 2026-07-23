"""Format-decoupled ingestion for external velocity fields (post-V29 research).

Adapters (CSV, NPZ, legacy-ASCII VTK, OpenFOAM export, PIV) produce the typed,
immutable :class:`~itd_research.io.field_data.FieldData2D` /
:class:`~itd_research.io.field_data.FieldData3D` model. This subpackage is part
of the isolated ``itd_research`` namespace, never modifies the certified V29.18
core, is never imported by ``itd_v29_core``, imports no plotting library, and
performs no network access. All parsing is NumPy-only and refuses symlinks and
oversized inputs; ``.npz`` loading disables pickle.
"""

from __future__ import annotations

from itd_research.io.csv_fields import (
    read_csv_field_2d,
    read_csv_field_3d,
    write_csv_field_2d,
)
from itd_research.io.field_data import (
    FieldData2D,
    FieldData3D,
    FieldMetadata,
    is_uniform,
    metadata_from_mapping,
)
from itd_research.io.metadata import (
    DatasetProvenance,
    load_registry,
    provenance_from_mapping,
    sha256_of,
    verify_checksum,
)
from itd_research.io.npz import (
    read_npz_field_2d,
    read_npz_field_3d,
    write_npz_field_2d,
    write_npz_field_3d,
)
from itd_research.io.openfoam import read_openfoam_vtk
from itd_research.io.piv import PivRepairReport, read_piv_csv_2d
from itd_research.io.vtk import read_vtk_structured, write_vtk_structured_points_3d

__all__ = (
    # model
    "FieldData2D",
    "FieldData3D",
    "FieldMetadata",
    "is_uniform",
    "metadata_from_mapping",
    # provenance
    "DatasetProvenance",
    "load_registry",
    "provenance_from_mapping",
    "sha256_of",
    "verify_checksum",
    # adapters
    "read_csv_field_2d",
    "read_csv_field_3d",
    "write_csv_field_2d",
    "read_npz_field_2d",
    "read_npz_field_3d",
    "write_npz_field_2d",
    "write_npz_field_3d",
    "read_vtk_structured",
    "write_vtk_structured_points_3d",
    "read_openfoam_vtk",
    "read_piv_csv_2d",
    "PivRepairReport",
)
