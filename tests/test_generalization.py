"""Tests for the cross-flow transfer / generalization studies (H8/H9/H10/H13)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.generalization.baselines import (
    BASELINE_FEATURES,
    baseline_features_on_subcube,
)
from itd_research.generalization.transfer import (
    classify_h9,
    classify_h10,
    classify_h13,
    component_transfer,
    family_generalization,
    sample_generalization,
    threshold_transfer,
)
from itd_research.spectral3d import spectral_grid_3d, taylor_green_velocity
from itd_research.validation_lab.flows import lab_flows


@pytest.fixture(scope="module")
def samples():  # type: ignore[no-untyped-def]
    return sample_generalization(lab_flows(nodes=16), subcubes_per_axis=2)


def test_baseline_features_present_and_finite() -> None:
    grid = spectral_grid_3d(16)
    u, v, w = taylor_green_velocity(grid)
    values = baseline_features_on_subcube(
        u, v, w, grid.coordinates, grid.coordinates, grid.coordinates, "finite"
    )
    assert tuple(values) == BASELINE_FEATURES
    assert all(np.isfinite(x) for x in values.values())
    assert 0.0 <= values["q_positive_fraction"] <= 1.0


def test_sampling_shapes_and_determinism(samples) -> None:  # type: ignore[no-untyped-def]
    n_flows = len(lab_flows(nodes=16))
    assert samples.itd_matrix.shape == (n_flows * 8, len(samples.itd_channels))
    assert samples.baseline_matrix.shape == (n_flows * 8, len(BASELINE_FEATURES))
    again = sample_generalization(lab_flows(nodes=16), subcubes_per_axis=2)
    assert np.array_equal(samples.itd_matrix, again.itd_matrix)


def test_family_generalization_bounded_and_verdict(samples) -> None:  # type: ignore[no-untyped-def]
    result = family_generalization(samples)
    assert 0.0 <= result.itd_balanced_accuracy <= 1.0
    assert 0.0 <= result.baseline_balanced_accuracy <= 1.0
    verdict, _ = classify_h13(result)
    assert verdict in {
        "supported within tested scope",
        "partially supported",
        "not supported",
    }


def test_component_transfer_reports_degradation(samples) -> None:  # type: ignore[no-untyped-def]
    transfers = [component_transfer(samples, t) for t in ("q_positive_fraction", "enstrophy")]
    for c in transfers:
        assert c.in_family_r2 <= 1.0 + 1e-9
        assert set(c.per_family_r2) <= set(samples.family_labels)
    verdict, _ = classify_h9(transfers)
    assert verdict in {"partially supported", "not supported", "inconclusive"}


def test_threshold_transfer_bounded_and_verdict(samples) -> None:  # type: ignore[no-untyped-def]
    transfers = [
        threshold_transfer(samples, "intensity", "itd"),
        threshold_transfer(samples, "enstrophy", "baseline"),
    ]
    for t in transfers:
        # accuracy is NaN only when a fold admits a single label class (degenerate).
        assert np.isnan(t.in_sample_accuracy) or 0.0 <= t.in_sample_accuracy <= 1.0
        assert np.isnan(t.transfer_accuracy) or 0.0 <= t.transfer_accuracy <= 1.0
    verdict, _ = classify_h10(transfers)
    assert verdict in {"supported within tested scope", "not supported", "inconclusive"}
