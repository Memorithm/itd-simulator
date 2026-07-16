"""
Extraction de l'orchestration de déformation matérielle.

Module généré automatiquement pour ITD V29.17.
L'API historique reste réexportée par itd_v29.py.
"""

from __future__ import annotations

import numpy as np

from compare_scenarios import (
    Config,
    curvature_field,
)

from itd_v29_core.constants import (
    DEFAULT_STRUCTURAL_WEIGHTS,
    STRUCTURAL_LENGTH,
)

from itd_v29_core.material_interval import material_vorticity_interval

from itd_v29_core.simulation_engine import simulate

from itd_v29_core.spatial_geometry import (
    normalize_spatial_geometry,
    validate_mesh_geometry,
)

from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    validate_boundary_mode,
)

from itd_v29_core.time_geometry import normalize_time_grid

from typing import Callable

def interpolate_interval_series_to_nodes(
    times: object,
    interval_values: object,
) -> np.ndarray:
    temporal_geometry = normalize_time_grid(
        times
    )

    values = np.asarray(
        interval_values,
        dtype=np.float64,
    )

    expected_shape = (
        temporal_geometry.interval_count,
    )

    if values.shape != expected_shape:
        raise ValueError(
            "La série d'intervalle doit avoir la "
            f"forme {expected_shape}, obtenue "
            f"{values.shape}."
        )

    if not np.all(np.isfinite(values)):
        raise ValueError(
            "La série d'intervalle contient une "
            "valeur non finie."
        )

    midpoints = 0.5 * (
        temporal_geometry.times[:-1]
        + temporal_geometry.times[1:]
    )

    return np.interp(
        temporal_geometry.times,
        midpoints,
        values,
        left=float(values[0]),
        right=float(values[-1]),
    )


def simulate_material_deformation(
    name: str,
    velocity_function: Callable,
    x: np.ndarray,
    y: np.ndarray,
    times: object,
    spacing: object,
    cfg: Config,
    curvature_function: Callable = curvature_field,
    structural_length: float = STRUCTURAL_LENGTH,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
    boundary_mode: str = "finite",
    advection_velocity_function: Callable | None = None,
) -> dict[str, object]:
    """
    Exécute la simulation historique eulérienne puis
    ajoute un diagnostic local de dérivée matérielle.

    Par défaut, la vitesse d'advection est le champ de
    vitesse du scénario. Elle peut être fournie
    séparément lorsque le transport est connu par une
    autre source.

    Le diagnostic matériel n'est pas injecté
    automatiquement dans la signature structurelle.
    """
    if not callable(velocity_function):
        raise ValueError(
            "Le champ de vitesse doit être appelable."
        )

    if advection_velocity_function is None:
        advection_function = velocity_function
        advection_source = "velocity_function"
    elif callable(advection_velocity_function):
        advection_function = (
            advection_velocity_function
        )

        advection_source = (
            "advection_velocity_function"
        )
    else:
        raise ValueError(
            "Le champ de vitesse d'advection doit "
            "être appelable ou nul."
        )

    temporal_geometry = normalize_time_grid(
        times
    )

    time_values = temporal_geometry.times

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

    geometry = normalize_spatial_geometry(
        spacing
    )

    validate_mesh_geometry(
        x,
        y,
        geometry,
    )

    baseline = simulate(
        name,
        velocity_function,
        x,
        y,
        time_values,
        geometry,
        cfg,
        curvature_function=curvature_function,
        structural_length=structural_length,
        structural_weights=structural_weights,
        boundary_mode=boundary_mode,
        temporal_deformation_mode="eulerian",
    )

    interval_count = (
        temporal_geometry.interval_count
    )

    eulerian_rates = np.empty(
        interval_count,
        dtype=np.float64,
    )

    advective_rates = np.empty(
        interval_count,
        dtype=np.float64,
    )

    material_rates = np.empty(
        interval_count,
        dtype=np.float64,
    )

    previous_omega: np.ndarray | None = None
    previous_time: float | None = None

    interval_index = 0

    for time_value in time_values:
        time = float(time_value)

        vx, vy = velocity_function(
            x,
            y,
            time,
        )

        vx = np.asarray(
            vx,
            dtype=np.float64,
        )

        vy = np.asarray(
            vy,
            dtype=np.float64,
        )

        if (
            vx.shape != x.shape
            or vy.shape != x.shape
        ):
            raise ValueError(
                "Le champ de vitesse doit avoir "
                "la forme du maillage."
            )

        if not (
            np.all(np.isfinite(vx))
            and np.all(np.isfinite(vy))
        ):
            raise ValueError(
                "Le champ de vitesse contient une "
                "valeur non finie."
            )

        omega = numerical_vorticity_with_boundary(
            vx,
            vy,
            geometry,
            boundary_mode,
        )

        if previous_omega is not None:
            delta_time = (
                time - float(previous_time)
            )

            midpoint_time = 0.5 * (
                time + float(previous_time)
            )

            midpoint_vx, midpoint_vy = (
                advection_function(
                    x,
                    y,
                    midpoint_time,
                )
            )

            interval = material_vorticity_interval(
                previous_omega,
                omega,
                midpoint_vx,
                midpoint_vy,
                geometry,
                delta_time,
                boundary_mode=boundary_mode,
            )

            eulerian_rates[
                interval_index
            ] = float(
                interval["eulerian_rate"]
            )

            advective_rates[
                interval_index
            ] = float(
                interval["advective_rate"]
            )

            material_rates[
                interval_index
            ] = float(
                interval["material_rate"]
            )

            interval_index += 1

        previous_omega = omega.copy()
        previous_time = time

    interval_dt = (
        temporal_geometry.interval_dt
    )

    duration = temporal_geometry.duration

    eulerian_index = float(
        np.sum(
            eulerian_rates
            * interval_dt,
            dtype=np.float64,
        )
        / duration
    )

    advective_index = float(
        np.sum(
            advective_rates
            * interval_dt,
            dtype=np.float64,
        )
        / duration
    )

    material_index = float(
        np.sum(
            material_rates
            * interval_dt,
            dtype=np.float64,
        )
        / duration
    )

    baseline_eulerian = np.asarray(
        baseline[
            "temporal_deformation_eulerian_interval"
        ],
        dtype=np.float64,
    )

    consistency_error = float(
        np.max(
            np.abs(
                eulerian_rates
                - baseline_eulerian
            )
        )
    )

    result = dict(baseline)

    result.update(
        {
            "material_derivative": {
                "enabled": True,
                "advection_source": (
                    advection_source
                ),
                "temporal_discretization": (
                    "centered_interval"
                ),
                "spatial_discretization": (
                    "existing_scalar_gradient"
                ),
                "selected_for_structure": False,
            },
            "material_eulerian_rate_interval": (
                eulerian_rates
            ),
            "material_advective_rate_interval": (
                advective_rates
            ),
            "material_deformation_interval": (
                material_rates
            ),
            "material_eulerian_rate": (
                interpolate_interval_series_to_nodes(
                    time_values,
                    eulerian_rates,
                )
            ),
            "material_advective_rate": (
                interpolate_interval_series_to_nodes(
                    time_values,
                    advective_rates,
                )
            ),
            "material_deformation": (
                interpolate_interval_series_to_nodes(
                    time_values,
                    material_rates,
                )
            ),
            "material_eulerian_rate_index": (
                eulerian_index
            ),
            "material_advective_rate_index": (
                advective_index
            ),
            "material_deformation_index": (
                material_index
            ),
            "material_eulerian_consistency_error": (
                consistency_error
            ),
        }
    )

    return result
