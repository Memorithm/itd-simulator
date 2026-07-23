"""3D ITD candidate versus established 3D diagnostics (research).

Places the experimental 3D ITD candidate channels (magnitude intensity/
heterogeneity/localization/roughness, orientation dispersion, helicity, and
vortex-stretching rate) beside the established 3D vortex-identification
diagnostics (Q-criterion, lambda_2, swirling strength) on the *same*
velocity-gradient tensor. The genuinely 3D channels (orientation dispersion,
normalized helicity, stretching rate) have no 2D analogue and are the point of
the candidate; this module quantifies them against Q/lambda_2 on real or
analytical 3D fields.

Part of the isolated ``itd_research`` namespace; never modifies V29.18; imports
no plotting library; performs no network access (an external 3D field is loaded
from a local ``.npz`` prepared by ``tools/datasets/fetch_jhtdb_cutout.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d
from itd_research.diagnostics_3d.operators import (
    velocity_gradient_3d,
    vorticity_3d_from_gradient,
)
from itd_research.diagnostics_3d.velocity_gradient import (
    lambda2,
    q_criterion,
    swirling_strength,
)
from itd_research.external_validation.comparison import (
    pearson_correlation,
    region_overlap,
    spearman_correlation,
)

FloatArray: TypeAlias = NDArray[np.float64]

_SWIRL_REL_TOL = 1.0e-6
_HIGH_VORTICITY_QUANTILE = 0.8


@dataclass(frozen=True)
class Comparison3DResult:
    """3D ITD candidate channels, established diagnostics, and their agreement."""

    name: str
    category: str
    description: str
    shape: tuple[int, int, int]
    boundary_mode: str
    itd3d: dict[str, float]
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
            "itd3d": self.itd3d,
            "diagnostics": self.diagnostics,
            "regions": self.regions,
            "correlations": self.correlations,
        }


def run_3d_comparison(
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    boundary_mode: str,
    name: str,
    category: str,
    description: str,
) -> Comparison3DResult:
    """Compute the 3D ITD candidate and established diagnostics on one field."""
    signature = evaluate_itd3d(u, v, w, x, y, z, boundary_mode)
    gradient = velocity_gradient_3d(u, v, w, x, y, z, boundary_mode)
    omega = vorticity_3d_from_gradient(gradient)
    abs_omega = np.sqrt(np.sum(omega**2, axis=-1))
    q_field = q_criterion(gradient)
    lambda_2 = lambda2(gradient)
    swirl = swirling_strength(gradient)

    rotation = q_field > 0.0
    lambda_vortex = lambda_2 < 0.0
    swirl_max = float(np.max(swirl)) if swirl.size else 0.0
    swirl_active = swirl >= _SWIRL_REL_TOL * swirl_max if swirl_max > 0.0 else np.zeros_like(swirl, dtype=bool)
    high_omega = abs_omega >= float(np.quantile(abs_omega, _HIGH_VORTICITY_QUANTILE))

    total = float(abs_omega.size)
    diagnostics = {
        "enstrophy": float(0.5 * np.mean(abs_omega**2)),
        "vorticity_magnitude_rms": float(np.sqrt(np.mean(abs_omega**2))),
        "q_mean": float(np.mean(q_field)),
        "swirl_rms": float(np.sqrt(np.mean(swirl**2))),
    }
    regions = {
        "rotation_fraction_q": float(np.count_nonzero(rotation)) / total,
        "lambda2_vortex_fraction": float(np.count_nonzero(lambda_vortex)) / total,
        "swirl_active_fraction": float(np.count_nonzero(swirl_active)) / total,
        "jaccard_q_lambda2": region_overlap(rotation, lambda_vortex).jaccard,
        "jaccard_highomega_q": region_overlap(high_omega, rotation).jaccard,
        "high_vorticity_quantile": _HIGH_VORTICITY_QUANTILE,
    }
    flat_abs = abs_omega.reshape(1, -1)
    flat_swirl = swirl.reshape(1, -1)
    correlations: dict[str, float | None] = {
        "absomega_swirl_pearson": pearson_correlation(flat_abs, flat_swirl),
        "absomega_swirl_spearman": spearman_correlation(flat_abs, flat_swirl),
    }
    return Comparison3DResult(
        name=name,
        category=category,
        description=description,
        shape=(int(z.size), int(y.size), int(x.size)),
        boundary_mode=boundary_mode,
        itd3d=signature.as_dict(),
        diagnostics=diagnostics,
        regions=regions,
        correlations=correlations,
    )


def fluctuation_intensity(
    u: FloatArray, homogeneous_axes: tuple[int, ...] = (0, 2)
) -> float:
    """RMS velocity fluctuation about the mean profile over homogeneous directions.

    An **ITD-independent** turbulence-intensity marker: it subtracts the mean
    taken over the statistically homogeneous directions (default: axes 0 and 2,
    i.e. spanwise ``z`` and streamwise ``x`` for a boundary layer) and returns the
    RMS of the remainder. It is low in laminar flow and rises across transition.
    """
    array = np.asarray(u, dtype=np.float64)
    mean = np.mean(array, axis=homogeneous_axes, keepdims=True)
    return float(np.sqrt(np.mean((array - mean) ** 2)))


def transition_markers(
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    boundary_mode: str = "finite",
) -> dict[str, float]:
    """ITD-independent and ITD markers for a station in a transitional flow.

    Returns the ITD-independent fluctuation intensity and vorticity RMS, the
    rotation fraction, and the ITD intensity/localization. Across a streamwise
    sequence the fluctuation intensity rises and the ITD localization falls
    through the laminar-to-turbulent transition.
    """
    gradient = velocity_gradient_3d(u, v, w, x, y, z, boundary_mode)
    omega = vorticity_3d_from_gradient(gradient)
    abs_omega = np.sqrt(np.sum(omega**2, axis=-1))
    q_field = q_criterion(gradient)
    signature = evaluate_itd3d(u, v, w, x, y, z, boundary_mode)
    return {
        "fluctuation_intensity": fluctuation_intensity(u),
        "vorticity_rms": float(np.sqrt(np.mean(abs_omega**2))),
        "rotation_fraction_q": float(np.mean(q_field > 0.0)),
        "itd_intensity": signature.intensity,
        "itd_localization": signature.localization,
    }


def aggregate_3d_channels(
    results: list[Comparison3DResult],
    keys: tuple[str, ...] = (
        "orientation_dispersion", "normalized_helicity", "stretching_rate",
        "localization", "heterogeneity",
    ),
    region_keys: tuple[str, ...] = (
        "rotation_fraction_q", "lambda2_vortex_fraction", "jaccard_q_lambda2",
    ),
) -> dict[str, dict[str, float]]:
    """Mean/std/min/max of key 3D channels across an ensemble of cutouts.

    Turns a set of independent boxes into a small statistical summary, so a robust
    property (for example a consistently positive vortex-stretching rate) can be
    distinguished from a single-box coincidence.
    """
    summary: dict[str, dict[str, float]] = {"n_samples": {"value": float(len(results))}}
    for key in keys:
        values = np.array([r.itd3d[key] for r in results], dtype=np.float64)
        summary[key] = {
            "mean": float(np.mean(values)), "std": float(np.std(values)),
            "min": float(np.min(values)), "max": float(np.max(values)),
        }
    for key in region_keys:
        values = np.array([r.regions[key] for r in results], dtype=np.float64)
        summary[key] = {
            "mean": float(np.mean(values)), "std": float(np.std(values)),
            "min": float(np.min(values)), "max": float(np.max(values)),
        }
    return summary


def analytical_3d_cases() -> list[Comparison3DResult]:
    """Two exact 3D fields exercising the genuinely 3D channels in CI."""
    from itd_research.diagnostics_3d import analytical_fields as af

    results: list[Comparison3DResult] = []
    grid = af.periodic_grid_3d(24, 2.0 * np.pi)
    u, v, w = af.abc_flow(grid, 1.0, 1.0, 1.0)
    results.append(run_3d_comparison(
        u, v, w, grid.x, grid.y, grid.z, "periodic",
        "abc_flow", "analytical",
        "Arnold-Beltrami-Childress flow: curl u = u, normalized helicity = 1",
    ))
    u, v, w = af.taylor_green_3d(grid, 1.0, 1.0)
    results.append(run_3d_comparison(
        u, v, w, grid.x, grid.y, grid.z, "periodic",
        "taylor_green_3d", "analytical",
        "Taylor-Green initial field: rotation cores and strain braids",
    ))
    return results


def external_3d_case(
    npz_path: str | Path,
    boundary_mode: str = "finite",
    name: str = "jhtdb_isotropic",
    description: str = "JHTDB forced isotropic turbulence DNS cutout",
) -> Comparison3DResult:
    """Load a 3D velocity field from ``.npz`` (x,y,z,u,v,w) as an external case."""
    from itd_research.io.field_data import FieldMetadata
    from itd_research.io.npz import read_npz_field_3d

    metadata = FieldMetadata(
        source="JHU Turbulence Database (JHTDB) isotropic1024coarse",
        length_unit="nondimensional",
        velocity_unit="nondimensional",
        boundary_mode=boundary_mode,
    )
    field = read_npz_field_3d(npz_path, metadata)
    return run_3d_comparison(
        np.asarray(field.u), np.asarray(field.v), np.asarray(field.w),
        np.asarray(field.x), np.asarray(field.y), np.asarray(field.z),
        boundary_mode, name, "external", description,
    )
