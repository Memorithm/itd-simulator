"""Leakage-safe cross-flow transfer studies (research, H8/H9/H10/H13).

Three well-posed, ITD-independent-labelled transfer measurements on the
deterministic 3D flow catalogue, each with an explicit held-out set:

* **family_generalization (H13, H8)** -- leave-one-flow-out family classification
  (each held-out flow's family is present in training): does ITD discriminate the
  family of an *unseen flow* as well as established diagnostics? Per-family recalls
  expose where ITD is and is not superior (H8).
* **component_transfer (H9)** -- leave-one-family-out linear regression from ITD
  channels onto an established diagnostic: does the ITD->physics relationship hold on
  an *unseen family*? Out-of-family R^2 vs in-family R^2 quantifies transfer.
* **threshold_transfer (H10)** -- a single scalar threshold calibrated on training
  flows to detect rotation-dominated sub-cubes (label: majority Q>0, ITD-independent)
  and transferred to a held-out flow: how much does one fixed threshold degrade
  across flows, for ITD scalars vs baseline scalars?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.generalization.baselines import (
    BASELINE_FEATURES,
    baseline_features_on_subcube,
)
from itd_research.validation_lab.candidates import channel_superset, evaluate_channels
from itd_research.validation_lab.flows import LabFlow

FloatArray: TypeAlias = NDArray[np.float64]
_EPS = 1.0e-12


@dataclass(frozen=True)
class GeneralizationSamples:
    """ITD and baseline sub-cube features with flow/family provenance."""

    itd_channels: tuple[str, ...]
    baseline_channels: tuple[str, ...]
    itd_matrix: FloatArray
    baseline_matrix: FloatArray
    flow_labels: tuple[str, ...]
    family_labels: tuple[str, ...]


def sample_generalization(
    flows: list[LabFlow], subcubes_per_axis: int = 3
) -> GeneralizationSamples:
    """Evaluate ITD channels and established baselines on sub-cubes of every flow."""
    itd_channels = channel_superset()
    itd_rows: list[list[float]] = []
    base_rows: list[list[float]] = []
    flow_labels: list[str] = []
    family_labels: list[str] = []
    for flow in flows:
        nodes = flow.u.shape[0]
        block = nodes // subcubes_per_axis
        if block < 5:
            raise ValueError("sub-cubes too small (need >= 5 nodes per axis).")
        for i in range(subcubes_per_axis):
            for j in range(subcubes_per_axis):
                for k in range(subcubes_per_axis):
                    xs = slice(i * block, (i + 1) * block)
                    ys = slice(j * block, (j + 1) * block)
                    zs = slice(k * block, (k + 1) * block)
                    args = (
                        flow.u[xs, ys, zs], flow.v[xs, ys, zs], flow.w[xs, ys, zs],
                        flow.coordinates[xs], flow.coordinates[ys], flow.coordinates[zs],
                        "finite",
                    )
                    itd = evaluate_channels(*args)
                    base = baseline_features_on_subcube(*args)
                    itd_rows.append([itd[name] for name in itd_channels])
                    base_rows.append([base[name] for name in BASELINE_FEATURES])
                    flow_labels.append(flow.name)
                    family_labels.append(flow.family)
    return GeneralizationSamples(
        itd_channels=itd_channels,
        baseline_channels=BASELINE_FEATURES,
        itd_matrix=np.array(itd_rows, dtype=np.float64),
        baseline_matrix=np.array(base_rows, dtype=np.float64),
        flow_labels=tuple(flow_labels),
        family_labels=tuple(family_labels),
    )


def _standardize_train_test(train: FloatArray, test: FloatArray) -> tuple[FloatArray, FloatArray]:
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    return (train - mean) / std, (test - mean) / std


def _centroid_predict(
    train_x: FloatArray, train_labels: list[str], test_x: FloatArray
) -> list[str]:
    classes = sorted(set(train_labels))
    centroids = np.array(
        [train_x[[i for i, c in enumerate(train_labels) if c == cls]].mean(axis=0) for cls in classes]
    )
    predictions: list[str] = []
    for row in test_x:
        distances = np.sum((centroids - row) ** 2, axis=1)
        predictions.append(classes[int(np.argmin(distances))])
    return predictions


def _per_class_recall(true: list[str], predicted: list[str]) -> dict[str, float]:
    recalls: dict[str, float] = {}
    for cls in sorted(set(true)):
        idx = [i for i, t in enumerate(true) if t == cls]
        recalls[cls] = sum(1 for i in idx if predicted[i] == cls) / len(idx) if idx else 0.0
    return recalls


@dataclass(frozen=True)
class GeneralizationResult:
    """Leave-one-flow-out family classification for ITD vs baseline."""

    itd_balanced_accuracy: float
    baseline_balanced_accuracy: float
    itd_per_family_recall: dict[str, float]
    baseline_per_family_recall: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "itd_balanced_accuracy": self.itd_balanced_accuracy,
            "baseline_balanced_accuracy": self.baseline_balanced_accuracy,
            "itd_per_family_recall": self.itd_per_family_recall,
            "baseline_per_family_recall": self.baseline_per_family_recall,
        }


def _leave_one_flow_out_family(
    matrix: FloatArray, flow_labels: tuple[str, ...], family_labels: tuple[str, ...]
) -> tuple[list[str], list[str]]:
    flows = np.array(flow_labels)
    families = list(family_labels)
    true: list[str] = []
    predicted: list[str] = []
    for held in sorted(set(flow_labels)):
        test_mask = flows == held
        train_mask = ~test_mask
        if not np.any(train_mask) or not np.any(test_mask):
            continue
        train_z, test_z = _standardize_train_test(matrix[train_mask], matrix[test_mask])
        train_families = [families[i] for i in np.flatnonzero(train_mask)]
        predicted.extend(_centroid_predict(train_z, train_families, test_z))
        true.extend(families[i] for i in np.flatnonzero(test_mask))
    return true, predicted


def family_generalization(samples: GeneralizationSamples) -> GeneralizationResult:
    """Leave-one-flow-out family classification: ITD vs established baselines."""
    itd_true, itd_pred = _leave_one_flow_out_family(
        samples.itd_matrix, samples.flow_labels, samples.family_labels
    )
    base_true, base_pred = _leave_one_flow_out_family(
        samples.baseline_matrix, samples.flow_labels, samples.family_labels
    )
    itd_recall = _per_class_recall(itd_true, itd_pred)
    base_recall = _per_class_recall(base_true, base_pred)
    return GeneralizationResult(
        itd_balanced_accuracy=float(np.mean(list(itd_recall.values()))) if itd_recall else 0.0,
        baseline_balanced_accuracy=float(np.mean(list(base_recall.values()))) if base_recall else 0.0,
        itd_per_family_recall=itd_recall,
        baseline_per_family_recall=base_recall,
    )


def _ridge_fit(x: FloatArray, y: FloatArray, ridge: float = 1.0e-3) -> FloatArray:
    design = np.column_stack([np.ones(x.shape[0]), x])
    penalty = ridge * np.eye(design.shape[1])
    penalty[0, 0] = 0.0
    return np.linalg.solve(design.T @ design + penalty, design.T @ y)


def _r_squared(y_true: FloatArray, y_pred: FloatArray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > _EPS else 0.0


@dataclass(frozen=True)
class ComponentTransfer:
    """Leave-one-family-out regression from ITD channels onto a baseline diagnostic."""

    target: str
    in_family_r2: float
    out_of_family_r2: float
    per_family_r2: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "in_family_r2": self.in_family_r2,
            "out_of_family_r2": self.out_of_family_r2,
            "per_family_r2": self.per_family_r2,
        }


def component_transfer(samples: GeneralizationSamples, target: str = "q_positive_fraction") -> ComponentTransfer:
    """How well does the ITD->diagnostic relation transfer to an unseen family?"""
    target_index = samples.baseline_channels.index(target)
    y = samples.baseline_matrix[:, target_index]
    families = np.array(samples.family_labels)

    # In-family reference: fit and score on all samples (upper bound; same distribution).
    train_z_all, _ = _standardize_train_test(samples.itd_matrix, samples.itd_matrix)
    weights_all = _ridge_fit(train_z_all, y)
    pred_all = np.column_stack([np.ones(train_z_all.shape[0]), train_z_all]) @ weights_all
    in_family = _r_squared(y, pred_all)

    per_family: dict[str, float] = {}
    for held in sorted(set(samples.family_labels)):
        test_mask = families == held
        train_mask = ~test_mask
        if not np.any(train_mask) or not np.any(test_mask):
            continue
        train_z, test_z = _standardize_train_test(
            samples.itd_matrix[train_mask], samples.itd_matrix[test_mask]
        )
        weights = _ridge_fit(train_z, y[train_mask])
        pred = np.column_stack([np.ones(test_z.shape[0]), test_z]) @ weights
        per_family[held] = _r_squared(y[test_mask], pred)

    out_of_family = float(np.mean(list(per_family.values()))) if per_family else 0.0
    return ComponentTransfer(target, in_family, out_of_family, per_family)


@dataclass(frozen=True)
class ThresholdTransfer:
    """Leave-one-flow-out single-threshold transfer for one scalar feature."""

    feature: str
    source: str
    in_sample_accuracy: float
    transfer_accuracy: float

    def as_dict(self) -> dict[str, object]:
        return {
            "feature": self.feature,
            "source": self.source,
            "in_sample_accuracy": self.in_sample_accuracy,
            "transfer_accuracy": self.transfer_accuracy,
        }


def _best_threshold(scores: FloatArray, labels: NDArray[np.int64]) -> tuple[float, bool]:
    """Threshold and polarity maximizing balanced accuracy on (scores, labels)."""
    order = np.argsort(scores, kind="mergesort")
    candidates = np.unique(scores[order])
    midpoints = (candidates[:-1] + candidates[1:]) / 2.0 if candidates.size > 1 else candidates
    best_threshold = float(candidates[0]) if candidates.size else 0.0
    best_polarity = True
    best_score = -1.0
    positive = labels == 1
    for threshold in midpoints:
        for polarity in (True, False):
            predicted = (scores >= threshold) if polarity else (scores < threshold)
            tp = float(np.sum(predicted & positive))
            tn = float(np.sum(~predicted & ~positive))
            n_pos = float(np.sum(positive))
            n_neg = float(np.sum(~positive))
            if n_pos == 0 or n_neg == 0:
                continue
            balanced = 0.5 * (tp / n_pos + tn / n_neg)
            if balanced > best_score:
                best_score, best_threshold, best_polarity = balanced, float(threshold), polarity
    return best_threshold, best_polarity


def _apply_threshold(scores: FloatArray, threshold: float, polarity: bool) -> NDArray[np.bool_]:
    return (scores >= threshold) if polarity else (scores < threshold)


def _balanced_accuracy(labels: NDArray[np.int64], predicted: NDArray[np.bool_]) -> float:
    positive = labels == 1
    n_pos = float(np.sum(positive))
    n_neg = float(np.sum(~positive))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    tp = float(np.sum(predicted & positive))
    tn = float(np.sum(~predicted & ~positive))
    return 0.5 * (tp / n_pos + tn / n_neg)


def threshold_transfer(
    samples: GeneralizationSamples, feature: str, source: str
) -> ThresholdTransfer:
    """One scalar's threshold: in-sample vs leave-one-flow-out transfer accuracy.

    Label (ITD-independent): a sub-cube is rotation-dominated iff its majority is
    Q>0. ``source`` is ``"itd"`` or ``"baseline"``; ``feature`` names the scalar.
    """
    q_index = samples.baseline_channels.index("q_positive_fraction")
    labels = (samples.baseline_matrix[:, q_index] > 0.5).astype(np.int64)
    if source == "itd":
        scores = samples.itd_matrix[:, samples.itd_channels.index(feature)]
    else:
        scores = samples.baseline_matrix[:, samples.baseline_channels.index(feature)]
    flows = np.array(samples.flow_labels)

    threshold, polarity = _best_threshold(scores, labels)
    in_sample = _balanced_accuracy(labels, _apply_threshold(scores, threshold, polarity))

    transfer_scores: list[float] = []
    for held in sorted(set(samples.flow_labels)):
        test_mask = flows == held
        train_mask = ~test_mask
        if not np.any(train_mask) or not np.any(test_mask):
            continue
        train_threshold, train_polarity = _best_threshold(scores[train_mask], labels[train_mask])
        predicted = _apply_threshold(scores[test_mask], train_threshold, train_polarity)
        value = _balanced_accuracy(labels[test_mask], predicted)
        if not np.isnan(value):
            transfer_scores.append(value)
    transfer = float(np.mean(transfer_scores)) if transfer_scores else float("nan")
    return ThresholdTransfer(feature, source, float(in_sample), transfer)


def classify_h13(result: GeneralizationResult) -> tuple[str, str]:
    """H13 verdict: does ITD generalize to unseen flows (leave-one-flow-out)?"""
    chance = 1.0 / max(len(result.itd_per_family_recall), 1)
    itd = result.itd_balanced_accuracy
    baseline = result.baseline_balanced_accuracy
    if itd <= chance + 0.02:
        return ("not supported", f"ITD balanced accuracy {itd:.2f} is at chance ({chance:.2f}).")
    weakest = min(result.itd_per_family_recall.values())
    if itd > baseline and itd >= 0.5 and weakest >= 0.4:
        return (
            "supported within tested scope",
            f"ITD generalizes to unseen flows (balanced acc {itd:.2f} > baseline {baseline:.2f}), "
            f"every family recalled >= {weakest:.2f}.",
        )
    return (
        "partially supported",
        f"ITD generalizes above chance (balanced acc {itd:.2f}, baseline {baseline:.2f}) but is "
        f"family-dependent: weakest family recall {weakest:.2f}.",
    )


def classify_h9(transfers: list[ComponentTransfer]) -> tuple[str, str]:
    """H9 verdict: do ITD->diagnostic relations transfer to an unseen family?"""
    holds = [
        t for t in transfers if t.in_family_r2 > 0.3 and t.out_of_family_r2 > 0.5 * t.in_family_r2
    ]
    collapses = [t for t in transfers if t.out_of_family_r2 < 0.0]
    if holds:
        return (
            "partially supported",
            f"{len(holds)}/{len(transfers)} ITD->diagnostic relations retained out-of-family; "
            "the rest collapse, so component meaning is not universal.",
        )
    if collapses:
        worst = min(collapses, key=lambda t: t.out_of_family_r2)
        return (
            "not supported",
            f"every ITD->diagnostic relation collapses on an unseen family "
            f"(e.g. {worst.target}: in-family R^2 {worst.in_family_r2:.2f} -> out-of-family "
            f"R^2 {worst.out_of_family_r2:.1f}); relations are family-specific.",
        )
    return ("inconclusive", "out-of-family fits neither clearly hold nor clearly collapse.")


def classify_h10(transfers: list[ThresholdTransfer]) -> tuple[str, str]:
    """H10 verdict: does a single threshold transfer across flows (chance 0.5)?"""
    valid = [t for t in transfers if not np.isnan(t.transfer_accuracy)]
    if not valid:
        return ("inconclusive", "no flow admitted both label classes; threshold transfer undefined.")
    best = max(valid, key=lambda t: t.transfer_accuracy)
    if best.transfer_accuracy >= 0.7:
        return (
            "supported within tested scope",
            f"{best.source} {best.feature} threshold transfers (accuracy {best.transfer_accuracy:.2f}).",
        )
    best_in_sample = max(transfers, key=lambda t: t.in_sample_accuracy)
    return (
        "not supported",
        f"no single threshold transfers across flows: best transfer accuracy "
        f"{best.transfer_accuracy:.2f} (chance 0.50), though in-sample reaches "
        f"{best_in_sample.in_sample_accuracy:.2f} ({best_in_sample.source} "
        f"{best_in_sample.feature}) -- thresholds are flow-dependent.",
    )
