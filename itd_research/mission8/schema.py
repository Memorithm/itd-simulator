"""Shared dataclasses for the Mission 8 structural/topological pipeline.

Kept separate from the modules that populate them so every stage of the pipeline
(regions, events, features, prediction, transfer, degradation) serialises the same shapes.
Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RegionRecord:
    """One connected structural region in one frame (established-diagnostic derived)."""

    label: int
    volume_cells: int
    centroid: tuple[float, float, float]

    def as_dict(self) -> dict[str, object]:
        return {"label": self.label, "volume_cells": self.volume_cells,
                "centroid": list(self.centroid)}


@dataclass(frozen=True)
class FrameRegions:
    """All regions detected in one frame, plus the frame's region count."""

    frame_index: int
    time: float
    regions: tuple[RegionRecord, ...]

    @property
    def count(self) -> int:
        return len(self.regions)

    def as_dict(self) -> dict[str, object]:
        return {"frame_index": self.frame_index, "time": self.time, "count": self.count,
                "regions": [r.as_dict() for r in self.regions]}


@dataclass(frozen=True)
class StructuralEvent:
    """One ITD-independent topology-change event (Mission 8 event schema, section 9)."""

    event_id: str
    event_type: str          # "core_merger" | "core_split"
    event_time: float
    event_frame: int
    event_uncertainty: float  # in frames (persistence window half-width)
    label_source: str
    label_method: str
    source_file: str
    source_index: int
    itd_independence: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id, "event_type": self.event_type,
            "event_time": self.event_time, "event_frame": self.event_frame,
            "event_uncertainty": self.event_uncertainty, "label_source": self.label_source,
            "label_method": self.label_method, "source_file": self.source_file,
            "source_index": self.source_index, "itd_independence": self.itd_independence,
        }


@dataclass(frozen=True)
class TaskScreeningResult:
    """Saturation-screen outcome for one candidate task (Mission 8 section 6)."""

    task_id: str
    event_definition: str
    baseline_development_auc: float
    baseline_development_pr_auc: float
    saturation_status: str   # "saturated" | "unsaturated"
    selected_for_primary_test: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id, "event_definition": self.event_definition,
            "baseline_development_auc": self.baseline_development_auc,
            "baseline_development_pr_auc": self.baseline_development_pr_auc,
            "saturation_status": self.saturation_status,
            "selected_for_primary_test": self.selected_for_primary_test,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SequenceData:
    """A loaded external sequence plus its derived per-frame region/feature tables."""

    source_id: str
    times: list[float] = field(default_factory=list)
