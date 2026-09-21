"""ITD-35.x deterministic structured sequence-mixing references.

These operators are research controls for mechanistic experiments. They do not
modify ITD V29.18 and are not FLAT-ATTENTION execution kernels.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


def causal_toeplitz_weights(kernel: FloatArray, length: int) -> FloatArray:
    """Build a causal lower-triangular Toeplitz mixing matrix.

    kernel[lag] is the non-negative weight assigned to a key lag steps
    behind the query. Each non-empty row is normalized independently.
    """

    kernel_array: FloatArray = np.asarray(kernel, dtype=np.float64)
    if kernel_array.ndim != 1 or kernel_array.size == 0:
        raise ValueError("kernel must be a non-empty one-dimensional array.")
    if length < 1:
        raise ValueError("length must be positive.")
    if not np.all(np.isfinite(kernel_array)):
        raise ValueError("kernel must contain only finite values.")
    if np.any(kernel_array < 0.0):
        raise ValueError("kernel weights must be non-negative.")
    if not np.any(kernel_array > 0.0):
        raise ValueError("kernel must contain positive mass.")

    weights: FloatArray = np.zeros((length, length), dtype=np.float64)
    max_lag = int(kernel_array.size - 1)
    for query in range(length):
        first_key = max(0, query - max_lag)
        for key in range(first_key, query + 1):
            weights[query, key] = kernel_array[query - key]
        row_sum = float(np.sum(weights[query]))
        if row_sum <= 0.0:
            raise ValueError(
                "kernel must provide positive mass for every causal query row."
            )
        weights[query] /= row_sum
    return weights


def apply_structured_mixer(weights: FloatArray, values: FloatArray) -> FloatArray:
    """Apply an explicit row-normalized structured mixer to value vectors."""

    matrix: FloatArray = np.asarray(weights, dtype=np.float64)
    value_array: FloatArray = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("weights must be a square two-dimensional matrix.")
    if value_array.ndim != 2 or value_array.shape[0] != matrix.shape[1]:
        raise ValueError("values must contain one row per mixer key.")
    if not np.all(np.isfinite(matrix)) or not np.all(np.isfinite(value_array)):
        raise ValueError("weights and values must contain only finite values.")
    if np.any(matrix < 0.0):
        raise ValueError("structured mixer weights must be non-negative.")
    if not np.allclose(np.sum(matrix, axis=1), 1.0, rtol=0.0, atol=1.0e-12):
        raise ValueError("every structured mixer row must sum to one.")

    return np.asarray(matrix @ value_array, dtype=np.float64)
