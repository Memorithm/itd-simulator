"""
Extraction du moteur principal de simulation.

Module généré automatiquement pour ITD V29.16.
L'API historique reste réexportée par itd_v29.py.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from compare_scenarios import (
    Config,
    curvature_field,
)
from itd_v29_core.constants import (
    DEFAULT_STRUCTURAL_WEIGHTS,
    STRUCTURAL_COMPONENT_NAMES,
    STRUCTURAL_LENGTH,
    TEMPORAL_DEFORMATION_MODES,
)
from itd_v29_core.multiscale_structure import (
    derive_multiscale_profile,
    validate_structural_length_grid,
)
from itd_v29_core.periodic_transport import (
    transport_previous_vorticity_periodic,
    validate_periodic_transport_mesh,
    validate_transport_interpolation,
    validate_transport_trajectory_method,
)
from itd_v29_core.spatial_geometry import (
    normalize_spatial_geometry,
    spatial_geometry_metadata,
    validate_mesh_geometry,
)
from itd_v29_core.spatial_operators import (
    numerical_vorticity_with_boundary,
    spatial_mean,
    validate_boundary_mode,
)
from itd_v29_core.structural_metrics import (
    normalize_structural_weights,
    structural_metrics,
)
from itd_v29_core.time_geometry import normalize_time_grid


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
    if not callable(velocity_function):
        raise ValueError("Le champ de vitesse doit être appelable.")

    if not callable(curvature_function):
        raise ValueError("Le champ de courbure doit être appelable.")

    try:
        characteristic_length = float(cfg.characteristic_length)
    except (AttributeError, TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            "La longueur caractéristique doit être un nombre réel."
        ) from error

    if (
        not np.isfinite(characteristic_length)
        or characteristic_length < 0.0
    ):
        raise ValueError(
            "La longueur caractéristique doit être finie et "
            "positive ou nulle."
        )

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

    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

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

        vx = np.asarray(vx, dtype=np.float64)
        vy = np.asarray(vy, dtype=np.float64)

        if vx.shape != x.shape or vy.shape != x.shape:
            raise ValueError(
                "Le champ de vitesse doit avoir la même forme "
                "que le maillage spatial."
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
            characteristic_length**2
            * curvature
        )

        if not np.all(np.isfinite(curvature_weight)):
            raise ValueError(
                "La pondération de courbure dépasse le domaine "
                "numérique fini."
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
