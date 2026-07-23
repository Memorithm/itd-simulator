"""External diagnostics, complementarity, events and locked prediction (Mission 7).

Computes per-frame ITD-3D and established diagnostics on an ingested external sequence
(H51), measures which ITD channels carry information *not* in the primary established
scalar (H54), labels an ITD-independent extreme-enstrophy event (H52), and runs a locked
temporal-split comparison of established vs established+ITD (H53). Every step is
deterministic; negatives are preserved. The prediction is honest about statistical power:
a short external cutout yields few frames, so a wide-CI / inconclusive verdict is expected
and reported as such rather than being inflated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d import (
    lambda2,
    q_criterion,
    swirling_strength,
    velocity_gradient_3d,
)
from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d
from itd_research.hard_prediction.models import LogisticRegression
from itd_research.mission7.ingestion import Frame
from itd_research.prediction.evaluation import roc_auc

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]
_EPS = 1.0e-12

_ITD_CHANNELS = ("intensity", "heterogeneity", "localization", "roughness",
                 "orientation_dispersion", "helicity_mean", "normalized_helicity", "stretching_rate")
_ESTABLISHED = ("enstrophy", "q_positive_fraction", "lambda2_negative_fraction", "swirl_mean")


@dataclass(frozen=True)
class DiagnosticTrajectories:
    """Per-frame ITD-3D and established diagnostic time series."""

    times: list[float]
    itd: dict[str, list[float]]
    established: dict[str, list[float]]

    def as_dict(self) -> dict[str, object]:
        return {"times": self.times, "itd": self.itd, "established": self.established}


def _established(fr: Frame) -> dict[str, float]:
    grad = velocity_gradient_3d(fr.u, fr.v, fr.w, fr.x, fr.y, fr.z, "finite")
    omega = np.stack([grad[..., 2, 1] - grad[..., 1, 2],
                      grad[..., 0, 2] - grad[..., 2, 0],
                      grad[..., 1, 0] - grad[..., 0, 1]], axis=-1)
    return {
        "enstrophy": 0.5 * float(np.mean(np.sum(omega**2, axis=-1))),
        "q_positive_fraction": float(np.mean(q_criterion(grad) > 0.0)),
        "lambda2_negative_fraction": float(np.mean(lambda2(grad) < 0.0)),
        "swirl_mean": float(np.mean(swirling_strength(grad))),
    }


def compute_trajectories(frames: list[Frame]) -> DiagnosticTrajectories:
    """Per-frame ITD-3D channels and established diagnostics (H51 descriptive)."""
    itd: dict[str, list[float]] = {name: [] for name in _ITD_CHANNELS}
    est: dict[str, list[float]] = {name: [] for name in _ESTABLISHED}
    for fr in frames:
        channels = evaluate_itd3d(fr.u, fr.v, fr.w, fr.x, fr.y, fr.z, "finite").as_dict()
        for name in _ITD_CHANNELS:
            itd[name].append(float(channels[name]))
        for name, value in _established(fr).items():
            est[name].append(value)
    return DiagnosticTrajectories([fr.time for fr in frames], itd, est)


def _spearman(a: FloatArray, b: FloatArray) -> float:
    if a.size < 2:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    if np.std(ra) < _EPS or np.std(rb) < _EPS:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


@dataclass(frozen=True)
class ComplementarityResult:
    """Rank correlation of each ITD channel with the primary established scalar (H54)."""

    reference: str
    correlations: dict[str, float]
    distinct_channels: list[str]   # |rho| < threshold: information not in the reference

    def as_dict(self) -> dict[str, object]:
        return {
            "reference": self.reference,
            "correlations": self.correlations,
            "distinct_channels": self.distinct_channels,
        }


def rank_complementarity(
    traj: DiagnosticTrajectories, *, reference: str = "enstrophy", distinct_threshold: float = 0.3,
) -> ComplementarityResult:
    """Which ITD channels are rank-distinct from the reference established scalar (H54)."""
    ref = np.asarray(traj.established[reference], dtype=np.float64)
    corr = {name: _spearman(np.asarray(vals, dtype=np.float64), ref) for name, vals in traj.itd.items()}
    distinct = [name for name, rho in corr.items() if not np.isnan(rho) and abs(rho) < distinct_threshold]
    return ComplementarityResult(reference=reference, correlations=corr, distinct_channels=distinct)


def label_enstrophy_event(
    traj: DiagnosticTrajectories, *, dev_frames: int, quantile: float = 0.67,
) -> tuple[IntArray, float]:
    """ITD-independent event: enstrophy above a DEV-derived quantile threshold.

    The threshold is fixed from the development frames only (no holdout-label fitting);
    a frame is positive iff its enstrophy exceeds it. Uses ONLY established enstrophy.
    """
    enst = np.asarray(traj.established["enstrophy"], dtype=np.float64)
    threshold = float(np.quantile(enst[:dev_frames], quantile)) if dev_frames > 0 else float(np.quantile(enst, quantile))
    labels = (enst > threshold).astype(np.int64)
    return labels, threshold


@dataclass(frozen=True)
class ExternalPredictionResult:
    """Locked temporal-split established-vs-established+ITD comparison (H52/H53)."""

    n_frames: int
    n_dev: int
    n_holdout: int
    holdout_positives: int
    auc_established: float
    auc_itd: float
    auc_augmented: float
    added_value: float
    margin: float
    verdict: str
    note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "n_frames": self.n_frames, "n_dev": self.n_dev, "n_holdout": self.n_holdout,
            "holdout_positives": self.holdout_positives,
            "auc_established": self.auc_established, "auc_itd": self.auc_itd,
            "auc_augmented": self.auc_augmented, "added_value": self.added_value,
            "margin": self.margin, "verdict": self.verdict, "note": self.note,
        }


def _matrix(traj: DiagnosticTrajectories, names: tuple[str, ...], source: str) -> FloatArray:
    table = traj.itd if source == "itd" else traj.established
    return np.column_stack([np.asarray(table[n], dtype=np.float64) for n in names])


def _auc_temporal(feats: FloatArray, labels: IntArray, n_dev: int) -> float:
    train_x, train_y = feats[:n_dev], labels[:n_dev].astype(np.float64)
    test_x, test_y = feats[n_dev:], labels[n_dev:]
    if len(np.unique(train_y)) < 2 or len(np.unique(test_y)) < 2:
        return float("nan")
    mean, std = train_x.mean(axis=0), train_x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    model = LogisticRegression().fit((train_x - mean) / std, train_y)
    scores = model.predict_proba((test_x - mean) / std)
    return roc_auc(scores, test_y)


def external_prediction(
    traj: DiagnosticTrajectories, *, holdout_fraction: float = 0.375, margin: float = 0.02,
) -> ExternalPredictionResult:
    """Compare established vs established+ITD on a locked temporal holdout (H52/H53).

    Frames are split by time (no adjacent-frame leakage): the earlier block develops the
    model and the event threshold; the later block is the held-out test. With few external
    frames the AUC is coarse; the verdict is ``inconclusive`` unless the added value clears
    the margin on a holdout with both classes present.
    """
    n = len(traj.times)
    n_holdout = max(2, int(round(n * holdout_fraction)))
    n_dev = n - n_holdout
    labels, _ = label_enstrophy_event(traj, dev_frames=n_dev)
    est = _matrix(traj, _ESTABLISHED, "established")
    itd = _matrix(traj, _ITD_CHANNELS, "itd")
    aug = np.column_stack([est, itd])
    auc_est = _auc_temporal(est, labels, n_dev)
    auc_itd = _auc_temporal(itd, labels, n_dev)
    auc_aug = _auc_temporal(aug, labels, n_dev)
    holdout_pos = int(np.sum(labels[n_dev:]))
    added = (auc_aug - auc_est) if not (np.isnan(auc_aug) or np.isnan(auc_est)) else float("nan")
    underpowered = n_holdout < 8 or holdout_pos < 2 or (n_holdout - holdout_pos) < 2
    if np.isnan(added):
        verdict = "inconclusive"
    elif underpowered:
        verdict = "inconclusive"
    elif added >= margin:
        verdict = "supported within tested scope"
    else:
        verdict = "not supported"
    note = (
        f"{n_holdout} holdout frames ({holdout_pos} positive): statistically underpowered; "
        "reported descriptively, not as evidence of value." if underpowered else
        "locked temporal holdout; added value vs competent established baseline."
    )
    return ExternalPredictionResult(
        n_frames=n, n_dev=n_dev, n_holdout=n_holdout, holdout_positives=holdout_pos,
        auc_established=auc_est, auc_itd=auc_itd, auc_augmented=auc_aug,
        added_value=added, margin=margin, verdict=verdict, note=note,
    )
