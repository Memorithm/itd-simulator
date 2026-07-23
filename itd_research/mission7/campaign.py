"""Orchestrate the external-evidence campaign (Mission 7).

Given a directory of external ``frame_*.npz`` files (real JHTDB data in a manual run, or a
synthetic fixture in offline CI), ingest with provenance, validate physics, compute
ITD-vs-established diagnostics + complementarity, and run the locked prediction. Returns a
single result object that the CLI serialises. No network access occurs here -- the caller
supplies an already-downloaded directory.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from itd_research.mission7.analysis import (
    ComplementarityResult,
    DiagnosticTrajectories,
    ExternalPredictionResult,
    compute_trajectories,
    external_prediction,
    rank_complementarity,
)
from itd_research.mission7.fixtures import write_synthetic_sequence
from itd_research.mission7.ingestion import SequenceProvenance, load_field_sequence
from itd_research.mission7.physics import PhysicalValidation, validate_isotropic_dns


@dataclass(frozen=True)
class ExternalCampaignResult:
    """Full external-evidence campaign outcome for one source."""

    source_id: str
    is_synthetic_fixture: bool
    provenance: SequenceProvenance
    physics: PhysicalValidation
    trajectories: DiagnosticTrajectories
    complementarity: ComplementarityResult
    prediction: ExternalPredictionResult

    def as_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "is_synthetic_fixture": self.is_synthetic_fixture,
            "evidence_class": "synthetic-code-verification (NOT external evidence)"
            if self.is_synthetic_fixture else "external",
            "provenance": self.provenance.as_dict(),
            "physics": self.physics.as_dict(),
            "trajectories": self.trajectories.as_dict(),
            "complementarity": self.complementarity.as_dict(),
            "prediction": self.prediction.as_dict(),
        }


def run_external_campaign(
    directory: str | Path, *, source_id: str, is_synthetic_fixture: bool = False,
) -> ExternalCampaignResult:
    """Ingest, physically validate, and analyse an external field sequence."""
    frames, provenance = load_field_sequence(directory, source_id=source_id)
    physics = validate_isotropic_dns(frames)
    trajectories = compute_trajectories(frames)
    complementarity = rank_complementarity(trajectories)
    prediction = external_prediction(trajectories)
    return ExternalCampaignResult(
        source_id=source_id, is_synthetic_fixture=is_synthetic_fixture, provenance=provenance,
        physics=physics, trajectories=trajectories, complementarity=complementarity,
        prediction=prediction,
    )


def run_fixture_campaign(*, nodes: int = 12, n_frames: int = 12) -> ExternalCampaignResult:
    """Offline CI path: synthesise a sequence and run the campaign on it (no network)."""
    with tempfile.TemporaryDirectory(prefix="itd-m7-fixture-") as tmp:
        write_synthetic_sequence(tmp, nodes=nodes, n_frames=n_frames)
        return run_external_campaign(tmp, source_id="synthetic_fixture", is_synthetic_fixture=True)
