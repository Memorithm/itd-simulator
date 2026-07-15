#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from compare_scenarios import (
    Config,
    calm_field,
    coherent_vortex,
    curvature_field,
    multi_vortex_field,
    numerical_vorticity,
)

from itd_v29_core.constants import (
    BOUNDARY_MODES,
    DEFAULT_STRUCTURAL_WEIGHTS,
    STRUCTURAL_COMPONENT_NAMES,
    STRUCTURAL_LENGTH,
    TEMPORAL_DEFORMATION_MODES,
    TRANSPORT_INTERPOLATIONS,
    TRANSPORT_TRAJECTORY_METHODS,
    ZERO_THRESHOLD,
)




# Longueur physique de référence utilisée pour rendre
# la rugosité adimensionnelle. Elle est indépendante
# du pas numérique de la grille.




from itd_v29_core.geometric_transforms import (
    BilinearTransformPlan,
    make_sampled_transformed_scalar_function,
    make_sampled_transformed_velocity_function,
    rotation_matrix,
    transform_coordinates,
    transform_scalar_function,
    transform_velocity_function,
    validate_orthogonal_matrix,
    validate_rotation_angle,
    validate_transform_origin,
    validate_uniform_axis_coordinates,
)


def normalize_structural_weights(
    weights: object,
) -> np.ndarray:
    """
    Valide et normalise cinq poids positifs ou nuls.

    L'ordre est :
        hétérogénéité,
        localisation,
        rugosité,
        mélange des signes,
        déformation temporelle.
    """
    array = np.asarray(
        weights,
        dtype=np.float64,
    )

    if array.shape != (5,):
        raise ValueError(
            "Les poids structurels doivent contenir "
            "exactement cinq valeurs."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "Les poids structurels doivent être finis."
        )

    if np.any(array < 0.0):
        raise ValueError(
            "Les poids structurels doivent être "
            "positifs ou nuls."
        )

    total = float(np.sum(array))

    if total <= 0.0:
        raise ValueError(
            "Au moins un poids structurel doit être "
            "strictement positif."
        )

    return array / total


from itd_v29_core.time_geometry import (
    TemporalGeometry,
    normalize_time_grid,
)

from itd_v29_core.spatial_scaling import (
    inverse_scale_coordinates,
    scale_curvature_function,
    scale_length,
    scale_spatial_geometry,
    scale_velocity_function,
    validate_nonnegative_length,
    validate_spatial_scale_factor,
)


from itd_v29_core.multiscale_structure import (
    derive_multiscale_profile,
    validate_structural_length_grid,
)


def simulate_multiscale(
    name: str,
    velocity_function: Callable,
    x: np.ndarray,
    y: np.ndarray,
    times: object,
    spacing: object,
    cfg: Config,
    structural_lengths: object,
    curvature_function: Callable = curvature_field,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
    boundary_mode: str = "finite",
    temporal_deformation_mode: str = "eulerian",
    transport_velocity_function: Callable | None = None,
    transport_interpolation: str = (
        "bilinear_periodic"
    ),
    transport_trajectory_method: str = (
        "midpoint_time_velocity"
    ),
) -> dict[str, object]:
    """
    Calcule un profil multi-échelle en une seule
    simulation dynamique.

    Une simulation de référence est effectuée avec
    structural_length = 1. Les autres longueurs sont
    ensuite dérivées exactement à partir de la loi
    linéaire de la rugosité brute.
    """
    lengths = validate_structural_length_grid(
        structural_lengths
    )

    reference_result = simulate(
        name,
        velocity_function,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=curvature_function,
        structural_length=1.0,
        structural_weights=structural_weights,
        boundary_mode=boundary_mode,
        temporal_deformation_mode=(
            temporal_deformation_mode
        ),
        transport_velocity_function=(
            transport_velocity_function
        ),
        transport_interpolation=(
            transport_interpolation
        ),
        transport_trajectory_method=(
            transport_trajectory_method
        ),
    )

    profile = derive_multiscale_profile(
        reference_result,
        lengths,
    )

    profile[
        "spatial_geometry"
    ] = reference_result[
        "spatial_geometry"
    ]

    profile[
        "temporal_geometry"
    ] = reference_result[
        "temporal_geometry"
    ]

    profile[
        "boundary_mode"
    ] = reference_result[
        "boundary_mode"
    ]

    profile[
        "temporal_deformation_mode"
    ] = reference_result[
        "temporal_deformation_mode"
    ]

    profile[
        "transport_compensation"
    ] = reference_result[
        "transport_compensation"
    ]

    return profile



