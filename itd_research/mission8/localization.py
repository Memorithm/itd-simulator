"""Non-redundancy (H63) and region-level localization (H69) analysis (Mission 8).

H63 requires more than a low pairwise correlation: a channel is non-redundant only if it
keeps predictive/associative value after the effect of a magnitude diagnostic (enstrophy)
is linearly removed (partial correlation), evaluated per development sequence and pooled.

H69 (does ITD improve independently-labelled REGION localization, e.g. IoU/Dice against
the Q-criterion ground truth) requires ITD to produce a per-cell spatial map. The existing,
already-implemented ITD-3D channels (``itd_research.diagnostics_3d.itd_3d``) are GLOBAL
per-snapshot scalars -- there is no per-cell ITD field to threshold into a region mask.
This is an honest ARCHITECTURAL finding, not a missing-data block: H69 cannot be tested
with the existing channel set without inventing a new per-cell channel, which the
preregistration and Mission 8 instructions explicitly forbid ("do not create new ITD
channels merely to obtain a positive result"). The region-metric machinery
(:mod:`itd_research.mission8.vortex_regions`) is otherwise complete and reusable if a
future, explicitly-scoped mission adds a spatial ITD channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.mission8.baselines import BaselineTrajectory
from itd_research.mission8.statistics import (
    partial_correlation,
    pearson_correlation,
    spearman_correlation,
)
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    StructuralTrajectory,
)

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class ChannelNonRedundancy:
    channel: str
    spearman_vs_enstrophy: float
    pearson_vs_enstrophy: float
    partial_correlation_vs_event_given_enstrophy: float

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "spearman_vs_enstrophy": self.spearman_vs_enstrophy,
            "pearson_vs_enstrophy": self.pearson_vs_enstrophy,
            "partial_correlation_vs_event_given_enstrophy": self.partial_correlation_vs_event_given_enstrophy,
        }


@dataclass(frozen=True)
class NonRedundancyResult:
    """H63: is any ITD structural channel non-redundant with a magnitude diagnostic?"""

    per_channel: list[ChannelNonRedundancy]
    non_redundant_channels: list[str]
    verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "per_channel": [c.as_dict() for c in self.per_channel],
            "non_redundant_channels": self.non_redundant_channels,
            "verdict": self.verdict,
        }


def evaluate_nonredundancy(
    structural: StructuralTrajectory, baseline: BaselineTrajectory, labels: NDArray[np.int64],
    *, channels: tuple[str, ...] = ITD_3D_NONREDUNDANT,
    correlation_threshold: float = 0.3, partial_threshold: float = 0.1,
) -> NonRedundancyResult:
    """H63: a channel is non-redundant only if it survives BOTH checks (never one alone).

    (1) low correlation with enstrophy AND (2) a non-trivial partial correlation with the
    event label after controlling for enstrophy. Per the preregistration, ``|rho| < 0.3``
    alone is explicitly NOT sufficient.
    """
    enstrophy = np.asarray(baseline.channels["enstrophy"], dtype=np.float64)
    label_f = labels.astype(np.float64)
    per_channel = []
    non_redundant = []
    for name in channels:
        values = np.asarray(structural.channels[name], dtype=np.float64)
        rho_s = spearman_correlation(values, enstrophy)
        rho_p = pearson_correlation(values, enstrophy)
        partial = partial_correlation(values, label_f, enstrophy)
        per_channel.append(ChannelNonRedundancy(name, rho_s, rho_p, partial))
        low_corr = (not np.isnan(rho_s)) and abs(rho_s) < correlation_threshold
        useful_partial = (not np.isnan(partial)) and abs(partial) >= partial_threshold
        if low_corr and useful_partial:
            non_redundant.append(name)
    verdict = "supported within tested scope" if non_redundant else "not supported"
    return NonRedundancyResult(per_channel=per_channel, non_redundant_channels=non_redundant, verdict=verdict)


@dataclass(frozen=True)
class RegionLocalizationStatus:
    """H69 status: architecturally blocked (no per-cell ITD channel), not data-blocked."""

    verdict: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {"verdict": self.verdict, "reason": self.reason}


def evaluate_region_localization() -> RegionLocalizationStatus:
    """H69: honestly blocked -- the existing ITD-3D channels have no spatial output."""
    return RegionLocalizationStatus(
        verdict="blocked",
        reason=(
            "Existing ITD-3D channels (intensity, heterogeneity, localization, roughness, "
            "orientation_dispersion, helicity_mean, normalized_helicity, stretching_rate) are "
            "GLOBAL per-snapshot scalars, not per-cell fields. Region-level IoU/Dice/centroid "
            "comparison against the established Q-criterion ground truth requires a spatial ITD "
            "map, which does not exist in the current signature. Per the preregistration and "
            "Mission 8 instructions, no new channel is invented to manufacture a testable "
            "region-level ITD output. The region-metric machinery (vortex_regions.py: iou, "
            "dice, centroid_distance, max_nearest_distance) is complete and reusable if a "
            "future, explicitly-scoped mission adds a spatial channel."
        ),
    )
