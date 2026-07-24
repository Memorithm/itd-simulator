"""Grouped statistics, region metrics wrappers, and the saturation screen (Mission 8).

Independent units for bootstrap are DNS SEQUENCES, never individual frames (adjacent
frames are never treated as independent). Reused across prediction, transfer and
degradation so every H6x test shares one statistical protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.evaluation import pr_auc as _pr_auc
from itd_research.mission8.schema import TaskScreeningResult
from itd_research.prediction.evaluation import roc_auc

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]


def temporal_rate(values: list[float], times: list[float]) -> list[float]:
    """Centered finite difference of a scalar time series (forward/backward at the ends).

    Shared by ``structural_features`` (ITD_TEMPORAL) and ``baselines``
    (BASELINE_TEMPORAL) so both use the identical, deterministic definition.
    """
    v = np.asarray(values, dtype=np.float64)
    t = np.asarray(times, dtype=np.float64)
    n = v.size
    rate = np.zeros(n, dtype=np.float64)
    if n < 2:
        return rate.tolist()
    rate[0] = (v[1] - v[0]) / max(t[1] - t[0], 1e-12)
    rate[-1] = (v[-1] - v[-2]) / max(t[-1] - t[-2], 1e-12)
    for i in range(1, n - 1):
        rate[i] = (v[i + 1] - v[i - 1]) / max(t[i + 1] - t[i - 1], 1e-12)
    return rate.tolist()


def spearman_correlation(a: FloatArray, b: FloatArray) -> float:
    """Spearman rank correlation (NaN if either series is constant)."""
    if a.size < 2:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    if np.std(ra) < 1e-12 or np.std(rb) < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def pearson_correlation(a: FloatArray, b: FloatArray) -> float:
    """Pearson correlation (NaN if either series is constant)."""
    if a.size < 2 or np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def partial_correlation(a: FloatArray, b: FloatArray, control: FloatArray) -> float:
    """Pearson correlation of ``a`` and ``b`` after linearly regressing out ``control``.

    The standard non-redundancy check (H63): a channel correlated with a magnitude
    diagnostic will have LOW partial correlation with the event/target once the magnitude
    diagnostic's own linear effect is removed; a channel with genuinely independent
    information keeps a non-trivial partial correlation.
    """
    def residual(y: FloatArray) -> FloatArray:
        c = np.column_stack([np.ones_like(control), control])
        coeffs, *_ = np.linalg.lstsq(c, y, rcond=None)
        return y - c @ coeffs

    if a.size < 3 or np.std(control) < 1e-12:
        return float("nan")
    return pearson_correlation(residual(a), residual(b))


def saturation_screen(
    task_id: str, event_definition: str, established_scores: FloatArray, labels: IntArray,
    *, threshold: float = 0.98, select_if_unsaturated: bool = True,
) -> TaskScreeningResult:
    """Screen a candidate task on DEVELOPMENT data only (Mission 8 section 6).

    Uses ONLY established-only performance -- ITD is never consulted here. A saturated
    task (established AUC or PR-AUC >= threshold) is retained for descriptive/regression
    use but is never selected as the primary incremental-value test.
    """
    auc = roc_auc(established_scores, labels)
    pr = _pr_auc(established_scores, labels)
    saturated = (not np.isnan(auc) and auc >= threshold) or (not np.isnan(pr) and pr >= threshold)
    status = "saturated" if saturated else "unsaturated"
    selected = select_if_unsaturated and not saturated
    reason = (
        f"established dev AUC={auc:.3f} PR-AUC={pr:.3f} >= {threshold}: saturated, excluded from primary H62 test"
        if saturated else
        f"established dev AUC={auc:.3f} PR-AUC={pr:.3f} < {threshold}: unsaturated, eligible for primary H62 test"
    )
    return TaskScreeningResult(
        task_id=task_id, event_definition=event_definition,
        baseline_development_auc=float(auc), baseline_development_pr_auc=float(pr),
        saturation_status=status, selected_for_primary_test=selected, reason=reason,
    )


@dataclass(frozen=True)
class GroupedDiffResult:
    """Grouped-bootstrap difference of a metric between two feature sets."""

    diff_mean: float
    ci_low: float
    ci_high: float
    margin: float
    verdict: str

    def as_dict(self) -> dict[str, object]:
        return {"diff_mean": self.diff_mean, "ci_low": self.ci_low, "ci_high": self.ci_high,
                "margin": self.margin, "verdict": self.verdict}


def grouped_bootstrap_diff(
    per_unit_base: list[tuple[FloatArray, IntArray]],
    per_unit_aug: list[tuple[FloatArray, IntArray]],
    *, metric: str = "auc", margin: float = 0.02, bootstrap: int = 2000, seed: int = 6161,
) -> GroupedDiffResult:
    """Paired grouped bootstrap of metric(aug) - metric(base), resampling whole units.

    ``per_unit_*`` are (scores, labels) pairs, one per independent unit (sequence). Units
    are resampled with replacement so no adjacent-frame pair is ever treated as
    independent. ``metric`` is ``"auc"`` or ``"pr_auc"``.
    """
    scorer = roc_auc if metric == "auc" else _pr_auc
    rng = np.random.default_rng(seed)
    n = len(per_unit_base)
    if n == 0:
        return GroupedDiffResult(float("nan"), float("nan"), float("nan"), margin, "inconclusive")
    diffs: list[float] = []
    for _ in range(bootstrap):
        pick = rng.integers(0, n, size=n)
        base_scores = np.concatenate([per_unit_base[i][0] for i in pick])
        base_labels = np.concatenate([per_unit_base[i][1] for i in pick])
        aug_scores = np.concatenate([per_unit_aug[i][0] for i in pick])
        aug_labels = np.concatenate([per_unit_aug[i][1] for i in pick])
        base_metric = scorer(base_scores, base_labels)
        aug_metric = scorer(aug_scores, aug_labels)
        if not (np.isnan(base_metric) or np.isnan(aug_metric)):
            diffs.append(float(aug_metric - base_metric))
    if not diffs:
        return GroupedDiffResult(float("nan"), float("nan"), float("nan"), margin, "inconclusive")
    arr = np.asarray(diffs)
    mean, lo, hi = float(np.mean(arr)), float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))
    if lo >= margin:
        verdict = "supported within tested scope"
    else:
        verdict = "not supported"
    return GroupedDiffResult(mean, lo, hi, margin, verdict)
