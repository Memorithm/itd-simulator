"""Python side of the Python<->Rust equivalence check (Mission 5, H36).

The committed fixture ``itd-rs/fixtures/diagnostics.txt`` is the shared oracle: the
Rust crate reproduces it within 1e-9 (``cargo test``), and here we confirm the Python
reference recomputes the same expected values from the fixture's own input. Both sides
matching the fixture establishes Python<->Rust equivalence on the diagnostics subset.
This test does not run cargo and does not modify tracked files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _ROOT / "itd-rs" / "fixtures" / "diagnostics.txt"


def _diagnostics(u: np.ndarray, v: np.ndarray, h: float) -> tuple[float, float, float]:
    dv_dx = (np.roll(v, -1, axis=1) - np.roll(v, 1, axis=1)) / (2.0 * h)
    du_dy = (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0)) / (2.0 * h)
    omega = dv_dx - du_dy
    m2 = float(np.mean(omega**2))
    m4 = float(np.mean(omega**4))
    return 0.5 * m2, float(np.sqrt(max(m2, 0.0))), (m4 / (m2 * m2) - 1.0 if m2 > 0.0 else 0.0)


def test_python_reference_matches_committed_fixture() -> None:
    assert _FIXTURE.exists(), "run tools/rust/generate_diagnostics_fixture.py"
    lines = _FIXTURE.read_text(encoding="utf-8").splitlines()
    ny, nx, h = (float(x) for x in lines[0].split())
    ny, nx = int(ny), int(nx)
    u = np.array([float(x) for x in lines[1].split()], dtype=np.float64).reshape(ny, nx)
    v = np.array([float(x) for x in lines[2].split()], dtype=np.float64).reshape(ny, nx)
    expected = [float(x) for x in lines[3].split()]
    got = _diagnostics(u, v, h)
    for actual, target in zip(got, expected, strict=True):
        assert actual == pytest.approx(target, rel=1e-12, abs=1e-12)


def test_fixture_is_regenerable_in_memory() -> None:
    # The generator's own field/diagnostics reproduce the committed expected values,
    # so the fixture is not stale (without writing any file).
    from tools.rust.generate_diagnostics_fixture import diagnostics, smooth_field

    lines = _FIXTURE.read_text(encoding="utf-8").splitlines()
    n = int(lines[0].split()[0])
    u, v, h = smooth_field(n)
    expected = [float(x) for x in lines[3].split()]
    got = diagnostics(u, v, h)
    for actual, target in zip(got, expected, strict=True):
        assert actual == pytest.approx(target, rel=1e-12, abs=1e-12)
