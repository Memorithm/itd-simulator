#!/usr/bin/env python3
"""Generate the Python<->Rust equivalence fixture for the ITD diagnostics subset.

Writes ``itd-rs/fixtures/diagnostics.txt`` with SEVEN deterministic 2D velocity fields
(zero, rigid rotation, simple shear, Taylor-Green, Lamb-Oseen, vortex pair, noisy) and,
for each, the periodic-central-difference diagnostics computed in Python: enstrophy,
vorticity RMS, localization, palinstrophy, and vorticity flatness. The Rust crate
``itd-diagnostics`` reads this fixture and must reproduce every value within the
preregistered tolerance (1e-9); ``tests/test_rust_equivalence.py`` recomputes them and
must match. This is a clearly-defined PERIODIC subset of the ITD 2D diagnostics -- it is
NOT the certified V29.18 finite-boundary signature (structural_metrics / multiscale),
which remains Python-only and is never re-derived here.

Regenerate explicitly: ``python tools/rust/generate_diagnostics_fixture.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _ROOT / "itd-rs" / "fixtures" / "diagnostics.txt"
_TWO_PI = 2.0 * np.pi


def _grid(n: int) -> tuple[np.ndarray, np.ndarray, float]:
    h = _TWO_PI / n
    coords = np.arange(n, dtype=np.float64) * h
    return coords[None, :], coords[:, None], h  # x (cols), y (rows)


def zero_field(n: int) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((n, n)), np.zeros((n, n))


def rigid_rotation(n: int) -> tuple[np.ndarray, np.ndarray]:
    x, y, _ = _grid(n)
    u = -(y - np.pi) * np.ones((1, n))
    v = (x - np.pi) * np.ones((n, 1))
    return u, v


def simple_shear(n: int) -> tuple[np.ndarray, np.ndarray]:
    x, y, _ = _grid(n)
    return (y - np.pi) * np.ones((1, n)), np.zeros((n, n))


def taylor_green(n: int) -> tuple[np.ndarray, np.ndarray]:
    x, y, _ = _grid(n)
    return np.sin(x) * np.cos(y), -np.cos(x) * np.sin(y)


def _gaussian_vortex(x: np.ndarray, y: np.ndarray, cx: float, cy: float, core: float) -> tuple[np.ndarray, np.ndarray]:
    dx, dy = x - cx, y - cy
    r2 = dx * dx + dy * dy
    swirl = np.exp(-r2 / (2.0 * core * core))
    return -dy * swirl, dx * swirl


def lamb_oseen(n: int) -> tuple[np.ndarray, np.ndarray]:
    x, y, _ = _grid(n)
    return _gaussian_vortex(x * np.ones((n, 1)), y * np.ones((1, n)), np.pi, np.pi, 0.8)


def vortex_pair(n: int) -> tuple[np.ndarray, np.ndarray]:
    x, y, _ = _grid(n)
    xg, yg = x * np.ones((n, 1)), y * np.ones((1, n))
    u1, v1 = _gaussian_vortex(xg, yg, np.pi - 1.0, np.pi, 0.6)
    u2, v2 = _gaussian_vortex(xg, yg, np.pi + 1.0, np.pi, 0.6)
    return u1 + u2, v1 + v2


def noisy_field(n: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20240601)
    x, y, _ = _grid(n)
    base_u = np.sin(x) * np.cos(y)
    base_v = -np.cos(x) * np.sin(y)
    return base_u + 0.1 * rng.standard_normal((n, n)), base_v + 0.1 * rng.standard_normal((n, n))


FIELDS: dict[str, Callable[[int], tuple[np.ndarray, np.ndarray]]] = {
    "zero_field": zero_field,
    "rigid_rotation": rigid_rotation,
    "simple_shear": simple_shear,
    "taylor_green": taylor_green,
    "lamb_oseen": lamb_oseen,
    "vortex_pair": vortex_pair,
    "noisy_field": noisy_field,
}


def diagnostics(u: np.ndarray, v: np.ndarray, h: float) -> tuple[float, float, float, float, float]:
    """Periodic central-difference diagnostics: the reproduced 2D subset.

    Returns (enstrophy, vorticity_rms, localization, palinstrophy, vorticity_flatness).
    All use ``np.roll`` central differences, matching the Rust reference exactly.
    """
    dv_dx = (np.roll(v, -1, axis=1) - np.roll(v, 1, axis=1)) / (2.0 * h)
    du_dy = (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0)) / (2.0 * h)
    omega = dv_dx - du_dy
    m2 = float(np.mean(omega**2))
    m4 = float(np.mean(omega**4))
    enstrophy = 0.5 * m2
    vorticity_rms = float(np.sqrt(max(m2, 0.0)))
    localization = (m4 / (m2 * m2) - 1.0) if m2 > 0.0 else 0.0
    vorticity_flatness = (m4 / (m2 * m2)) if m2 > 0.0 else 0.0
    # Palinstrophy 0.5<|grad omega|^2>, same periodic central-difference operator.
    dw_dx = (np.roll(omega, -1, axis=1) - np.roll(omega, 1, axis=1)) / (2.0 * h)
    dw_dy = (np.roll(omega, -1, axis=0) - np.roll(omega, 1, axis=0)) / (2.0 * h)
    palinstrophy = 0.5 * float(np.mean(dw_dx**2 + dw_dy**2))
    return enstrophy, vorticity_rms, localization, palinstrophy, vorticity_flatness


def _format_field(values: np.ndarray) -> str:
    return " ".join(repr(float(x)) for x in values.ravel())


def write_fixture(n: int = 24) -> Path:
    _, _, h = _grid(n)
    lines = [f"CASES {len(FIELDS)}"]
    for name, builder in FIELDS.items():
        u, v = builder(n)
        u = np.ascontiguousarray(np.asarray(u, dtype=np.float64) * np.ones((n, n)))
        v = np.ascontiguousarray(np.asarray(v, dtype=np.float64) * np.ones((n, n)))
        diag = diagnostics(u, v, h)
        lines.append(f"CASE {name}")
        lines.append(f"{n} {n} {h!r}")
        lines.append(_format_field(u))
        lines.append(_format_field(v))
        lines.append(" ".join(repr(float(x)) for x in diag))
    _FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    _FIXTURE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return _FIXTURE


if __name__ == "__main__":
    path = write_fixture()
    print(f"wrote {path}")
