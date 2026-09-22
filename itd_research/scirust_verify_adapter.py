"""ITD-39.2 SciRust-Verify evidence-dossier adapter.

SciRust-Verify owns evidence normalization, integrity, scope and verification
verdicts. ITD preserves those verdicts exactly and adds only protocol/campaign
linkage needed for ITD research interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from itd_research.experiment_schema import SourceIdentity


class VerifyOverallVerdict(StrEnum):
    PASS = "PASS"
    PASS_WITH_GAPS = "PASS_WITH_GAPS"
    FAIL = "FAIL"


class VerifyClaimVerdict(StrEnum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    NOT_VERIFIED = "NOT_VERIFIED"
    SKIPPED = "SKIPPED"
    UNSUPPORTED = "UNSUPPORTED"


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class VerifyClaimRef:
    """One preserved claim evaluation from a SciRust-Verify dossier."""

    claim_id: str
    verdict: VerifyClaimVerdict
    required: bool

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty.")


@dataclass(frozen=True)
class SciRustVerifyDossierRef:
    """Exact identity and preserved verdicts of one finalized evidence dossier."""

    source: SourceIdentity
    run_id: str
    bundle_sha256: str
    report_sha256: str
    plan_sha256: str
    overall_verdict: VerifyOverallVerdict
    claims: tuple[VerifyClaimRef, ...]
    limitations: tuple[str, ...]
    integrity_checked: bool

    def __post_init__(self) -> None:
        if self.source.source != "Memorithm/SciRust-Verify":
            raise ValueError("dossier source must be Memorithm/SciRust-Verify.")
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty.")
        for field_name in ("bundle_sha256", "report_sha256", "plan_sha256"):
            object.__setattr__(
                self,
                field_name,
                _validate_sha256(field_name, getattr(self, field_name)),
            )
        claim_ids = tuple(claim.claim_id for claim in self.claims)
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("claim identifiers must be unique.")
        if any(not limitation.strip() for limitation in self.limitations):
            raise ValueError("limitations must not contain empty entries.")

    @property
    def clean_pass(self) -> bool:
        return self.integrity_checked and self.overall_verdict is VerifyOverallVerdict.PASS

    @property
    def pass_with_gaps(self) -> bool:
        return (
            self.integrity_checked
            and self.overall_verdict is VerifyOverallVerdict.PASS_WITH_GAPS
        )

    @property
    def failed(self) -> bool:
        return self.overall_verdict is VerifyOverallVerdict.FAIL


@dataclass(frozen=True)
class ItdDossierBinding:
    """Bind one preserved dossier to exact ITD protocol/campaign identities."""

    protocol_fingerprint: str
    campaign_fingerprint: str
    dossier: SciRustVerifyDossierRef

    def __post_init__(self) -> None:
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

    def assert_integrity_checked(self) -> None:
        if not self.dossier.integrity_checked:
            raise ValueError("SciRust-Verify dossier integrity was not checked.")

    @property
    def authorizes_scientific_conclusion(self) -> bool:
        """Verification evidence never owns ITD scientific interpretation."""

        return False

    @property
    def authorizes_formal_proof_claim(self) -> bool:
        """Execution evidence is empirical, not formal proof."""

        return False
