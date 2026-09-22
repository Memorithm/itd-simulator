"""Versioned result/evidence contracts for ITD-3X experiments.

The result layer binds observed outcomes to an immutable experiment protocol
fingerprint without reopening protocol selection.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import ExperimentProtocolV1, SourceIdentity


class StudyClass(StrEnum):
    """Scientific status of a study execution."""

    EXPLORATORY = "exploratory"
    CONFIRMATORY = "confirmatory"


class StudyOutcome(StrEnum):
    """Declared outcome classes for a completed or blocked study."""

    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"
    NEGATIVE = "negative"
    EQUIVALENT = "equivalent"
    POSITIVE = "positive"


@dataclass(frozen=True)
class AdapterIdentityV1:
    """Identity of one external ecosystem adapter."""

    ecosystem: str
    interface: str
    source: SourceIdentity

    def __post_init__(self) -> None:
        if not self.ecosystem.strip():
            raise ValueError("ecosystem must not be empty.")
        if not self.interface.strip():
            raise ValueError("interface must not be empty.")

    def as_dict(self) -> dict[str, object]:
        return {
            "ecosystem": self.ecosystem,
            "interface": self.interface,
            "source": self.source.as_dict(),
        }


@dataclass(frozen=True)
class CampaignIdentityV1:
    """Immutable campaign identity independent of observed values."""

    campaign_id: str
    protocol_fingerprint: str
    implementation: SourceIdentity
    adapters: tuple[AdapterIdentityV1, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "adapters", tuple(self.adapters))
        if not self.campaign_id.strip():
            raise ValueError("campaign_id must not be empty.")
        digest = self.protocol_fingerprint.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("protocol_fingerprint must be a SHA-256 hex digest.")
        object.__setattr__(self, "protocol_fingerprint", digest)

        identities = tuple(
            (adapter.ecosystem, adapter.interface, adapter.source.source, adapter.source.revision)
            for adapter in self.adapters
        )
        if len(set(identities)) != len(identities):
            raise ValueError("campaign adapters must be unique.")

    def assert_matches_protocol(self, protocol: ExperimentProtocolV1) -> None:
        """Check the protocol and implementation declared for this campaign."""
        if self.protocol_fingerprint != protocol.fingerprint():
            raise ValueError("campaign protocol fingerprint does not match protocol.")
        if self.implementation != protocol.implementation:
            raise ValueError("campaign implementation does not match protocol.")

    @classmethod
    def from_protocol(
        cls,
        campaign_id: str,
        protocol: ExperimentProtocolV1,
        *,
        implementation: SourceIdentity,
        adapters: tuple[AdapterIdentityV1, ...] = (),
    ) -> CampaignIdentityV1:
        return cls(
            campaign_id=campaign_id,
            protocol_fingerprint=protocol.fingerprint(),
            implementation=implementation,
            adapters=adapters,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "campaign_id": self.campaign_id,
            "protocol_fingerprint": self.protocol_fingerprint,
            "implementation": self.implementation.as_dict(),
            "adapters": [adapter.as_dict() for adapter in self.adapters],
        }

    def fingerprint(self) -> str:
        payload = json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MetricObservationV1:
    """One finite observed metric bound to a declared metric name."""

    name: str
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric observation name must not be empty.")
        if not self.unit.strip():
            raise ValueError("metric observation unit must not be empty.")
        if not math.isfinite(self.value):
            raise ValueError("metric observation value must be finite.")

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "value": self.value, "unit": self.unit}


@dataclass(frozen=True)
class ExperimentResultV1:
    """Observed result bound to immutable protocol and campaign identities."""

    experiment_id: str
    protocol_fingerprint: str
    campaign_fingerprint: str
    study_class: StudyClass
    outcome: StudyOutcome
    observations: tuple[MetricObservationV1, ...]
    limitations: tuple[str, ...] = ()
    result_version: str = "itd-ai-result-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "study_class", StudyClass(self.study_class))
        object.__setattr__(self, "outcome", StudyOutcome(self.outcome))
        object.__setattr__(self, "observations", tuple(self.observations))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must not be empty.")
        if self.result_version != "itd-ai-result-v1":
            raise ValueError("unsupported result version.")

        for field_name, digest in (
            ("protocol_fingerprint", self.protocol_fingerprint),
            ("campaign_fingerprint", self.campaign_fingerprint),
        ):
            lowered = digest.lower()
            if len(lowered) != 64 or any(char not in "0123456789abcdef" for char in lowered):
                raise ValueError(f"{field_name} must be a SHA-256 hex digest.")
            object.__setattr__(self, field_name, lowered)

        names = tuple(item.name for item in self.observations)
        if len(set(names)) != len(names):
            raise ValueError("metric observation names must be unique.")

        if self.outcome is StudyOutcome.BLOCKED and self.observations:
            raise ValueError("blocked studies must not report task metric observations.")

    def assert_matches_campaign(self, campaign: CampaignIdentityV1) -> None:
        """Check both campaign identity and its declared protocol binding.

        Also call assert_matches_protocol with the actual protocol to validate
        the experiment ID and metric declarations; a digest alone is not proof.
        """
        if self.campaign_fingerprint != campaign.fingerprint():
            raise ValueError("result campaign fingerprint does not match campaign.")
        if self.protocol_fingerprint != campaign.protocol_fingerprint:
            raise ValueError("result protocol fingerprint does not match campaign.")

    def assert_matches_protocol(self, protocol: ExperimentProtocolV1) -> None:
        if self.experiment_id != protocol.experiment_id:
            raise ValueError("result experiment_id does not match protocol.")
        if self.protocol_fingerprint != protocol.fingerprint():
            raise ValueError("result protocol fingerprint does not match protocol.")

        declared = {metric.name: metric.unit for metric in protocol.metrics}
        for observation in self.observations:
            if observation.name not in declared:
                raise ValueError(f"undeclared metric observation: {observation.name}")
            if observation.unit != declared[observation.name]:
                raise ValueError(
                    f"metric unit mismatch for {observation.name}: "
                    f"{observation.unit!r} != {declared[observation.name]!r}"
                )

    def as_dict(self) -> dict[str, object]:
        return {
            "result_version": self.result_version,
            "experiment_id": self.experiment_id,
            "protocol_fingerprint": self.protocol_fingerprint,
            "campaign_fingerprint": self.campaign_fingerprint,
            "study_class": self.study_class.value,
            "outcome": self.outcome.value,
            "observations": [item.as_dict() for item in self.observations],
            "limitations": list(self.limitations),
        }
