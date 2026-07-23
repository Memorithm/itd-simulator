"""Tests for the vortex-merger prediction study (H7)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.prediction.ensemble import quick_ensemble, simulate_merger_run
from itd_research.prediction.evaluation import (
    FEATURE_SETS,
    build_frame_labels,
    classify_h7,
    evaluate_all,
    roc_auc,
)
from itd_research.prediction.events import (
    count_vortex_cores,
    detect_merger_frame,
)


@pytest.fixture(scope="module")
def quick_runs() -> tuple:
    return tuple(
        simulate_merger_run(cfg, nodes=48, steps=1100, record_every=55, min_cells=8)
        for cfg in quick_ensemble()
    )


def _blob(center: tuple[float, float], nodes: int = 40, core: float = 0.15) -> np.ndarray:
    xs = np.linspace(0.0, 1.0, nodes)
    yy, xx = np.meshgrid(xs, xs, indexing="ij")
    cy, cx = center
    return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / core**2))


def test_count_vortex_cores_counts_separated_blobs() -> None:
    two = _blob((0.5, 0.3)) + _blob((0.5, 0.7))
    one = _blob((0.5, 0.5))
    assert count_vortex_cores(two, fraction=0.5, min_cells=5) == 2
    assert count_vortex_cores(one, fraction=0.5, min_cells=5) == 1
    assert count_vortex_cores(np.zeros((20, 20))) == 0


def test_detect_merger_frame_requires_persistent_single_core() -> None:
    assert detect_merger_frame((2, 2, 2, 1, 1, 1)) == 3
    assert detect_merger_frame((2, 2, 1, 2, 1, 1)) == 4  # transient dip ignored
    assert detect_merger_frame((2, 2, 2, 2)) is None  # never merges
    assert detect_merger_frame((1, 1, 1)) is None  # never multi-core


def test_roc_auc_perfect_and_chance() -> None:
    labels = np.array([0, 0, 1, 1], dtype=np.int64)
    assert roc_auc(np.array([0.1, 0.2, 0.8, 0.9]), labels) == pytest.approx(1.0)
    assert roc_auc(np.array([0.9, 0.8, 0.2, 0.1]), labels) == pytest.approx(0.0)
    assert np.isnan(roc_auc(np.array([0.5, 0.5]), np.array([1, 1], dtype=np.int64)))


def test_quick_ensemble_runs_merge_and_pipeline_is_deterministic(quick_runs: tuple) -> None:
    a = quick_runs[0]
    b = simulate_merger_run(
        quick_ensemble()[0], nodes=48, steps=1100, record_every=55, min_cells=8
    )
    assert a.event_frame is not None  # the quick config is tuned to merge
    for name in a.features:
        assert np.array_equal(a.features[name], b.features[name])  # deterministic


def test_evaluate_all_and_classify_are_leakage_safe_and_bounded(quick_runs: tuple) -> None:
    metrics, n_events = evaluate_all(quick_runs, horizon_frames=4, bootstrap=200)
    assert n_events == 3
    names = {m.name for m in metrics}
    assert names == set(FEATURE_SETS)
    for m in metrics:
        assert np.isnan(m.pooled_auc) or 0.0 <= m.pooled_auc <= 1.0
    verdict, _ = classify_h7(metrics, n_events)
    assert verdict == "inconclusive"  # 3 events is below the verdict threshold


def test_frame_labels_drop_post_event_and_label_by_horizon(quick_runs: tuple) -> None:
    frames = build_frame_labels(quick_runs[:1], horizon_frames=3)
    assert len(frames) == 1
    label = frames[0]
    event = quick_runs[0].event_frame
    assert event is not None
    assert label.labels.size == event  # only pre-event frames
    assert label.labels[-1] == 1  # the frame just before the event is positive
    assert label.labels[0] == 0  # the first frame is far from the event
