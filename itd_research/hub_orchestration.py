"""ITD-39.3 SciRust Hub orchestration contracts.

The Hub owns component registration, capability discovery, execution
orchestration, immutable artifacts and provenance. ITD submits only frozen
campaign identities and interprets returned evidence outside the Hub.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity


class HubRunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class HubCampaignSubmission:
    """Frozen ITD campaign identity submitted to one registered Hub capability."""

    source: SourceIdentity
    component_id: str
    capability: str
    campaign_plan_fingerprint: str
    params_sha256: str
    maximum_parallelism: int
    maximum_attempts: int
    timeout_seconds: float

    def __post_init__(self) -> None:
        if self.source.source != "Memorithm/scirust-hub":
            raise ValueError("Hub submission source must be Memorithm/scirust-hub.")
        if not self.component_id.strip() or not self.capability.strip():
            raise ValueError("Hub component_id and capability must not be empty.")
        object.__setattr__(
            self,
            "campaign_plan_fingerprint",
            _validate_sha256(
                "campaign_plan_fingerprint",
                self.campaign_plan_fingerprint,
            ),
        )
        object.__setattr__(
            self,
            "params_sha256",
            _validate_sha256("params_sha256", self.params_sha256),
        )
        if self.maximum_parallelism <= 0:
            raise ValueError("maximum_parallelism must be positive.")
        if self.maximum_attempts <= 0:
            raise ValueError("maximum_attempts must be positive.")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be finite and positive.")


@dataclass(frozen=True)
class HubArtifactRef:
    """Immutable Hub artifact identity returned by a run."""

    artifact_id: str
    content_sha256: str

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id must not be empty.")
        object.__setattr__(
            self,
            "content_sha256",
            _validate_sha256("content_sha256", self.content_sha256),
        )


@dataclass(frozen=True)
class HubRunRecord:
    """ITD-facing record of one Hub run and its immutable outputs."""

    submission: HubCampaignSubmission
    run_id: str
    state: HubRunState
    attempt_count: int
    provenance_sha256: str
    artifacts: tuple[HubArtifactRef, ...]

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty.")
        if self.attempt_count <= 0:
            raise ValueError("attempt_count must be positive.")
        if self.attempt_count > self.submission.maximum_attempts:
            raise ValueError("attempt_count exceeds submission maximum_attempts.")
        object.__setattr__(
            self,
            "provenance_sha256",
            _validate_sha256("provenance_sha256", self.provenance_sha256),
        )
        artifact_ids = tuple(artifact.artifact_id for artifact in self.artifacts)
        if len(set(artifact_ids)) != len(artifact_ids):
            raise ValueError("Hub artifact identifiers must be unique.")
        if self.state is HubRunState.SUCCEEDED and not self.artifacts:
            raise ValueError("successful Hub runs must retain at least one artifact.")

    @property
    def authorizes_scientific_conclusion(self) -> bool:
        return False

    @property
    def claims_os_sandbox(self) -> bool:
        """The current Hub executor boundary is supervision, not containment."""

        return False
