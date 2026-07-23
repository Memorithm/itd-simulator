"""External-evidence acquisition and analysis (research, Mission 7).

Mission 6 established a decisive negative for ITD's cross-code advantage on *local*
simulations. Mission 7 stops manufacturing local flows and instead asks whether ITD
carries reproducible information on **genuinely external** fluid-dynamics data generated
independently of this repository. This package provides safe external ingestion with
provenance, physical validation that must pass before any predictive claim, descriptive
ITD-vs-established analysis, an ITD-independent event definition, and a locked prediction
protocol -- operating on real external sources (JHTDB DNS, Zenodo PIV) or, in offline CI,
a clearly-labelled synthetic fixture that is NEVER presented as external evidence.

Experimental research; does not modify ``ITD V29.18``. Depends on the certified core and
``itd_research`` diagnostics, never the reverse. Normal CI never touches the network.
"""

from __future__ import annotations

from itd_research.mission7.analysis import (
    ComplementarityResult,
    DiagnosticTrajectories,
    ExternalPredictionResult,
    compute_trajectories,
    external_prediction,
    label_enstrophy_event,
    rank_complementarity,
)
from itd_research.mission7.campaign import ExternalCampaignResult, run_external_campaign
from itd_research.mission7.ingestion import (
    IngestionLimits,
    SequenceProvenance,
    load_field_sequence,
)
from itd_research.mission7.physics import PhysicalValidation, validate_isotropic_dns

__all__ = [
    "ComplementarityResult",
    "DiagnosticTrajectories",
    "ExternalCampaignResult",
    "ExternalPredictionResult",
    "IngestionLimits",
    "PhysicalValidation",
    "SequenceProvenance",
    "compute_trajectories",
    "external_prediction",
    "label_enstrophy_event",
    "load_field_sequence",
    "rank_complementarity",
    "run_external_campaign",
    "validate_isotropic_dns",
]
