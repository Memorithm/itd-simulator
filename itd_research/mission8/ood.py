"""Structural out-of-distribution detection and abstention (Mission 8, H73).

H73 asks whether a structural-feature OOD detector can distinguish VALID structural
variation (e.g. a held-out sequence from the same source, a different phase of the same
event) from a genuine distribution shift (resolution change, measurement degradation, a
new source/new physics) -- using accept / accept_with_reduced_confidence / abstain,
never a single global distance alone. This module does not invent new OOD machinery: it
reuses Mission 6's shift-aware detector and three-state policy
(:mod:`itd_research.ood_shift`) verbatim, applied to the ``ITD_3D_NONREDUNDANT`` feature
set, and calibrates bands the same way Mission 6 did -- ``s_low`` from the in-domain
(development) severity bulk, ``s_high`` from a designated "far" (genuinely shifted)
reference category -- never from the categories being judged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    StructuralTrajectory,
)
from itd_research.ood_shift.detector import ShiftReference, fit_shift_reference
from itd_research.ood_shift.policy import three_state_policy

FloatArray: TypeAlias = NDArray[np.float64]

# Categories a priori expected to be VALID structural variation (should mostly accept).
_VALID_VARIATION_CATEGORIES = ("holdout_same_source",)
# Categories a priori expected to be a genuine shift (should show reduced/abstain).
_SHIFT_CATEGORIES = (
    "resolution_downsample", "measurement_noise", "measurement_mask", "new_source_physics",
)


def fit_structural_shift_reference(
    dev_trajectories: list[StructuralTrajectory], *, channels: tuple[str, ...] = ITD_3D_NONREDUNDANT,
) -> ShiftReference:
    """Fit the shift-aware reference on DEVELOPMENT sequences' structural features only."""
    x = np.concatenate([t.matrix(channels) for t in dev_trajectories], axis=0)
    return fit_shift_reference(x, channels)


@dataclass(frozen=True)
class ShiftCategoryResult:
    """Severity, global-radius and three-state decision summary for one shift category."""

    category: str
    description: str
    n_frames: int
    mean_severity: float
    mean_global_mahalanobis: float
    accept_fraction: float
    reduce_fraction: float
    abstain_fraction: float
    mean_confidence: float

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category, "description": self.description, "n_frames": self.n_frames,
            "mean_severity": self.mean_severity, "mean_global_mahalanobis": self.mean_global_mahalanobis,
            "accept_fraction": self.accept_fraction, "reduce_fraction": self.reduce_fraction,
            "abstain_fraction": self.abstain_fraction, "mean_confidence": self.mean_confidence,
        }


def evaluate_shift_category(
    reference: ShiftReference, category: str, description: str, trajectory: StructuralTrajectory,
    *, channels: tuple[str, ...] = ITD_3D_NONREDUNDANT, s_low: float, s_high: float,
) -> ShiftCategoryResult:
    x = trajectory.matrix(channels)
    severity = reference.severity(x)
    global_maha = reference.global_mahalanobis(x)
    decision = three_state_policy(severity, s_low, s_high)
    n = len(decision.states)
    accept_frac = decision.states.count("accept") / n if n else float("nan")
    reduce_frac = decision.states.count("accept_with_reduced_confidence") / n if n else float("nan")
    abstain_frac = decision.states.count("abstain") / n if n else float("nan")
    return ShiftCategoryResult(
        category=category, description=description, n_frames=n,
        mean_severity=float(np.mean(severity)) if n else float("nan"),
        mean_global_mahalanobis=float(np.mean(global_maha)) if n else float("nan"),
        accept_fraction=accept_frac, reduce_fraction=reduce_frac, abstain_fraction=abstain_frac,
        mean_confidence=float(np.mean(decision.confidence)) if n else float("nan"),
    )


@dataclass(frozen=True)
class StructuralOODResult:
    """H73 outcome: does the shift-aware detector usefully separate the two category sets?"""

    reference_channels: tuple[str, ...]
    s_low: float
    s_high: float
    calibration_note: str
    categories: list[ShiftCategoryResult]
    valid_variation_mean_abstain: float
    shift_mean_abstain: float
    verdict: str
    reasoning: str

    def as_dict(self) -> dict[str, object]:
        return {
            "reference_channels": list(self.reference_channels), "s_low": self.s_low, "s_high": self.s_high,
            "calibration_note": self.calibration_note,
            "categories": [c.as_dict() for c in self.categories],
            "valid_variation_mean_abstain": self.valid_variation_mean_abstain,
            "shift_mean_abstain": self.shift_mean_abstain,
            "verdict": self.verdict, "reasoning": self.reasoning,
        }


