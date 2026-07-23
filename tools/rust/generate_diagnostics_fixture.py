#!/usr/bin/env python3
"""Generate the Python<->Rust equivalence fixture for the ITD diagnostics subset.

Writes ``itd-rs/fixtures/diagnostics.txt`` with a deterministic smooth 2D velocity
field and the periodic-central-difference diagnostics (enstrophy, vorticity RMS,
localization) computed in Python. The Rust crate `itd-diagnostics` reads this fixture
and must reproduce the expected values within the preregistered tolerance (1e-9); the
Python test `tests/test_rust_equivalence.py` recomputes them and must match exactly.

Regenerate explicitly: ``python tools/rust/generate_diagnostics_fixture.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _ROOT / "itd-rs" / "fixtures" / "diagnostics.txt"


def smooth_field(n: int) -> tuple[np.ndarray, np.ndarray, float]:
    """A deterministic smooth periodic velocity field (axis0=y, axis1=x)."""
    length = 2.0 * np.pi
    h = length / n
    coords = np.arange(n, dtype=np.float64) * h
    x = coords[None, :]
    y = coords[:, None]
    u = np.sin(x) * np.cos(y) + 0.3 * np.cos(2.0 * x)
    v = -np.cos(x) * np.sin(y) + 0.2 * np.sin(3.0 * y)
    return np.ascontiguousarray(u), np.ascontiguousarray(v), h


def diagnostics(u: np.ndarray, v: np.ndarray, h: float) -> tuple[float, float, float]:
    """Periodic central-difference enstrophy, vorticity RMS, localization."""
    dv_dx = (np.roll(v, -1, axis=1) - np.roll(v, 1, axis=1)) / (2.0 * h)
    du_dy = (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0)) / (2.0 * h)
    omega = dv_dx - du_dy
    m2 = float(np.mean(omega**2))
    m4 = float(np.mean(omega**4))
    enstrophy = 0.5 * m2
    vorticity_rms = float(np.sqrt(max(m2, 0.0)))
    localization = (m4 / (m2 * m2) - 1.0) if m2 > 0.0 else 0.0
    return enstrophy, vorticity_rms, localization


def write_fixture(n: int = 24) -> Path:
    u, v, h = smooth_field(n)
    enstrophy, vorticity_rms, localization = diagnostics(u, v, h)
    lines = [
        f"{n} {n} {h!r}",
        " ".join(repr(float(x)) for x in u.ravel()),
        " ".join(repr(float(x)) for x in v.ravel()),
        f"{enstrophy!r} {vorticity_rms!r} {localization!r}",
    ]
    _FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    _FIXTURE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return _FIXTURE


if __name__ == "__main__":
    path = write_fixture()
    print(f"wrote {path}")
