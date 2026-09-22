from __future__ import annotations

import pytest

from itd_research.adapter_schema import (
    AdapterContractV1,
    AdapterDirection,
    EcosystemComponent,
    EvidenceClass,
    EvidenceEnvelopeV1,
)
from itd_research.experiment_schema import SourceIdentity


def _adapter() -> AdapterContractV1:
    return AdapterContractV1(
        adapter_id="tdi-trajectory-v1",
        component=EcosystemComponent.TDI,
        direction=AdapterDirection.IMPORT,
        interface="trajectory-records",
        source=SourceIdentity("Memorithm/TDI", "abc123"),
        semantics_owner="Memorithm/TDI",
        input_schema="tdi-trajectory-record-v1",
        output_schema="itd-trajectory-adapter-v1",
    )


def test_adapter_fingerprint_is_deterministic() -> None:
    left = _adapter()
    right = _adapter()

    assert left.canonical_json() == right.canonical_json()
    assert left.fingerprint() == right.fingerprint()
    assert len(left.fingerprint()) == 64


def test_evidence_envelope_preserves_ownership_boundaries() -> None:
    adapter = _adapter()
    envelope = EvidenceEnvelopeV1(
        producer=EcosystemComponent.TDI,
        producer_source=adapter.source,
        protocol_fingerprint="a" * 64,
        campaign_fingerprint="b" * 64,
        adapter_fingerprint=adapter.fingerprint(),
        payload_sha256="c" * 64,
        evidence_class=EvidenceClass.CONTROLLED_SIMULATION,
        scope="development-only deterministic trajectory fixture",
        limitations=("not confirmatory",),
    )

    envelope.assert_adapter(adapter)
    assert envelope.authorizes_runtime_policy is False
    assert envelope.authorizes_final_holdout_access is False
    assert len(envelope.fingerprint()) == 64


def test_evidence_envelope_rejects_adapter_mismatch() -> None:
    adapter = _adapter()
    envelope = EvidenceEnvelopeV1(
        producer=EcosystemComponent.TDI,
        producer_source=adapter.source,
        protocol_fingerprint="a" * 64,
        campaign_fingerprint="b" * 64,
        adapter_fingerprint="d" * 64,
        payload_sha256="c" * 64,
        evidence_class=EvidenceClass.SOFTWARE_ORACLE,
        scope="reference fixture",
    )

    with pytest.raises(ValueError, match="adapter contract"):
        envelope.assert_adapter(adapter)


def test_evidence_envelope_rejects_bad_digest() -> None:
    adapter = _adapter()

    with pytest.raises(ValueError, match="payload_sha256"):
        EvidenceEnvelopeV1(
            producer=EcosystemComponent.TDI,
            producer_source=adapter.source,
            protocol_fingerprint="a" * 64,
            campaign_fingerprint="b" * 64,
            adapter_fingerprint=adapter.fingerprint(),
            payload_sha256="not-a-digest",
            evidence_class=EvidenceClass.SOFTWARE_ORACLE,
            scope="fixture",
        )
