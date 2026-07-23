"""Provenance metadata for the Re=3900 cylinder-wake dataset (research, Mission 5).

This records what is needed to integrate the dataset through the manual, network-enabled
workflow. It carries no field data and asserts no result: ``integration_status`` is
``blocked-by-{network,size}`` in the offline CI environment. Independent event labels
(lift/drag zero-crossings, shedding phase, published Strouhal frequency, core tracks)
are all ITD-independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CylinderDatasetMetadata:
    """Full provenance for an external cylinder-wake dataset (no field data)."""

    dataset_id: str
    title: str
    institution: str
    doi: str
    url: str
    licence: str
    reynolds_number: float
    dimensionality: str
    time_resolved: bool
    velocity_components: tuple[str, ...]
    pressure_available: bool
    force_available: bool
    independent_labels: tuple[str, ...]
    integration_status: str
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "institution": self.institution,
            "doi": self.doi,
            "url": self.url,
            "licence": self.licence,
            "reynolds_number": self.reynolds_number,
            "dimensionality": self.dimensionality,
            "time_resolved": self.time_resolved,
            "velocity_components": list(self.velocity_components),
            "pressure_available": self.pressure_available,
            "force_available": self.force_available,
            "independent_labels": list(self.independent_labels),
            "integration_status": self.integration_status,
            "blocked_reasons": list(self.blocked_reasons),
            "notes": self.notes,
        }


CYLINDER_RE3900 = CylinderDatasetMetadata(
    dataset_id="cylinder_re3900_lagrangian_eulerian",
    title="Lagrangian and Eulerian dataset of the wake downstream of a smooth cylinder at Re=3900",
    institution="(published dataset; see source record)",
    doi="unverified -- confirm at the source record before citing",
    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8713130/",
    licence="see source (verify redistribution before download)",
    reynolds_number=3900.0,
    dimensionality="3D (time-resolved) + 2D snapshots",
    time_resolved=True,
    velocity_components=("u", "v", "w"),
    pressure_available=True,
    force_available=True,
    independent_labels=(
        "lift/drag coefficient zero-crossings",
        "alternating shedding phase",
        "published Strouhal frequency",
        "pressure-minimum passage",
        "published/derived vortex-core tracks",
    ),
    integration_status="blocked-by-{network,size}",
    blocked_reasons=(
        "no network download in CI",
        "full time-resolved 3D dataset is large (GB-scale); not committed",
    ),
    notes=(
        "Highest-priority external target (Mission 4 inventory). Integration is via the "
        "manual workflow in tools/datasets/cylinder_re3900/. A small subset would enable "
        "H27/H24/H28; none is integrated in this offline environment."
    ),
)
