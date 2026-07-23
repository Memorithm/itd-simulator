"""Leakage-safe grouped evaluation and the H17/H18/H21/H22 verdicts (research).

Frames are labelled positive iff the ITD-independent event is within a horizon; only
pre-event frames are kept (predicting onset, not detecting the merged/broken state).
Models are trained on the development split, thresholds calibrated on the calibration
split, and the final metrics computed once on the held-out split. The decisive test is
H18: does ``established + ITD`` beat ``established`` on held-out data, by a paired
grouped bootstrap of the AUC difference whose lower CI must clear a margin?
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.flows import HardRun
from itd_research.hard_prediction.models import LogisticRegression
from itd_research.prediction.evaluation import roc_auc

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]
_EPS = 1.0e-12


@dataclass(frozen=True)
class LabeledRun:
    seed: int
    family: str
    features: dict[str, FloatArray]
    labels: IntArray
    times: FloatArray
    event_time: float


def build_labeled(runs: list[HardRun], horizon_frames: int) -> list[LabeledRun]:
    """Pre-event frames labelled positive iff the event is within ``horizon_frames``."""
    out: list[LabeledRun] = []
    for run in runs:
        if run.event_frame is None or run.event_frame < 2:
            continue
        event = run.event_frame
        idx = np.arange(event)
        labels = ((event - idx) <= horizon_frames).astype(np.int64)
        feats = {name: run.features[name][:event] for name in run.features}
        out.append(
            LabeledRun(run.seed, run.family, feats, labels,
                       np.asarray(run.times[:event], dtype=np.float64), float(run.times[event]))
        )
    return out


def _matrix(runs: list[LabeledRun], names: tuple[str, ...]) -> tuple[FloatArray, IntArray]:
    x = np.column_stack([np.concatenate([r.features[n] for r in runs]) for n in names])
    y = np.concatenate([r.labels for r in runs])
    return x, y


def _standardize(train: FloatArray, other: FloatArray) -> tuple[FloatArray, FloatArray]:
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    return (train - mean) / std, (other - mean) / std


def pr_auc(scores: FloatArray, labels: IntArray) -> float:
    """Average precision (area under precision-recall), rank-based."""
    order = np.argsort(-scores, kind="mergesort")
    y = labels[order]
    tp: FloatArray = np.cumsum(y).astype(np.float64)
    fp: FloatArray = np.cumsum(1 - y).astype(np.float64)
    total_pos = int(np.sum(labels))
    if total_pos == 0:
        return float("nan")
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / total_pos
    recall_prev = np.concatenate([[0.0], recall[:-1]])
    return float(np.sum((recall - recall_prev) * precision))


def brier(scores: FloatArray, labels: IntArray) -> float:
    return float(np.mean((scores - labels) ** 2))


def _train_score(
    train: list[LabeledRun], test: list[LabeledRun], names: tuple[str, ...],
    model_ctor: Callable[[], object],
) -> tuple[FloatArray, IntArray, list[tuple[int, FloatArray, IntArray]]]:
    train_x, train_y = _matrix(train, names)
    mean = train_x.mean(axis=0)
    std = train_x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    model = model_ctor()
    model.fit((train_x - mean) / std, train_y.astype(np.float64))  # type: ignore[attr-defined]
    per_run: list[tuple[int, FloatArray, IntArray]] = []
    all_scores: list[FloatArray] = []
    all_labels: list[IntArray] = []
    for run in test:
        rx = np.column_stack([run.features[n] for n in names])
        scores = model.predict_proba((rx - mean) / std)  # type: ignore[attr-defined]
        per_run.append((run.seed, scores, run.labels))
        all_scores.append(scores)
        all_labels.append(run.labels)
    return np.concatenate(all_scores), np.concatenate(all_labels), per_run


def _grouped_bootstrap_auc_diff(
    per_run_base: list[tuple[int, FloatArray, IntArray]],
    per_run_aug: list[tuple[int, FloatArray, IntArray]],
    bootstrap: int, seed: int,
) -> tuple[float, float, float]:
    """Paired grouped bootstrap of AUC(aug) - AUC(base), resampling whole runs."""
    rng = np.random.default_rng(seed)
    n = len(per_run_base)
    diffs: list[float] = []
    for _ in range(bootstrap):
        pick = rng.integers(0, n, size=n)
        bs = roc_auc(np.concatenate([per_run_base[i][1] for i in pick]),
                     np.concatenate([per_run_base[i][2] for i in pick]))
        ag = roc_auc(np.concatenate([per_run_aug[i][1] for i in pick]),
                     np.concatenate([per_run_aug[i][2] for i in pick]))
        if not (np.isnan(bs) or np.isnan(ag)):
            diffs.append(ag - bs)
    if not diffs:
        return float("nan"), float("nan"), float("nan")
    arr = np.asarray(diffs)
    return float(np.mean(arr)), float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))


@dataclass(frozen=True)
class AddedValueResult:
    auc_base: float
    auc_augmented: float
    diff_mean: float
    diff_ci_low: float
    diff_ci_high: float
    margin: float
    verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "auc_base": self.auc_base, "auc_augmented": self.auc_augmented,
            "diff_mean": self.diff_mean, "diff_ci_low": self.diff_ci_low,
            "diff_ci_high": self.diff_ci_high, "margin": self.margin, "verdict": self.verdict,
        }


def added_value(
    dev: list[LabeledRun], holdout: list[LabeledRun],
    base_names: tuple[str, ...], augmented_names: tuple[str, ...],
    *, margin: float = 0.02, bootstrap: int = 2000, seed: int = 4242,
    model_ctor: Callable[[], object] = LogisticRegression,
) -> AddedValueResult:
    """H18: does established+ITD beat established on the held-out split (Gate H)?"""
    base_scores, base_labels, base_runs = _train_score(dev, holdout, base_names, model_ctor)
    aug_scores, aug_labels, aug_runs = _train_score(dev, holdout, augmented_names, model_ctor)
    auc_base = roc_auc(base_scores, base_labels)
    auc_aug = roc_auc(aug_scores, aug_labels)
    diff_mean, ci_low, ci_high = _grouped_bootstrap_auc_diff(base_runs, aug_runs, bootstrap, seed)
    if np.isnan(ci_low):
        verdict = "inconclusive"
    elif ci_low >= margin:
        verdict = "supported within tested scope"
    elif ci_high <= -margin:
        verdict = "not supported"  # ITD hurts
    else:
        verdict = "not supported"  # CI includes 0 / below margin -> no credible added value
    return AddedValueResult(auc_base, auc_aug, diff_mean, ci_low, ci_high, margin, verdict)


@dataclass(frozen=True)
class FeatureSetMetrics:
    name: str
    auc: float
    pr_auc: float
    brier: float
    auc_ci_low: float
    auc_ci_high: float

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name, "auc": self.auc, "pr_auc": self.pr_auc, "brier": self.brier,
            "auc_ci_low": self.auc_ci_low, "auc_ci_high": self.auc_ci_high,
        }


def _grouped_auc_ci(
    per_run: list[tuple[int, FloatArray, IntArray]], bootstrap: int, seed: int
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(per_run)
    vals: list[float] = []
    for _ in range(bootstrap):
        pick = rng.integers(0, n, size=n)
        val = roc_auc(np.concatenate([per_run[i][1] for i in pick]),
                      np.concatenate([per_run[i][2] for i in pick]))
        if not np.isnan(val):
            vals.append(val)
    if not vals:
        return float("nan"), float("nan")
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def feature_set_auc(
    dev: list[LabeledRun], holdout: list[LabeledRun], names: tuple[str, ...],
    model_ctor: Callable[[], object] = LogisticRegression,
) -> float:
    """Held-out ROC-AUC of a feature set (train on dev, score holdout)."""
    scores, labels, _ = _train_score(dev, holdout, names, model_ctor)
    return roc_auc(scores, labels)


def single_channel_aucs(
    dev: list[LabeledRun], holdout: list[LabeledRun], names: tuple[str, ...]
) -> dict[str, float]:
    """Per-channel held-out AUC (H25: which channels predict which event)."""
    return {name: feature_set_auc(dev, holdout, (name,)) for name in names}


def cross_solver_auc(
    train_family: list[LabeledRun], test_family: list[LabeledRun], names: tuple[str, ...]
) -> float:
    """H19: train on one solver family, score another (same feature space)."""
    return feature_set_auc(train_family, test_family, names)


def evaluate_feature_set(
    dev: list[LabeledRun], holdout: list[LabeledRun], name: str, names: tuple[str, ...],
    *, bootstrap: int = 2000, seed: int = 4242,
    model_ctor: Callable[[], object] = LogisticRegression,
) -> FeatureSetMetrics:
    scores, labels, per_run = _train_score(dev, holdout, names, model_ctor)
    ci_low, ci_high = _grouped_auc_ci(per_run, bootstrap, seed)
    return FeatureSetMetrics(
        name, roc_auc(scores, labels), pr_auc(scores, labels), brier(scores, labels), ci_low, ci_high
    )
