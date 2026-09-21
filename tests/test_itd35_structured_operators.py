from __future__ import annotations

import numpy as np
import pytest

from itd_research.structured_operators import (
    apply_structured_mixer,
    causal_toeplitz_weights,
)


def test_causal_toeplitz_reference_is_normalized_and_causal() -> None:
    weights = causal_toeplitz_weights(np.array([1.0, 0.5, 0.25]), 5)

    assert weights.shape == (5, 5)
    assert np.allclose(weights.sum(axis=1), 1.0)
    assert np.allclose(np.triu(weights, k=1), 0.0)
    assert weights[4, 4] / weights[4, 3] == pytest.approx(2.0)
    assert weights[4, 3] / weights[4, 2] == pytest.approx(2.0)


def test_structured_mixer_applies_reference_weights() -> None:
    weights = causal_toeplitz_weights(np.array([1.0, 1.0]), 3)
    values = np.array([[1.0], [3.0], [9.0]])

    output = apply_structured_mixer(weights, values)

    assert output[:, 0] == pytest.approx([1.0, 2.0, 6.0])


def test_causal_toeplitz_rejects_missing_current_mass() -> None:
    with pytest.raises(ValueError, match="positive mass"):
        causal_toeplitz_weights(np.array([0.0, 1.0]), 3)
