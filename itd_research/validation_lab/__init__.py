"""ITD validation laboratory: candidates, statistics, ablation, thresholds (research).

Controlled, evidence-based campaigns for the falsifiable questions H9-H12: which
ITD channels carry non-redundant information, whether a reduced/modified 3D
candidate improves the accuracy-robustness-cost trade-off, which components
transfer across flow families, and whether thresholds transfer. Part of the
isolated ``itd_research`` namespace; never modifies the certified V29.18 core;
imports no plotting library at import time; performs no network access.
"""

from __future__ import annotations

from itd_research.validation_lab.candidates import (
    CANDIDATES,
    Candidate,
    channel_superset,
    evaluate_channels,
)
from itd_research.validation_lab.statistics import (
    ChannelDependence,
    channel_dependence,
    condition_number,
    pca_explained_variance,
    pearson_matrix,
    spearman_matrix,
    variance_inflation_factors,
)

__all__ = (
    "Candidate",
    "CANDIDATES",
    "channel_superset",
    "evaluate_channels",
    "ChannelDependence",
    "channel_dependence",
    "pearson_matrix",
    "spearman_matrix",
    "variance_inflation_factors",
    "condition_number",
    "pca_explained_variance",
)
