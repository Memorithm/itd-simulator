"""Cross-source structural transfer (Mission 8, H65).

Calibrates (fits) established-only and established+ITD_STRUCTURAL models on the PRIMARY
source's development sequences, then evaluates them WITHOUT REFITTING on a second source.
Both sources are JHTDB (same institution/access modality); this is a within-institution
cross-PHYSICS transfer test (isotropic hydrodynamic turbulence -> MHD-forced turbulence),
never claimed as cross-institution -- see the preregistration's honesty note.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.models import LogisticRegression
from itd_research.mission8.baselines import BASELINE_COMPETENT_COMBINED
from itd_research.mission8.prediction import Sequence, feature_matrix
from itd_research.mission8.structural_features import ITD_3D_NONREDUNDANT
from itd_research.prediction.evaluation import roc_auc

FloatArray: TypeAlias = NDArray[np.float64]
_EPS = 1e-12


@dataclass(frozen=True)
class TransferResult:
    """H65: performance developed on source A, applied without refitting to source B."""

    source_a: str
    source_b: str
    development_auc_established: float
    development_auc_augmented: float
    transfer_auc_established: float
    transfer_auc_augmented: float
    performance_drop_established: float
    performance_drop_augmented: float
    verdict: str
    comparability_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "source_a": self.source_a, "source_b": self.source_b,
            "development_auc_established": self.development_auc_established,
            "development_auc_augmented": self.development_auc_augmented,
            "transfer_auc_established": self.transfer_auc_established,
            "transfer_auc_augmented": self.transfer_auc_augmented,
            "performance_drop_established": self.performance_drop_established,
            "performance_drop_augmented": self.performance_drop_augmented,
            "verdict": self.verdict,
            "comparability_note": self.comparability_note,
        }


def _fit_and_auc(
    train: list[Sequence], test: list[Sequence], established_names: tuple[str, ...], itd_names: tuple[str, ...],
) -> float:
    train_x = np.concatenate([feature_matrix(s, established_names, itd_names) for s in train], axis=0)
    train_y = np.concatenate([s.labels for s in train]).astype(np.float64)
    if len(np.unique(train_y)) < 2:
        return float("nan")
    mean, std = train_x.mean(axis=0), train_x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    model = LogisticRegression().fit((train_x - mean) / std, train_y)
    test_x = np.concatenate([feature_matrix(s, established_names, itd_names) for s in test], axis=0)
    test_y = np.concatenate([s.labels for s in test])
    scores = model.predict_proba((test_x - mean) / std)
    return roc_auc(scores, test_y)


def evaluate_cross_source_transfer(
    source_a_dev: list[Sequence], source_a_holdout: list[Sequence], source_b_sequences: list[Sequence],
    *, source_a_name: str = "jhtdb_isotropic1024coarse", source_b_name: str = "jhtdb_mhd1024",
    established_names: tuple[str, ...] = BASELINE_COMPETENT_COMBINED,
    itd_names: tuple[str, ...] = ITD_3D_NONREDUNDANT,
) -> TransferResult:
    """H65: calibrate on source A's dev, score source A's holdout AND source B (no refit)."""
    dev_auc_est = _fit_and_auc(source_a_dev, source_a_dev, established_names, ())
    dev_auc_aug = _fit_and_auc(source_a_dev, source_a_dev, established_names, itd_names)
    a_holdout_auc_est = _fit_and_auc(source_a_dev, source_a_holdout, established_names, ())
    a_holdout_auc_aug = _fit_and_auc(source_a_dev, source_a_holdout, established_names, itd_names)
    b_auc_est = _fit_and_auc(source_a_dev, source_b_sequences, established_names, ())
    b_auc_aug = _fit_and_auc(source_a_dev, source_b_sequences, established_names, itd_names)

    drop_est = (
        a_holdout_auc_est - b_auc_est if not (np.isnan(a_holdout_auc_est) or np.isnan(b_auc_est)) else float("nan")
    )
    drop_aug = (
        a_holdout_auc_aug - b_auc_aug if not (np.isnan(a_holdout_auc_aug) or np.isnan(b_auc_aug)) else float("nan")
    )

    if np.isnan(b_auc_aug):
        verdict = "inconclusive"
    elif b_auc_aug > 0.5 and (np.isnan(drop_aug) or drop_aug < 0.2):
        verdict = "supported within tested scope"
    else:
        verdict = "not supported"

    return TransferResult(
        source_a=source_a_name, source_b=source_b_name,
        development_auc_established=float(dev_auc_est), development_auc_augmented=float(dev_auc_aug),
        transfer_auc_established=float(b_auc_est), transfer_auc_augmented=float(b_auc_aug),
        performance_drop_established=float(drop_est), performance_drop_augmented=float(drop_aug),
        verdict=verdict,
        comparability_note=(
            "Both sources are JHTDB (same institution/access modality); this is a "
            "within-institution cross-PHYSICS transfer test (isotropic hydrodynamic -> "
            "MHD-forced turbulence), NOT a cross-institution claim."
        ),
    )
