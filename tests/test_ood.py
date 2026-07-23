"""Tests for OOD detection and abstention (H23)."""

from __future__ import annotations

import numpy as np

from itd_research.ood.abstention import (
    abstention_benefit,
    risk_coverage_curve,
    selective_evaluation,
)
from itd_research.ood.reference import fit_reference


def test_reference_scores_far_points_higher() -> None:
    rng = np.random.default_rng(0)
    in_dist = rng.normal(0.0, 1.0, size=(200, 5))
    reference = fit_reference(in_dist)
    near = reference.score(rng.normal(0.0, 1.0, size=(50, 5)))
    far = reference.score(np.full((50, 5), 20.0))
    assert float(np.mean(far)) > float(np.mean(near))
    assert float(np.mean(near)) < 10.0


def test_reference_scores_are_nonnegative_and_deterministic() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(100, 4))
    ref = fit_reference(x)
    s1 = ref.score(x)
    s2 = fit_reference(x).score(x)
    assert np.all(s1 >= 0.0)
    assert np.array_equal(s1, s2)
    assert np.all(ref.pca_residual(x) >= 0.0)
    assert np.all(ref.nearest_distance(x) >= 0.0)


def test_selective_evaluation_coverage_and_risk() -> None:
    score = np.array([0.1, 0.2, 5.0, 6.0])
    error = np.array([0.0, 0.0, 1.0, 1.0])
    is_ood = np.array([False, False, True, True])
    result = selective_evaluation(score, error, is_ood, threshold=1.0)
    assert result.coverage == 0.5
    assert result.in_domain_coverage == 1.0
    assert result.selective_risk == 0.0
    assert result.false_confidence_rate == 0.0


def test_abstention_benefit_reduces_risk_on_ood() -> None:
    # In-domain: low score, low error. OOD: high score, high error.
    score = np.concatenate([np.linspace(0.1, 1.0, 20), np.linspace(10.0, 20.0, 20)])
    error = np.concatenate([np.zeros(20), np.ones(20)])
    is_ood = np.concatenate([np.zeros(20, bool), np.ones(20, bool)])
    result, supported, verdict = abstention_benefit(score, error, is_ood)
    assert supported
    assert verdict == "supported within tested scope"
    assert result.selective_risk < result.full_risk
    assert result.in_domain_coverage >= 0.5
    curve = risk_coverage_curve(score, error)
    assert curve and all(0.0 <= c <= 1.0 for c, _ in curve)
