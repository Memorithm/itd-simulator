"""ITD-30.2 cross-repository adapter and evidence-envelope contracts.

These contracts bind exact external identities to ITD experiments while
preserving ownership boundaries.  They transport evidence metadata; they do not
transfer scientific verdicts, runtime-policy authority, or final-holdout access.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity


class EcosystemComponent(StrEnum):
    """Named Memorithm components with explicit ITD integration boundaries."""

    TDI = "Memorithm/TDI"
    FLAT_ATTENTION = "Memorithm/FLAT-ATTENTION"
    SCIRUST = "Memorithm/scirust"
    ELASTICXXX = "Memorithm/ElasticXxx"
    NEURAL_OPERATOR = "Memorithm/NeuralOperator"
    NOISELAB = "Memorithm/NoiseLab"
    FORGE = "Memorithm/Forge"
    SCIRUST_VERIFY = "Memorithm/SciRust-Verify"
    SCIRUST_HUB = "Memorithm/scirust-hub"


class AdapterDirection(StrEnum):
    """Direction of information flow relative to ITD Research Lab."""

    IMPORT = "import"
    EXPORT = "export"
    BIDIRECTIONAL = "bidirectional"


class EvidenceClass(StrEnum):
    """Declared evidence-strength category without an implied verdict."""

    SOFTWARE_ORACLE = "software_oracle"
    MANUFACTURED = "manufactured"
    CONTROLLED_SIMULATION = "controlled_simulation"
    PUBLIC_BENCHMARK = "public_benchmark"
    EXTERNAL_REAL_WORLD = "external_real_world"
    CROSS_SOURCE_REPLICATION = "cross_source_replication"
    CROSS_DOMAIN_REPLICATION = "cross_domain_replication"
    PROSPECTIVE_MEASUREMENT = "prospective_measurement"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class AdapterContractV1:
    """Versioned identity and ownership boundary for one ecosystem adapter."""

    adapter_id: str
    component: EcosystemComponent
    direction: AdapterDirection
    interface: str
    source: SourceIdentity
    semantics_owner: str
    input_schema: str
    output_schema: str
    contract_version: str = "itd-adapter-v1"

    def __post_init__(self) -> None:
        for name, value in (
            ("adapter_id", self.adapter_id),
            ("interface", self.interface),
            ("semantics_owner", self.semantics_owner),
            ("input_schema", self.input_schema),
            ("output_schema", self.output_schema),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty.")
        if self.contract_version != "itd-adapter-v1":
            raise ValueError("unsupported adapter contract version.")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "adapter_id": self.adapter_id,
            "component": self.component.value,
            "direction": self.direction.value,
            "interface": self.interface,
            "source": self.source.as_dict(),
            "semantics_owner": self.semantics_owner,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
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


@dataclass(frozen=True)
class EvidenceEnvelopeV1:
    """Tamper-evident metadata binding for evidence transferred across repos."""

    producer: EcosystemComponent
    producer_source: SourceIdentity
    protocol_fingerprint: str
    campaign_fingerprint: str
    adapter_fingerprint: str
    payload_sha256: str
    evidence_class: EvidenceClass
    scope: str
    limitations: tuple[str, ...] = ()
    envelope_version: str = "itd-evidence-envelope-v1"

    def __post_init__(self) -> None:
        if self.envelope_version != "itd-evidence-envelope-v1":
            raise ValueError("unsupported evidence envelope version.")
        if not self.scope.strip():
            raise ValueError("evidence scope must not be empty.")
        object.__setattr__(
            self,
            "protocol_fingerprint",
            _validate_sha256("protocol_fingerprint", self.protocol_fingerprint),
        )
        object.__setattr__(
            self,
            "campaign_fingerprint",
            _validate_sha256("campaign_fingerprint", self.campaign_fingerprint),
        )
        object.__setattr__(
            self,
            "adapter_fingerprint",
            _validate_sha256("adapter_fingerprint", self.adapter_fingerprint),
        )
        object.__setattr__(
            self,
            "payload_sha256",
            _validate_sha256("payload_sha256", self.payload_sha256),
        )
        if any(not limitation.strip() for limitation in self.limitations):
            raise ValueError("evidence limitations must not contain empty entries.")

    @property
    def authorizes_runtime_policy(self) -> bool:
        """Evidence transfer never authorizes downstream actuation."""

        return False

    @property
    def authorizes_final_holdout_access(self) -> bool:
        """Evidence transfer never grants access to protected final data."""

        return False

    def assert_adapter(self, adapter: AdapterContractV1) -> None:
        if self.adapter_fingerprint != adapter.fingerprint():
            raise ValueError("evidence envelope does not match adapter contract.")
        if self.producer is not adapter.component:
            raise ValueError("evidence producer does not match adapter component.")
        if self.producer_source != adapter.source:
            raise ValueError("evidence producer source does not match adapter source.")

    def as_dict(self) -> dict[str, object]:
        return {
            "envelope_version": self.envelope_version,
            "producer": self.producer.value,
            "producer_source": self.producer_source.as_dict(),
            "protocol_fingerprint": self.protocol_fingerprint,
            "campaign_fingerprint": self.campaign_fingerprint,
            "adapter_fingerprint": self.adapter_fingerprint,
            "payload_sha256": self.payload_sha256,
            "evidence_class": self.evidence_class.value,
            "scope": self.scope,
            "limitations": list(self.limitations),
        }

    def fingerprint(self) -> str:
        payload = json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
