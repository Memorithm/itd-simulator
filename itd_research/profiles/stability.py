"""Event-profile stability across two independent sources (research, Mission 5, H34).

Compares per-channel predictive importance (single-channel held-out AUC) for the *same*
event produced by two independent codes -- the pseudo-spectral and finite-difference
Taylor-Green breakdowns. If the important channels agree across sources, the profile is
stable; if the ranking reshuffles, it is source-dependent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.evaluation import build_labeled, single_channel_aucs
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    features_from_raw,
    simulate_taylorgreen_raw,
)

FloatArray: TypeAlias = NDArray[np.float64]


def _spearman(a: FloatArray, b: FloatArray) -> float:
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    denom = float(np.sqrt(np.sum(ra**2) * np.sum(rb**2)))
    return float(np.sum(ra * rb) / denom) if denom > 0 else float("nan")


def channel_importance(dev, holdout) -> dict[str, float]:  # type: ignore[no-untyped-def]
    """Per-channel held-out AUC for one source."""
    return single_channel_aucs(dev, holdout, ALL_FEATURES)


@dataclass(frozen=True)
class ProfileStability:
    """Cross-source stability of the event-channel importance profile."""

    source_a: str
    source_b: str
    importance_a: dict[str, float]
    importance_b: dict[str, float]
    rank_correlation: float
    top3_overlap: float
    verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "source_a": self.source_a,
            "source_b": self.source_b,
            "importance_a": self.importance_a,
            "importance_b": self.importance_b,
            "rank_correlation": self.rank_correlation,
            "top3_overlap": self.top3_overlap,
            "verdict": self.verdict,
        }


def profile_stability(importance_a: dict[str, float], importance_b: dict[str, float],
                      source_a: str = "A", source_b: str = "B") -> ProfileStability:
    """Rank-correlate two channel-importance profiles for the same event."""
    channels = [c for c in ALL_FEATURES if c in importance_a and c in importance_b]
    a = np.array([importance_a[c] for c in channels])
    b = np.array([importance_b[c] for c in channels])
    correlation = _spearman(a, b)
    top_a = {channels[i] for i in np.argsort(a)[-3:]}
    top_b = {channels[i] for i in np.argsort(b)[-3:]}
    overlap = len(top_a & top_b) / 3.0
    if correlation >= 0.7 and overlap >= 2 / 3:
        verdict = "supported within tested scope"
    elif correlation >= 0.4 or overlap >= 1 / 3:
        verdict = "partially supported"
    else:
        verdict = "not supported"
    return ProfileStability(source_a, source_b, importance_a, importance_b, correlation, overlap, verdict)


def run_stability_study(*, quick: bool = False) -> ProfileStability:
    """H34: is the Taylor-Green channel profile stable across spectral and FD codes?"""
    from itd_research.cross_code.comparison import simulate_taylorgreen_fd_raw

    spec_kwargs = {"nodes": 16, "steps": 700, "record_every": 50} if quick else {}
    fd_kwargs = {"nodes": 16, "steps": 500, "record_every": 40} if quick else {}
    dev_seeds = (10, 11, 12) if quick else (10, 11, 12, 13)
    hold_seeds = (90, 91, 92) if quick else (90, 91, 92, 93)

    spec_dev = build_labeled([features_from_raw(simulate_taylorgreen_raw(s, **spec_kwargs)) for s in dev_seeds], 4)
    spec_hold = build_labeled([features_from_raw(simulate_taylorgreen_raw(s, **spec_kwargs)) for s in hold_seeds], 4)
    fd_dev = build_labeled([features_from_raw(simulate_taylorgreen_fd_raw(s, **fd_kwargs)) for s in dev_seeds], 4)
    fd_hold = build_labeled([features_from_raw(simulate_taylorgreen_fd_raw(s, **fd_kwargs)) for s in hold_seeds], 4)

    importance_spectral = channel_importance(spec_dev, spec_hold)
    importance_fd = channel_importance(fd_dev, fd_hold)
    return profile_stability(importance_spectral, importance_fd, "taylorgreen_spectral", "taylorgreen_fd")
