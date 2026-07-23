"""Python side of the Python<->Rust equivalence check (Mission 5 H36; Mission 6 H47).

The committed fixture ``itd-rs/fixtures/diagnostics.txt`` is the shared oracle: it holds
seven named velocity fields and, for each, the periodic-central-difference diagnostics
(enstrophy, vorticity RMS, localization, palinstrophy, vorticity flatness). The Rust crate
reproduces them within 1e-9 (``cargo test``), and here we confirm the Python reference
recomputes the same expected values from each field. Both sides matching the fixture
establishes Python<->Rust equivalence on the diagnostics subset. This test does not run
cargo and does not modify tracked files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _ROOT / "itd-rs" / "fixtures" / "diagnostics.txt"


def _diagnostics(u: np.ndarray, v: np.ndarray, h: float) -> tuple[float, ...]:
    dv_dx = (np.roll(v, -1, axis=1) - np.roll(v, 1, axis=1)) / (2.0 * h)
    du_dy = (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0)) / (2.0 * h)
    omega = dv_dx - du_dy
    m2 = float(np.mean(omega**2))
    m4 = float(np.mean(omega**4))
    enstrophy = 0.5 * m2
    rms = float(np.sqrt(max(m2, 0.0)))
    localization = (m4 / (m2 * m2) - 1.0) if m2 > 0.0 else 0.0
    flatness = (m4 / (m2 * m2)) if m2 > 0.0 else 0.0
    dw_dx = (np.roll(omega, -1, axis=1) - np.roll(omega, 1, axis=1)) / (2.0 * h)
    dw_dy = (np.roll(omega, -1, axis=0) - np.roll(omega, 1, axis=0)) / (2.0 * h)
    palinstrophy = 0.5 * float(np.mean(dw_dx**2 + dw_dy**2))
    return enstrophy, rms, localization, palinstrophy, flatness


def _parse_cases(lines: list[str]) -> list[tuple[str, np.ndarray, np.ndarray, float, list[float]]]:
    header = lines[0].split()
    assert header[0] == "CASES"
    count = int(header[1])
    cases = []
    i = 1
    while i < len(lines):
        assert lines[i].split()[0] == "CASE"
        name = lines[i].split()[1]
        ny, nx, h = lines[i + 1].split()
        ny, nx, h = int(ny), int(nx), float(h)
        u = np.array([float(x) for x in lines[i + 2].split()], dtype=np.float64).reshape(ny, nx)
        v = np.array([float(x) for x in lines[i + 3].split()], dtype=np.float64).reshape(ny, nx)
        expected = [float(x) for x in lines[i + 4].split()]
        cases.append((name, u, v, h, expected))
        i += 5
    assert len(cases) == count
    return cases


def test_python_reference_matches_committed_fixture() -> None:
    assert _FIXTURE.exists(), "run tools/rust/generate_diagnostics_fixture.py"
    cases = _parse_cases(_FIXTURE.read_text(encoding="utf-8").splitlines())
    assert len(cases) == 7  # the seven named fields
    for name, u, v, h, expected in cases:
        got = _diagnostics(u, v, h)
        for actual, target in zip(got, expected, strict=True):
            assert actual == pytest.approx(target, rel=1e-12, abs=1e-12), name


def test_fixture_is_regenerable_in_memory() -> None:
    # The generator's own fields/diagnostics reproduce the committed expected values,
    # so the fixture is not stale (without writing any file).
    from tools.rust.generate_diagnostics_fixture import FIELDS, diagnostics

    cases = _parse_cases(_FIXTURE.read_text(encoding="utf-8").splitlines())
    n = cases[0][1].shape[0]
    h = 2.0 * np.pi / n
    for name, _u, _v, _h, expected in cases:
        u, v = FIELDS[name](n)
        u = np.ascontiguousarray(np.asarray(u, dtype=np.float64) * np.ones((n, n)))
        v = np.ascontiguousarray(np.asarray(v, dtype=np.float64) * np.ones((n, n)))
        got = diagnostics(u, v, h)
        for actual, target in zip(got, expected, strict=True):
            assert actual == pytest.approx(target, rel=1e-12, abs=1e-12), name
