"""Targeted hypothesis demonstrations H1 and H2 (research).

Two focused, deterministic demonstrations that the general suite frames but does
not isolate:

* :func:`equal_enstrophy_separation` (H1) -- two velocity fields with *identical*
  enstrophy that a single scalar cannot tell apart, yet whose ITD structural
  vectors differ by a large margin. This is the core ITD claim: the
  five-component vector carries organisation information a scalar does not.
* :func:`vortex_merger_sequence` (H2 mechanism) -- a kinematic two-vortex merger
  in which an ITD-independent transition marker (the count of significant
  rotation regions) drops from two to one, tracked alongside the ITD channels.
  This is a **synthetic** demonstration of the transition-detection mechanism, not
  a test on externally annotated data.

Nothing here is a certified revision; synthetic sequences are never presented as
external empirical validation.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.operators import velocity_gradient_2d
from itd_research.diagnostics_3d.velocity_gradient import q_criterion
from itd_research.established_diagnostics import established_diagnostics
from itd_research.external_validation import synthetic_flows as sf
from itd_research.external_validation.comparison import (
    connected_components,
    threshold_region,
)
from itd_research.signature import evaluate_signature

FloatArray: TypeAlias = NDArray[np.float64]


def equal_enstrophy_separation() -> dict[str, object]:
    """H1: match enstrophy exactly, then show the ITD vector still separates.

    Field A is a distributed Taylor-Green checkerboard; field B is a single
    concentrated vortex. Field B is rescaled so its enstrophy equals field A's.
    The magnitude-based ITD components are amplitude-invariant, so the rescaling
    does not manufacture the separation -- it removes the only scalar (enstrophy)
    that could have distinguished the two.
    """
    grid_a = sf.periodic_grid_2d(64, 2.0 * np.pi)
    u_a, v_a = sf.taylor_green_2d(grid_a, 1.0, 1.0)
    spacing_a = grid_a.spacing

    grid_b = sf.finite_grid_2d(64, 64, (-3.0, 3.0), (-3.0, 3.0))
    u_b, v_b = sf.lamb_oseen_vortex(grid_b, 3.0, 0.4)
    spacing_b = grid_b.spacing

    enstrophy_a = float(established_diagnostics(u_a, v_a, spacing_a, "periodic")["enstrophy"])
    enstrophy_b = float(established_diagnostics(u_b, v_b, spacing_b, "finite")["enstrophy"])
    scale = float(np.sqrt(enstrophy_a / enstrophy_b))
    u_b, v_b = u_b * scale, v_b * scale
    enstrophy_b_scaled = float(established_diagnostics(u_b, v_b, spacing_b, "finite")["enstrophy"])

    signature_a = evaluate_signature(u_a, v_a, spacing_a, "periodic")
    signature_b = evaluate_signature(u_b, v_b, spacing_b, "finite")
    localization_ratio = (
        signature_b.localization / signature_a.localization
        if signature_a.localization > 0.0 else float("inf")
    )
    heterogeneity_ratio = (
        signature_b.heterogeneity / signature_a.heterogeneity
        if signature_a.heterogeneity > 0.0 else float("inf")
    )
    return {
        "enstrophy_a": enstrophy_a,
        "enstrophy_b": enstrophy_b_scaled,
        "enstrophy_matched": bool(np.isclose(enstrophy_a, enstrophy_b_scaled, rtol=1e-6)),
        "itd_distributed": signature_a.as_dict(),
        "itd_concentrated": signature_b.as_dict(),
        "localization_ratio": localization_ratio,
        "heterogeneity_ratio": heterogeneity_ratio,
    }


def _significant_components(mask: NDArray[np.bool_], min_size: int) -> tuple[int, int]:
    """Count connected components with at least ``min_size`` cells; return the largest."""
    _, sizes = connected_components(mask)
    kept = [size for size in sizes if size >= min_size]
    return len(kept), (kept[0] if kept else 0)


def vortex_merger_sequence(
    separations: tuple[float, ...] = (3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.6, 0.3),
    min_component_cells: int = 8,
) -> list[dict[str, object]]:
    """H2 mechanism: two co-rotating vortices approach and merge.

    For each frame (decreasing separation) it reports the count of *significant*
    rotation regions (small strain-fragmented patches are filtered by
    ``min_component_cells``), the largest region's cell count, and the ITD
    signature including the temporal-deformation channel relative to the previous
    frame. The significant-region count drops from two to one at the merger -- an
    ITD-independent transition marker -- while the ITD localization and intensity
    change across the event.
    """
    grid = sf.finite_grid_2d(96, 64, (-4.0, 4.0), (-3.0, 3.0))
    spacing = grid.spacing
    frames: list[dict[str, object]] = []
    previous_omega: FloatArray | None = None
    from itd_v29_core.spatial_operators import numerical_vorticity_with_boundary

    for separation in separations:
        ua, va = sf._lamb_oseen_velocity(grid.xx, grid.yy, 3.0, 0.5, (-separation / 2.0, 0.0))
        ub, vb = sf._lamb_oseen_velocity(grid.xx, grid.yy, 3.0, 0.5, (separation / 2.0, 0.0))
        u, v = ua + ub, va + vb

        gradient = velocity_gradient_2d(u, v, grid.x, grid.y, "finite")
        rotation = threshold_region(q_criterion(gradient), sign="positive")
        n_significant, largest = _significant_components(rotation, min_component_cells)

        signature = evaluate_signature(
            u, v, spacing, "finite",
            previous_omega=previous_omega,
            delta_time=1.0 if previous_omega is not None else None,
        )
        frames.append({
            "separation": float(separation),
            "significant_rotation_regions": n_significant,
            "largest_region_cells": largest,
            "itd_intensity": signature.intensity,
            "itd_localization": signature.localization,
            "itd_heterogeneity": signature.heterogeneity,
            "itd_temporal_deformation": signature.temporal_deformation,
        })
        previous_omega = numerical_vorticity_with_boundary(u, v, spacing, "finite")
    return frames
