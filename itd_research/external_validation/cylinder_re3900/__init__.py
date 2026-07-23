"""Cylinder-wake Re=3900 external-dataset integration (research, Mission 5).

Metadata and provenance for the highest-priority external target identified in
Mission 4: a time-resolved cylinder-wake DNS with Eulerian + Lagrangian fields and
independent labels (force/pressure), purpose-built for PIV/PTV validation. Integration
is **attempted** via a documented manual workflow (``tools/datasets/cylinder_re3900/``)
and is **blocked-by-{network,size}** in this offline CI environment -- no result is
fabricated. Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.external_validation.cylinder_re3900.integration import (
    EVIDENCE_LEVELS,
    WORKFLOW_STAGES,
    IntegrationStatus,
    SchemaResult,
    manifest_schema,
    validate_manifest,
    workflow_status,
)
from itd_research.external_validation.cylinder_re3900.metadata import (
    CYLINDER_RE3900,
    CylinderDatasetMetadata,
)

__all__ = [
    "CYLINDER_RE3900",
    "EVIDENCE_LEVELS",
    "WORKFLOW_STAGES",
    "CylinderDatasetMetadata",
    "IntegrationStatus",
    "SchemaResult",
    "manifest_schema",
    "validate_manifest",
    "workflow_status",
]
