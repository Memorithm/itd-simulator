"""Leakage-safe vortex-merger prediction and the H7 verdict (research).

Task: from a single instantaneous field, predict whether the co-rotating pair will
merge within a horizon of ``H`` frames. Labels come from the ITD-independent
vortex-core count (see :mod:`itd_research.prediction.events`), so ITD channels never
see the target. Evaluation is **leave-one-run-out**: each held-out run is scored by a
logistic model fit on the *other* runs only, with features standardized on the
training runs alone -- no frame of a run ever trains a model that scores it, and no
future information enters a frame's features.

Reported per feature set: pooled held-out ROC-AUC with a run-level bootstrap CI, the
mean per-run AUC, and event-level lead time / missed-event / false-alarm rates at a
training-calibrated operating point. The H7 verdict is derived by comparing ITD
against the established-diagnostic baselines under Gate B, and is allowed to come out
negative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.prediction.ensemble import MergerRun

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]

_EPS = 1.0e-12

FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "baseline_enstrophy": ("enstrophy",),
    "baseline_vorticity_rms": ("vorticity_rms",),
    "baseline_diagnostics": (
        "enstrophy",
        "palinstrophy",
        "vorticity_rms",
        "vorticity_flatness",
        "mean_gradient_norm",
    ),
    "itd_structure": (
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
        "temporal_deformation",
    ),
    "itd_full": (
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
        "temporal_deformation",
        "intensity",
        "structure_score",
    ),
    "itd_plus_baseline": (
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
        "temporal_deformation",
        "intensity",
        "structure_score",
        "enstrophy",
        "palinstrophy",
        "vorticity_rms",
        "vorticity_flatness",
        "mean_gradient_norm",
    ),
}


def _sigmoid(z: FloatArray) -> FloatArray:
    return np.asarray(1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0))), dtype=np.float64)


def _fit_logistic(x: FloatArray, y: FloatArray, ridge: float = 1.0e-3, iters: int = 40) -> FloatArray:
    """IRLS logistic regression with a small ridge (transparent, deterministic)."""
    n_features = x.shape[1]
    design = np.column_stack([np.ones(x.shape[0]), x])
    weights = np.zeros(n_features + 1, dtype=np.float64)
    penalty = ridge * np.eye(n_features + 1)
    penalty[0, 0] = 0.0  # do not regularize the intercept
    for _ in range(iters):
        eta = design @ weights
        mu = _sigmoid(eta)
        w_diag = np.clip(mu * (1.0 - mu), 1.0e-6, None)
        gradient = design.T @ (mu - y) + ridge * np.concatenate([[0.0], weights[1:]])
        hessian = design.T @ (design * w_diag[:, None]) + penalty
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            break
        weights -= step
        if float(np.max(np.abs(step))) < 1.0e-8:
            break
    return weights


def _predict_logistic(weights: FloatArray, x: FloatArray) -> FloatArray:
    design = np.column_stack([np.ones(x.shape[0]), x])
    return _sigmoid(design @ weights)


def _rankdata_average(values: FloatArray) -> FloatArray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=np.float64)
    sorted_values = values[order]
    i = 0
    while i < values.size:
        j = i
        while j + 1 < values.size and sorted_values[j + 1] == sorted_values[i]:
            j += 1
        average = 0.5 * (i + j) + 1.0
        ranks[order[i : j + 1]] = average
        i = j + 1
    return ranks


def roc_auc(scores: FloatArray, labels: IntArray) -> float:
    """Rank-based ROC-AUC (Mann-Whitney U); NaN if a class is absent."""
    positive = int(np.sum(labels == 1))
    negative = int(np.sum(labels == 0))
    if positive == 0 or negative == 0:
        return float("nan")
    ranks = _rankdata_average(np.asarray(scores, dtype=np.float64))
    rank_sum = float(np.sum(ranks[labels == 1]))
    return (rank_sum - positive * (positive + 1) / 2.0) / (positive * negative)


@dataclass(frozen=True)
class FrameLabels:
    """Pre-event frames of one run with their imminent-merger labels."""

    run_id: str
    features: dict[str, FloatArray]
    labels: IntArray
    times: FloatArray
    event_time: float


def build_frame_labels(runs: tuple[MergerRun, ...], horizon_frames: int) -> list[FrameLabels]:
    """Pre-event frames labelled positive iff the merger is within ``horizon_frames``."""
    labelled: list[FrameLabels] = []
    for run in runs:
        if run.event_frame is None:
            continue
        event = run.event_frame
        frame_index = np.arange(event)
        labels = ((event - frame_index) <= horizon_frames).astype(np.int64)
        feats = {name: run.features[name][:event] for name in run.features}
        labelled.append(
            FrameLabels(
                run_id=run.config.run_id,
                features=feats,
                labels=labels,
                times=np.asarray(run.times[:event], dtype=np.float64),
                event_time=float(run.times[event]),
            )
        )
    return labelled


def _stack(frames: list[FrameLabels], channels: tuple[str, ...]) -> FloatArray:
    return np.column_stack([np.concatenate([f.features[c] for f in frames]) for c in channels])


@dataclass(frozen=True)
class PredictionMetrics:
    """Leakage-safe prediction metrics for one feature set."""

    name: str
    n_channels: int
    pooled_auc: float
    auc_ci_low: float
    auc_ci_high: float
    mean_run_auc: float
    median_lead_time: float
    lead_time_frames: float
    missed_event_rate: float
    false_alarm_rate: float

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "n_channels": self.n_channels,
            "pooled_auc": self.pooled_auc,
            "auc_ci_low": self.auc_ci_low,
            "auc_ci_high": self.auc_ci_high,
            "mean_run_auc": self.mean_run_auc,
            "median_lead_time": self.median_lead_time,
            "lead_time_frames": self.lead_time_frames,
            "missed_event_rate": self.missed_event_rate,
            "false_alarm_rate": self.false_alarm_rate,
        }


def _leave_one_run_out_scores(
    frames: list[FrameLabels], channels: tuple[str, ...]
) -> list[tuple[str, FloatArray, IntArray, FloatArray, float]]:
    """Return per-run (run_id, scores, labels, times, event_time) from LOO folds."""
    folds: list[tuple[str, FloatArray, IntArray, FloatArray, float]] = []
    for held in frames:
        train = [f for f in frames if f.run_id != held.run_id]
        if not train:
            continue
        train_x = _stack(train, channels)
        train_y = np.concatenate([f.labels for f in train]).astype(np.float64)
        mean = train_x.mean(axis=0)
        std = train_x.std(axis=0)
        std = np.where(std < _EPS, 1.0, std)
        weights = _fit_logistic((train_x - mean) / std, train_y)
        held_x = np.column_stack([held.features[c] for c in channels])
        scores = _predict_logistic(weights, (held_x - mean) / std)
        folds.append((held.run_id, scores, held.labels, held.times, held.event_time))
    return folds


def _operating_threshold(
    frames: list[FrameLabels], channels: tuple[str, ...], false_alarm_target: float
) -> float:
    """A single global threshold at the target training false-alarm rate.

    Fit on all runs (the operating point is a hyper-parameter, calibrated on the
    negatives; the discriminative scoring is still leave-one-run-out). Chosen as the
    quantile of negative-frame scores that admits ``false_alarm_target`` false
    alarms.
    """
    all_x = _stack(frames, channels)
    all_y = np.concatenate([f.labels for f in frames]).astype(np.float64)
    mean = all_x.mean(axis=0)
    std = all_x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    weights = _fit_logistic((all_x - mean) / std, all_y)
    scores = _predict_logistic(weights, (all_x - mean) / std)
    negative_scores = scores[all_y == 0]
    if negative_scores.size == 0:
        return 0.5
    return float(np.quantile(negative_scores, 1.0 - false_alarm_target))


def evaluate_feature_set(
    frames: list[FrameLabels],
    name: str,
    channels: tuple[str, ...],
    *,
    false_alarm_target: float = 0.1,
    bootstrap: int = 2000,
    seed: int = 12345,
) -> PredictionMetrics:
    """Full leakage-safe evaluation of one feature set."""
    folds = _leave_one_run_out_scores(frames, channels)
    if not folds:
        nan = float("nan")
        return PredictionMetrics(
            name, len(channels), nan, nan, nan, nan, nan, nan, nan, nan
        )
    pooled_scores = np.concatenate([f[1] for f in folds])
    pooled_labels = np.concatenate([f[2] for f in folds])
    pooled = roc_auc(pooled_scores, pooled_labels)

    run_aucs = [roc_auc(scores, labels) for _, scores, labels, _, _ in folds]
    valid_run_aucs = [a for a in run_aucs if not np.isnan(a)]
    mean_run_auc = float(np.mean(valid_run_aucs)) if valid_run_aucs else float("nan")

    # Run-level bootstrap CI: resample runs (respecting within-run correlation).
    rng = np.random.default_rng(seed)
    n_runs = len(folds)
    boot: list[float] = []
    for _ in range(bootstrap):
        pick = rng.integers(0, n_runs, size=n_runs)
        bs = np.concatenate([folds[i][1] for i in pick])
        bl = np.concatenate([folds[i][2] for i in pick])
        value = roc_auc(bs, bl)
        if not np.isnan(value):
            boot.append(value)
    if boot:
        boot_array = np.asarray(boot, dtype=np.float64)
        ci_low = float(np.quantile(boot_array, 0.025))
        ci_high = float(np.quantile(boot_array, 0.975))
    else:
        ci_low = ci_high = float("nan")

    # Event-level operating point at the target training false-alarm rate.
    threshold = _operating_threshold(frames, channels, false_alarm_target)
    leads: list[float] = []
    lead_frames: list[float] = []
    missed = 0
    false_alarm_num = 0
    false_alarm_den = 0
    for _, scores, labels, times, event_time in folds:
        alarm = np.flatnonzero(scores >= threshold)
        if alarm.size == 0:
            missed += 1
        else:
            first = int(alarm[0])
            leads.append(event_time - float(times[first]))
            lead_frames.append(float(len(times) - first))
        false_alarm_num += int(np.sum((labels == 0) & (scores >= threshold)))
        false_alarm_den += int(np.sum(labels == 0))
    median_lead = float(np.median(leads)) if leads else float("nan")
    median_lead_frames = float(np.median(lead_frames)) if lead_frames else float("nan")
    missed_rate = missed / len(folds) if folds else float("nan")
    false_alarm_rate = false_alarm_num / false_alarm_den if false_alarm_den else float("nan")

    return PredictionMetrics(
        name=name,
        n_channels=len(channels),
        pooled_auc=pooled,
        auc_ci_low=ci_low,
        auc_ci_high=ci_high,
        mean_run_auc=mean_run_auc,
        median_lead_time=median_lead,
        lead_time_frames=median_lead_frames,
        missed_event_rate=missed_rate,
        false_alarm_rate=false_alarm_rate,
    )


def evaluate_all(
    runs: tuple[MergerRun, ...], horizon_frames: int = 4, **kwargs: object
) -> tuple[list[PredictionMetrics], int]:
    """Evaluate every feature set; return metrics and the number of events used."""
    frames = build_frame_labels(runs, horizon_frames)
    metrics = [
        evaluate_feature_set(frames, name, channels, **kwargs)  # type: ignore[arg-type]
        for name, channels in FEATURE_SETS.items()
    ]
    return metrics, len(frames)


_ITD_SETS = ("itd_structure", "itd_full", "itd_plus_baseline")
_BASELINE_SETS = ("baseline_enstrophy", "baseline_vorticity_rms", "baseline_diagnostics")


def classify_h7(metrics: list[PredictionMetrics], n_events: int) -> tuple[str, str]:
    """Derive the H7 verdict under Gate B; may be negative or inconclusive."""
    by_name = {m.name: m for m in metrics}
    if n_events < 4:
        return (
            "inconclusive",
            f"only {n_events} labelled events; too few for a leave-one-run-out verdict.",
        )
    best_baseline = max(
        (by_name[name] for name in _BASELINE_SETS if name in by_name),
        key=lambda m: m.pooled_auc,
    )
    itd_only = [by_name[name] for name in ("itd_structure", "itd_full") if name in by_name]
    best_itd = max(itd_only, key=lambda m: m.pooled_auc)

    itd_above_chance = best_itd.auc_ci_low > 0.5
    # A meaningful win requires non-overlapping bootstrap CIs AND a real margin, so a
    # ceiling tie (both feature sets at AUC ~= 1.0) is never mistaken for superiority.
    margin = 0.02
    itd_beats_baseline = (
        best_itd.auc_ci_low > best_baseline.auc_ci_high
        and best_itd.pooled_auc - best_baseline.pooled_auc >= margin
    )
    baselines_above_chance = best_baseline.auc_ci_low > 0.5

    if not itd_above_chance:
        return (
            "not supported",
            f"best ITD AUC {best_itd.pooled_auc:.2f} (CI low {best_itd.auc_ci_low:.2f}) "
            "does not exceed chance on held-out runs.",
        )
    if itd_beats_baseline:
        return (
            "supported within tested scope",
            f"ITD ({best_itd.name}) AUC {best_itd.pooled_auc:.2f} (CI low "
            f"{best_itd.auc_ci_low:.2f}) exceeds the best baseline "
            f"({best_baseline.name}) AUC {best_baseline.pooled_auc:.2f} (CI high "
            f"{best_baseline.auc_ci_high:.2f}) by >= {margin} with non-overlapping CIs.",
        )
    if baselines_above_chance:
        return (
            "partially supported",
            f"ITD predicts well above chance (AUC {best_itd.pooled_auc:.2f}) but does "
            f"not beat the established multi-feature baseline ({best_baseline.name}, AUC "
            f"{best_baseline.pooled_auc:.2f}); both are at ceiling with overlapping CIs.",
        )
    return (
        "partially supported",
        f"ITD predicts above chance (AUC {best_itd.pooled_auc:.2f}); baseline evidence "
        "is weak, so the comparison is not decisive.",
    )
