"""Cylinder-wake Re=3900 integration workflow contract (research, Mission 6, H46).

The dataset integration is **attempted** through a manual, network-enabled, checksum-
verified workflow and is **blocked-in-CI** (no network, GB-scale data). This module
carries the parts that *can* run offline: the ordered workflow stages, the evidence-level
ladder, and a schema validator for the manifests the workflow produces. It downloads
nothing, fabricates no checksums, and asserts no scientific result -- it only defines and
validates the contract so a later offline run has a well-formed target. Experimental
research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from dataclasses import dataclass

from itd_research.external_validation.cylinder_re3900.metadata import CYLINDER_RE3900

# Ordered workflow stages (run manually, off CI). Only the first is a pure no-network step.
WORKFLOW_STAGES: tuple[str, ...] = (
    "discover", "download", "verify", "inspect", "convert", "subset", "manifest", "analyse",
)

# Evidence ladder: each level is only reachable after the ones before it. None are reached
# in CI (blocked at "download"); the ladder makes partial progress auditable.
EVIDENCE_LEVELS: tuple[str, ...] = (
    "ingestion_verified",       # files downloaded + checksummed + variables inspected
    "diagnostic_comparison",    # ITD vs established diagnostics on the converted subset
    "temporal_event_analysis",  # alignment to lift/pressure/shedding events
    "predictive_development",   # leakage-safe development on a subset
    "locked_external_holdout",  # single evaluation on a frozen external holdout
)

# Required keys for each manifest the workflow emits (validated offline against fixtures).
_MANIFEST_SCHEMA: dict[str, tuple[str, ...]] = {
    "source_manifest": ("dataset_id", "url", "files", "sha256", "licence", "verified_redistribution"),
    "inspect_report": ("variables", "dimensions", "cadence", "coordinate_system", "units"),
    "conversion_manifest": ("subset_frames", "spatial_crop", "field_model", "sha256"),
    "label_manifest": ("label_source", "labels", "provenance", "uncertainty"),
}


@dataclass(frozen=True)
class SchemaResult:
    """Outcome of validating one manifest against its required keys."""

    manifest: str
    valid: bool
    missing: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"manifest": self.manifest, "valid": self.valid, "missing": list(self.missing)}


def manifest_schema(name: str) -> tuple[str, ...]:
    if name not in _MANIFEST_SCHEMA:
        raise ValueError(f"unknown manifest {name!r}; choose from {tuple(_MANIFEST_SCHEMA)}")
    return _MANIFEST_SCHEMA[name]


def validate_manifest(name: str, payload: dict[str, object]) -> SchemaResult:
    """Check that a workflow manifest carries its required provenance keys.

    Structural validation only -- it never asserts the values are scientifically correct,
    and it never fabricates checksums or data. A real offline run feeds its emitted
    manifests here; CI feeds tiny synthetic fixtures.
    """
    required = manifest_schema(name)
    missing = tuple(key for key in required if key not in payload)
    return SchemaResult(manifest=name, valid=not missing, missing=missing)


@dataclass(frozen=True)
class IntegrationStatus:
    """Offline snapshot of how far the integration has progressed (blocked in CI)."""

    dataset_id: str
    stages: tuple[str, ...]
    blocked_stage: str
    evidence_levels: tuple[str, ...]
    reached_level: str | None
    blocked_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "stages": list(self.stages),
            "blocked_stage": self.blocked_stage,
            "evidence_levels": list(self.evidence_levels),
            "reached_level": self.reached_level,
            "blocked_reasons": list(self.blocked_reasons),
        }


def workflow_status() -> IntegrationStatus:
    """The current, honest integration state: blocked at ``download`` (no network)."""
    return IntegrationStatus(
        dataset_id=CYLINDER_RE3900.dataset_id,
        stages=WORKFLOW_STAGES,
        blocked_stage="download",
        evidence_levels=EVIDENCE_LEVELS,
        reached_level=None,  # nothing downloaded in this environment
        blocked_reasons=CYLINDER_RE3900.blocked_reasons,
    )
