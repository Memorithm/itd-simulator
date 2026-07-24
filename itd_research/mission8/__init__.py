"""Non-redundant structural and topological external validation (research, Mission 8).

Mission 7 showed ITD adds no incremental value on an externally-sourced event that
established magnitude diagnostics (enstrophy) already predict perfectly. Mission 8 does
not repeat that saturated experiment: it asks whether EXISTING non-magnitude ITD channels
(structural, orientation, temporal, 3D-nonredundant -- explicitly excluding ``intensity``
as primary evidence) provide reproducible, transferable, incrementally useful information
for external, ITD-INDEPENDENT structural/topological vortex events (core merger/split)
that competent established structural diagnostics (Q, lambda2, swirl, region counts, core
tracking) do not already capture. Events are labelled purely from the Q-criterion
connected-component count, never from ITD; a preregistered saturation screen excludes any
task the established baseline already solves before ITD is ever consulted.

Experimental research; does not modify ``ITD V29.18``. Depends on the certified core and
``itd_research`` diagnostics, never the reverse. Normal CI never touches the network --
it runs a bounded, deterministic manufactured-oracle fixture instead (never presented as
external evidence).
"""

from __future__ import annotations

from itd_research.mission8.baselines import (
    BASELINE_COMPETENT_COMBINED,
    compute_baseline_trajectory,
)
from itd_research.mission8.campaign import (
    Mission8CampaignResult,
    run_full_fixture_validation,
    run_structural_campaign,
)
from itd_research.mission8.event_labels import label_structural_events
from itd_research.mission8.ingestion import load_sequence_as_tuples
from itd_research.mission8.prediction import (
    PrimaryTestResult,
    Sequence,
    run_primary_test,
)
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    compute_structural_trajectory,
)

__all__ = [
    "BASELINE_COMPETENT_COMBINED",
    "ITD_3D_NONREDUNDANT",
    "Mission8CampaignResult",
    "PrimaryTestResult",
    "Sequence",
    "compute_baseline_trajectory",
    "compute_structural_trajectory",
    "label_structural_events",
    "load_sequence_as_tuples",
    "run_full_fixture_validation",
    "run_primary_test",
    "run_structural_campaign",
]
