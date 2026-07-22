"""Dataset provenance records and registry loading (research).

Every external dataset used for validation must carry complete provenance. This
module defines the provenance record, loads the machine-readable registry, and
verifies file checksums. It performs no network access.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_REQUIRED = (
    "id",
    "title",
    "source",
    "licence",
    "redistribution_allowed",
    "format",
    "dimensionality",
    "intended_experiment",
)


@dataclass(frozen=True)
class DatasetProvenance:
    """Immutable provenance for one external dataset."""

    id: str
    title: str
    source: str
    licence: str
    redistribution_allowed: bool
    format: str
    dimensionality: str
    intended_experiment: str
    authors: str = ""
    institution: str = ""
    url: str = ""
    doi: str = ""
    version: str = ""
    download_method: str = ""
    sha256: str = ""
    variables: tuple[str, ...] = ()
    units: tuple[tuple[str, str], ...] = ()
    coordinate_system: str = ""
    time_information: str = ""
    uncertainty_information: str = ""
    date_retrieved: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "authors": self.authors,
            "institution": self.institution,
            "url": self.url,
            "doi": self.doi,
            "version": self.version,
            "licence": self.licence,
            "redistribution_allowed": self.redistribution_allowed,
            "download_method": self.download_method,
            "sha256": self.sha256,
            "format": self.format,
            "dimensionality": self.dimensionality,
            "variables": list(self.variables),
            "units": {key: value for key, value in self.units},
            "coordinate_system": self.coordinate_system,
            "time_information": self.time_information,
            "uncertainty_information": self.uncertainty_information,
            "intended_experiment": self.intended_experiment,
            "date_retrieved": self.date_retrieved,
        }


def provenance_from_mapping(mapping: Mapping[str, object]) -> DatasetProvenance:
    """Build a :class:`DatasetProvenance`, requiring the core fields."""
    for required in _REQUIRED:
        if required not in mapping:
            raise ValueError(f"dataset entry is missing required key {required!r}.")
    units_value = mapping.get("units", {})
    if isinstance(units_value, Mapping):
        units = tuple((str(k), str(v)) for k, v in sorted(units_value.items()))
    else:
        units = ()
    variables_value = mapping.get("variables", ())
    if isinstance(variables_value, (list, tuple)):
        variables = tuple(str(item) for item in variables_value)
    else:
        variables = ()
    return DatasetProvenance(
        id=str(mapping["id"]),
        title=str(mapping["title"]),
        source=str(mapping["source"]),
        licence=str(mapping["licence"]),
        redistribution_allowed=bool(mapping["redistribution_allowed"]),
        format=str(mapping["format"]),
        dimensionality=str(mapping["dimensionality"]),
        intended_experiment=str(mapping["intended_experiment"]),
        authors=str(mapping.get("authors", "")),
        institution=str(mapping.get("institution", "")),
        url=str(mapping.get("url", "")),
        doi=str(mapping.get("doi", "")),
        version=str(mapping.get("version", "")),
        download_method=str(mapping.get("download_method", "")),
        sha256=str(mapping.get("sha256", "")),
        variables=variables,
        units=units,
        coordinate_system=str(mapping.get("coordinate_system", "")),
        time_information=str(mapping.get("time_information", "")),
        uncertainty_information=str(mapping.get("uncertainty_information", "")),
        date_retrieved=str(mapping.get("date_retrieved", "")),
    )


def load_registry(path: str | Path) -> dict[str, DatasetProvenance]:
    """Load and validate ``datasets/registry.json`` into a mapping by id."""
    registry_path = Path(path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = data.get("datasets", []) if isinstance(data, dict) else data
    result: dict[str, DatasetProvenance] = {}
    for entry in entries:
        provenance = provenance_from_mapping(entry)
        if provenance.id in result:
            raise ValueError(f"duplicate dataset id in registry: {provenance.id}")
        result[provenance.id] = provenance
    return result


def sha256_of(path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksum(path: str | Path, expected_sha256: str) -> None:
    """Raise :class:`ValueError` if the file's SHA-256 does not match."""
    actual = sha256_of(path)
    if actual.lower() != expected_sha256.strip().lower():
        raise ValueError(
            f"checksum mismatch for {path}: expected {expected_sha256}, got {actual}"
        )
