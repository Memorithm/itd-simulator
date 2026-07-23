"""Tests for the validation laboratory: statistics, candidates, ablation (H11/H12)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.validation_lab.ablation import evaluate_candidate
from itd_research.validation_lab.candidates import (
    CANDIDATES,
    channel_superset,
    evaluate_channels,
)
from itd_research.validation_lab.flows import lab_flows
from itd_research.validation_lab.sampling import sample_channels_from_flows
from itd_research.validation_lab.statistics import (
    channel_dependence,
    condition_number,
    mutual_information_pair,
    pca_explained_variance,
    pearson_matrix,
    variance_inflation_factors,
)


def test_pearson_matrix_perfect_correlation() -> None:
    x = np.linspace(0.0, 1.0, 50)
    matrix = np.column_stack([x, 2.0 * x + 1.0, -x])
    corr = pearson_matrix(matrix)
    assert corr[0, 1] == pytest.approx(1.0, abs=1e-9)
    assert corr[0, 2] == pytest.approx(-1.0, abs=1e-9)


def test_vif_high_for_collinear_columns() -> None:
    rng = np.random.default_rng(0)
    a = rng.normal(size=200)
    b = rng.normal(size=200)
    collinear = a + 1e-3 * rng.normal(size=200)
    matrix = np.column_stack([a, b, collinear])
    vif = variance_inflation_factors(matrix)
    assert vif[0] > 50.0 and vif[2] > 50.0  # a and its near-copy
    assert vif[1] < 2.0  # independent column


def test_condition_number_and_pca() -> None:
    rng = np.random.default_rng(1)
    independent = rng.normal(size=(300, 3))
    assert condition_number(independent) < 3.0
    explained = pca_explained_variance(independent)
    assert explained.sum() == pytest.approx(1.0, abs=1e-9)
    assert np.all(np.diff(explained) <= 1e-9)  # sorted descending


def test_mutual_information_independent_vs_dependent() -> None:
    rng = np.random.default_rng(2)
    x = rng.uniform(size=2000)
    y = rng.uniform(size=2000)
    assert mutual_information_pair(x, y, bins=8) < 0.05
    assert mutual_information_pair(x, x, bins=8) > 0.5  # identical -> high MI


def test_evaluate_channels_returns_superset() -> None:
    from itd_research.spectral3d import abc_flow_velocity, spectral_grid_3d

    grid = spectral_grid_3d(16)
    u, v, w = abc_flow_velocity(grid)
    values = evaluate_channels(u, v, w, grid.coordinates, grid.coordinates, grid.coordinates, "periodic")
    assert tuple(values) == channel_superset()
    assert all(np.isfinite(x) for x in values.values())


def test_candidate_vector_extraction() -> None:
    values = dict.fromkeys(channel_superset(), 0.0)
    values["stretching_rate"] = 2.0
    vector = CANDIDATES["C"].vector(values)
    assert vector.shape == (len(CANDIDATES["C"].channels),)


def test_sampling_is_deterministic_and_labelled() -> None:
    flows = lab_flows(nodes=16)
    a = sample_channels_from_flows(flows, subcubes_per_axis=2)
    b = sample_channels_from_flows(flows, subcubes_per_axis=2)
    assert np.array_equal(a.matrix, b.matrix)
    assert a.matrix.shape == (len(flows) * 8, len(channel_superset()))
    assert set(a.family_labels) <= {"laminar_coherent", "transitional", "turbulent"}


def test_channel_dependence_finds_nonredundant_3d_channels() -> None:
    flows = lab_flows(nodes=16)
    samples = sample_channels_from_flows(flows, subcubes_per_axis=2)
    dependence = channel_dependence(samples.matrix, samples.channels)
    vif = dict(zip(dependence.channels, dependence.vif, strict=True))
    # the genuinely-3D channels carry non-redundant information (low VIF)
    assert vif["stretching_rate"] < 3.0
    assert vif["normalized_helicity"] < 3.0
    assert 1.0 <= dependence.effective_rank <= len(dependence.channels)


def test_ablation_is_bounded_and_deterministic() -> None:
    flows = lab_flows(nodes=16)
    samples = sample_channels_from_flows(flows, subcubes_per_axis=2)
    r1 = evaluate_candidate(samples, CANDIDATES["A"])
    r2 = evaluate_candidate(samples, CANDIDATES["A"])
    assert 0.0 <= r1.balanced_accuracy <= 1.0
    assert r1.balanced_accuracy == r2.balanced_accuracy  # deterministic
    assert r1.channel_count == len(CANDIDATES["A"].channels)
