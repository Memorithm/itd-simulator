"""
Extraction des diagnostics d'intervalle matériel.

Module généré automatiquement pour ITD V29.14.
L'API historique reste réexportée par itd_v29.py.
"""

from __future__ import annotations

import numpy as np

from itd_v29_core.constants import ZERO_THRESHOLD

from itd_v29_core.spatial_geometry import (
    normalize_spatial_geometry,
    validate_field_shape_for_geometry,
)

from itd_v29_core.spatial_operators import (
    scalar_gradient_with_boundary,
    spatial_mean,
    validate_boundary_mode,
)

def validate_positive_time_interval(
    delta_time: object,
) -> float:
    try:
        value = float(delta_time)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "L'intervalle temporel doit être "
            "un nombre réel."
        ) from error

    if (
        not np.isfinite(value)
        or value <= 0.0
    ):
        raise ValueError(
            "L'intervalle temporel doit être fini "
            "et strictement positif."
        )

    return value


def validate_material_interval_fields(
    previous_omega: object,
    current_omega: object,
    midpoint_vx: object,
    midpoint_vy: object,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    arrays = []

    for value, name in (
        (
            previous_omega,
            "vorticité précédente",
        ),
        (
            current_omega,
            "vorticité courante",
        ),
        (
            midpoint_vx,
            "vitesse x au milieu",
        ),
        (
            midpoint_vy,
            "vitesse y au milieu",
        ),
    ):
        array = np.asarray(
            value,
            dtype=np.float64,
        )

        if array.ndim != 2:
            raise ValueError(
                f"Le champ {name} doit être 2D."
            )

        if min(array.shape) < 3:
            raise ValueError(
                f"Le champ {name} doit contenir "
                "au moins trois points par direction."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(
                f"Le champ {name} contient une "
                "valeur non finie."
            )

        arrays.append(array)

    reference_shape = arrays[0].shape

    if any(
        array.shape != reference_shape
        for array in arrays[1:]
    ):
        raise ValueError(
            "Les champs de l'intervalle matériel "
            "doivent avoir la même forme."
        )

    return (
        arrays[0],
        arrays[1],
        arrays[2],
        arrays[3],
    )


def normalized_field_rate(
    field: object,
    reference_rms: float,
    spacing: object,
    boundary_mode: str,
) -> float:
    array = np.asarray(
        field,
        dtype=np.float64,
    )

    if (
        not np.isfinite(reference_rms)
        or reference_rms < 0.0
    ):
        raise ValueError(
            "La RMS de référence doit être finie "
            "et positive ou nulle."
        )

    if reference_rms < ZERO_THRESHOLD:
        return 0.0

    mean_square = spatial_mean(
        array**2,
        spacing,
        boundary_mode,
    )

    return float(
        np.sqrt(
            max(
                mean_square,
                0.0,
            )
        )
        / reference_rms
    )


def material_vorticity_interval(
    previous_omega: object,
    current_omega: object,
    midpoint_vx: object,
    midpoint_vy: object,
    spacing: object,
    delta_time: object,
    boundary_mode: str = "finite",
) -> dict[str, object]:
    """
    Décompose l'évolution de la vorticité sur un
    intervalle temporel :

        temporal_tendency = d omega / dt

        advective_tendency = u . grad(omega)

        material_tendency =
            temporal_tendency + advective_tendency

    La vitesse et le gradient sont évalués au milieu
    de l'intervalle.

    Les trois diagnostics scalaires sont des normes
    indépendantes. Ils ne sont pas additifs.
    """
    dt = validate_positive_time_interval(
        delta_time
    )

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

    geometry = normalize_spatial_geometry(
        spacing
    )

    (
        previous,
        current,
        midpoint_velocity_x,
        midpoint_velocity_y,
    ) = validate_material_interval_fields(
        previous_omega,
        current_omega,
        midpoint_vx,
        midpoint_vy,
    )

    validate_field_shape_for_geometry(
        previous,
        geometry,
    )

    temporal_tendency = (
        current - previous
    ) / dt

    midpoint_omega = 0.5 * (
        previous + current
    )

    gradient_y, gradient_x = (
        scalar_gradient_with_boundary(
            midpoint_omega,
            geometry,
            boundary_mode,
        )
    )

    advective_tendency = (
        midpoint_velocity_x
        * gradient_x
        + midpoint_velocity_y
        * gradient_y
    )

    material_tendency = (
        temporal_tendency
        + advective_tendency
    )

    previous_rms = float(
        np.sqrt(
            max(
                spatial_mean(
                    previous**2,
                    geometry,
                    boundary_mode,
                ),
                0.0,
            )
        )
    )

    current_rms = float(
        np.sqrt(
            max(
                spatial_mean(
                    current**2,
                    geometry,
                    boundary_mode,
                ),
                0.0,
            )
        )
    )

    reference_rms = 0.5 * (
        previous_rms
        + current_rms
    )

    eulerian_rate = normalized_field_rate(
        temporal_tendency,
        reference_rms,
        geometry,
        boundary_mode,
    )

    advective_rate = normalized_field_rate(
        advective_tendency,
        reference_rms,
        geometry,
        boundary_mode,
    )

    material_rate = normalized_field_rate(
        material_tendency,
        reference_rms,
        geometry,
        boundary_mode,
    )

    return {
        "delta_time": dt,
        "reference_rms": reference_rms,
        "previous_rms": previous_rms,
        "current_rms": current_rms,
        "temporal_tendency": temporal_tendency,
        "advective_tendency": advective_tendency,
        "material_tendency": material_tendency,
        "eulerian_rate": eulerian_rate,
        "advective_rate": advective_rate,
        "material_rate": material_rate,
    }
