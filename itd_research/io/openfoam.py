"""OpenFOAM ingestion via a documented structured export (research).

Native OpenFOAM ``polyMesh``/field parsing for arbitrary cases is intentionally
**not** implemented here. Instead, exactly one robust, documented workflow is
supported: resample the OpenFOAM case onto a structured Cartesian grid and export
it to a legacy ASCII VTK ``STRUCTURED_POINTS``/``RECTILINEAR_GRID`` file or to the
canonical CSV layout, then ingest that.

Supported export workflow
-------------------------
1. Run the OpenFOAM case (e.g. ``blockMesh`` then ``pimpleFoam``/``icoFoam``).
2. Load the result in ParaView, apply **Resample To Image** (or **Resample With
   Dataset** onto a box) to obtain a uniform structured grid of the velocity
   field ``U``.
3. **Save Data** as *Legacy VTK* (ASCII), or export the resampled points as CSV
   with columns ``x,y,z,u,v,w``.
4. Ingest with :func:`read_openfoam_vtk` or the CSV adapter.

This keeps the supported convention explicit rather than pretending to parse any
OpenFOAM case directly.
"""

from __future__ import annotations

from pathlib import Path

from itd_research.io.field_data import FieldData2D, FieldData3D, FieldMetadata
from itd_research.io.vtk import read_vtk_structured


def read_openfoam_vtk(
    path: str | Path,
    metadata: FieldMetadata,
    time: float | None = None,
) -> FieldData2D | FieldData3D:
    """Read an OpenFOAM result exported to legacy-ASCII structured VTK.

    ``metadata`` should record the solver, OpenFOAM version, Reynolds number, and
    boundary conventions in its ``extra`` field so the provenance is complete.
    """
    return read_vtk_structured(path, metadata, time=time)
