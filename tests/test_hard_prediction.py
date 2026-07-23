"""Tests for the Mission 4 hard-prediction framework (H17/H18/H21/H22)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.hard_prediction.degradation import DegradationSpec
from itd_research.hard_prediction.evaluation import (
    added_value,
    build_labeled,
    evaluate_feature_set,
    pr_auc,
)
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    HardRun,
    features_from_raw,
    simulate_merger_raw,
)
from itd_research.hard_prediction.models import (
    DecisionTree,
    LinearDiscriminant,
    LogisticRegression,
)
from itd_research.hard_prediction.protocol import (
    PREREGISTERED_SHA256,
    load_protocol,
    protocol_sha256,
)


def test_protocol_hash_matches_preregistration() -> None:
    assert protocol_sha256() == PREREGISTERED_SHA256
    protocol = load_protocol(strict=True)
    assert protocol.matches_preregistration()
    # Splits are disjoint (no seed appears in two splits).
    seeds = protocol.development_seeds + protocol.calibration_seeds + protocol.final_holdout_seeds
    assert len(seeds) == len(set(seeds))


def test_degradation_is_deterministic_and_shapes() -> None:
    rng = np.random.default_rng(0)
    u, v = rng.normal(size=(20, 24)), rng.normal(size=(20, 24))
    x, y = np.arange(24.0), np.arange(20.0)
    spec = DegradationSpec("d", noise=0.05, downsample_factor=2, mask_fraction=0.1)
    a = spec.apply(u, v, x, y, seed=3)
    b = spec.apply(u, v, x, y, seed=3)
    assert np.array_equal(a.u, b.u)  # deterministic
    assert a.u.shape == (10, 12)  # downsampled by 2
    crop = DegradationSpec("c", window="central_crop").apply(u, v, x, y, seed=1)
    assert crop.u.shape[0] < u.shape[0]


def test_models_bounded_and_deterministic() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(80, 4))
    y = (x[:, 0] + 0.5 * rng.normal(size=80) > 0).astype(np.float64)
    for ctor in (LogisticRegression, LinearDiscriminant, DecisionTree):
        model = ctor().fit(x, y)
        p = model.predict_proba(x)
        assert np.all((p >= 0.0) & (p <= 1.0))
        assert np.array_equal(p, ctor().fit(x, y).predict_proba(x))


def _synthetic_runs(n: int, seed: int) -> list[HardRun]:
    rng = np.random.default_rng(seed)
    runs = []
    for i in range(n):
        length = 12
        event = 9
        # features that ramp toward the event, plus noise
        base = np.linspace(0.0, 1.0, length) + 0.05 * rng.normal(size=length)
        feats = {name: base + 0.01 * j * rng.normal(size=length) for j, name in enumerate(ALL_FEATURES)}
        runs.append(HardRun(seed=seed * 100 + i, family="synthetic",
                            times=tuple(float(t) for t in range(length)), event_frame=event, features=feats))
    return runs


def test_build_labeled_is_leakage_safe_and_pre_event() -> None:
    runs = _synthetic_runs(3, 7)
    labeled = build_labeled(runs, horizon_frames=3)
    for lab in labeled:
        assert lab.labels.size == 9  # only pre-event frames
        assert lab.labels[-1] == 1 and lab.labels[0] == 0


def test_added_value_and_metrics_bounded() -> None:
    dev = build_labeled(_synthetic_runs(4, 1), horizon_frames=3)
    holdout = build_labeled(_synthetic_runs(4, 2), horizon_frames=3)
    m = evaluate_feature_set(dev, holdout, "all", ALL_FEATURES, bootstrap=100)
    assert np.isnan(m.auc) or 0.0 <= m.auc <= 1.0
    value = added_value(dev, holdout, ALL_FEATURES[:6], ALL_FEATURES, bootstrap=100)
    assert value.verdict in {"supported within tested scope", "not supported", "inconclusive"}


def test_pr_auc_perfect() -> None:
    labels = np.array([0, 0, 1, 1], dtype=np.int64)
    assert pr_auc(np.array([0.1, 0.2, 0.8, 0.9]), labels) == pytest.approx(1.0)


def test_merger_run_produces_event_and_degrades() -> None:
    raw = simulate_merger_raw(90, nodes=56, steps=2000, record_every=100)
    assert raw.event_frame is not None
    clean = features_from_raw(raw)
    noisy = features_from_raw(raw, DegradationSpec("n", noise=0.05))
    assert set(clean.features) == set(ALL_FEATURES)
    # degradation changes the features but keeps the (independent) event label
    assert clean.event_frame == noisy.event_frame
    assert not np.array_equal(clean.features["intensity"], noisy.features["intensity"])