def run_structural_ood_analysis(
    dev_trajectories: list[StructuralTrajectory],
    categories: dict[str, tuple[str, StructuralTrajectory]],
    *, far_category: str, channels: tuple[str, ...] = ITD_3D_NONREDUNDANT,
    valid_variation_categories: tuple[str, ...] = _VALID_VARIATION_CATEGORIES,
    shift_categories: tuple[str, ...] = _SHIFT_CATEGORIES,
) -> StructuralOODResult:
    """H73: fit on dev, calibrate bands (s_low from dev bulk, s_high from ``far_category``),
    then score every declared category and compare abstention between the "valid
    structural variation" set and the "genuine shift" set.

    ``categories`` maps a category key to ``(description, trajectory)``; ``far_category``
    MUST be one of those keys and is used only to set ``s_high`` -- never as one of the
    judged valid/shift sets that decide the verdict, so the band is not calibrated on the
    same data it is being asked to separate.
    """
    reference = fit_structural_shift_reference(dev_trajectories, channels=channels)
    dev_x = np.concatenate([t.matrix(channels) for t in dev_trajectories], axis=0)
    in_severity = reference.severity(dev_x)
    s_low = float(np.quantile(in_severity, 0.90))

    far_description, far_trajectory = categories[far_category]
    far_severity = reference.severity(far_trajectory.matrix(channels))
    s_high = float(np.quantile(far_severity, 0.50))
    if s_high <= s_low:
        s_high = s_low + max(float(np.std(in_severity)), 1.0)

    results = []
    for key, (description, trajectory) in categories.items():
        results.append(evaluate_shift_category(
            reference, key, description, trajectory, channels=channels, s_low=s_low, s_high=s_high,
        ))
    by_key = {r.category: r for r in results}

    valid_present = [k for k in valid_variation_categories if k in by_key]
    shift_present = [k for k in shift_categories if k in by_key]
    valid_abstain = (
        float(np.mean([by_key[k].abstain_fraction for k in valid_present])) if valid_present else float("nan")
    )
    shift_abstain = (
        float(np.mean([by_key[k].abstain_fraction for k in shift_present])) if shift_present else float("nan")
    )

    if not valid_present or not shift_present or np.isnan(valid_abstain) or np.isnan(shift_abstain):
        verdict = "inconclusive"
        reasoning = "Insufficient categories present to compare valid-variation vs shift abstention."
    elif valid_abstain <= 0.10 and shift_abstain > valid_abstain + 0.10:
        verdict = "supported within tested scope"
        reasoning = (
            f"Valid structural variation is mostly accepted (abstain={valid_abstain:.2f}) while genuine "
            f"shift categories show materially higher abstention (abstain={shift_abstain:.2f}): the "
            "three-state policy usefully separates the two without excessive abstention on valid data."
        )
    elif valid_abstain > 0.10:
        verdict = "not supported"
        reasoning = (
            f"Valid structural variation is over-abstained (abstain={valid_abstain:.2f} > 0.10), "
            "repeating the Mission 5/6 over-abstention failure mode rather than fixing it."
        )
    else:
        verdict = "not supported"
        reasoning = (
            f"Genuine shift categories are not meaningfully more abstained than valid variation "
            f"(shift={shift_abstain:.2f} vs valid={valid_abstain:.2f}): the detector does not "
            "usefully separate the two on this evidence."
        )

    return StructuralOODResult(
        reference_channels=channels, s_low=s_low, s_high=s_high,
        calibration_note=(
            f"s_low = 90th percentile of in-domain (development) severity; s_high = 50th percentile "
            f"of the '{far_category}' ({far_description}) severity -- calibrated on development and "
            "a designated far category only, never on the judged categories themselves."
        ),
        categories=results, valid_variation_mean_abstain=valid_abstain, shift_mean_abstain=shift_abstain,
        verdict=verdict, reasoning=reasoning,
    )
