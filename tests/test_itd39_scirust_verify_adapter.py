from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity
from itd_research.scirust_verify_adapter import (
    ItdDossierBinding,
    SciRustVerifyDossierRef,
    VerifyClaimRef,
    VerifyClaimVerdict,
    VerifyOverallVerdict,
)


def _dossier(
    verdict: VerifyOverallVerdict,
    *,
    integrity_checked: bool = True,
) -> SciRustVerifyDossierRef:
    return SciRustVerifyDossierRef(
        source=SourceIdentity("Memorithm/SciRust-Verify", "verify-test"),
        run_id="run-1",
        bundle_sha256="a" * 64,
        report_sha256="b" * 64,
        plan_sha256="c" * 64,
        overall_verdict=verdict,
        claims=(
            VerifyClaimRef(
                claim_id="cargo-test",
                verdict=VerifyClaimVerdict.VERIFIED,
                required=True,
            ),
            VerifyClaimRef(
                claim_id="supply-chain",
                verdict=VerifyClaimVerdict.SKIPPED,
                required=False,
            ),
        ),
        limitations=("single-host execution",),
        integrity_checked=integrity_checked,
    )


def test_pass_with_gaps_is_not_flattened_to_clean_pass() -> None:
    dossier = _dossier(VerifyOverallVerdict.PASS_WITH_GAPS)

    assert dossier.clean_pass is False
    assert dossier.pass_with_gaps is True
    assert dossier.failed is False


def test_clean_pass_requires_integrity_check() -> None:
    dossier = _dossier(
        VerifyOverallVerdict.PASS,
        integrity_checked=False,
    )

    assert dossier.clean_pass is False


def test_binding_rejects_unchecked_integrity_when_required() -> None:
    binding = ItdDossierBinding(
        protocol_fingerprint="d" * 64,
        campaign_fingerprint="e" * 64,
        dossier=_dossier(
            VerifyOverallVerdict.PASS,
            integrity_checked=False,
        ),
    )

    with pytest.raises(ValueError, match="integrity was not checked"):
        binding.assert_integrity_checked()


def test_binding_preserves_nonclaim_boundary() -> None:
    binding = ItdDossierBinding(
        protocol_fingerprint="d" * 64,
        campaign_fingerprint="e" * 64,
        dossier=_dossier(VerifyOverallVerdict.PASS),
    )

    binding.assert_integrity_checked()
    assert binding.authorizes_scientific_conclusion is False
    assert binding.authorizes_formal_proof_claim is False


def test_claim_identifiers_must_be_unique() -> None:
    claim = VerifyClaimRef(
        claim_id="same",
        verdict=VerifyClaimVerdict.VERIFIED,
        required=True,
    )

    with pytest.raises(ValueError, match="claim identifiers"):
        SciRustVerifyDossierRef(
            source=SourceIdentity("Memorithm/SciRust-Verify", "verify-test"),
            run_id="run-1",
            bundle_sha256="a" * 64,
            report_sha256="b" * 64,
            plan_sha256="c" * 64,
            overall_verdict=VerifyOverallVerdict.PASS,
            claims=(claim, claim),
            limitations=(),
            integrity_checked=True,
        )
