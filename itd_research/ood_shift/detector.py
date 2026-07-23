"""Shift-aware, per-axis OOD detection (research, Mission 6, H43).

Mission 5's near-OOD detector collapsed every deviation into a single global Mahalanobis
radius, so it could say *how far* a sample was but not *along which axis* -- and it
over-abstained. This detector keeps the global radius (for comparison) but adds a
**per-axis standardized deviation** view: for each feature channel it reports the
standardized distance from the in-distribution mean, a robust aggregate *severity*, and
an *attribution* (which channel drives the shift). H43 asks whether that per-axis view
localizes the shift axis and tracks severity better than the single global radius.

Experimental research; does not modify ``ITD V29.18``. Reuses the transparent
``itd_research.ood.reference`` fit (Mahalanobis / PCA residual / nearest sample).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.ood.reference import OODReference, fit_reference

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]
_EPS = 1.0e-12


@dataclass(frozen=True)
class ShiftReference:
    """In-distribution reference exposing a global radius and a per-axis view."""

    base: OODReference
    feature_names: tuple[str, ...]
    severity_k: int = 3

    def global_mahalanobis(self, x: FloatArray) -> FloatArray:
        """The Mission 5 single-radius score (for the H43 comparison)."""
        return self.base.mahalanobis(np.asarray(x, dtype=np.float64))

    def pca_residual(self, x: FloatArray) -> FloatArray:
        return self.base.pca_residual(np.asarray(x, dtype=np.float64))

    def nearest(self, x: FloatArray) -> FloatArray:
        return self.base.nearest_distance(np.asarray(x, dtype=np.float64))

    def per_axis_deviation(self, x: FloatArray) -> FloatArray:
        """Absolute standardized deviation per feature channel, shape (n, d)."""
        z = (np.asarray(x, dtype=np.float64) - self.base.mean) / self.base.std
        return np.abs(z)

    def severity(self, x: FloatArray) -> FloatArray:
        """Robust per-axis severity: mean of the top-k standardized deviations.

        Top-k (not max) resists a single noisy channel while still rising with a genuine
        multi-axis shift. It is monotone in shift magnitude by construction.
        """
        dev = self.per_axis_deviation(x)
        k = max(1, min(self.severity_k, dev.shape[1]))
        topk = np.sort(dev, axis=1)[:, -k:]
        return np.asarray(topk.mean(axis=1), dtype=np.float64)

    def attribution(self, x: FloatArray) -> IntArray:
        """Index of the most-shifted feature channel per sample (global cannot do this)."""
        dev = self.per_axis_deviation(x)
        return np.asarray(np.argmax(dev, axis=1), dtype=np.int64)

    def dominant_feature(self, x: FloatArray) -> list[str]:
        return [self.feature_names[i] for i in self.attribution(x)]


def fit_shift_reference(
    x: FloatArray, feature_names: tuple[str, ...], *,
    shrinkage: float = 0.1, variance_kept: float = 0.95, severity_k: int = 3,
) -> ShiftReference:
    """Fit the shift-aware reference on in-distribution features (train only)."""
    array = np.asarray(x, dtype=np.float64)
    if array.shape[1] != len(feature_names):
        raise ValueError("feature_names length must match the feature matrix width.")
    base = fit_reference(array, shrinkage=shrinkage, variance_kept=variance_kept)
    return ShiftReference(base, tuple(feature_names), severity_k=severity_k)


def monotone_separation(scores: FloatArray, levels: IntArray) -> float:
    """Fraction of correctly-ordered (lower-level, higher-level) score pairs.

    A rank-agreement measure between an OOD score and the *known* ordinal shift level of
    a progressive sweep (0 = in-distribution, increasing with severity). 1.0 means the
    score orders every cross-level pair correctly; 0.5 is chance. Ties in level are
    skipped; ties in score count as half. This is how H43 compares the per-axis severity
    against the global radius -- higher is a better severity localizer.
    """
    s = np.asarray(scores, dtype=np.float64)
    lv = np.asarray(levels, dtype=np.int64)
    concordant = 0.0
    total = 0
    for i in range(s.size):
        for j in range(s.size):
            if lv[i] < lv[j]:
                total += 1
                if s[i] < s[j]:
                    concordant += 1.0
                elif s[i] == s[j]:
                    concordant += 0.5
    return float(concordant / total) if total else float("nan")
