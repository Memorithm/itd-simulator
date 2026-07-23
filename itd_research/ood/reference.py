"""Distance-based out-of-distribution reference (research, H23).

Fitted on the in-distribution feature matrix (train-only), it exposes three
transparent OOD scores per sample: Mahalanobis distance to the training mean under a
shrinkage covariance, the PCA reconstruction residual in a reduced basis, and the
distance to the nearest training sample. The primary score is the Mahalanobis
distance; the others are reported for cross-checking. Features are standardized with
training statistics only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
_EPS = 1.0e-9


@dataclass(frozen=True)
class OODReference:
    """In-distribution reference statistics for OOD scoring."""

    mean: FloatArray
    std: FloatArray
    inv_cov: FloatArray
    components: FloatArray  # PCA basis (rows), reduced
    train_z: FloatArray     # standardized training samples (for nearest-distance)

    def _standardize(self, x: FloatArray) -> FloatArray:
        return (np.asarray(x, dtype=np.float64) - self.mean) / self.std

    def mahalanobis(self, x: FloatArray) -> FloatArray:
        z = self._standardize(x)
        return np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", z, self.inv_cov, z), 0.0))

    def pca_residual(self, x: FloatArray) -> FloatArray:
        z = self._standardize(x)
        projected = z @ self.components.T @ self.components
        return np.sqrt(np.sum((z - projected) ** 2, axis=1))

    def nearest_distance(self, x: FloatArray) -> FloatArray:
        z = self._standardize(x)
        out = np.empty(z.shape[0], dtype=np.float64)
        for i in range(z.shape[0]):
            diff = self.train_z - z[i]
            out[i] = float(np.sqrt(np.min(np.sum(diff**2, axis=1))))
        return out

    def score(self, x: FloatArray) -> FloatArray:
        """Primary OOD score (Mahalanobis distance)."""
        return self.mahalanobis(x)


def fit_reference(x: FloatArray, shrinkage: float = 0.1, variance_kept: float = 0.95) -> OODReference:
    """Fit the OOD reference on in-distribution features (train only)."""
    array = np.asarray(x, dtype=np.float64)
    mean = array.mean(axis=0)
    std = array.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    z = (array - mean) / std
    cov = np.cov(z, rowvar=False)
    cov = np.atleast_2d(cov)
    # Ledoit-Wolf-style shrinkage toward the identity for a well-conditioned inverse.
    shrunk = (1.0 - shrinkage) * cov + shrinkage * np.eye(cov.shape[0])
    inv_cov = np.linalg.pinv(shrunk)
    eigvals, eigvecs = np.linalg.eigh(shrunk)
    order = np.argsort(eigvals)[::-1]
    eigvals, eigvecs = eigvals[order], eigvecs[:, order]
    fractions = np.cumsum(eigvals) / max(float(np.sum(eigvals)), _EPS)
    keep = int(np.searchsorted(fractions, variance_kept) + 1)
    keep = max(1, min(keep, eigvecs.shape[1]))
    components = eigvecs[:, :keep].T
    return OODReference(mean, std, inv_cov, np.ascontiguousarray(components), np.ascontiguousarray(z))
