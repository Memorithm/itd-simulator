"""Locked structural prediction protocol: saturation screen + H61/H62 (Mission 8).

Given a set of independent SEQUENCES (each with a baseline trajectory, a structural
trajectory, and ITD-independent event labels), this module:

1. screens the candidate task for saturation on DEVELOPMENT sequences only, via
   leave-one-dev-sequence-out cross-validation (never in-sample, never touching holdout);
2. if unsaturated, fits established-only and established+ITD_STRUCTURAL models on ALL
   development sequences and evaluates ONCE on the held-out sequences, reporting a
   grouped-bootstrap added-value estimate (independent unit = sequence, never a frame).

A saturated task is still scored (for the descriptive/regression record) but its result is
never treated as evidence for or against H62.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.models import LogisticRegression
from itd_research.mission8.baselines import BaselineTrajectory
from itd_research.mission8.schema import StructuralEvent, TaskScreeningResult
from itd_research.mission8.statistics import (
    GroupedDiffResult,
    grouped_bootstrap_diff,
    saturation_screen,
)
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    StructuralTrajectory,
)
from itd_research.prediction.evaluation import roc_auc

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]
_EPS = 1e-12


@dataclass(frozen=True)
class Sequence:
    """One independent unit: its established + structural trajectories and event labels."""

    sequence_id: str
    baseline: BaselineTrajectory
    structural: StructuralTrajectory
    events: list[StructuralEvent]
    labels: IntArray


def _labels_from_events(n_frames: int, events: list[StructuralEvent], horizon: int) -> IntArray:
    labels: IntArray = np.zeros(n_frames, dtype=np.int64)
    for event in events:
        for offset in range(horizon + 1):
            idx = event.event_frame - offset
            if 0 <= idx < n_frames:
                labels[idx] = 1
    return labels


def make_sequence(
    sequence_id: str, baseline: BaselineTrajectory, structural: StructuralTrajectory,
    events: list[StructuralEvent], *, horizon: int = 2,
) -> Sequence:
    labels = _labels_from_events(len(structural.times), events, horizon)
    return Sequence(sequence_id, baseline, structural, events, labels)


def feature_matrix(seq: Sequence, established_names: tuple[str, ...], itd_names: tuple[str, ...]) -> FloatArray:
    established = seq.baseline.matrix(established_names) if established_names else None
    itd = seq.structural.matrix(itd_names) if itd_names else None
    if established is not None and itd is not None:
        return np.column_stack([established, itd])
    return established if established is not None else itd


def _fit_score(
    train_seqs: list[Sequence], test_seqs: list[Sequence],
    established_names: tuple[str, ...], itd_names: tuple[str, ...],
) -> list[tuple[FloatArray, IntArray]]:
    """Fit on ``train_seqs`` (pooled), return per-test-sequence (scores, labels)."""
    train_x = np.concatenate([feature_matrix(s, established_names, itd_names) for s in train_seqs], axis=0)
    train_y = np.concatenate([s.labels for s in train_seqs]).astype(np.float64)
    mean, std = train_x.mean(axis=0), train_x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    if len(np.unique(train_y)) < 2:
        return [(np.full(len(s.labels), np.nan), s.labels) for s in test_seqs]
    model = LogisticRegression().fit((train_x - mean) / std, train_y)
    out = []
    for seq in test_seqs:
        x = feature_matrix(seq, established_names, itd_names)
        scores = model.predict_proba((x - mean) / std)
        out.append((scores, seq.labels))
    return out


@dataclass(frozen=True)
class PrimaryTestResult:
    """H61/H62 outcome: saturation screen + the (conditionally primary) added-value test."""

    screening: TaskScreeningResult
    holdout_auc_established: float
    holdout_auc_itd_only: float
    holdout_auc_augmented: float
    added_value: GroupedDiffResult
    h61_verdict: str
    h62_verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "screening": self.screening.as_dict(),
            "holdout_auc_established": self.holdout_auc_established,
            "holdout_auc_itd_only": self.holdout_auc_itd_only,
            "holdout_auc_augmented": self.holdout_auc_augmented,
            "added_value": self.added_value.as_dict(),
            "h61_verdict": self.h61_verdict,
            "h62_verdict": self.h62_verdict,
        }


def run_primary_test(
    dev_sequences: list[Sequence], holdout_sequences: list[Sequence],
    established_names: tuple[str, ...], *, itd_names: tuple[str, ...] = ITD_3D_NONREDUNDANT,
    task_id: str = "jhtdb_isotropic_core_topology_change", margin: float = 0.02, bootstrap: int = 2000,
) -> PrimaryTestResult:
    """Saturation-screen on DEV (leave-one-sequence-out), then the locked H62 holdout test."""
    # Screen: leave-one-dev-sequence-out, established-only, pooled out-of-sample scores.
    screen_scores: list[FloatArray] = []
    screen_labels: list[IntArray] = []
    for i in range(len(dev_sequences)):
        train = dev_sequences[:i] + dev_sequences[i + 1:]
        test = [dev_sequences[i]]
        if not train:
            continue
        for scores, labels in _fit_score(train, test, established_names, ()):
            screen_scores.append(scores)
            screen_labels.append(labels)
    pooled_scores = np.concatenate(screen_scores) if screen_scores else np.array([])
    pooled_labels = np.concatenate(screen_labels) if screen_labels else np.array([], dtype=np.int64)
    screening = saturation_screen(task_id, "Q_criterion_core_merger_split", pooled_scores, pooled_labels)

    # Holdout evaluation: fit once on ALL dev sequences, score once on ALL holdout sequences.
    est_pairs = _fit_score(dev_sequences, holdout_sequences, established_names, ())
    itd_pairs = _fit_score(dev_sequences, holdout_sequences, (), itd_names)
    aug_pairs = _fit_score(dev_sequences, holdout_sequences, established_names, itd_names)
    est_scores = np.concatenate([p[0] for p in est_pairs])
    est_labels = np.concatenate([p[1] for p in est_pairs])
    itd_scores = np.concatenate([p[0] for p in itd_pairs])
    itd_labels = np.concatenate([p[1] for p in itd_pairs])
    aug_scores = np.concatenate([p[0] for p in aug_pairs])
    auc_established = roc_auc(est_scores, est_labels)
    auc_itd_only = roc_auc(itd_scores, itd_labels)
    auc_augmented = roc_auc(aug_scores, np.concatenate([p[1] for p in aug_pairs]))

    added = grouped_bootstrap_diff(est_pairs, aug_pairs, metric="auc", margin=margin, bootstrap=bootstrap)

    if screening.saturation_status == "saturated":
        h61_verdict = "inconclusive"  # per protocol: a saturated task is never primary evidence
        h62_verdict = "inconclusive"
    else:
        h61_verdict = (
            "supported within tested scope" if not np.isnan(auc_itd_only) and auc_itd_only > 0.5
            else "not supported"
        )
        h62_verdict = added.verdict

    return PrimaryTestResult(
        screening=screening, holdout_auc_established=float(auc_established),
        holdout_auc_itd_only=float(auc_itd_only), holdout_auc_augmented=float(auc_augmented),
        added_value=added, h61_verdict=h61_verdict, h62_verdict=h62_verdict,
    )
