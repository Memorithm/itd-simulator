"""Deterministic velocity-field degradations for robustness tests (research, H21/H22).

Every degradation is a pure, seeded function of a 2D velocity field: additive
measurement-like noise, quantization, spatial smoothing, random/structured masking,
downsampling with an anti-alias pre-filter, and partial-domain windows. The original
external field remains the evidence source; degradations are applied at
feature-extraction time so the same run can be scored at several difficulty levels.
Masks are returned so downstream diagnostics can honour invalid vectors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]


@dataclass(frozen=True)
class DegradedField:
    """A degraded velocity field with its validity mask and coordinates."""

    u: FloatArray
    v: FloatArray
    x: FloatArray
    y: FloatArray
    valid: BoolArray


def _scale(u: FloatArray, v: FloatArray) -> float:
    return float(np.sqrt(np.mean(u**2 + v**2)) + 1e-12)


def add_noise(u: FloatArray, v: FloatArray, fraction: float, seed: int) -> tuple[FloatArray, FloatArray]:
    """Additive Gaussian noise at ``fraction`` of the RMS speed (seeded)."""
    if fraction <= 0.0:
        return u, v
    rng = np.random.default_rng(seed)
    sigma = fraction * _scale(u, v)
    return u + rng.normal(0.0, sigma, u.shape), v + rng.normal(0.0, sigma, v.shape)


def quantize(u: FloatArray, v: FloatArray, levels: int) -> tuple[FloatArray, FloatArray]:
    """Uniformly quantize each component into ``levels`` bins over its range."""
    if levels <= 0:
        return u, v

    def q(field: FloatArray) -> FloatArray:
        lo, hi = float(field.min()), float(field.max())
        if hi - lo < 1e-12:
            return field
        step = (hi - lo) / levels
        return lo + np.round((field - lo) / step) * step

    return q(u), q(v)


def smooth(u: FloatArray, v: FloatArray, passes: int) -> tuple[FloatArray, FloatArray]:
    """Deterministic 3x3 box smoothing applied ``passes`` times (reflect edges)."""

    def one(field: FloatArray) -> FloatArray:
        padded = np.pad(field, 1, mode="reflect")
        acc = np.zeros_like(field)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                acc += padded[1 + di : 1 + di + field.shape[0], 1 + dj : 1 + dj + field.shape[1]]
        return acc / 9.0

    for _ in range(max(passes, 0)):
        u, v = one(u), one(v)
    return u, v


def random_mask(shape: tuple[int, int], fraction: float, seed: int) -> BoolArray:
    """Random validity mask: ``fraction`` of nodes marked invalid (seeded)."""
    valid: BoolArray = np.ones(shape, dtype=bool)
    if fraction <= 0.0:
        return valid
    rng = np.random.default_rng(seed)
    invalid = rng.random(shape) < fraction
    valid[invalid] = False
    return valid


def downsample(
    u: FloatArray, v: FloatArray, x: FloatArray, y: FloatArray, factor: int
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Anti-aliased decimation by ``factor`` (box pre-filter then stride)."""
    if factor <= 1:
        return u, v, x, y
    us, vs = smooth(u, v, passes=1)  # simple anti-alias pre-filter
    return (
        np.ascontiguousarray(us[::factor, ::factor]),
        np.ascontiguousarray(vs[::factor, ::factor]),
        np.ascontiguousarray(x[::factor]),
        np.ascontiguousarray(y[::factor]),
    )


def window(
    u: FloatArray, v: FloatArray, x: FloatArray, y: FloatArray, name: str
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Return a partial-domain view (axis0=y, axis1=x)."""
    ny, nx = u.shape
    if name == "full":
        return u, v, x, y
    if name == "upstream_half":
        sl = (slice(None), slice(0, nx // 2))
        return u[sl], v[sl], x[: nx // 2], y
    if name == "downstream_half":
        sl = (slice(None), slice(nx // 2, nx))
        return u[sl], v[sl], x[nx // 2 :], y
    if name == "central_crop":
        sy, sx = slice(ny // 4, 3 * ny // 4), slice(nx // 4, 3 * nx // 4)
        return u[sy, sx], v[sy, sx], x[nx // 4 : 3 * nx // 4], y[ny // 4 : 3 * ny // 4]
    if name == "boundary_crop":
        sy, sx = slice(0, ny // 2), slice(0, nx)
        return u[sy, sx], v[sy, sx], x, y[: ny // 2]
    raise ValueError(f"unknown window {name!r}")


@dataclass(frozen=True)
class DegradationSpec:
    """A named, reproducible degradation configuration."""

    name: str
    noise: float = 0.0
    downsample_factor: int = 1
    mask_fraction: float = 0.0
    smooth_passes: int = 0
    window: str = "full"

    def apply(self, u: FloatArray, v: FloatArray, x: FloatArray, y: FloatArray, seed: int) -> DegradedField:
        u2, v2, x2, y2 = window(u, v, x, y, self.window)
        u2, v2, x2, y2 = downsample(u2, v2, x2, y2, self.downsample_factor)
        u2, v2 = smooth(u2, v2, self.smooth_passes)
        u2, v2 = add_noise(u2, v2, self.noise, seed)
        valid = random_mask(u2.shape, self.mask_fraction, seed + 1)
        return DegradedField(np.ascontiguousarray(u2), np.ascontiguousarray(v2), x2, y2, valid)
