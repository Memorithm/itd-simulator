"""Deterministic manufactured 3D vortex fields for the Mission 8 oracles (section 13).

These are SOFTWARE / INTERPRETATION oracles, never external scientific evidence. Each
builder returns ``(u, v, w, x, y, z)`` on a periodic box so the region/topology/structural
machinery can be validated against a KNOWN ground truth before any external claim is made.

Array axis convention (matches ``velocity_gradient_3d``): shape ``(nz, ny, nx)`` -- axis 0
varies with z, axis 1 with y, axis 2 with x. Building a fixture with the wrong axis order
is exactly the "axis permutation" failure mode Mission 8's oracles exist to catch.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]

_TWO_PI = 2.0 * np.pi


def _grid(n: int) -> tuple[FloatArray, FloatArray, FloatArray]:
    coords = np.linspace(0.0, _TWO_PI, n, endpoint=False)
    return coords, coords, coords


def _gaussian_swirl_3d(
    x: FloatArray, y: FloatArray, z: FloatArray, cx: float, cy: float, core: float, circulation: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """A z-aligned smooth Gaussian-swirl vortex tube, shape (nz,ny,nx).

    ``u = -y * f(r)``, ``v = x * f(r)`` is divergence-free for ANY radial profile
    ``f(r)`` (the x/y derivatives cancel identically), so this is exactly incompressible
    regardless of the profile. ``f(r) = circulation * exp(-r^2 / (2 core^2))`` decays to
    (numerically) zero well inside the domain for a sensible ``core``, so periodic wrap
    never reintroduces a spurious high-vorticity tail (unlike an algebraic Lamb-Oseen
    ``1/r^2`` tail, which does wrap around on a small periodic box).
    """
    _zg, yg, xg = np.meshgrid(z, y, x, indexing="ij")
    dx, dy = xg - cx, yg - cy
    r2 = dx * dx + dy * dy
    swirl = circulation * np.exp(-r2 / (2.0 * core * core))
    u = -dy * swirl
    v = dx * swirl
    w = np.zeros_like(u)
    return u, v, w


def two_separated_vortices(n: int = 64, separation: float = 4.0, core: float = 0.16) -> tuple[FloatArray, ...]:
    """Oracle A: two well-separated same-sign vortex tubes -- expect two stable cores.

    ``separation`` / ``core`` >~ 25 keeps the pair's mutual induction from distorting
    either core's local Q-topology into sub-lobes; verified empirically (see
    ``tests/test_mission8_oracles.py``) to give exactly two simply-connected Q>0 regions.
    """
    x, y, z = _grid(n)
    center = np.pi
    u1, v1, w1 = _gaussian_swirl_3d(x, y, z, center - separation / 2, center, core, 3.0)
    u2, v2, w2 = _gaussian_swirl_3d(x, y, z, center + separation / 2, center, core, 3.0)
    return u1 + u2, v1 + v2, w1 + w2, x, y, z


def merging_pair_sequence(
    n: int = 64, n_frames: int = 8, core: float = 0.16, start_separation: float = 4.0,
) -> list[tuple[FloatArray, ...]]:
    """Oracle B: a pair that is well separated, then abruptly fully merged (known event).

    A step transition at the midpoint frame -- rather than a linear separation ramp -- is
    used deliberately: closing the gap gradually passes through an intermediate regime
    where the two cores' mutual induction distorts their local Q-topology into transient
    bridging sub-lobes (a real, physically plausible feature of close vortex interaction,
    but NOT the clean, single, known transition a controlled software oracle needs). The
    step gives an unambiguous ground truth: N frames at the well-separated count, then N
    frames at the fully-merged count, with the merger at a known frame.
    """
    x, y, z = _grid(n)
    center = np.pi
    half = n_frames // 2
    frames = []
    for i in range(n_frames):
        sep = start_separation if i < half else 0.0
        u1, v1, w1 = _gaussian_swirl_3d(x, y, z, center - sep / 2, center, core, 3.0)
        u2, v2, w2 = _gaussian_swirl_3d(x, y, z, center + sep / 2, center, core, 3.0)
        frames.append((u1 + u2, v1 + v2, w1 + w2, x, y, z))
    return frames


def splitting_pair_sequence(
    n: int = 64, n_frames: int = 8, core: float = 0.16, start_separation: float = 4.0,
) -> list[tuple[FloatArray, ...]]:
    """Oracle C: the time-reverse of the merger -- a single structure splits in two."""
    return list(reversed(merging_pair_sequence(n=n, n_frames=n_frames, core=core, start_separation=start_separation)))


def translate_field(u: FloatArray, v: FloatArray, w: FloatArray, shift: tuple[int, int, int]) -> tuple[FloatArray, ...]:
    """Oracle D: rigid translation via periodic roll (exact on a periodic grid).

    ``shift`` is ``(dz, dy, dx)``, matching the array's ``(nz, ny, nx)`` axis order.
    """
    axes = (0, 1, 2)
    return (np.roll(u, shift, axes), np.roll(v, shift, axes), np.roll(w, shift, axes))


def rotate_field_xy(u: FloatArray, v: FloatArray, w: FloatArray, k_quarter_turns: int) -> tuple[FloatArray, ...]:
    """Oracle E: a rigid 90-degree-multiple rotation in the x-y plane (axes 2 and 1).

    Both the sampling grid (spatial ``rot90`` over the y,x axes) and the velocity
    components (each 90-degree turn maps ``(u, v) -> (-v, u)``) are rotated by the same
    amount, as a rigid rotation requires. The z axis (axis 0) is untouched.
    """
    k = k_quarter_turns % 4
    ru = np.rot90(u, k=k, axes=(1, 2))
    rv = np.rot90(v, k=k, axes=(1, 2))
    rw = np.rot90(w, k=k, axes=(1, 2))
    for _ in range(k):
        ru, rv = -rv, ru
    return ru, rv, rw


def scale_amplitude(u: FloatArray, v: FloatArray, w: FloatArray, factor: float) -> tuple[FloatArray, ...]:
    """Oracle F: uniform velocity amplitude scaling."""
    return u * factor, v * factor, w * factor


def resolution_sweep_grids(base_n: int, factors: tuple[int, ...] = (1, 2, 4)) -> list[int]:
    """Oracle G: node counts for a resolution sweep of the same analytic field."""
    return [base_n * f for f in factors]


def apply_mask(u: FloatArray, v: FloatArray, w: FloatArray, fraction: float, seed: int) -> tuple[FloatArray, ...]:
    """Oracle H: zero out a deterministic random fraction of cells (occlusion)."""
    rng = np.random.default_rng(seed)
    keep = rng.random(u.shape) >= fraction
    return u * keep, v * keep, w * keep


def apply_noise(u: FloatArray, v: FloatArray, w: FloatArray, level: float, seed: int) -> tuple[FloatArray, ...]:
    """Oracle I: additive Gaussian noise scaled to the field's own RMS (event unchanged)."""
    rng = np.random.default_rng(seed)
    rms = float(np.sqrt(np.mean(u**2 + v**2 + w**2) / 3.0))
    scale = max(rms, 1e-9) * level
    return (u + rng.normal(0.0, scale, u.shape), v + rng.normal(0.0, scale, v.shape),
            w + rng.normal(0.0, scale, w.shape))


