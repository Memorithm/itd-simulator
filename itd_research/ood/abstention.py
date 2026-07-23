"""Selective prediction via OOD abstention and risk-coverage analysis (research, H23).

Given per-sample OOD scores, a prediction error signal, and an abstention threshold,
the system predicts on in-domain samples and abstains on high-OOD samples. Reported:
coverage, selective risk (error on covered samples), the risk-coverage curve, and the
false-confidence rate (confident predictions on truly out-of-distribution samples).
The goal is to lower error on OOD flows without collapsing coverage on in-domain ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]


@dataclass(frozen=True)
class SelectiveResult:
    """Selective-prediction summary at one operating threshold."""

    threshold: float
    coverage: float
    in_domain_coverage: float
    selective_risk: float
    full_risk: float
    false_confidence_rate: float

    def as_dict(self) -> dict[str, float]:
        return {
            "threshold": self.threshold,
            "coverage": self.coverage,
            "in_domain_coverage": self.in_domain_coverage,
            "selective_risk": self.selective_risk,
            "full_risk": self.full_risk,
            "false_confidence_rate": self.false_confidence_rate,
        }


def selective_evaluation(
    ood_score: FloatArray, error: FloatArray, is_ood: BoolArray, threshold: float
) -> SelectiveResult:
    """Evaluate abstention at ``threshold``: predict where score <= threshold."""
    score = np.asarray(ood_score, dtype=np.float64)
    err = np.asarray(error, dtype=np.float64)
    ood = np.asarray(is_ood, dtype=bool)
    covered = score <= threshold
    coverage = float(np.mean(covered))
    in_domain = ~ood
    in_domain_coverage = (
        float(np.mean(covered[in_domain])) if np.any(in_domain) else 0.0
    )
    selective_risk = float(np.mean(err[covered])) if np.any(covered) else 0.0
    full_risk = float(np.mean(err))
    # A false-confident sample is truly OOD but predicted on (not abstained).
    false_confidence = float(np.mean(covered[ood])) if np.any(ood) else 0.0
    return SelectiveResult(
        threshold, coverage, in_domain_coverage, selective_risk, full_risk, false_confidence
    )


def risk_coverage_curve(
    ood_score: FloatArray, error: FloatArray, points: int = 20
) -> list[tuple[float, float]]:
    """Return (coverage, selective_risk) as the abstention threshold is swept."""
    score = np.asarray(ood_score, dtype=np.float64)
    err = np.asarray(error, dtype=np.float64)
    thresholds = np.atleast_1d(np.quantile(score, np.linspace(0.05, 1.0, points)))
    curve: list[tuple[float, float]] = []
    for threshold in thresholds:
        covered = score <= float(threshold)
        if not np.any(covered):
            continue
        curve.append((float(np.mean(covered)), float(np.mean(err[covered]))))
    return curve


def abstention_benefit(
    ood_score: FloatArray, error: FloatArray, is_ood: BoolArray, in_domain_coverage_floor: float = 0.5
) -> tuple[SelectiveResult, bool, str]:
    """Choose a threshold at the in-domain score quantile and test the H23 rule.

    The threshold is the ``in_domain_coverage_floor`` upper quantile of the *in-domain*
    OOD scores, so in-domain coverage stays near the floor by construction. H23 holds
    if selective risk is below full risk and OOD false-confidence is materially reduced.
    """
    score = np.asarray(ood_score, dtype=np.float64)
    ood = np.asarray(is_ood, dtype=bool)
    in_domain = score[~ood]
    # Keep ~80% of in-domain samples; OOD samples sit far above this quantile.
    if in_domain.size == 0:
        threshold = float(np.median(score))
    else:
        threshold = float(np.quantile(in_domain, 0.8))
    result = selective_evaluation(score, error, ood, threshold)
    supported = (
        result.selective_risk < result.full_risk - 1e-9
        and result.in_domain_coverage >= in_domain_coverage_floor
        and result.false_confidence_rate < float(np.mean(ood) if ood.size else 1.0)
    )
    verdict = "supported within tested scope" if supported else "not supported"
    return result, supported, verdict
