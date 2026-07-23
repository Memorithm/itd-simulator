"""Experiment catalogue: ITD versus established diagnostics on many flows (research).

Each case builds a 2D velocity field, then computes on the *same* second-order
velocity-gradient tensor:

* the established local diagnostics -- vorticity, Q-criterion, swirling strength,
  Okubo-Weiss -- reduced to rotation regions and correlations;
* the ITD structural signature and the established global diagnostics (enstrophy,
  palinstrophy, flatness) via the V29.18 operators.

The headline comparison is **shear versus rotation**: the region of large
vorticity magnitude (which drives ITD's rotational intensity) is overlapped with
the rotation region ``Q > 0`` (which swirling strength and lambda_2 also detect).
Pure shear has large vorticity but no rotation, so the overlap is near zero;
coherent vortices have both, so the overlap is high. This quantifies where ITD's
vorticity-based view coincides with, and where it departs from, rotation-based
vortex identification.

Cases are labelled ``analytical`` (exact oracles), ``synthetic`` (deterministic
CFD-like stand-ins -- never external empirical validation), or ``external``
(a licensed experimental PIV field).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.operators import (
    velocity_gradient_2d,
    vorticity_2d_from_gradient,
)
from itd_research.diagnostics_3d.velocity_gradient import (
    okubo_weiss_2d,
    q_criterion,
    strain_rate_magnitude,
    swirling_strength,
)
from itd_research.established_diagnostics import established_diagnostics
from itd_research.external_validation import synthetic_flows as sf
from itd_research.external_validation.comparison import (
    compare_scalar_fields,
    connected_components,
    region_overlap,
    threshold_region,
)
from itd_research.io.field_data import FieldData2D
from itd_research.io.npz import read_npz_field_2d
from itd_research.signature import evaluate_signature

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]

_SWIRL_REL_TOL = 1.0e-6
_HIGH_VORTICITY_QUANTILE = 0.8


@dataclass(frozen=True)
class FlowCase:
    """One velocity field with its metadata and evaluation convention."""

    name: str
    category: str
    description: str
    u: FloatArray
    v: FloatArray
    x: FloatArray
    y: FloatArray
    boundary_mode: str


@dataclass(frozen=True)
class ExperimentResult:
    """ITD signature, established diagnostics, and region agreement for one case."""

    name: str
    category: str
    description: str
    shape: tuple[int, int]
    boundary_mode: str
    itd: dict[str, float]
    established: dict[str, float]
    diagnostics: dict[str, float]
    regions: dict[str, float]
    correlations: dict[str, float | None]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "shape": list(self.shape),
            "boundary_mode": self.boundary_mode,
            "itd": self.itd,
            "established": self.established,
            "diagnostics": self.diagnostics,
            "regions": self.regions,
            "correlations": self.correlations,
        }


def _spacing(x: FloatArray, y: FloatArray) -> tuple[float, float]:
    return (float(x[1] - x[0]), float(y[1] - y[0]))


def run_case(case: FlowCase) -> ExperimentResult:
    """Compute the ITD signature, established diagnostics, and region agreement."""
    spacing = _spacing(case.x, case.y)
    gradient = velocity_gradient_2d(case.u, case.v, case.x, case.y, case.boundary_mode)
    omega = vorticity_2d_from_gradient(gradient)
    abs_omega = np.abs(omega)
    q_field = q_criterion(gradient)
    swirl = swirling_strength(gradient)
    weiss = okubo_weiss_2d(gradient)
    strain = strain_rate_magnitude(gradient)

    signature = evaluate_signature(case.u, case.v, spacing, case.boundary_mode)
    established = established_diagnostics(case.u, case.v, spacing, case.boundary_mode)

    # Regions: rotation (Q>0), swirl-active, Okubo-Weiss vortex (W<0), high-|omega|.
    rotation = threshold_region(q_field, sign="positive")
    weiss_vortex = threshold_region(weiss, sign="negative")
    swirl_max = float(np.max(swirl)) if swirl.size else 0.0
    if swirl_max > 0.0:
        swirl_active = swirl >= _SWIRL_REL_TOL * swirl_max
    else:
        swirl_active = np.zeros(swirl.shape, dtype=bool)
    high_omega = threshold_region(abs_omega, quantile=_HIGH_VORTICITY_QUANTILE)

    overlap_omega_rotation = region_overlap(high_omega, rotation)
    overlap_swirl_rotation = region_overlap(swirl_active, rotation)
    n_rotation, rotation_sizes = connected_components(rotation)
    n_high_omega, _ = connected_components(high_omega)

    total = float(omega.size)
    diagnostics = {
        "vorticity_rms": float(np.sqrt(np.mean(omega**2))),
        "abs_vorticity_mean": float(np.mean(abs_omega)),
        "q_mean": float(np.mean(q_field)),
        "q_max": float(np.max(q_field)),
        "swirl_rms": float(np.sqrt(np.mean(swirl**2))),
        "swirl_max": swirl_max,
        "strain_rms": float(np.sqrt(np.mean(strain**2))),
        "okubo_weiss_mean": float(np.mean(weiss)),
    }
    regions = {
        "rotation_fraction": float(np.count_nonzero(rotation)) / total,
        "swirl_active_fraction": float(np.count_nonzero(swirl_active)) / total,
        "weiss_vortex_fraction": float(np.count_nonzero(weiss_vortex)) / total,
        "high_vorticity_quantile": _HIGH_VORTICITY_QUANTILE,
        "jaccard_highomega_rotation": overlap_omega_rotation.jaccard,
        "dice_highomega_rotation": overlap_omega_rotation.dice,
        "jaccard_swirl_rotation": overlap_swirl_rotation.jaccard,
        "rotation_components": float(n_rotation),
        "largest_rotation_component": float(rotation_sizes[0]) if rotation_sizes else 0.0,
        "high_vorticity_components": float(n_high_omega),
    }
    correlations: dict[str, float | None] = {}
    correlations.update(
        {f"absomega_swirl_{k}": v for k, v in compare_scalar_fields(abs_omega, swirl).items()}
    )
    correlations.update(
        {f"absomega_q_{k}": v for k, v in compare_scalar_fields(abs_omega, q_field).items()}
    )

    return ExperimentResult(
        name=case.name,
        category=case.category,
        description=case.description,
        shape=(int(case.y.size), int(case.x.size)),
        boundary_mode=case.boundary_mode,
        itd=signature.as_dict(),
        established={k: float(v) for k, v in established.items()},
        diagnostics=diagnostics,
        regions=regions,
        correlations=correlations,
    )


# --------------------------------------------------------------------------- #
# Case builders.                                                              #
# --------------------------------------------------------------------------- #


def _linear_2d(grid: sf.Grid2D, a11: float, a12: float, a21: float, a22: float) -> tuple[FloatArray, FloatArray]:
    u = a11 * grid.xx + a12 * grid.yy
    v = a21 * grid.xx + a22 * grid.yy
    return u.astype(np.float64), v.astype(np.float64)


def analytical_cases() -> list[FlowCase]:
    """Exact analytical oracles with known shear/rotation content."""
    grid = sf.finite_grid_2d(41, 41, (-2.0, 2.0), (-2.0, 2.0))
    cases: list[FlowCase] = []

    u, v = _linear_2d(grid, 0.0, -1.3, 1.3, 0.0)
    cases.append(FlowCase("rigid_rotation", "analytical",
                          "solid-body rotation: rotation everywhere, zero strain",
                          u, v, grid.x, grid.y, "finite"))

    u, v = _linear_2d(grid, 0.9, 0.0, 0.0, -0.9)
    cases.append(FlowCase("pure_strain", "analytical",
                          "incompressible planar strain: strain only, zero vorticity",
                          u, v, grid.x, grid.y, "finite"))

    u, v = _linear_2d(grid, 0.0, 1.5, 0.0, 0.0)
    cases.append(FlowCase("simple_shear", "analytical",
                          "simple shear: large vorticity but Q=0 (no rotation)",
                          u, v, grid.x, grid.y, "finite"))

    u, v = _linear_2d(grid, 0.6, 1.5, 0.0, -0.6)
    cases.append(FlowCase("strain_plus_shear", "analytical",
                          "superposed strain and shear (still non-rotational)",
                          u, v, grid.x, grid.y, "finite"))

    u, v = sf.lamb_oseen_vortex(grid, circulation=3.0, core_radius=0.5)
    cases.append(FlowCase("lamb_oseen", "analytical",
                          "single Lamb-Oseen vortex: compact rotation-dominated core",
                          u, v, grid.x, grid.y, "finite"))

    u, v = sf.vortex_pair(grid, circulation=3.0, core_radius=0.4, separation=1.6)
    cases.append(FlowCase("vortex_pair", "analytical",
                          "counter-rotating vortex pair: two rotation cores",
                          u, v, grid.x, grid.y, "finite"))
    return cases


def synthetic_cfd_cases() -> list[FlowCase]:
    """Deterministic synthetic CFD-like flows (never external empirical data)."""
    cases: list[FlowCase] = []

    shear_grid = sf.finite_grid_2d(64, 48, (0.0, 2.0 * np.pi), (-2.5, 2.5))
    u, v = sf.shear_layer(shear_grid, u_infinity=1.0, thickness=0.5)
    cases.append(FlowCase("mixing_layer_base", "synthetic",
                          "tanh mixing-layer base state (pure shear, KH precursor)",
                          u, v, shear_grid.x, shear_grid.y, "finite"))

    u, v = sf.stuart_vortices(shear_grid, concentration=4.0, amplitude=1.0)
    cases.append(FlowCase("kh_rollup", "synthetic",
                          "Stuart cat's-eye roll-up (exact steady Euler mixing layer)",
                          u, v, shear_grid.x, shear_grid.y, "finite"))

    tg_grid = sf.periodic_grid_2d(64, 2.0 * np.pi)
    u, v = sf.taylor_green_2d(tg_grid, amplitude=1.0, wavenumber=1.0)
    cases.append(FlowCase("taylor_green", "synthetic",
                          "Taylor-Green cellular flow (checkerboard of vortices)",
                          u, v, tg_grid.x, tg_grid.y, "periodic"))

    wake_grid = sf.finite_grid_2d(120, 64, (0.0, 12.0), (-2.5, 2.5))
    u, v = sf.karman_street(wake_grid, circulation=1.2, core_radius=0.3,
                            row_spacing=1.2, vortex_spacing=2.0, rows=3)
    cases.append(FlowCase("karman_street", "synthetic",
                          "staggered vortex street (synthetic cylinder-wake analogue)",
                          u, v, wake_grid.x, wake_grid.y, "finite"))
    return cases


def _largest_valid_rectangle(mask: BoolArray) -> tuple[int, int, int, int]:
    """Largest all-valid axis-aligned rectangle (row0, row1, col0, col1) half-open."""
    ny, nx = mask.shape
    heights = np.zeros(nx, dtype=np.int64)
    best = (0, 0, 0, 0, 0)
    for r in range(ny):
        heights = np.where(mask[r], heights + 1, 0)
        stack: list[tuple[int, int]] = []
        for i in range(nx + 1):
            h = int(heights[i]) if i < nx else 0
            start = i
            while stack and stack[-1][1] > h:
                s, hh = stack.pop()
                area = hh * (i - s)
                if area > best[0]:
                    best = (area, r - hh + 1, r + 1, s, i)
                start = s
            stack.append((start, h))
    _, r0, r1, c0, c1 = best
    return r0, r1, c0, c1


def field_to_case(field: FieldData2D, name: str, description: str) -> FlowCase:
    """Turn an ingested 2D field into a case, cropping to the largest valid block.

    The gradient operators require finite data, so if the field carries a validity
    mask the largest fully-valid interior rectangle is used and the crop is part of
    the reported provenance (the caller logs it).
    """
    u = np.asarray(field.u, dtype=np.float64)
    v = np.asarray(field.v, dtype=np.float64)
    x = np.asarray(field.x, dtype=np.float64)
    y = np.asarray(field.y, dtype=np.float64)
    if field.mask is not None:
        r0, r1, c0, c1 = _largest_valid_rectangle(np.asarray(field.mask, dtype=bool))
        if (r1 - r0) < 3 or (c1 - c0) < 3:
            raise ValueError("no 3x3 fully-valid rectangle in the masked field.")
        u, v = u[r0:r1, c0:c1], v[r0:r1, c0:c1]
        y, x = y[r0:r1], x[c0:c1]
    declared = field.metadata.boundary_mode
    boundary_mode = declared if declared in ("finite", "periodic") else "finite"
    return FlowCase(name, "external", description, u, v, x, y, boundary_mode)


def external_piv_case(
    npz_path: str | Path,
    name: str = "biofilm_piv",
    description: str = "experimental PIV mean turbulent boundary layer (Zenodo 1175014)",
) -> FlowCase:
    """Load an external PIV field from ``.npz`` as an ``external`` case."""
    from itd_research.io.field_data import FieldMetadata

    metadata = FieldMetadata(
        source="Zenodo 1175014 (Murphy et al. 2018), CC-BY-4.0",
        length_unit="m",
        velocity_unit="m/s",
        boundary_mode="finite",
    )
    field = read_npz_field_2d(npz_path, metadata)
    return field_to_case(field, name, description)


def run_suite(cases: Sequence[FlowCase]) -> list[ExperimentResult]:
    """Run every case and return the results in order."""
    return [run_case(case) for case in cases]
