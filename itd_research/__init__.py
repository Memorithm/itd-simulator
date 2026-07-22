"""Post-V29 dimensional-validation research package.

This is an isolated *research* namespace layered on top of the certified,
immutable ``ITD V29.18`` baseline. It never modifies V29.18 behaviour and is
never imported by ``itd_v29_core``; the dependency direction is one-way
(``itd_research`` -> ``itd_v29_core``). Importing this package does not initialise
Matplotlib or select a plotting backend: plotting lives behind the explicit
``itd_research.plotting`` boundary and imports Matplotlib lazily.

Nothing here is a certified scientific revision. The work is labelled a
"post-V29 dimensional-temporal-deformation research candidate" until evidence
justifies a reviewed revision.
"""

from __future__ import annotations

from itd_research.analytical_cases import (
    Grid,
    counter_rotating_pair,
    finite_grid,
    lamb_oseen,
    lamb_oseen_vorticity,
    periodic_grid,
    solid_body_rotation,
    taylor_green,
    taylor_green_vorticity,
    uniform_shear,
    zero_field,
)
from itd_research.benchmark_runner import (
    FULL,
    QUICK,
    BenchmarkResolution,
    run_benchmarks,
)
from itd_research.convergence import observed_order, run_convergence
from itd_research.established_diagnostics import (
    established_diagnostics,
    vorticity_diagnostics,
)
from itd_research.sensitivity import run_sensitivity
from itd_research.signature import SignatureResult, evaluate_signature
from itd_research.temporal_scaling import (
    TemporalDeformationResult,
    TemporalScaleDefinition,
    TemporalScalePolicy,
    raw_temporal_deformation,
    scale_temporal_deformation,
    temporal_deformation_from_fields,
)

__all__ = (
    # temporal scaling (the research centrepiece)
    "TemporalScalePolicy",
    "TemporalScaleDefinition",
    "TemporalDeformationResult",
    "raw_temporal_deformation",
    "scale_temporal_deformation",
    "temporal_deformation_from_fields",
    # analytical cases
    "Grid",
    "finite_grid",
    "periodic_grid",
    "zero_field",
    "solid_body_rotation",
    "uniform_shear",
    "taylor_green",
    "taylor_green_vorticity",
    "lamb_oseen",
    "lamb_oseen_vorticity",
    "counter_rotating_pair",
    # signature and diagnostics
    "SignatureResult",
    "evaluate_signature",
    "established_diagnostics",
    "vorticity_diagnostics",
    # runners
    "BenchmarkResolution",
    "QUICK",
    "FULL",
    "run_benchmarks",
    "run_convergence",
    "observed_order",
    "run_sensitivity",
)
