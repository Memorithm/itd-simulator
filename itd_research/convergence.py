"""Deterministic grid-convergence study for the post-V29 research phase.

The study refines the mesh and measures how discrete ITD-relevant quantities
approach analytical references. Observed convergence orders are estimated only
where they are meaningful: not for exact algebraic identities (roundoff-limited),
not when a reference is numerically zero, and not when the errors are not
monotonically decreasing (a sign that a grid is outside the asymptotic regime).

Rows carry every quantity needed to reproduce and audit a data point, including
the software commit and interpreter/NumPy versions supplied by the caller.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research import analytical_cases as ac
from itd_research.signature import evaluate_signature
from itd_v29_core.constants import ZERO_THRESHOLD
from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    spatial_mean,
)

FloatArray: TypeAlias = NDArray[np.float64]

CONVERGENCE_COLUMNS = (
    "study",
    "case",
    "resolution",
    "spacing",
    "timestep",
    "boundary_mode",
    "interpolation",
    "reference_value",
    "computed_value",
    "absolute_error",
    "relative_error",
    "observed_order",
)

# Errors at or below this multiple of the reference are treated as roundoff and
# excluded from order estimation.
_ROUNDOFF_FLOOR = 1.0e3 * np.finfo(np.float64).eps

FINITE_GRID_SIZES = (17, 33, 65, 129)
PERIODIC_GRID_SIZES = (16, 32, 64, 128)


@dataclass(frozen=True)
class ConvergencePoint:
    study: str
    case: str
    resolution: int
    spacing: float
    boundary_mode: str
    reference_value: float
    computed_value: float

    @property
    def absolute_error(self) -> float:
        return abs(self.computed_value - self.reference_value)

    @property
    def relative_error(self) -> float | None:
        if abs(self.reference_value) < ZERO_THRESHOLD:
            return None
        return self.absolute_error / abs(self.reference_value)


def observed_order(
    coarse_error: float,
    fine_error: float,
    coarse_spacing: float,
    fine_spacing: float,
    *,
    reference_magnitude: float,
) -> float | None:
    """Return the observed order or ``None`` when it is not estimable.

    ``None`` is returned when either error is at or below the roundoff floor
    relative to the reference, when an error is non-positive, or when the error
    did not decrease under refinement (outside the asymptotic regime).
    """
    floor = max(_ROUNDOFF_FLOOR * max(reference_magnitude, 1.0), np.finfo(np.float64).tiny)
    if coarse_error <= floor or fine_error <= floor:
        return None
    if fine_error >= coarse_error:
        return None
    ratio = coarse_spacing / fine_spacing
    if ratio <= 1.0:
        return None
    return float(np.log(coarse_error / fine_error) / np.log(ratio))


def _points_to_rows(
    points: Sequence[ConvergencePoint],
    interpolation: str,
) -> list[list[object]]:
    rows: list[list[object]] = []
    for index, point in enumerate(points):
        order: float | None = None
        if index > 0:
            previous = points[index - 1]
            order = observed_order(
                previous.absolute_error,
                point.absolute_error,
                previous.spacing,
                point.spacing,
                reference_magnitude=abs(point.reference_value),
            )
        relative = point.relative_error
        rows.append(
            [
                point.study,
                point.case,
                point.resolution,
                point.spacing,
                "n/a",
                point.boundary_mode,
                interpolation,
                point.reference_value,
                point.computed_value,
                point.absolute_error,
                "n/a" if relative is None else relative,
                "n/a" if order is None else order,
            ]
        )
    return rows


def _taylor_green_enstrophy(sizes: Sequence[int]) -> list[ConvergencePoint]:
    amplitude, wavenumber = 1.0, 1.0
    period = 2.0 * np.pi / wavenumber
    reference = ac.taylor_green_mean_square_vorticity(amplitude, wavenumber)
    points: list[ConvergencePoint] = []
    for size in sizes:
        grid = ac.periodic_grid(size, period)
        vx, vy = ac.taylor_green(grid.x, grid.y, amplitude, wavenumber)
        omega = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "periodic")
        computed = float(spatial_mean(omega**2, grid.spacing, "periodic"))
        points.append(
            ConvergencePoint(
                "taylor_green_enstrophy",
                "taylor_green",
                size,
                grid.spacing,
                "periodic",
                reference,
                computed,
            )
        )
    return points


def _taylor_green_heterogeneity(sizes: Sequence[int]) -> list[ConvergencePoint]:
    amplitude, wavenumber = 1.0, 1.0
    period = 2.0 * np.pi / wavenumber
    reference = ac.taylor_green_heterogeneity_continuum()
    points: list[ConvergencePoint] = []
    for size in sizes:
        grid = ac.periodic_grid(size, period)
        vx, vy = ac.taylor_green(grid.x, grid.y, amplitude, wavenumber)
        signature = evaluate_signature(vx, vy, grid.spacing, "periodic")
        points.append(
            ConvergencePoint(
                "taylor_green_heterogeneity",
                "taylor_green",
                size,
                grid.spacing,
                "periodic",
                reference,
                signature.heterogeneity,
            )
        )
    return points


def _lamb_oseen_vorticity_error(sizes: Sequence[int]) -> list[ConvergencePoint]:
    circulation, core, half = 2.0, 0.5, 3.0
    points: list[ConvergencePoint] = []
    for size in sizes:
        grid = ac.finite_grid(size, -half, half)
        vx, vy = ac.lamb_oseen(grid.x, grid.y, circulation, core)
        omega_num = numerical_vorticity_with_boundary(vx, vy, grid.spacing, "finite")
        omega_ana = ac.lamb_oseen_vorticity(grid.x, grid.y, circulation, core)
        rms_error = float(
            np.sqrt(max(spatial_mean((omega_num - omega_ana) ** 2, grid.spacing, "finite"), 0.0))
        )
        points.append(
            ConvergencePoint(
                "lamb_oseen_vorticity_rms_error",
                "lamb_oseen",
                size,
                grid.spacing,
                "finite",
                0.0,
                rms_error,
            )
        )
    return points


def run_convergence(
    finite_sizes: Sequence[int] = FINITE_GRID_SIZES,
    periodic_sizes: Sequence[int] = PERIODIC_GRID_SIZES,
) -> dict[str, Any]:
    """Run all convergence studies and return structured rows plus a summary."""
    studies = {
        "taylor_green_enstrophy": (
            _taylor_green_enstrophy(periodic_sizes),
            "analytical",
        ),
        "taylor_green_heterogeneity": (
            _taylor_green_heterogeneity(periodic_sizes),
            "analytical",
        ),
        "lamb_oseen_vorticity_rms_error": (
            _lamb_oseen_vorticity_error(finite_sizes),
            "analytical",
        ),
    }
    rows: list[list[object]] = []
    summary: list[dict[str, object]] = []
    for name, (points, interpolation) in studies.items():
        study_rows = _points_to_rows(points, interpolation)
        rows.extend(study_rows)
        order_column = CONVERGENCE_COLUMNS.index("observed_order")
        finest_orders = [
            value
            for value in (row[order_column] for row in study_rows)
            if isinstance(value, float)
        ]
        summary.append(
            {
                "study": name,
                "points": len(points),
                "finest_observed_order": (
                    finest_orders[-1] if finest_orders else None
                ),
            }
        )
    return {
        "columns": list(CONVERGENCE_COLUMNS),
        "rows": rows,
        "summary": summary,
    }
