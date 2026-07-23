"""External-validation experiments comparing ITD with established diagnostics.

This subpackage runs a deterministic suite that places the ITD structural
signature side by side with established vortex-identification diagnostics
(vorticity, Q-criterion, swirling strength, Okubo-Weiss, enstrophy) on:

* exact analytical fields (rigid rotation, strain, shear, Lamb-Oseen, ...),
* deterministic **synthetic** CFD-like fields (Karman street, Kelvin-Helmholtz
  roll-up, Taylor-Green) that stand in for solver output we cannot run in this
  environment, and
* at least one genuinely external, licensed **experimental PIV** field.

It is part of the isolated ``itd_research`` namespace, never modifies the
certified V29.18 core, is never imported by ``itd_v29_core``, imports no plotting
library at import time, and performs no network access. Nothing here is a
certified scientific revision; synthetic fields are never presented as external
empirical validation.
"""

from __future__ import annotations

from itd_research.external_validation.comparison import (
    RegionOverlap,
    compare_scalar_fields,
    connected_components,
    pearson_correlation,
    region_overlap,
    spearman_correlation,
    threshold_region,
)
from itd_research.external_validation.experiments import (
    ExperimentResult,
    analytical_cases,
    external_piv_case,
    run_case,
    run_suite,
    synthetic_cfd_cases,
)
from itd_research.external_validation.hypotheses import (
    equal_enstrophy_separation,
    vortex_merger_sequence,
)
from itd_research.external_validation.transport import (
    TransportDecomposition,
    translate_periodic,
    transport_decomposition,
)

__all__ = (
    "RegionOverlap",
    "region_overlap",
    "threshold_region",
    "connected_components",
    "pearson_correlation",
    "spearman_correlation",
    "compare_scalar_fields",
    "ExperimentResult",
    "run_case",
    "run_suite",
    "analytical_cases",
    "synthetic_cfd_cases",
    "external_piv_case",
    "equal_enstrophy_separation",
    "vortex_merger_sequence",
    "TransportDecomposition",
    "transport_decomposition",
    "translate_periodic",
)
