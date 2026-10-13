"""Supply-chain failure paths and supported interpreter coverage."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "wheel_lock", Path(__file__).resolve().parents[1] / "tools/lock_wheels.py"
)
assert SPEC is not None and SPEC.loader is not None
LOCK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCK)


def test_all_supported_interpreters_have_complete_exact_pin_inventory() -> None:
    manifest = json.loads(LOCK.MANIFEST.read_text())
    groups = [
        LOCK.pins(LOCK.ROOT / name)
        for name in (
            "requirements.lock",
            "requirements-dev.lock",
            "requirements-bootstrap.lock",
        )
    ]
    all_pins = [pin for group in groups for pin in group]
    for version in LOCK.VERSIONS:
        expected = {
            LOCK.distribution(pin) for pin in all_pins if LOCK.applies(pin, version)
        }
        selected = [
            row for row in manifest["wheels"] if version in row["python_versions"]
        ]
        assert len(selected) == len(expected)
        assert {(row["distribution"], row["version"]) for row in selected} == expected
        for row in selected:
            assert any(
                "--hash=sha256:" + row["sha256"] in (LOCK.ROOT / name).read_text()
                for name in (
                    "requirements.lock",
                    "requirements-dev.lock",
                    "requirements-bootstrap.lock",
                )
            )


def test_inventory_rejects_tampering_missing_extra_and_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filename = "example-1.0-py3-none-any.whl"
    payload = b"wheel bytes recorded by a producer"
    wheel = tmp_path / filename
    wheel.write_bytes(payload)
    manifest = tmp_path.parent / (tmp_path.name + ".json")
    manifest.write_text(
        json.dumps(
            {
                "wheels": [
                    {
                        "filename": filename,
                        "distribution": "example",
                        "version": "1.0",
                        "python_versions": ["3.12"],
                        "size_bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(LOCK, "MANIFEST", manifest)
    LOCK.verify(tmp_path, "3.12")
    wheel.write_bytes(b"x" * len(payload))
    with pytest.raises(ValueError, match="integrity"):
        LOCK.verify(tmp_path, "3.12")
    wheel.unlink()
    with pytest.raises(ValueError, match="inventory"):
        LOCK.verify(tmp_path, "3.12")
    wheel.write_bytes(payload)
    extra = tmp_path / "unrecorded.whl"
    extra.write_bytes(payload)
    with pytest.raises(ValueError, match="inventory"):
        LOCK.verify(tmp_path, "3.12")
    extra.unlink()
    wheel.unlink()
    wheel.symlink_to(manifest)
    with pytest.raises(ValueError, match="integrity"):
        LOCK.verify(tmp_path, "3.12")


def test_lock_parser_refuses_unpinned_or_arbitrary_requirements(tmp_path: Path) -> None:
    lock = tmp_path / "requirements.lock"
    for text in ("numpy>=2", "https://invalid.example/package.whl", "-e ../package"):
        lock.write_text(text)
        with pytest.raises(ValueError, match="Unsupported"):
            LOCK.pins(lock)
