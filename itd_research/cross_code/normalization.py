"""Competent feature normalizations for cross-code transfer (research, Mission 6).

The Mission 5 established diagnostics anti-transferred (AUC ~0.03) because they are
scale/amplitude-dependent across numerical methods, while ITD channels are dimensionless
ratios. These normalizers make an established baseline *competent* by removing absolute
scale, so the honest question becomes: does ITD still transfer better once the baseline
is normalized? All normalizations are leakage-safe (per-run, or fit on the training
source only) and never use holdout labels.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.flows import HardRun

FloatArray: TypeAlias = NDArray[np.float64]
_EPS = 1.0e-12

# Normalization methods applied to each run's per-frame feature trajectory.
METHODS = ("raw", "per_run_zscore", "per_run_rank", "per_run_minmax")


def _per_run_zscore(x: FloatArray) -> FloatArray:
    mean = float(np.mean(x))
    std = float(np.std(x))
    return (x - mean) / std if std > _EPS else x - mean


def _per_run_rank(x: FloatArray) -> FloatArray:
    order = np.argsort(np.argsort(x, kind="mergesort"))
    return (order.astype(np.float64) + 0.5) / max(x.size, 1)


def _per_run_minmax(x: FloatArray) -> FloatArray:
    lo, hi = float(np.min(x)), float(np.max(x))
    return (x - lo) / (hi - lo) if hi - lo > _EPS else np.zeros_like(x)


_FUNCS = {
    "raw": lambda x: x,
    "per_run_zscore": _per_run_zscore,
    "per_run_rank": _per_run_rank,
    "per_run_minmax": _per_run_minmax,
}


def normalize_run(run: HardRun, method: str) -> HardRun:
    """Return a new run whose per-frame features are normalized within the run.

    ``per_run_*`` methods remove the run's absolute scale/amplitude (which differs
    between codes), keeping only the trajectory shape -- the fair competent-baseline
    transform. ``raw`` is the identity (the Mission 5 reference).
    """
    if method not in _FUNCS:
        raise ValueError(f"unknown normalization {method!r}; choose from {METHODS}")
    func = _FUNCS[method]
    normalized = {name: np.asarray(func(values), dtype=np.float64) for name, values in run.features.items()}
    return HardRun(run.seed, run.family, run.times, run.event_frame, normalized)


def normalize_runs(runs: list[HardRun], method: str) -> list[HardRun]:
    return [normalize_run(run, method) for run in runs]
