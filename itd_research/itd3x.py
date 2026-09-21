"""ITD-3X research-engine bootstrap contracts.

This module launches the ITD Research Lab V30+ research-engine lineage while
keeping the certified ITD V29.18 scientific model immutable.  It contains only
programme metadata and deterministic registry contracts: no V29 numerical
semantics are changed or reinterpreted.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

FROZEN_SCIENTIFIC_BASELINE = "ITD V29.18"
RESEARCH_ENGINE_REVISION = "ITD Research Lab V30.0-alpha"


class ResearchTrack(StrEnum):
    """Named ITD-3X programme tracks."""

    CORE = "core"
    REPRESENTATION = "representation"
    AI = "ai"
    TRAJECTORY = "trajectory"
    UQ = "uq"
    ATTENTION = "attention"
    ADAPTIVE = "adaptive"
    PERTURBATION = "perturbation"
    SEARCH = "search"
    RUST_EVIDENCE = "rust_evidence"


class SeriesStatus(StrEnum):
    """Lifecycle state for a research series."""

    BOOTSTRAP = "bootstrap"
    ACTIVE = "active"
    PLANNED = "planned"
    CONDITIONAL = "conditional"


@dataclass(frozen=True)
class SeriesSpec:
    """One immutable ITD-3X programme declaration."""

    series_id: str
    title: str
    track: ResearchTrack
    status: SeriesStatus
    objective: str
    prerequisites: tuple[str, ...] = ()
    ecosystem: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.series_id.startswith("ITD-3"):
            raise ValueError("ITD-3X series identifiers must start with 'ITD-3'.")
        if not self.title.strip():
            raise ValueError("series title must not be empty.")
        if not self.objective.strip():
            raise ValueError("series objective must not be empty.")

    def as_dict(self) -> dict[str, object]:
        return {
            "series_id": self.series_id,
            "title": self.title,
            "track": self.track.value,
            "status": self.status.value,
            "objective": self.objective,
            "prerequisites": list(self.prerequisites),
            "ecosystem": list(self.ecosystem),
        }


@dataclass(frozen=True)
class SeriesRegistry:
    """Deterministic registry for the ITD-3X research programme."""

    series: tuple[SeriesSpec, ...]
    programme: str = RESEARCH_ENGINE_REVISION
    frozen_baseline: str = FROZEN_SCIENTIFIC_BASELINE

    def __post_init__(self) -> None:
        identifiers = tuple(item.series_id for item in self.series)
        if not identifiers:
            raise ValueError("ITD-3X registry must contain at least one series.")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("ITD-3X series identifiers must be unique.")

    def as_dict(self) -> dict[str, object]:
        return {
            "programme": self.programme,
            "frozen_baseline": self.frozen_baseline,
            "series": [item.as_dict() for item in self.series],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def get(self, series_id: str) -> SeriesSpec:
        for item in self.series:
            if item.series_id == series_id:
                return item
        raise KeyError(series_id)


def default_itd3x_registry() -> SeriesRegistry:
    """Return the bootstrap ITD-30.x..39.x programme registry."""

    s = SeriesSpec
    return SeriesRegistry(
        (
            s("ITD-30.0", "Research Lab bootstrap and governance", ResearchTrack.CORE, SeriesStatus.ACTIVE,
              "Establish V30+ research-engine identity, immutable V29.18 boundary, lifecycle and evidence gates."),
            s("ITD-30.1", "Experiment contract consolidation", ResearchTrack.CORE, SeriesStatus.ACTIVE,
              "Extend leakage-safe protocol contracts with versioned result, adapter and campaign identities.",
              ("ITD-30.0",)),
            s("ITD-30.2", "Adapter and evidence envelopes", ResearchTrack.CORE, SeriesStatus.PLANNED,
              "Define cross-repository adapter boundaries and machine-readable evidence envelopes.",
              ("ITD-30.1",), ("SciRust-Verify", "scirust-hub")),
            s("ITD-30.3", "Campaign runner and outcome lifecycle", ResearchTrack.CORE, SeriesStatus.PLANNED,
              "Execute bounded campaigns while preserving blocked, inconclusive, negative and positive outcomes.",
              ("ITD-30.2",)),
            s("ITD-31.0", "Representation strata foundation", ResearchTrack.REPRESENTATION, SeriesStatus.ACTIVE,
              "Turn dense, sparse, low-rank, quantized and mixed representations into measurable experimental strata.",
              ("ITD-30.1",), ("SciRust", "ElasticXxx")),
            s("ITD-31.1", "Exact representation accounting", ResearchTrack.REPRESENTATION, SeriesStatus.PLANNED,
              "Measure fidelity, exact storage including metadata, transition cost and peak memory.",
              ("ITD-31.0",), ("SciRust",)),
            s("ITD-31.2", "Representation transition graph", ResearchTrack.REPRESENTATION, SeriesStatus.PLANNED,
              "Compare flat format selection with constrained graph/path planning under frozen objectives.",
              ("ITD-31.1",), ("ElasticXxx",)),
            s("ITD-31.3", "Representation OOD transfer", ResearchTrack.REPRESENTATION, SeriesStatus.PLANNED,
              "Measure path stability and regret when tensor/data geometry changes.",
              ("ITD-31.2",)),
            s("ITD-31.4", "Elastic representation qualification", ResearchTrack.REPRESENTATION, SeriesStatus.CONDITIONAL,
              "Export qualified transition evidence to ElasticXxx without creating runtime policy.",
              ("ITD-31.3",), ("ElasticXxx",)),
            s("ITD-32.0", "ITD-AI adapter laboratory", ResearchTrack.AI, SeriesStatus.ACTIVE,
              "Create fair raw/ITD/learned/combined comparison ladders for AI and SciML.",
              ("ITD-30.1",)),
            s("ITD-32.1", "NeuralOperator bridge", ResearchTrack.AI, SeriesStatus.PLANNED,
              "Evaluate ITD research representations on Burgers/Darcy operator-learning tasks.",
              ("ITD-32.0",), ("NeuralOperator", "SciRust")),
            s("ITD-32.2", "Auxiliary structural supervision", ResearchTrack.AI, SeriesStatus.PLANNED,
              "Test whether structural targets improve sample efficiency, calibration or robustness.",
              ("ITD-32.1",)),
            s("ITD-32.3", "Learned local and multiscale structure", ResearchTrack.AI, SeriesStatus.PLANNED,
              "Study patchwise, graph, spectral and multiscale research representations without revising V29.18.",
              ("ITD-32.1",)),
            s("ITD-33.0", "ITD-TRAJECTORY foundation", ResearchTrack.TRAJECTORY, SeriesStatus.ACTIVE,
              "Define research-only descriptors over state, memory and inference trajectories.",
              ("ITD-30.1",), ("TDI",)),
            s("ITD-33.1", "TDI trajectory descriptors", ResearchTrack.TRAJECTORY, SeriesStatus.PLANNED,
              "Compare state deformation, concentration, churn and disagreement with competent TDI/static controls.",
              ("ITD-33.0",), ("TDI",)),
            s("ITD-33.2", "Trajectory intervention experiments", ResearchTrack.TRAJECTORY, SeriesStatus.PLANNED,
              "Separate prediction from causal intervention on controlled inference trajectories.",
              ("ITD-33.1",), ("TDI", "NoiseLab")),
            s("ITD-33.3", "Adaptive inference bridge", ResearchTrack.TRAJECTORY, SeriesStatus.CONDITIONAL,
              "Evaluate trajectory evidence for continue/verify/recover/stop research policies under TDI-9.x contracts.",
              ("ITD-33.2",), ("TDI", "ElasticXxx")),
            s("ITD-34.0", "ITD-UQ foundation", ResearchTrack.UQ, SeriesStatus.ACTIVE,
              "Unify OOD, calibration, selective prediction and abstention experiments."),
            s("ITD-34.1", "Calibration and selective prediction", ResearchTrack.UQ, SeriesStatus.PLANNED,
              "Measure calibration error, risk-coverage and false-confidence under declared shifts.",
              ("ITD-34.0",)),
            s("ITD-34.2", "Spatial and structural uncertainty", ResearchTrack.UQ, SeriesStatus.PLANNED,
              "Test whether structural signals localize error or uncertainty beyond standard UQ controls.",
              ("ITD-34.1",), ("NeuralOperator",)),
            s("ITD-35.0", "Structured attention/operator laboratory", ResearchTrack.ATTENTION, SeriesStatus.ACTIVE,
              "Run deterministic mechanistic tests for structured sequence-mixing operators.",
              ("ITD-30.1",), ("FLAT-ATTENTION", "TDI")),
            s("ITD-35.1", "FLAT reference semantics", ResearchTrack.ATTENTION, SeriesStatus.PLANNED,
              "Bind ITD experiments to frozen FLAT host/reference semantics before hardware claims.",
              ("ITD-35.0",), ("FLAT-ATTENTION",)),
            s("ITD-35.2", "Multi-Algebra Attention studies", ResearchTrack.ATTENTION, SeriesStatus.PLANNED,
              "Test Boolean/F2/Zhegalkin/max-plus research mechanisms with matched controls and ablations.",
              ("ITD-35.1",), ("FLAT-ATTENTION", "TDI")),
            s("ITD-35.3", "Structured spectral operator studies", ResearchTrack.ATTENTION, SeriesStatus.PLANNED,
              "Test Toeplitz, prolate, Green-kernel and controlled spectral-flow mechanisms without importing RH claims.",
              ("ITD-35.1",), ("riemann_ndim_bench", "SciRust")),
            s("ITD-36.0", "ITD-ADAPTIVE foundation", ResearchTrack.ADAPTIVE, SeriesStatus.ACTIVE,
              "Define quality/cost/invariant experiments for adaptive resource decisions.",
              ("ITD-30.2",), ("ElasticXxx",)),
            s("ITD-36.1", "Elastic shadow policies", ResearchTrack.ADAPTIVE, SeriesStatus.PLANNED,
              "Evaluate hypothetical Elastic decisions without actuation and report regret/invariant risk.",
              ("ITD-36.0",), ("ElasticXxx",)),
            s("ITD-36.2", "Precision and representation adaptation", ResearchTrack.ADAPTIVE, SeriesStatus.PLANNED,
              "Test adaptive precision, compression and representation choices under explicit invariants.",
              ("ITD-31.2", "ITD-36.1"), ("ElasticXxx", "SciRust")),
            s("ITD-36.3", "Model and compute adaptation", ResearchTrack.ADAPTIVE, SeriesStatus.PLANNED,
              "Test bounded model/compute allocation policies against fixed and static-preallocation controls.",
              ("ITD-33.3", "ITD-36.1"), ("ElasticXxx", "TDI")),
            s("ITD-37.0", "Perturbation laboratory bridge", ResearchTrack.PERTURBATION, SeriesStatus.ACTIVE,
              "Use controlled perturbations to test structural sensitivity and robustness.",
              ("ITD-30.1",), ("NoiseLab",)),
            s("ITD-37.1", "Perturbation-response maps", ResearchTrack.PERTURBATION, SeriesStatus.PLANNED,
              "Map intervention amplitude/location to structural change, task error and uncertainty.",
              ("ITD-37.0",), ("NoiseLab",)),
            s("ITD-37.2", "Robustness and causal falsification", ResearchTrack.PERTURBATION, SeriesStatus.PLANNED,
              "Test whether candidate descriptors survive matched stochastic and adversarial controls.",
              ("ITD-37.1",), ("NoiseLab", "TDI")),
            s("ITD-38.0", "Forge bounded search bridge", ResearchTrack.SEARCH, SeriesStatus.ACTIVE,
              "Make Forge a bounded candidate-search engine while ITD retains protocol and holdout authority.",
              ("ITD-30.2",), ("Forge",)),
            s("ITD-38.1", "Descriptor and operator search", ResearchTrack.SEARCH, SeriesStatus.PLANNED,
              "Search bounded descriptor/operator families against frozen development objectives.",
              ("ITD-38.0",), ("Forge", "SciRust")),
            s("ITD-38.2", "Policy search under frozen contracts", ResearchTrack.SEARCH, SeriesStatus.CONDITIONAL,
              "Search adaptive policies only after upstream action/observation domains are leakage-safe and frozen.",
              ("ITD-36.1", "ITD-38.0"), ("Forge", "ElasticXxx", "TDI")),
            s("ITD-39.0", "Rust/SciRust parity programme", ResearchTrack.RUST_EVIDENCE, SeriesStatus.ACTIVE,
              "Build a Rust execution path checked against independent analytical and Python regression oracles.",
              ("ITD-30.1",), ("SciRust",)),
            s("ITD-39.1", "SciRust primitive promotion", ResearchTrack.RUST_EVIDENCE, SeriesStatus.PLANNED,
              "Promote only generalized independently validated mathematical/statistical primitives.",
              ("ITD-39.0",), ("SciRust",)),
            s("ITD-39.2", "SciRust-Verify evidence dossiers", ResearchTrack.RUST_EVIDENCE, SeriesStatus.PLANNED,
              "Normalize ITD campaign evidence into integrity-sealed dossiers without changing scientific verdict semantics.",
              ("ITD-30.2",), ("SciRust-Verify",)),
            s("ITD-39.3", "Hub campaign orchestration", ResearchTrack.RUST_EVIDENCE, SeriesStatus.PLANNED,
              "Orchestrate reproducible non-privileged ITD campaigns through scirust-hub.",
              ("ITD-39.2",), ("scirust-hub",)),
        )
    )
