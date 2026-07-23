"""Leakage-safe ablation of ITD-3D candidates on a flow-family task (research, H12).

Task: classify the flow family of a sub-cube from a candidate's channel vector.
Evaluation is **leave-one-flow-out**: all sub-cubes of a held-out flow are the test
set, the classifier is fit on the remaining flows only, and features are
standardized with training statistics only -- so sub-cubes of the same flow never
appear in both train and test. The classifier is a transparent nearest
-standardized-centroid rule. Balanced accuracy is reported per candidate together
with its channel count (a cost proxy) for a Pareto comparison. No candidate is
certified; this ranks hypotheses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.validation_lab.candidates import Candidate
from itd_research.validation_lab.sampling import ChannelSamples

FloatArray: TypeAlias = NDArray[np.float64]
_EPS = 1.0e-12


def _balanced_accuracy(true: list[str], predicted: list[str]) -> float:
    classes = sorted(set(true))
    recalls = []
    for cls in classes:
        idx = [i for i, t in enumerate(true) if t == cls]
        if not idx:
            continue
        correct = sum(1 for i in idx if predicted[i] == cls)
        recalls.append(correct / len(idx))
    return float(np.mean(recalls)) if recalls else 0.0


def _submatrix(samples: ChannelSamples, candidate: Candidate) -> FloatArray:
    index = [samples.channels.index(name) for name in candidate.channels]
    return samples.matrix[:, index]


@dataclass(frozen=True)
class AblationResult:
    """Leave-one-flow-out family-classification score for one candidate."""

    name: str
    channel_count: int
    balanced_accuracy: float

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "channel_count": self.channel_count,
            "balanced_accuracy": self.balanced_accuracy,
        }


def evaluate_candidate(samples: ChannelSamples, candidate: Candidate) -> AblationResult:
    """Leave-one-flow-out balanced accuracy of a candidate on the family task."""
    features = _submatrix(samples, candidate)
    flows = np.array(samples.flow_labels)
    families = list(samples.family_labels)
    unique_flows = sorted(set(samples.flow_labels))

    true: list[str] = []
    predicted: list[str] = []
    for held_out in unique_flows:
        test_mask = flows == held_out
        train_mask = ~test_mask
        if not np.any(train_mask) or not np.any(test_mask):
            continue
        train_x = features[train_mask]
        mean = train_x.mean(axis=0)
        std = train_x.std(axis=0)
        std = np.where(std < _EPS, 1.0, std)
        train_z = (train_x - mean) / std
        train_families = [families[i] for i in np.flatnonzero(train_mask)]
        centroids: dict[str, FloatArray] = {}
        for cls in sorted(set(train_families)):
            rows = [train_z[i] for i, f in enumerate(train_families) if f == cls]
            centroids[cls] = np.mean(np.array(rows), axis=0)
        test_z = (features[test_mask] - mean) / std
        classes = list(centroids)
        centroid_stack = np.array([centroids[c] for c in classes])
        for row in test_z:
            distances = np.sum((centroid_stack - row) ** 2, axis=1)
            predicted.append(classes[int(np.argmin(distances))])
        true.extend(families[i] for i in np.flatnonzero(test_mask))

    return AblationResult(
        name=candidate.name,
        channel_count=len(candidate.channels),
        balanced_accuracy=_balanced_accuracy(true, predicted),
    )
