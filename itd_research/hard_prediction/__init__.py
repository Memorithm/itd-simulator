"""Hard external predictive validation of ITD (research, Mission 4, H17-H22).

Leakage-safe, grouped-by-simulation prediction on deliberately hard held-out flows
(perturbed, jittered, degraded), centred on the decisive question: does adding ITD to
a locked established-diagnostic set improve held-out prediction? Experimental research
code; it does not modify or re-certify ``ITD V29.18``. Negative and blocked outcomes
are valid and preserved.
"""

from __future__ import annotations

from itd_research.hard_prediction.degradation import DegradationSpec
from itd_research.hard_prediction.evaluation import (
    AddedValueResult,
    FeatureSetMetrics,
    added_value,
    build_labeled,
    evaluate_feature_set,
)
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    ESTABLISHED_FEATURES,
    ITD_FEATURES,
    HardRun,
    RawRun,
    features_from_raw,
    simulate_merger_raw,
    simulate_taylorgreen_raw,
)
from itd_research.hard_prediction.protocol import (
    PREREGISTERED_SHA256,
    load_protocol,
    protocol_sha256,
)

__all__ = [
    "ALL_FEATURES",
    "ESTABLISHED_FEATURES",
    "ITD_FEATURES",
    "PREREGISTERED_SHA256",
    "AddedValueResult",
    "DegradationSpec",
    "FeatureSetMetrics",
    "HardRun",
    "RawRun",
    "added_value",
    "build_labeled",
    "evaluate_feature_set",
    "features_from_raw",
    "load_protocol",
    "protocol_sha256",
    "simulate_merger_raw",
    "simulate_taylorgreen_raw",
]