def pure_shear_control(n: int = 24, rate: float = 1.0) -> tuple[FloatArray, ...]:
    """Oracle J: uniform shear, no vortex core -- Q<=0 everywhere, zero regions expected."""
    x, y, z = _grid(n)
    _zg, yg, _xg = np.meshgrid(z, y, x, indexing="ij")
    u = rate * (yg - np.pi)
    v = np.zeros_like(u)
    w = np.zeros_like(u)
    return u, v, w, x, y, z


def write_synthetic_sequence(
    directory: str | Path, *, nodes: int = 24, n_frames: int = 16, seed: int = 0,
) -> Path:
    """Write a deterministic synthetic ``frame_*.npz`` sequence for OFFLINE CI (Mission 8).

    A known controlled merger (built on :func:`merging_pair_sequence` with the ``core=0.16``/
    ``start_separation=4.0`` values empirically validated at ``n=64`` in the Oracle A/B tests,
    seed-perturbed so different calls are not byte-identical) plus small deterministic noise.
    ``nodes`` defaults to 24, NOT the ``n=64`` used to validate a clean two-region topology:
    at 24 nodes the two cores are under-resolved into several mutual-induction sub-lobes
    (region count ~6 rather than 2), but the pre/post-merger region COUNT is still stable and
    the merger transition itself is still clean and persistent -- sufficient for a fast,
    deterministic CI code-path exercise. CODE-VERIFICATION fixture ONLY -- never external
    evidence, and never used to claim "exactly two vortices" the way the Oracle A/B tests do.
    """
    base = Path(directory)
    base.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    core = 0.16 * float(rng.uniform(0.85, 1.15))
    start_separation = 4.0 * float(rng.uniform(0.9, 1.1))
    frames = merging_pair_sequence(n=nodes, n_frames=n_frames, core=core, start_separation=start_separation)
    for i, (u, v, w, x, y, z) in enumerate(frames):
        nu, nv, nw = apply_noise(u, v, w, level=0.005, seed=seed * 1000 + i)
        path = base / f"frame_{i:02d}.npz"
        np.savez(
            path, x=x.astype(np.float64), y=y.astype(np.float64), z=z.astype(np.float64),
            u=nu.astype(np.float64), v=nv.astype(np.float64), w=nw.astype(np.float64),
            time=np.array([0.1 * i], dtype=np.float64),
        )
    return base
