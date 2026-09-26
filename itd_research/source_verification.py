"""ITD-30.4 source-byte and authorization-artifact verification.

Recording a SHA-256 identity is not verification. This module hashes actual
bytes and compares them to a declared digest. A matching authorization digest
is not a newly issued scientific permission.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from itd_research.campaign_runner import FinalEvaluationAuthorizationV1
from itd_research.experiment_schema import SourceIdentity


def digest_bytes(payload: bytes) -> str:
    """Return the SHA-256 hex digest of exact payload bytes."""

    return hashlib.sha256(payload).hexdigest()


def _validate_digest(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class SourceVerificationV1:
    """Observed byte hash for one declared source identity."""

    identity: SourceIdentity
    observed_sha256: str
    byte_count: int
    method: str = "sha256_bytes"
    verification_version: str = "itd-source-verification-v1"

    def __post_init__(self) -> None:
        if self.verification_version != "itd-source-verification-v1":
            raise ValueError("unsupported source verification version.")
        if self.method != "sha256_bytes":
            raise ValueError("unsupported source verification method.")
        if self.byte_count < 0:
            raise ValueError("byte_count must be non-negative.")
        object.__setattr__(
            self,
            "observed_sha256",
            _validate_digest("observed_sha256", self.observed_sha256),
        )

    def assert_matches_declared_identity(self) -> None:
        declared = self.identity.sha256
        if declared is None:
            raise ValueError("source identity has no declared sha256 to verify against.")
        if declared != self.observed_sha256:
            raise ValueError("observed source bytes do not match declared sha256.")

    def as_dict(self) -> dict[str, object]:
        return {
            "verification_version": self.verification_version,
            "identity": self.identity.as_dict(),
            "observed_sha256": self.observed_sha256,
            "byte_count": self.byte_count,
            "method": self.method,
        }


@dataclass(frozen=True)
class AuthorizationVerificationV1:
    """Observed byte hash for one recorded authorization identity."""

    authorization_sha256: str
    observed_sha256: str
    byte_count: int
    method: str = "sha256_bytes"
    verification_version: str = "itd-authorization-verification-v1"

    def __post_init__(self) -> None:
        if self.verification_version != "itd-authorization-verification-v1":
            raise ValueError("unsupported authorization verification version.")
        if self.method != "sha256_bytes":
            raise ValueError("unsupported authorization verification method.")
        if self.byte_count < 0:
            raise ValueError("byte_count must be non-negative.")
        object.__setattr__(
            self,
            "authorization_sha256",
            _validate_digest("authorization_sha256", self.authorization_sha256),
        )
        object.__setattr__(
            self,
            "observed_sha256",
            _validate_digest("observed_sha256", self.observed_sha256),
        )

    def assert_matches_declared_authorization(self) -> None:
        if self.authorization_sha256 != self.observed_sha256:
            raise ValueError("authorization artifact bytes do not match declared digest.")

    def as_dict(self) -> dict[str, object]:
        return {
            "verification_version": self.verification_version,
            "authorization_sha256": self.authorization_sha256,
            "observed_sha256": self.observed_sha256,
            "byte_count": self.byte_count,
            "method": self.method,
        }


def verify_source_bytes(identity: SourceIdentity, payload: bytes) -> SourceVerificationV1:
    """Hash payload bytes and require an exact match to the declared digest."""

    record = SourceVerificationV1(
        identity=identity,
        observed_sha256=digest_bytes(payload),
        byte_count=len(payload),
    )
    record.assert_matches_declared_identity()
    return record


def verify_source_path(identity: SourceIdentity, path: Path) -> SourceVerificationV1:
    """Read a regular file and verify its bytes against the declared digest."""

    resolved = path.expanduser()
    if resolved.is_symlink() or not resolved.is_file():
        raise ValueError("source path must be a regular file.")
    return verify_source_bytes(identity, resolved.read_bytes())


def verify_authorization_bytes(
    authorization: FinalEvaluationAuthorizationV1,
    payload: bytes,
) -> AuthorizationVerificationV1:
    """Hash authorization artifact bytes. Matching is not a permission grant."""

    record = AuthorizationVerificationV1(
        authorization_sha256=authorization.authorization_sha256,
        observed_sha256=digest_bytes(payload),
        byte_count=len(payload),
    )
    record.assert_matches_declared_authorization()
    return record
