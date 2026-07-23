"""Cross-flow generalization and transfer studies (research, H8/H9/H10/H13).

Tests, under leakage-safe leave-one-flow-out and the harder leave-one-family-out
protocols, whether ITD-3D channels (and thresholds and component relationships)
transfer to unseen flows and unseen flow families -- and how they compare to
established velocity-gradient diagnostics. Experimental research code; it does not
modify or re-certify ``ITD V29.18``. Negative transfer is a valid outcome and is
reported as such.
"""

from __future__ import annotations

from itd_research.generalization.baselines import (
    BASELINE_FEATURES,
    baseline_features_on_subcube,
)
from itd_research.generalization.transfer import (
    ComponentTransfer,
    GeneralizationResult,
    GeneralizationSamples,
    ThresholdTransfer,
    classify_h9,
    classify_h10,
    classify_h13,
    component_transfer,
    family_generalization,
    sample_generalization,
    threshold_transfer,
)

__all__ = [
    "BASELINE_FEATURES",
    "ComponentTransfer",
    "GeneralizationResult",
    "GeneralizationSamples",
    "ThresholdTransfer",
    "baseline_features_on_subcube",
    "classify_h9",
    "classify_h10",
    "classify_h13",
    "component_transfer",
    "family_generalization",
    "sample_generalization",
    "threshold_transfer",
]
