"""Channel dependence and redundancy statistics (research, H11).

Given a data matrix ``X`` of shape ``(n_samples, n_channels)`` these functions
quantify how much information the channels share: linear (Pearson, condition
number, variance-inflation factors, PCA), monotonic (Spearman), and nonlinear
(a binned mutual-information estimate, reported with its estimator caveat). The
point is to distinguish *linear independence*, *nonlinear dependence*, and
*predictive complementarity* -- a channel may be correlated yet still useful, so
nothing is dropped on global Pearson alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]

_EPS = 1.0e-12


def _standardize(matrix: FloatArray) -> FloatArray:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    scale = centered.std(axis=0, keepdims=True)
    scale = np.where(scale < _EPS, 1.0, scale)
    return centered / scale


def pearson_matrix(matrix: FloatArray) -> FloatArray:
    """Pearson correlation matrix of the columns of ``X``."""
    standardized = _standardize(np.asarray(matrix, dtype=np.float64))
    n = max(standardized.shape[0], 1)
    # _standardize uses the population std, so dividing by n yields unit diagonals.
    return np.asarray(standardized.T @ standardized / n, dtype=np.float64)


def _rankdata(column: FloatArray) -> FloatArray:
    order = np.argsort(column, kind="mergesort")
    ranks = np.empty(column.size, dtype=np.float64)
    ranks[order] = np.arange(1, column.size + 1, dtype=np.float64)
    return ranks


def spearman_matrix(matrix: FloatArray) -> FloatArray:
    """Spearman rank-correlation matrix of the columns of ``X``."""
    array = np.asarray(matrix, dtype=np.float64)
    ranked = np.column_stack([_rankdata(array[:, j]) for j in range(array.shape[1])])
    return pearson_matrix(ranked)


def condition_number(matrix: FloatArray) -> float:
    """Condition number of the correlation matrix (large = collinear channels)."""
    correlation = pearson_matrix(matrix)
    eigenvalues = np.linalg.eigvalsh(correlation)
    smallest = float(np.min(eigenvalues))
    largest = float(np.max(eigenvalues))
    if smallest <= _EPS:
        return float("inf")
    return largest / smallest


def variance_inflation_factors(matrix: FloatArray) -> FloatArray:
    """VIF per channel: ``1/(1 - R^2)`` from regressing each on the others."""
    array = _standardize(np.asarray(matrix, dtype=np.float64))
    n_channels = array.shape[1]
    vifs = np.ones(n_channels, dtype=np.float64)
    for j in range(n_channels):
        others = np.delete(array, j, axis=1)
        target = array[:, j]
        if others.shape[1] == 0:
            continue
        coefficients, residuals, _, _ = np.linalg.lstsq(others, target, rcond=None)
        prediction = others @ coefficients
        ss_res = float(np.sum((target - prediction) ** 2))
        ss_tot = float(np.sum(target**2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > _EPS else 0.0
        vifs[j] = 1.0 / (1.0 - r_squared) if r_squared < 1.0 - _EPS else float("inf")
    return vifs


def pca_explained_variance(matrix: FloatArray) -> FloatArray:
    """Fraction of variance per principal component of the standardized channels."""
    standardized = _standardize(np.asarray(matrix, dtype=np.float64))
    covariance = np.cov(standardized, rowvar=False)
    eigenvalues = np.linalg.eigvalsh(np.atleast_2d(covariance))[::-1]
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    total = float(np.sum(eigenvalues))
    if total <= _EPS:
        return np.zeros_like(eigenvalues)
    return np.asarray(eigenvalues / total, dtype=np.float64)


def mutual_information_pair(x: FloatArray, y: FloatArray, bins: int = 8) -> float:
    """Binned mutual-information estimate (nats) for two columns.

    A simple histogram estimator; sensitive to ``bins`` and sample size, so it is
    reported alongside its parameters and never treated as exact.
    """
    xi = np.asarray(x, dtype=np.float64)
    yi = np.asarray(y, dtype=np.float64)
    if xi.size < 4:
        return 0.0
    joint, _, _ = np.histogram2d(xi, yi, bins=bins)
    joint = joint / joint.sum() if joint.sum() > 0 else joint
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    nonzero = joint > 0
    outer = px @ py
    with np.errstate(divide="ignore", invalid="ignore"):
        contributions = joint[nonzero] * np.log(joint[nonzero] / outer[nonzero])
    return float(np.sum(contributions))


@dataclass(frozen=True)
class ChannelDependence:
    """A full channel-dependence summary for one data matrix."""

    channels: tuple[str, ...]
    n_samples: int
    pearson: FloatArray
    spearman: FloatArray
    vif: FloatArray
    condition_number: float
    pca_explained: FloatArray
    effective_rank: float
    max_abs_offdiag_pearson: float

    def redundant_channels(self, threshold: float = 5.0) -> tuple[str, ...]:
        """Channels whose VIF exceeds ``threshold`` (strong linear redundancy)."""
        return tuple(
            name for name, value in zip(self.channels, self.vif, strict=True) if value > threshold
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "channels": list(self.channels),
            "n_samples": self.n_samples,
            "pearson": self.pearson.tolist(),
            "spearman": self.spearman.tolist(),
            "vif": self.vif.tolist(),
            "condition_number": self.condition_number,
            "pca_explained": self.pca_explained.tolist(),
            "effective_rank": self.effective_rank,
            "max_abs_offdiag_pearson": self.max_abs_offdiag_pearson,
            "redundant_channels_vif_gt_5": list(self.redundant_channels()),
        }


def channel_dependence(matrix: FloatArray, channels: tuple[str, ...]) -> ChannelDependence:
    """Compute the full dependence summary for a channel data matrix."""
    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != len(channels):
        raise ValueError("matrix must be (n_samples, n_channels) matching channels.")
    pearson = pearson_matrix(array)
    explained = pca_explained_variance(array)
    # participation-ratio effective rank of the standardized channels
    effective_rank = (
        float((np.sum(explained) ** 2) / np.sum(explained**2)) if np.sum(explained**2) > _EPS else 0.0
    )
    offdiag = pearson - np.diag(np.diag(pearson))
    return ChannelDependence(
        channels=channels,
        n_samples=int(array.shape[0]),
        pearson=pearson,
        spearman=spearman_matrix(array),
        vif=variance_inflation_factors(array),
        condition_number=condition_number(array),
        pca_explained=explained,
        effective_rank=effective_rank,
        max_abs_offdiag_pearson=float(np.max(np.abs(offdiag))) if offdiag.size else 0.0,
    )
