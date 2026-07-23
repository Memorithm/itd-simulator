"""Load and integrity-check the Mission 4 preregistered protocol (research).

The protocol is a machine-readable TOML whose SHA-256 is the preregistration
commitment. This module reads it, exposes the locked split seeds, and can assert the
file has not changed since preregistration -- the runtime guard behind the
"final_holdout is immutable" discipline. It never edits the protocol.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = _ROOT / "configs" / "mission4" / "preregistered_protocol.toml"

# The preregistration commitment recorded in the report/commit. If the protocol file
# is edited, this constant will no longer match and load_protocol(strict=True) fails.
PREREGISTERED_SHA256 = "b49049e02d28561326c170c32ae34055b9e712bfca8721eb09404fbd35e1523f"


def protocol_sha256(path: Path | None = None) -> str:
    """SHA-256 of the protocol file (the preregistration commitment)."""
    target = path or PROTOCOL_PATH
    return hashlib.sha256(target.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Protocol:
    """The locked decisions needed at runtime."""

    sha256: str
    development_seeds: tuple[int, ...]
    calibration_seeds: tuple[int, ...]
    final_holdout_seeds: tuple[int, ...]
    added_value_margin: float
    raw: dict[str, object]

    def matches_preregistration(self) -> bool:
        return self.sha256 == PREREGISTERED_SHA256


def load_protocol(path: Path | None = None, *, strict: bool = False) -> Protocol:
    """Load the protocol; if ``strict`` assert its hash matches preregistration."""
    target = path or PROTOCOL_PATH
    digest = protocol_sha256(target)
    if strict and digest != PREREGISTERED_SHA256:
        raise ValueError(
            "preregistered protocol has changed since commitment "
            f"(sha256 {digest} != {PREREGISTERED_SHA256}); final_holdout is immutable."
        )
    with target.open("rb") as handle:
        raw = tomllib.load(handle)
    splits = raw["splits"]
    assert isinstance(splits, dict)
    final = raw["final_holdout"]
    assert isinstance(final, dict)
    return Protocol(
        sha256=digest,
        development_seeds=tuple(int(s) for s in splits["development_seeds"]),
        calibration_seeds=tuple(int(s) for s in splits["calibration_seeds"]),
        final_holdout_seeds=tuple(int(s) for s in final["seeds"]),
        added_value_margin=float(final["added_value_margin"]),
        raw=raw,
    )