from itd_v29_core.numerical_certification import (
    analyze_multiscale_profile_triplet,
    analyze_result_triplet,
    combine_decoupled_convergence_rows,
    convergence_error_is_estimable,
    convergence_row_key,
    extract_single_scale_diagnostics,
    richardson_triplet,
    summarize_convergence_rows,
    summarize_decoupled_convergence_rows,
    validate_convergence_tolerance,
    validate_refinement_ratio,
)


def validate_temporal_deformation_mode(
    mode: object,
) -> str:
    if not isinstance(
        mode,
        str,
    ):
        raise ValueError(
            "Le mode de déformation temporelle "
            "doit être une chaîne."
        )

    normalized = mode.strip().lower()

    if (
        normalized
        not in TEMPORAL_DEFORMATION_MODES
    ):
        allowed = ", ".join(
            TEMPORAL_DEFORMATION_MODES
        )

        raise ValueError(
            "Mode de déformation temporelle "
            f"inconnu : {mode!r}. "
            f"Modes autorisés : {allowed}."
        )

    return normalized


from itd_v29_core.periodic_transport import (
    validate_periodic_transport_mesh,
    periodic_bilinear_backtrace,
    periodic_coordinate_geometry,
    wrap_periodic_points,
    evaluate_periodic_transport_velocity,
    rk4_periodic_departure_points,
    transport_previous_vorticity_periodic,
    validate_transport_interpolation,
    validate_transport_trajectory_method,
    periodic_cubic_lagrange_weights,
    periodic_cubic_backtrace,
    periodic_bilinear_departure_bounds,
    normalize_periodic_departure_geometry,
    periodic_bilinear_sample_at_departures,
    cubic_lagrange_weights_at_fraction,
    periodic_cubic_sample_at_departures,
    periodic_departure_bounds,
    periodic_cubic_local_bounded_sample_at_departures,
    periodic_cubic_local_sum_preserving_sample_at_departures,
    periodic_sample_at_departures,
    convex_local_bound_limiter,
    periodic_cubic_local_bounded_backtrace,
    precise_discrete_sum,
    periodic_expand_mask,
    restore_sum_with_local_bounds,
    periodic_cubic_local_sum_preserving_backtrace,
    periodic_backtrace,
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


from itd_v29_core.reference_frames import (
    evaluate_translating_frame_vector,
    galilean_metadata,
    galilean_source_coordinates,
    galilean_transform_scalar_function,
    galilean_transform_velocity_function,
    translating_frame_metadata,
    translating_frame_source_coordinates,
    translating_frame_transform_scalar_function,
    translating_frame_transform_velocity_function,
    validate_galilean_frame_velocity,
    validate_galilean_reference_time,
)








def validate_boundary_mode(
    boundary_mode: str,
) -> str:
    """
    Valide la convention utilisée aux limites.

    finite
        Domaine fini, quadrature trapézoïdale et
        dérivées unilatérales aux bords.

    periodic
        Domaine périodique, grille sans extrémité
        dupliquée et différences centrées circulaires.
    """
    if not isinstance(boundary_mode, str):
        raise ValueError(
            "Le mode de frontière doit être une chaîne."
        )

    normalized = boundary_mode.strip().lower()

    if normalized not in BOUNDARY_MODES:
        allowed = ", ".join(BOUNDARY_MODES)

        raise ValueError(
            "Mode de frontière inconnu : "
            f"{boundary_mode!r}. "
            f"Valeurs autorisées : {allowed}."
        )

    return normalized


from itd_v29_core.spatial_geometry import (
    RectilinearGeometry,
    SpatialGeometry,
    normalize_spatial_geometry,
    spatial_geometry_metadata,
    validate_axis_spacing,
    validate_field_shape_for_geometry,
    validate_mesh_geometry,
    validate_rectilinear_axis_coordinates,
    validate_spacing,
)


def numerical_vorticity_with_boundary(
    vx: np.ndarray,
    vy: np.ndarray,
    spacing: object,
    boundary_mode: str = "finite",
) -> np.ndarray:
    """
    Calcule :

        omega = d(v_y)/dx - d(v_x)/dy

    sur une grille uniforme ou rectiligne non uniforme.
    """
    geometry = normalize_spatial_geometry(
        spacing
    )

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

    vx = np.asarray(
        vx,
        dtype=np.float64,
    )

    vy = np.asarray(
        vy,
        dtype=np.float64,
    )

    if vx.shape != vy.shape:
        raise ValueError(
            "Les composantes de vitesse doivent "
            "avoir la même forme."
        )

    if vx.ndim != 2:
        raise ValueError(
            "Le calcul de vorticité attend deux "
            "tableaux bidimensionnels."
        )

    if min(vx.shape) < 3:
        raise ValueError(
            "La grille doit contenir au moins "
            "trois points par direction."
        )

    if not (
        np.all(np.isfinite(vx))
        and np.all(np.isfinite(vy))
    ):
        raise ValueError(
            "Le champ de vitesse contient une "
            "valeur non finie."
        )

    validate_field_shape_for_geometry(
        vx,
        geometry,
    )

    if boundary_mode == "finite":
        if isinstance(
            geometry,
            RectilinearGeometry,
        ):
            _, derivative_vy_x = np.gradient(
                vy,
                geometry.y_coordinates,
                geometry.x_coordinates,
                edge_order=2,
            )

            derivative_vx_y, _ = np.gradient(
                vx,
                geometry.y_coordinates,
                geometry.x_coordinates,
                edge_order=2,
            )

            return (
                derivative_vy_x
                - derivative_vx_y
            )

        if geometry.isotropic:
            return numerical_vorticity(
                vx,
                vy,
                geometry.dx,
            )

        _, derivative_vy_x = np.gradient(
            vy,
            geometry.dy,
            geometry.dx,
            edge_order=2,
        )

        derivative_vx_y, _ = np.gradient(
            vx,
            geometry.dy,
            geometry.dx,
            edge_order=2,
        )

        return (
            derivative_vy_x
            - derivative_vx_y
        )

    if isinstance(
        geometry,
        RectilinearGeometry,
    ):
        if not geometry.uniform:
            raise ValueError(
                "Le mode périodique exige encore "
                "une géométrie uniforme."
            )

        dx = float(geometry.dx)
        dy = float(geometry.dy)
    else:
        dx = geometry.dx
        dy = geometry.dy

    derivative_vy_x = (
        np.roll(vy, -1, axis=1)
        - np.roll(vy, 1, axis=1)
    ) / (2.0 * dx)

    derivative_vx_y = (
        np.roll(vx, -1, axis=0)
        - np.roll(vx, 1, axis=0)
    ) / (2.0 * dy)

    return (
        derivative_vy_x
        - derivative_vx_y
    )

def scalar_gradient_with_boundary(
    field: np.ndarray,
    spacing: object,
    boundary_mode: str = "finite",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Retourne :

        (d(field)/dy, d(field)/dx)

    sur une grille uniforme ou rectiligne.
    """
    geometry = normalize_spatial_geometry(
        spacing
    )

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

    field = np.asarray(
        field,
        dtype=np.float64,
    )

    if field.ndim != 2:
        raise ValueError(
            "Le gradient attend un tableau 2D."
        )

    if min(field.shape) < 3:
        raise ValueError(
            "La grille doit contenir au moins "
            "trois points par direction."
        )

    if not np.all(np.isfinite(field)):
        raise ValueError(
            "Le champ scalaire contient une "
            "valeur non finie."
        )

    validate_field_shape_for_geometry(
        field,
        geometry,
    )

    if boundary_mode == "finite":
        if isinstance(
            geometry,
            RectilinearGeometry,
        ):
            return np.gradient(
                field,
                geometry.y_coordinates,
                geometry.x_coordinates,
                edge_order=2,
            )

        return np.gradient(
            field,
            geometry.dy,
            geometry.dx,
            edge_order=2,
        )

    if isinstance(
        geometry,
        RectilinearGeometry,
    ):
        if not geometry.uniform:
            raise ValueError(
                "Le mode périodique exige encore "
                "une géométrie uniforme."
            )

        dx = float(geometry.dx)
        dy = float(geometry.dy)
    else:
        dx = geometry.dx
        dy = geometry.dy

    gradient_x = (
        np.roll(field, -1, axis=1)
        - np.roll(field, 1, axis=1)
    ) / (2.0 * dx)

    gradient_y = (
        np.roll(field, -1, axis=0)
        - np.roll(field, 1, axis=0)
    ) / (2.0 * dy)

    return gradient_y, gradient_x

def bounded(value: float) -> float:
    """
    Projection d'une grandeur positive dans [0, 1[.

        b(x) = x / (1 + x)
    """
    value = max(0.0, float(value))
    return value / (1.0 + value)


def spatial_mean(
    field: np.ndarray,
    spacing: object,
    boundary_mode: str = "finite",
) -> float:
    """
    Moyenne spatiale sur une grille uniforme ou
    rectiligne non uniforme.
    """
    field = np.asarray(
        field,
        dtype=np.float64,
    )

    geometry = normalize_spatial_geometry(
        spacing
    )

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

    if field.ndim != 2:
        raise ValueError(
            "La moyenne spatiale attend un tableau 2D."
        )

    if not np.all(np.isfinite(field)):
        raise ValueError(
            "Le champ à intégrer contient une "
            "valeur non finie."
        )

    if min(field.shape) < 2:
        raise ValueError(
            "La grille doit contenir au moins "
            "deux points par direction."
        )

    validate_field_shape_for_geometry(
        field,
        geometry,
    )

    if boundary_mode == "periodic":
        if (
            isinstance(
                geometry,
                RectilinearGeometry,
            )
            and not geometry.uniform
        ):
            raise ValueError(
                "La moyenne périodique exige encore "
                "une géométrie uniforme."
            )

        return float(
            np.mean(
                field,
                dtype=np.float64,
            )
        )

    if isinstance(
        geometry,
        RectilinearGeometry,
    ):
        integral_x = np.trapezoid(
            field,
            x=geometry.x_coordinates,
            axis=1,
        )

        integral = float(
            np.trapezoid(
                integral_x,
                x=geometry.y_coordinates,
                axis=0,
            )
        )

        return (
            integral
            / geometry.domain_area
        )

    height = (
        field.shape[0] - 1
    ) * geometry.dy

    width = (
        field.shape[1] - 1
    ) * geometry.dx

    area = height * width

    if area <= 0.0:
        raise ValueError(
            "L'aire du domaine doit être "
            "strictement positive."
        )

    integral_x = np.trapezoid(
        field,
        dx=geometry.dx,
        axis=1,
    )

    integral = float(
        np.trapezoid(
            integral_x,
            dx=geometry.dy,
            axis=0,
        )
    )

    return integral / area

def structural_metrics(
    omega: np.ndarray,
    spacing: object,
    previous_omega: np.ndarray | None,
    delta_time: float | None,
    structural_length: float = STRUCTURAL_LENGTH,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
    boundary_mode: str = "finite",
) -> dict[str, float]:
    geometry = normalize_spatial_geometry(
        spacing
    )

    structural_length = float(
        structural_length
    )

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

    if (
        not np.isfinite(structural_length)
        or structural_length < 0.0
    ):
        raise ValueError(
            "La longueur structurelle doit être "
            "finie et positive ou nulle."
        )

    weights_array = normalize_structural_weights(
        structural_weights
    )

    omega = np.asarray(
        omega,
        dtype=np.float64,
    )

    if omega.ndim != 2:
        raise ValueError(
            "Le champ de vorticité doit être 2D."
        )

    if not np.all(np.isfinite(omega)):
        raise ValueError(
            "Le champ de vorticité contient une "
            "valeur non finie."
        )

    def mean_field(
        field: np.ndarray,
    ) -> float:
        return spatial_mean(
            field,
            geometry,
            boundary_mode,
        )

    abs_omega = np.abs(omega)
    mean_square = mean_field(omega**2)

    rms = float(
        np.sqrt(
            max(mean_square, 0.0)
        )
    )

    if rms < ZERO_THRESHOLD:
        return {
            "heterogeneity": 0.0,
            "localization": 0.0,
            "roughness": 0.0,
            "sign_mixing": 0.0,
            "temporal_deformation": 0.0,
            "structure_score": 0.0,
        }

    mean_absolute = mean_field(abs_omega)

    absolute_deviation = (
        abs_omega - mean_absolute
    )

    weighted_variance = mean_field(
        absolute_deviation**2
    )

    heterogeneity = float(
        np.sqrt(
            max(weighted_variance, 0.0)
        )
        / max(mean_absolute, ZERO_THRESHOLD)
    )

    localization = float(
        mean_field(omega**4)
        / max(mean_square**2, ZERO_THRESHOLD)
        - 1.0
    )

    gradient_y, gradient_x = (
        scalar_gradient_with_boundary(
            omega,
            geometry,
            boundary_mode,
        )
    )

    gradient_norm = np.sqrt(
        gradient_x**2
        + gradient_y**2
    )

    roughness = float(
        structural_length
        * mean_field(gradient_norm)
        / max(rms, ZERO_THRESHOLD)
    )

    sign_mixing = float(
        1.0
        - abs(mean_field(omega))
        / max(mean_absolute, ZERO_THRESHOLD)
    )

    sign_mixing = float(
        np.clip(
            sign_mixing,
            0.0,
            1.0,
        )
    )

    temporal_deformation = 0.0

    if (
        previous_omega is not None
        and delta_time is not None
        and delta_time > 0.0
    ):
        previous_omega = np.asarray(
            previous_omega,
            dtype=np.float64,
        )

        if previous_omega.shape != omega.shape:
            raise ValueError(
                "Les champs de vorticité successifs "
                "doivent avoir la même forme."
            )

        previous_rms = float(
            np.sqrt(
                max(
                    mean_field(
                        previous_omega**2
                    ),
                    0.0,
                )
            )
        )

        reference_rms = 0.5 * (
            rms + previous_rms
        )

        if reference_rms >= ZERO_THRESHOLD:
            temporal_deformation = float(
                np.sqrt(
                    max(
                        mean_field(
                            (
                                omega
                                - previous_omega
                            ) ** 2
                        ),
                        0.0,
                    )
                )
                / (
                    delta_time
                    * reference_rms
                )
            )

    bounded_components = (
        bounded(heterogeneity),
        bounded(localization),
        bounded(roughness),
        sign_mixing,
        bounded(temporal_deformation),
    )

    structure_score = float(
        np.dot(
            weights_array,
            np.asarray(
                bounded_components,
                dtype=np.float64,
            ),
        )
    )

    return {
        "heterogeneity": heterogeneity,
        "localization": localization,
        "roughness": roughness,
        "sign_mixing": sign_mixing,
        "temporal_deformation": temporal_deformation,
        "structure_score": structure_score,
    }

def simulate(
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
    temporal_deformation_mode: str = "eulerian",
    transport_velocity_function: Callable | None = None,
    transport_interpolation: str = (
        "bilinear_periodic"
    ),
    transport_trajectory_method: str = (
        "midpoint_time_velocity"
    ),
) -> dict[str, object]:
    structural_length = float(structural_length)

    if (
        not np.isfinite(structural_length)
        or structural_length < 0.0
    ):
        raise ValueError(
            "La longueur structurelle doit être "
            "finie et positive ou nulle."
        )
    temporal_geometry = normalize_time_grid(
        times
    )

    times = temporal_geometry.times

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

    temporal_deformation_mode = (
        validate_temporal_deformation_mode(
            temporal_deformation_mode
        )
    )

    transport_interpolation = (
        validate_transport_interpolation(
            transport_interpolation
        )
    )

    transport_trajectory_method = (
        validate_transport_trajectory_method(
            transport_trajectory_method
        )
    )

    transport_x_coordinates = None
    transport_y_coordinates = None

    if (
        temporal_deformation_mode
        == "transport_compensated"
    ):
        if not callable(
            transport_velocity_function
        ):
            raise ValueError(
                "Le mode transport_compensated "
                "exige un champ de transport "
                "explicite et appelable."
            )

        (
            transport_x_coordinates,
            transport_y_coordinates,
            _,
            _,
        ) = validate_periodic_transport_mesh(
            x,
            y,
            geometry,
            boundary_mode,
        )

    weights_array = normalize_structural_weights(
        structural_weights
    )

    intensity_rate = np.zeros_like(times)
    structure_rate = np.zeros_like(times)
    coupled_rate = np.zeros_like(times)

    heterogeneity = np.zeros_like(times)
    localization = np.zeros_like(times)
    roughness = np.zeros_like(times)
    sign_mixing = np.zeros_like(times)
    temporal_deformation = np.zeros_like(times)

    temporal_deformation_eulerian = (
        np.zeros_like(times)
    )

    temporal_deformation_compensated = (
        np.zeros_like(times)
        if (
            temporal_deformation_mode
            == "transport_compensated"
        )
        else None
    )

    previous_omega: np.ndarray | None = None
    previous_time: float | None = None

    for index, time_value in enumerate(times):
        time = float(time_value)

        vx, vy = velocity_function(
            x,
            y,
            time,
        )

        omega = numerical_vorticity_with_boundary(
            vx,
            vy,
            geometry,
            boundary_mode,
        )

        curvature = np.asarray(
            curvature_function(
                x,
                y,
                time,
            ),
            dtype=np.float64,
        )

        if curvature.shape != x.shape:
            raise ValueError(
                "Le champ de courbure doit avoir la même "
                "forme que la grille spatiale."
            )

        if not np.all(np.isfinite(curvature)):
            raise ValueError(
                "Le champ de courbure contient une valeur "
                "non finie."
            )

        curvature_weight = np.exp(
            cfg.characteristic_length**2
            * curvature
        )

        intensity_rate[index] = spatial_mean(
            omega**2 * curvature_weight,
            geometry,
            boundary_mode,
        )

        delta_time = (
            time - previous_time
            if previous_time is not None
            else None
        )

        eulerian_metrics = structural_metrics(
            omega,
            geometry,
            previous_omega,
            delta_time,
            structural_length=structural_length,
            structural_weights=weights_array,
            boundary_mode=boundary_mode,
        )

        compensated_metrics = None

        if (
            temporal_deformation_mode
            == "transport_compensated"
        ):
            if previous_omega is None:
                compensated_metrics = (
                    eulerian_metrics
                )
            else:
                transported_previous_omega = (
                    transport_previous_vorticity_periodic(
                        previous_omega,
                        x,
                        y,
                        transport_x_coordinates,
                        transport_y_coordinates,
                        float(previous_time),
                        time,
                        transport_velocity_function,
                        transport_interpolation=(
                            transport_interpolation
                        ),
                        transport_trajectory_method=(
                            transport_trajectory_method
                        ),
                    )
                )

                compensated_metrics = (
                    structural_metrics(
                        omega,
                        geometry,
                        transported_previous_omega,
                        delta_time,
                        structural_length=structural_length,
                        structural_weights=weights_array,
                        boundary_mode=boundary_mode,
                    )
                )

        metrics = (
            compensated_metrics
            if compensated_metrics is not None
            else eulerian_metrics
        )

        structure_rate[index] = metrics[
            "structure_score"
        ]

        heterogeneity[index] = metrics[
            "heterogeneity"
        ]

        localization[index] = metrics[
            "localization"
        ]

        roughness[index] = metrics[
            "roughness"
        ]

        sign_mixing[index] = metrics[
            "sign_mixing"
        ]

        temporal_deformation_eulerian[
            index
        ] = eulerian_metrics[
            "temporal_deformation"
        ]

        if (
            temporal_deformation_compensated
            is not None
        ):
            temporal_deformation_compensated[
                index
            ] = compensated_metrics[
                "temporal_deformation"
            ]

        temporal_deformation[index] = metrics[
            "temporal_deformation"
        ]

        # Diagnostic couplé expérimental.
        # Il ne remplace pas les deux axes indépendants.
        coupled_rate[index] = (
            intensity_rate[index]
            * (1.0 + structure_rate[index])
        )

        previous_omega = omega.copy()
        previous_time = time

    # La déformation calculée à l'indice i correspond à
    # l'intervalle temporel [t_(i-1), t_i].
    #
    # Elle est donc intégrée directement sur les intervalles,
    # sans lui attribuer artificiellement une valeur nodale.
    interval_dt = (
        temporal_geometry.interval_dt
    )

    observed_duration = (
        temporal_geometry.duration
    )

    interval_midpoints = 0.5 * (
        times[:-1] + times[1:]
    )

    interval_deformation_eulerian = (
        temporal_deformation_eulerian[
            1:
        ].copy()
    )

    interval_deformation_compensated = (
        temporal_deformation_compensated[
            1:
        ].copy()
        if (
            temporal_deformation_compensated
            is not None
        )
        else None
    )

    interval_deformation = (
        interval_deformation_compensated
        if (
            temporal_deformation_mode
            == "transport_compensated"
        )
        else interval_deformation_eulerian
    )

    bounded_heterogeneity = (
        np.maximum(heterogeneity, 0.0)
        / (
            1.0
            + np.maximum(heterogeneity, 0.0)
        )
    )

    bounded_localization = (
        np.maximum(localization, 0.0)
        / (
            1.0
            + np.maximum(localization, 0.0)
        )
    )

    bounded_roughness = (
        np.maximum(roughness, 0.0)
        / (
            1.0
            + np.maximum(roughness, 0.0)
        )
    )

    bounded_sign_mixing = np.clip(
        sign_mixing,
        0.0,
        1.0,
    )

    bounded_interval_deformation = (
        np.maximum(interval_deformation, 0.0)
        / (
            1.0
            + np.maximum(interval_deformation, 0.0)
        )
    )

    # Les quatre composantes nodales sont évaluées au milieu
    # de chaque intervalle par moyenne trapézoïdale.
    component_intervals = np.vstack(
        (
            0.5 * (
                bounded_heterogeneity[:-1]
                + bounded_heterogeneity[1:]
            ),
            0.5 * (
                bounded_localization[:-1]
                + bounded_localization[1:]
            ),
            0.5 * (
                bounded_roughness[:-1]
                + bounded_roughness[1:]
            ),
            0.5 * (
                bounded_sign_mixing[:-1]
                + bounded_sign_mixing[1:]
            ),
            bounded_interval_deformation,
        )
    )

    interval_structure = np.tensordot(
        weights_array,
        component_intervals,
        axes=(0, 0),
    )

    component_index_values = (
        np.sum(
            component_intervals * interval_dt,
            axis=1,
        )
        / observed_duration
    )

    component_indices = {
        component_name: float(component_value)
        for component_name, component_value in zip(
            STRUCTURAL_COMPONENT_NAMES,
            component_index_values,
            strict=True,
        )
    }

    intensity_interval = 0.5 * (
        intensity_rate[:-1]
        + intensity_rate[1:]
    )

    coupled_interval = (
        intensity_interval
        * (1.0 + interval_structure)
    )

    intensity_index = float(
        np.trapezoid(
            intensity_rate,
            times,
        )
        / observed_duration
    )

    temporal_deformation_eulerian_index = float(
        np.sum(
            interval_deformation_eulerian
            * interval_dt
        )
        / observed_duration
    )

    temporal_deformation_compensated_index = (
        float(
            np.sum(
                interval_deformation_compensated
                * interval_dt
            )
            / observed_duration
        )
        if (
            interval_deformation_compensated
            is not None
        )
        else None
    )

    temporal_deformation_index = (
        temporal_deformation_compensated_index
        if (
            temporal_deformation_mode
            == "transport_compensated"
        )
        else temporal_deformation_eulerian_index
    )

    structure_index = float(
        np.sum(
            interval_structure
            * interval_dt
        )
        / observed_duration
    )

    coupled_index = float(
        np.sum(
            coupled_interval
            * interval_dt
        )
        / observed_duration
    )

    # Séries nodales uniquement destinées aux graphiques
    # et aux fichiers CSV. Les indices ci-dessus utilisent
    # directement les valeurs d'intervalle.
    temporal_deformation_eulerian = np.interp(
        times,
        interval_midpoints,
        interval_deformation_eulerian,
        left=float(
            interval_deformation_eulerian[0]
        ),
        right=float(
            interval_deformation_eulerian[-1]
        ),
    )

    temporal_deformation_compensated = (
        np.interp(
            times,
            interval_midpoints,
            interval_deformation_compensated,
            left=float(
                interval_deformation_compensated[0]
            ),
            right=float(
                interval_deformation_compensated[-1]
            ),
        )
        if (
            interval_deformation_compensated
            is not None
        )
        else None
    )

    temporal_deformation = (
        temporal_deformation_compensated
        if (
            temporal_deformation_mode
            == "transport_compensated"
        )
        else temporal_deformation_eulerian
    )

    structure_rate = np.interp(
        times,
        interval_midpoints,
        interval_structure,
        left=float(interval_structure[0]),
        right=float(interval_structure[-1]),
    )

    coupled_rate = np.interp(
        times,
        interval_midpoints,
        coupled_interval,
        left=float(coupled_interval[0]),
        right=float(coupled_interval[-1]),
    )

    return {
        "name": name,
        "boundary_mode": boundary_mode,
        "temporal_deformation_mode": (
            temporal_deformation_mode
        ),
        "transport_compensation": (
            {
                "enabled": True,
                "boundary_mode": "periodic",
                "interpolation": (
                    transport_interpolation
                ),
                "backtrace": (
                    transport_trajectory_method
                ),
            }
            if (
                temporal_deformation_mode
                == "transport_compensated"
            )
            else {
                "enabled": False,
            }
        ),
        "spatial_geometry": (
            spatial_geometry_metadata(
                geometry
            )
        ),
        "temporal_geometry": (
            temporal_geometry.as_dict()
        ),
        "intensity_rate": intensity_rate,
        "structure_rate": structure_rate,
        "coupled_rate": coupled_rate,
        "heterogeneity": heterogeneity,
        "localization": localization,
        "roughness": roughness,
        "sign_mixing": sign_mixing,
        "temporal_deformation": temporal_deformation,
        "temporal_deformation_interval": interval_deformation,
        "temporal_deformation_index": (
            temporal_deformation_index
        ),
        "temporal_deformation_eulerian": (
            temporal_deformation_eulerian
        ),
        "temporal_deformation_eulerian_interval": (
            interval_deformation_eulerian
        ),
        "temporal_deformation_eulerian_index": (
            temporal_deformation_eulerian_index
        ),
        "temporal_deformation_compensated": (
            temporal_deformation_compensated
        ),
        "temporal_deformation_compensated_interval": (
            interval_deformation_compensated
        ),
        "temporal_deformation_compensated_index": (
            temporal_deformation_compensated_index
        ),
        "temporal_interval_dt": interval_dt,
        "temporal_interval_midpoints": interval_midpoints,
        "structure_interval": interval_structure,
        "coupled_interval": coupled_interval,
        "structural_component_names": STRUCTURAL_COMPONENT_NAMES,
        "structural_weights": tuple(
            float(value)
            for value in weights_array
        ),
        "component_indices": component_indices,
        "intensity_index": intensity_index,
        "structure_index": structure_index,
        "coupled_index": coupled_index,
    }



def main() -> None:
    cfg = Config()

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        dtype=np.float64,
    )

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    spacing = float(
        coordinates[1] - coordinates[0]
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    scenarios = (
        (
            "calme_irrotationnel",
            calm_field,
        ),
        (
            "vortex_coherent",
            coherent_vortex,
        ),
        (
            "multi_vortex_complexe",
            multi_vortex_field,
        ),
    )

    results = [
        simulate(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )
        for name, velocity_function in scenarios
    ]

    output_dir = Path("itd_v29_results")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_path = output_dir / "summary.csv"

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as summary_file:
        summary_file.write(
            "scenario,"
            "intensity_index,"
            "structure_index,"
            "coupled_diagnostic\n"
        )

        for result in results:
            summary_file.write(
                f'{result["name"]},'
                f'{result["intensity_index"]},'
                f'{result["structure_index"]},'
                f'{result["coupled_index"]}\n'
            )

    for result in results:
        name = str(result["name"])

        table = np.column_stack(
            (
                times,
                np.asarray(result["intensity_rate"]),
                np.asarray(result["structure_rate"]),
                np.asarray(result["coupled_rate"]),
                np.asarray(result["heterogeneity"]),
                np.asarray(result["localization"]),
                np.asarray(result["roughness"]),
                np.asarray(result["sign_mixing"]),
                np.asarray(
                    result["temporal_deformation"]
                ),
            )
        )

        np.savetxt(
            output_dir / f"{name}.csv",
            table,
            delimiter=",",
            header=(
                "time,"
                "intensity_rate,"
                "structure_rate,"
                "coupled_rate,"
                "heterogeneity,"
                "localization,"
                "roughness,"
                "sign_mixing,"
                "temporal_deformation"
            ),
            comments="",
        )

    plt.figure(figsize=(10, 6))

    for result in results:
        plt.plot(
            times,
            np.asarray(result["structure_rate"]),
            label=str(result["name"]),
        )

    plt.xlabel("Temps")
    plt.ylabel("Indice structurel instantané")
    plt.title("Évolution de la complexité structurelle")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir / "structure_over_time.png",
        dpi=160,
    )
    plt.close()

    plt.figure(figsize=(9, 7))

    for result in results:
        intensity = float(
            result["intensity_index"]
        )

        structure = float(
            result["structure_index"]
        )

        plt.scatter(
            intensity,
            structure,
            s=100,
        )

        plt.annotate(
            str(result["name"]),
            (intensity, structure),
            xytext=(8, 6),
            textcoords="offset points",
        )

    plt.xlabel("Intensité dynamique ITD")
    plt.ylabel("Complexité structurelle")
    plt.title(
        "Espace dynamique à deux dimensions"
    )
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        output_dir / "intensity_structure_map.png",
        dpi=160,
    )
    plt.close()

    calm = results[0]
    coherent = results[1]
    complex_result = results[2]

    assert float(calm["intensity_index"]) < 1.0e-20
    assert float(calm["structure_index"]) < 1.0e-20

    assert (
        float(coherent["intensity_index"])
        > float(complex_result["intensity_index"])
    )

    assert (
        float(complex_result["structure_index"])
        > float(coherent["structure_index"])
    )

    print("=== SIMULATEUR ITD VERSION 29 ===")
    print(
        "Longueur structurelle :",
        f"{STRUCTURAL_LENGTH:.6f}",
    )

    for result in results:
        print()
        print(
            "Scénario             :",
            result["name"],
        )
        print(
            "Intensité ITD        :",
            f'{float(result["intensity_index"]):.12f}',
        )
        print(
            "Structure            :",
            f'{float(result["structure_index"]):.12f}',
        )
        print(
            "Diagnostic couplé    :",
            f'{float(result["coupled_index"]):.12f}',
        )

    print()
    print(
        "Validation deux axes : RÉUSSIE"
    )
    print(
        "Résumé               :",
        summary_path.resolve(),
    )


if __name__ == "__main__":
    main()
