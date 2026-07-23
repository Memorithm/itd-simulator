"""Interpretable, deterministic classifiers for the hard-prediction study (research).

Regularized logistic regression (primary, IRLS + ridge), linear discriminant
analysis, and a shallow CART decision tree (secondary). All are NumPy-only, seeded,
and expose a common ``fit`` / ``predict_proba`` interface. Normalization is the
caller's responsibility and must use training statistics only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

_EPS = 1.0e-12


def _sigmoid(z: FloatArray) -> FloatArray:
    return np.asarray(1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0))), dtype=np.float64)


@dataclass
class LogisticRegression:
    """IRLS logistic regression with an L2 ridge (intercept unpenalized)."""

    ridge: float = 1.0e-3
    iters: int = 40
    weights: FloatArray = field(default_factory=lambda: np.zeros(0))

    def fit(self, x: FloatArray, y: FloatArray) -> LogisticRegression:
        design = np.column_stack([np.ones(x.shape[0]), x])
        weights = np.zeros(design.shape[1], dtype=np.float64)
        penalty = self.ridge * np.eye(design.shape[1])
        penalty[0, 0] = 0.0
        for _ in range(self.iters):
            mu = _sigmoid(design @ weights)
            w_diag = np.clip(mu * (1.0 - mu), 1.0e-6, None)
            gradient = design.T @ (mu - y) + self.ridge * np.concatenate([[0.0], weights[1:]])
            hessian = design.T @ (design * w_diag[:, None]) + penalty
            try:
                step = np.linalg.solve(hessian, gradient)
            except np.linalg.LinAlgError:
                break
            weights -= step
            if float(np.max(np.abs(step))) < 1.0e-8:
                break
        self.weights = weights
        return self

    def predict_proba(self, x: FloatArray) -> FloatArray:
        design = np.column_stack([np.ones(x.shape[0]), x])
        return _sigmoid(design @ self.weights)


@dataclass
class LinearDiscriminant:
    """Two-class LDA; posterior via the Gaussian discriminant with pooled covariance."""

    shrinkage: float = 1.0e-3
    _w: FloatArray = field(default_factory=lambda: np.zeros(0))
    _b: float = 0.0

    def fit(self, x: FloatArray, y: FloatArray) -> LinearDiscriminant:
        pos = x[y == 1]
        neg = x[y == 0]
        if pos.shape[0] == 0 or neg.shape[0] == 0:
            self._w = np.zeros(x.shape[1])
            self._b = 0.0
            return self
        mu1, mu0 = pos.mean(axis=0), neg.mean(axis=0)
        cov = np.cov(x, rowvar=False)
        cov = np.atleast_2d(cov) + self.shrinkage * np.eye(x.shape[1])
        inv = np.linalg.pinv(cov)
        self._w = inv @ (mu1 - mu0)
        prior = np.log(max(pos.shape[0], 1) / max(neg.shape[0], 1))
        self._b = float(-0.5 * (mu1 + mu0) @ self._w + prior)
        return self

    def predict_proba(self, x: FloatArray) -> FloatArray:
        return _sigmoid(x @ self._w + self._b)


@dataclass
class _Node:
    feature: int = -1
    threshold: float = 0.0
    left: _Node | None = None
    right: _Node | None = None
    value: float = 0.5


@dataclass
class DecisionTree:
    """Shallow CART (Gini) for probability estimation; depth-limited, deterministic."""

    max_depth: int = 3
    min_samples: int = 8
    _root: _Node = field(default_factory=_Node)

    def fit(self, x: FloatArray, y: FloatArray) -> DecisionTree:
        self._root = self._build(x, y, depth=0)
        return self

    def _build(self, x: FloatArray, y: FloatArray, depth: int) -> _Node:
        prob = float(np.mean(y)) if y.size else 0.5
        node = _Node(value=prob)
        if depth >= self.max_depth or y.size < 2 * self.min_samples or len(set(y.tolist())) < 2:
            return node
        best_gini = 1.0
        best: tuple[int, float] | None = None
        for feature in range(x.shape[1]):
            values = np.unique(x[:, feature])
            if values.size < 2:
                continue
            midpoints = (values[:-1] + values[1:]) / 2.0
            for threshold in midpoints:
                left = x[:, feature] <= threshold
                if int(left.sum()) < self.min_samples or int((~left).sum()) < self.min_samples:
                    continue
                gini = self._weighted_gini(y[left], y[~left])
                if gini < best_gini:
                    best_gini, best = gini, (feature, float(threshold))
        if best is None:
            return node
        feature, threshold = best
        mask = x[:, feature] <= threshold
        node.feature, node.threshold = feature, threshold
        node.left = self._build(x[mask], y[mask], depth + 1)
        node.right = self._build(x[~mask], y[~mask], depth + 1)
        return node

    @staticmethod
    def _gini(y: FloatArray) -> float:
        if y.size == 0:
            return 0.0
        p = float(np.mean(y))
        return 1.0 - p**2 - (1.0 - p) ** 2

    def _weighted_gini(self, left: FloatArray, right: FloatArray) -> float:
        n = left.size + right.size
        return (left.size * self._gini(left) + right.size * self._gini(right)) / max(n, 1)

    def predict_proba(self, x: FloatArray) -> FloatArray:
        return np.array([self._predict_row(row) for row in x], dtype=np.float64)

    def _predict_row(self, row: FloatArray) -> float:
        node = self._root
        while node.feature >= 0 and node.left is not None and node.right is not None:
            node = node.left if row[node.feature] <= node.threshold else node.right
        return node.value


MODELS = {
    "logistic": LogisticRegression,
    "lda": LinearDiscriminant,
    "tree": DecisionTree,
}
