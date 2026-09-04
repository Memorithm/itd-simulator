"""Versioned, leakage-safe experiment contracts for ITD AI research.

This module is research infrastructure only. It does not modify the frozen
ITD V29.18 core, define an attention mechanism, supply TDI observables, or turn
a diagnostic into an optimization objective. The contract exists so future AI
experiments can bind hypotheses, split roles, provenance, metrics, compute and
uncertainty before final evaluation.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum


class SplitRole(str, Enum):
    """Research-data role with final evaluation structurally separated."""

    DEVELOPMENT = "development"
    VALIDATION = "validation"
    FINAL = "final"


class MetricRole(str, Enum):
    """Declared role of one metric in an experiment."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DIAGNOSTIC = "diagnostic"


class MetricDirection(str, Enum):
    """Direction used only when a metric is an optimization objective."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    DESCRIPTIVE = "descriptive"


@dataclass(frozen=True)
class SourceIdentity:
    """Immutable identity for code, data, protocol, or an external artifact."""

    source: str
    revision: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty.")
        if not self.revision.strip():
            raise ValueError("revision must not be empty.")
        if self.sha256 is not None:
            digest = self.sha256.lower()
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("sha256 must contain exactly 64 hexadecimal characters.")
            object.__setattr__(self, "sha256", digest)

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "revision": self.revision,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class SplitIdentity:
    """Identity of one immutable development, validation, or final partition."""

    role: SplitRole
    source: SourceIdentity

    def as_dict(self) -> dict[str, object]:
        return {"role": self.role.value, "source": self.source.as_dict()}


@dataclass(frozen=True)
class HypothesisContract:
    """Preregistered hypothesis statement and its falsifiable comparison."""

    hypothesis_id: str
    statement: str
    comparison: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("hypothesis_id", self.hypothesis_id),
            ("statement", self.statement),
            ("comparison", self.comparison),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty.")

    def as_dict(self) -> dict[str, str]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "statement": self.statement,
            "comparison": self.comparison,
        }


@dataclass(frozen=True)
class MetricContract:
    """One metric declaration without observed values."""

    name: str
    role: MetricRole
    direction: MetricDirection
    unit: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name must not be empty.")
        if not self.unit.strip():
            raise ValueError("metric unit must not be empty.")
        if self.role is MetricRole.DIAGNOSTIC and self.direction is not MetricDirection.DESCRIPTIVE:
            raise ValueError("diagnostic metrics must remain descriptive.")

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "role": self.role.value,
            "direction": self.direction.value,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class ComputeBudget:
    """Explicit bounded compute quantity using a protocol-defined unit."""

    unit: str
    maximum: float

    def __post_init__(self) -> None:
        if not self.unit.strip():
            raise ValueError("compute-budget unit must not be empty.")
        if not math.isfinite(self.maximum) or self.maximum <= 0.0:
            raise ValueError("compute-budget maximum must be finite and positive.")

    def as_dict(self) -> dict[str, object]:
        return {"unit": self.unit, "maximum": self.maximum}


@dataclass(frozen=True)
class UncertaintyContract:
    """Declared uncertainty procedure; this class does not choose the method."""

    method: str
    confidence_level: float
    paired: bool

    def __post_init__(self) -> None:
        if not self.method.strip():
            raise ValueError("uncertainty method must not be empty.")
        if not math.isfinite(self.confidence_level) or not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must be finite and strictly between zero and one.")

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "confidence_level": self.confidence_level,
            "paired": self.paired,
        }


@dataclass(frozen=True)
class ExperimentProtocolV1:
    """Canonical non-result contract for one leakage-safe AI experiment."""

    experiment_id: str
    hypothesis: HypothesisContract
    implementation: SourceIdentity
    splits: tuple[SplitIdentity, ...]
    metrics: tuple[MetricContract, ...]
    compute_budget: ComputeBudget
    uncertainty: UncertaintyContract
    protocol_version: str = "itd-ai-experiment-v1"

    def __post_init__(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must not be empty.")
        if self.protocol_version != "itd-ai-experiment-v1":
            raise ValueError("unsupported experiment protocol version.")

        roles = tuple(split.role for split in self.splits)
        expected_roles = {SplitRole.DEVELOPMENT, SplitRole.VALIDATION, SplitRole.FINAL}
        if len(self.splits) != 3 or set(roles) != expected_roles:
            raise ValueError("exactly one development, validation, and final split is required.")

        source_keys = {
            (split.source.source, split.source.revision, split.source.sha256)
            for split in self.splits
        }
        if len(source_keys) != len(self.splits):
            raise ValueError("development, validation, and final split identities must differ.")

        metric_names = tuple(metric.name for metric in self.metrics)
        if not metric_names:
            raise ValueError("at least one metric is required.")
        if len(set(metric_names)) != len(metric_names):
            raise ValueError("metric names must be unique.")
        if not any(metric.role is MetricRole.PRIMARY for metric in self.metrics):
            raise ValueError("at least one primary metric is required.")

    def split(self, role: SplitRole) -> SplitIdentity:
        """Return the unique split identity for one declared role."""
        return next(split for split in self.splits if split.role is role)

    def assert_selection_allowed(self, role: SplitRole) -> None:
        """Forbid fitting, threshold selection, or search on the final split."""
        if role is SplitRole.FINAL:
            raise ValueError("final split cannot be used for fitting or selection.")

    def assert_final_evaluation(self, source: SourceIdentity) -> None:
        """Require final reporting to bind exactly to the preregistered final source."""
        if source != self.split(SplitRole.FINAL).source:
            raise ValueError("final evaluation source does not match the frozen final split.")

    def as_dict(self) -> dict[str, object]:
        """Return a canonical JSON-compatible protocol payload without results."""
        ordered_splits = tuple(sorted(self.splits, key=lambda split: split.role.value))
        return {
            "protocol_version": self.protocol_version,
            "experiment_id": self.experiment_id,
            "hypothesis": self.hypothesis.as_dict(),
            "implementation": self.implementation.as_dict(),
            "splits": [split.as_dict() for split in ordered_splits],
            "metrics": [metric.as_dict() for metric in self.metrics],
            "compute_budget": self.compute_budget.as_dict(),
            "uncertainty": self.uncertainty.as_dict(),
        }

    def canonical_json(self) -> str:
        """Serialize deterministically for cross-repository evidence binding."""
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def fingerprint(self) -> str:
        """SHA-256 identity of the complete preregistered protocol."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
