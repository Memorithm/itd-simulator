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


def validate_structural_length_grid(
    structural_lengths: object,
) -> np.ndarray:
    """
    Valide une grille strictement croissante de
    longueurs structurelles positives ou nulles.
    """
    if isinstance(
        structural_lengths,
        (str, bytes),
    ):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "former une séquence numérique."
        )

    try:
        array = np.asarray(
            structural_lengths,
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Les longueurs structurelles doivent "
            "former une séquence numérique réelle."
        ) from error

    if array.ndim != 1:
        raise ValueError(
            "Les longueurs structurelles doivent "
            "former un tableau unidimensionnel."
        )

    if array.size < 2:
        raise ValueError(
            "Un profil multi-échelle exige au moins "
            "deux longueurs structurelles."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "être finies."
        )

    if np.any(array < 0.0):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "être positives ou nulles."
        )

    if np.any(np.diff(array) <= 0.0):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "être strictement croissantes."
        )

    copied = np.array(
        array,
        dtype=np.float64,
        copy=True,
    )

    copied.setflags(
        write=False
    )

    return copied


def derive_multiscale_profile(
    reference_result: dict[str, object],
    structural_lengths: object,
) -> dict[str, object]:
    """
    Dérive un profil multi-échelle à partir d'une
    simulation effectuée avec structural_length = 1.

    La rugosité brute vérifie exactement :

        Q_raw(ell) = ell * Q_raw(1).

    Les autres composantes ne dépendent pas de ell.
    """
    lengths = validate_structural_length_grid(
        structural_lengths
    )

    required_keys = (
        "intensity_rate",
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
        "temporal_deformation_interval",
        "temporal_interval_dt",
        "structural_weights",
        "intensity_index",
        "temporal_deformation_index",
    )

    missing = tuple(
        key
        for key in required_keys
        if key not in reference_result
    )

    if missing:
        raise ValueError(
            "Le résultat de référence ne contient "
            "pas toutes les données nécessaires : "
            + ", ".join(missing)
        )

    intensity_rate = np.asarray(
        reference_result["intensity_rate"],
        dtype=np.float64,
    )

    heterogeneity = np.asarray(
        reference_result["heterogeneity"],
        dtype=np.float64,
    )

    localization = np.asarray(
        reference_result["localization"],
        dtype=np.float64,
    )

    unit_roughness = np.asarray(
        reference_result["roughness"],
        dtype=np.float64,
    )

    sign_mixing = np.asarray(
        reference_result["sign_mixing"],
        dtype=np.float64,
    )

    interval_deformation = np.asarray(
        reference_result[
            "temporal_deformation_interval"
        ],
        dtype=np.float64,
    )

    interval_dt = np.asarray(
        reference_result[
            "temporal_interval_dt"
        ],
        dtype=np.float64,
    )

    weights = np.asarray(
        reference_result["structural_weights"],
        dtype=np.float64,
    )

    nodal_size = intensity_rate.size
    interval_size = nodal_size - 1

    nodal_arrays = (
        heterogeneity,
        localization,
        unit_roughness,
        sign_mixing,
    )

    if nodal_size < 2:
        raise ValueError(
            "Le résultat de référence doit contenir "
            "au moins deux instants."
        )

    if any(
        array.shape != (nodal_size,)
        for array in nodal_arrays
    ):
        raise ValueError(
            "Les séries nodales du résultat de "
            "référence ont des formes incohérentes."
        )

    if interval_deformation.shape != (
        interval_size,
    ):
        raise ValueError(
            "La série de déformation d'intervalle "
            "a une forme incohérente."
        )

    if interval_dt.shape != (
        interval_size,
    ):
        raise ValueError(
            "La grille des intervalles temporels "
            "a une forme incohérente."
        )

    if weights.shape != (
        len(STRUCTURAL_COMPONENT_NAMES),
    ):
        raise ValueError(
            "Le vecteur de pondération structurelle "
            "a une forme incohérente."
        )

    all_arrays = (
        intensity_rate,
        heterogeneity,
        localization,
        unit_roughness,
        sign_mixing,
        interval_deformation,
        interval_dt,
        weights,
    )

    if not all(
        np.all(np.isfinite(array))
        for array in all_arrays
    ):
        raise ValueError(
            "Le résultat de référence contient "
            "une valeur non finie."
        )

    if np.any(interval_dt <= 0.0):
        raise ValueError(
            "Les intervalles temporels doivent être "
            "strictement positifs."
        )

    duration = float(
        np.sum(
            interval_dt,
            dtype=np.float64,
        )
    )

    if (
        not np.isfinite(duration)
        or duration <= 0.0
    ):
        raise ValueError(
            "La durée du profil doit être finie "
            "et strictement positive."
        )

    bounded_heterogeneity = (
        np.maximum(
            heterogeneity,
            0.0,
        )
        / (
            1.0
            + np.maximum(
                heterogeneity,
                0.0,
            )
        )
    )

    bounded_localization = (
        np.maximum(
            localization,
            0.0,
        )
        / (
            1.0
            + np.maximum(
                localization,
                0.0,
            )
        )
    )

    bounded_sign_mixing = np.clip(
        sign_mixing,
        0.0,
        1.0,
    )

    bounded_interval_deformation = (
        np.maximum(
            interval_deformation,
            0.0,
        )
        / (
            1.0
            + np.maximum(
                interval_deformation,
                0.0,
            )
        )
    )

    heterogeneity_interval = 0.5 * (
        bounded_heterogeneity[:-1]
        + bounded_heterogeneity[1:]
    )

    localization_interval = 0.5 * (
        bounded_localization[:-1]
        + bounded_localization[1:]
    )

    sign_mixing_interval = 0.5 * (
        bounded_sign_mixing[:-1]
        + bounded_sign_mixing[1:]
    )

    intensity_interval = 0.5 * (
        intensity_rate[:-1]
        + intensity_rate[1:]
    )

    length_count = int(
        lengths.size
    )

    signatures = np.empty(
        (
            length_count,
            len(STRUCTURAL_COMPONENT_NAMES),
        ),
        dtype=np.float64,
    )

    raw_roughness_indices = np.empty(
        length_count,
        dtype=np.float64,
    )

    structure_indices = np.empty(
        length_count,
        dtype=np.float64,
    )

    coupled_indices = np.empty(
        length_count,
        dtype=np.float64,
    )

    component_indices: list[
        dict[str, float]
    ] = []

    structure_intervals: list[
        np.ndarray
    ] = []

    coupled_intervals: list[
        np.ndarray
    ] = []

    for index, structural_length in enumerate(
        lengths
    ):
        raw_roughness = (
            structural_length
            * unit_roughness
        )

        bounded_roughness = (
            np.maximum(
                raw_roughness,
                0.0,
            )
            / (
                1.0
                + np.maximum(
                    raw_roughness,
                    0.0,
                )
            )
        )

        roughness_interval = 0.5 * (
            bounded_roughness[:-1]
            + bounded_roughness[1:]
        )

        raw_roughness_interval = 0.5 * (
            raw_roughness[:-1]
            + raw_roughness[1:]
        )

        component_interval = np.vstack(
            (
                heterogeneity_interval,
                localization_interval,
                roughness_interval,
                sign_mixing_interval,
                bounded_interval_deformation,
            )
        )

        signature = (
            np.sum(
                component_interval
                * interval_dt,
                axis=1,
            )
            / duration
        )

        structure_interval = np.tensordot(
            weights,
            component_interval,
            axes=(0, 0),
        )

        coupled_interval = (
            intensity_interval
            * (
                1.0
                + structure_interval
            )
        )

        structure_index = float(
            np.sum(
                structure_interval
                * interval_dt,
                dtype=np.float64,
            )
            / duration
        )

        coupled_index = float(
            np.sum(
                coupled_interval
                * interval_dt,
                dtype=np.float64,
            )
            / duration
        )

        raw_roughness_index = float(
            np.sum(
                raw_roughness_interval
                * interval_dt,
                dtype=np.float64,
            )
            / duration
        )

        signatures[index] = signature

        structure_indices[index] = (
            structure_index
        )

        coupled_indices[index] = (
            coupled_index
        )

        raw_roughness_indices[index] = (
            raw_roughness_index
        )

        component_indices.append(
            {
                name: float(value)
                for name, value in zip(
                    STRUCTURAL_COMPONENT_NAMES,
                    signature,
                    strict=True,
                )
            }
        )

        structure_intervals.append(
            structure_interval.copy()
        )

        coupled_intervals.append(
            coupled_interval.copy()
        )

    return {
        "name": reference_result.get(
            "name",
            "multiscale",
        ),
        "structural_lengths": lengths,
        "length_count": length_count,
        "structural_component_names": (
            STRUCTURAL_COMPONENT_NAMES
        ),
        "structural_weights": tuple(
            float(value)
            for value in weights
        ),
        "structural_signatures": signatures,
        "component_indices": tuple(
            component_indices
        ),
        "raw_roughness_indices": (
            raw_roughness_indices
        ),
        "structure_indices": structure_indices,
        "coupled_indices": coupled_indices,
        "intensity_index": float(
            reference_result["intensity_index"]
        ),
        "temporal_deformation_index": float(
            reference_result[
                "temporal_deformation_index"
            ]
        ),
        "structure_intervals": tuple(
            structure_intervals
        ),
        "coupled_intervals": tuple(
            coupled_intervals
        ),
        "reference_structural_length": 1.0,
        "reference_result": reference_result,
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



def validate_refinement_ratio(
    refinement_ratio: float,
) -> float:
    try:
        ratio = float(refinement_ratio)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Le rapport de raffinement doit être "
            "un nombre réel."
        ) from error

    if (
        not np.isfinite(ratio)
        or ratio <= 1.0
    ):
        raise ValueError(
            "Le rapport de raffinement doit être "
            "fini et strictement supérieur à un."
        )

    return ratio


def validate_convergence_tolerance(
    equality_tolerance: float,
) -> float:
    try:
        tolerance = float(
            equality_tolerance
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "La tolérance d'égalité doit être "
            "un nombre réel."
        ) from error

    if (
        not np.isfinite(tolerance)
        or tolerance < 0.0
    ):
        raise ValueError(
            "La tolérance d'égalité doit être "
            "finie et positive ou nulle."
        )

    return tolerance


def richardson_triplet(
    coarse: float,
    medium: float,
    fine: float,
    refinement_ratio: float = 2.0,
    equality_tolerance: float = 1.0e-14,
) -> dict[str, object]:
    """
    Analyse trois approximations obtenues avec :

        h, h/r, h/r².

    Statuts possibles :

    resolved
        Les trois valeurs sont égales à la tolérance
        numérique choisie.

    asymptotic
        Les différences sont monotones et permettent
        d'estimer un ordre strictement positif.

    non_monotone
        Les deux différences changent de signe ou
        l'ordre observé n'est pas positif.

    degenerate
        Une seule différence est numériquement nulle ;
        aucun ordre fiable ne peut être calculé.
    """
    ratio = validate_refinement_ratio(
        refinement_ratio
    )

    tolerance = validate_convergence_tolerance(
        equality_tolerance
    )

    try:
        values = np.asarray(
            (
                coarse,
                medium,
                fine,
            ),
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Les trois approximations doivent être "
            "des nombres réels."
        ) from error

    if not np.all(np.isfinite(values)):
        raise ValueError(
            "Les trois approximations doivent "
            "être finies."
        )

    coarse_value = float(values[0])
    medium_value = float(values[1])
    fine_value = float(values[2])

    coarse_medium_difference = (
        coarse_value
        - medium_value
    )

    medium_fine_difference = (
        medium_value
        - fine_value
    )

    scale = max(
        1.0,
        abs(coarse_value),
        abs(medium_value),
        abs(fine_value),
    )

    absolute_tolerance = (
        tolerance
        * scale
    )

    coarse_medium_zero = (
        abs(coarse_medium_difference)
        <= absolute_tolerance
    )

    medium_fine_zero = (
        abs(medium_fine_difference)
        <= absolute_tolerance
    )

    common = {
        "coarse": coarse_value,
        "medium": medium_value,
        "fine": fine_value,
        "refinement_ratio": ratio,
        "coarse_medium_difference": (
            coarse_medium_difference
        ),
        "medium_fine_difference": (
            medium_fine_difference
        ),
    }

    if (
        coarse_medium_zero
        and medium_fine_zero
    ):
        return {
            **common,
            "status": "resolved",
            "observed_order": float("inf"),
            "convergence_ratio": 0.0,
            "extrapolated_limit": fine_value,
            "estimated_fine_error": 0.0,
            "estimated_relative_fine_error": 0.0,
        }

    if (
        coarse_medium_zero
        or medium_fine_zero
    ):
        return {
            **common,
            "status": "degenerate",
            "observed_order": None,
            "convergence_ratio": None,
            "extrapolated_limit": None,
            "estimated_fine_error": None,
            "estimated_relative_fine_error": None,
        }

    difference_ratio = abs(
        coarse_medium_difference
        / medium_fine_difference
    )

    observed_order = float(
        np.log(difference_ratio)
        / np.log(ratio)
    )

    convergence_ratio = float(
        abs(
            medium_fine_difference
            / coarse_medium_difference
        )
    )

    monotone = (
        coarse_medium_difference
        * medium_fine_difference
        > 0.0
    )

    if (
        not monotone
        or not np.isfinite(observed_order)
        or observed_order <= 0.0
    ):
        return {
            **common,
            "status": "non_monotone",
            "observed_order": observed_order,
            "convergence_ratio": convergence_ratio,
            "extrapolated_limit": None,
            "estimated_fine_error": None,
            "estimated_relative_fine_error": None,
        }

    denominator = (
        ratio**observed_order
        - 1.0
    )

    if (
        not np.isfinite(denominator)
        or denominator <= 0.0
    ):
        return {
            **common,
            "status": "degenerate",
            "observed_order": observed_order,
            "convergence_ratio": convergence_ratio,
            "extrapolated_limit": None,
            "estimated_fine_error": None,
            "estimated_relative_fine_error": None,
        }

    extrapolated_limit = float(
        fine_value
        + (
            fine_value
            - medium_value
        ) / denominator
    )

    estimated_fine_error = abs(
        extrapolated_limit
        - fine_value
    )

    estimated_relative_fine_error = (
        estimated_fine_error
        / max(
            1.0e-15,
            abs(extrapolated_limit),
        )
    )

    return {
        **common,
        "status": "asymptotic",
        "observed_order": observed_order,
        "convergence_ratio": convergence_ratio,
        "extrapolated_limit": extrapolated_limit,
        "estimated_fine_error": (
            estimated_fine_error
        ),
        "estimated_relative_fine_error": (
            estimated_relative_fine_error
        ),
    }


def extract_single_scale_diagnostics(
    result: dict[str, object],
) -> dict[str, float]:
    required_scalar_keys = (
        "intensity_index",
        "structure_index",
        "coupled_index",
        "temporal_deformation_index",
    )

    missing = tuple(
        key
        for key in required_scalar_keys
        if key not in result
    )

    if missing:
        raise ValueError(
            "Le résultat ne contient pas les "
            "diagnostics requis : "
            + ", ".join(missing)
        )

    if "component_indices" not in result:
        raise ValueError(
            "Le résultat ne contient pas la "
            "signature structurelle."
        )

    diagnostics = {
        key: float(result[key])
        for key in required_scalar_keys
    }

    components = dict(
        result["component_indices"]
    )

    for component_name in (
        STRUCTURAL_COMPONENT_NAMES
    ):
        if component_name not in components:
            raise ValueError(
                "La signature ne contient pas la "
                f"composante {component_name!r}."
            )

        diagnostics[
            f"component:{component_name}"
        ] = float(
            components[component_name]
        )

    values = np.asarray(
        tuple(diagnostics.values()),
        dtype=np.float64,
    )

    if not np.all(np.isfinite(values)):
        raise ValueError(
            "Les diagnostics contiennent une "
            "valeur non finie."
        )

    return diagnostics


def analyze_result_triplet(
    coarse_result: dict[str, object],
    medium_result: dict[str, object],
    fine_result: dict[str, object],
    refinement_ratio: float = 2.0,
    equality_tolerance: float = 1.0e-14,
) -> tuple[dict[str, object], ...]:
    coarse = extract_single_scale_diagnostics(
        coarse_result
    )

    medium = extract_single_scale_diagnostics(
        medium_result
    )

    fine = extract_single_scale_diagnostics(
        fine_result
    )

    if not (
        coarse.keys()
        == medium.keys()
        == fine.keys()
    ):
        raise ValueError(
            "Les trois résultats ne contiennent "
            "pas les mêmes diagnostics."
        )

    rows: list[
        dict[str, object]
    ] = []

    for metric_name in coarse:
        estimate = richardson_triplet(
            coarse[metric_name],
            medium[metric_name],
            fine[metric_name],
            refinement_ratio=refinement_ratio,
            equality_tolerance=equality_tolerance,
        )

        rows.append(
            {
                "metric": metric_name,
                "structural_length": None,
                **estimate,
            }
        )

    return tuple(rows)


def analyze_multiscale_profile_triplet(
    coarse_profile: dict[str, object],
    medium_profile: dict[str, object],
    fine_profile: dict[str, object],
    refinement_ratio: float = 2.0,
    equality_tolerance: float = 1.0e-14,
) -> tuple[dict[str, object], ...]:
    profiles = (
        coarse_profile,
        medium_profile,
        fine_profile,
    )

    for profile in profiles:
        required = (
            "structural_lengths",
            "structural_signatures",
            "structure_indices",
            "coupled_indices",
            "raw_roughness_indices",
            "intensity_index",
            "temporal_deformation_index",
            "structural_component_names",
        )

        missing = tuple(
            key
            for key in required
            if key not in profile
        )

        if missing:
            raise ValueError(
                "Un profil ne contient pas les "
                "données requises : "
                + ", ".join(missing)
            )

    lengths = tuple(
        np.asarray(
            profile["structural_lengths"],
            dtype=np.float64,
        )
        for profile in profiles
    )

    if not (
        np.array_equal(
            lengths[0],
            lengths[1],
        )
        and np.array_equal(
            lengths[1],
            lengths[2],
        )
    ):
        raise ValueError(
            "Les trois profils doivent utiliser "
            "les mêmes longueurs structurelles."
        )

    component_names = tuple(
        coarse_profile[
            "structural_component_names"
        ]
    )

    if not (
        component_names
        == tuple(
            medium_profile[
                "structural_component_names"
            ]
        )
        == tuple(
            fine_profile[
                "structural_component_names"
            ]
        )
    ):
        raise ValueError(
            "Les profils ne contiennent pas les "
            "mêmes composantes structurelles."
        )

    signature_arrays = tuple(
        np.asarray(
            profile["structural_signatures"],
            dtype=np.float64,
        )
        for profile in profiles
    )

    expected_shape = (
        lengths[0].size,
        len(component_names),
    )

    if any(
        array.shape != expected_shape
        for array in signature_arrays
    ):
        raise ValueError(
            "Une matrice de signatures possède "
            "une forme incohérente."
        )

    structure_arrays = tuple(
        np.asarray(
            profile["structure_indices"],
            dtype=np.float64,
        )
        for profile in profiles
    )

    coupled_arrays = tuple(
        np.asarray(
            profile["coupled_indices"],
            dtype=np.float64,
        )
        for profile in profiles
    )

    raw_roughness_arrays = tuple(
        np.asarray(
            profile["raw_roughness_indices"],
            dtype=np.float64,
        )
        for profile in profiles
    )

    expected_vector_shape = (
        lengths[0].size,
    )

    for arrays in (
        structure_arrays,
        coupled_arrays,
        raw_roughness_arrays,
    ):
        if any(
            array.shape != expected_vector_shape
            for array in arrays
        ):
            raise ValueError(
                "Un profil scalaire multi-échelle "
                "possède une forme incohérente."
            )

    all_arrays = (
        *signature_arrays,
        *structure_arrays,
        *coupled_arrays,
        *raw_roughness_arrays,
    )

    if not all(
        np.all(np.isfinite(array))
        for array in all_arrays
    ):
        raise ValueError(
            "Un profil contient une valeur "
            "non finie."
        )

    rows: list[
        dict[str, object]
    ] = []

    for metric_name in (
        "intensity_index",
        "temporal_deformation_index",
    ):
        estimate = richardson_triplet(
            float(coarse_profile[metric_name]),
            float(medium_profile[metric_name]),
            float(fine_profile[metric_name]),
            refinement_ratio=refinement_ratio,
            equality_tolerance=equality_tolerance,
        )

        rows.append(
            {
                "metric": metric_name,
                "structural_length": None,
                **estimate,
            }
        )

    for length_index, structural_length in enumerate(
        lengths[0]
    ):
        length_value = float(
            structural_length
        )

        for component_index, component_name in enumerate(
            component_names
        ):
            estimate = richardson_triplet(
                signature_arrays[0][
                    length_index,
                    component_index,
                ],
                signature_arrays[1][
                    length_index,
                    component_index,
                ],
                signature_arrays[2][
                    length_index,
                    component_index,
                ],
                refinement_ratio=refinement_ratio,
                equality_tolerance=equality_tolerance,
            )

            rows.append(
                {
                    "metric": (
                        f"component:{component_name}"
                    ),
                    "structural_length": (
                        length_value
                    ),
                    **estimate,
                }
            )

        for (
            metric_name,
            arrays,
        ) in (
            (
                "structure_index",
                structure_arrays,
            ),
            (
                "coupled_index",
                coupled_arrays,
            ),
            (
                "raw_roughness_index",
                raw_roughness_arrays,
            ),
        ):
            estimate = richardson_triplet(
                arrays[0][length_index],
                arrays[1][length_index],
                arrays[2][length_index],
                refinement_ratio=refinement_ratio,
                equality_tolerance=equality_tolerance,
            )

            rows.append(
                {
                    "metric": metric_name,
                    "structural_length": (
                        length_value
                    ),
                    **estimate,
                }
            )

    return tuple(rows)


def summarize_convergence_rows(
    rows: object,
) -> dict[str, object]:
    try:
        row_tuple = tuple(rows)
    except TypeError as error:
        raise ValueError(
            "Les diagnostics de convergence doivent "
            "former une séquence."
        ) from error

    if not row_tuple:
        raise ValueError(
            "Le résumé exige au moins un diagnostic."
        )

    status_counts: dict[str, int] = {}

    finite_orders: list[float] = []
    relative_errors: list[float] = []

    for row in row_tuple:
        if not isinstance(row, dict):
            raise ValueError(
                "Chaque diagnostic doit être "
                "représenté par un dictionnaire."
            )

        status = str(
            row.get(
                "status",
                "missing",
            )
        )

        status_counts[status] = (
            status_counts.get(status, 0)
            + 1
        )

        order = row.get(
            "observed_order"
        )

        if order is not None:
            order_value = float(order)

            if np.isfinite(order_value):
                finite_orders.append(
                    order_value
                )

        relative_error = row.get(
            "estimated_relative_fine_error"
        )

        if relative_error is not None:
            relative_error_value = float(
                relative_error
            )

            if np.isfinite(
                relative_error_value
            ):
                relative_errors.append(
                    relative_error_value
                )

    return {
        "row_count": len(row_tuple),
        "status_counts": status_counts,
        "minimum_finite_order": (
            min(finite_orders)
            if finite_orders
            else None
        ),
        "maximum_finite_order": (
            max(finite_orders)
            if finite_orders
            else None
        ),
        "maximum_estimated_relative_fine_error": (
            max(relative_errors)
            if relative_errors
            else None
        ),
    }


def convergence_row_key(
    row: dict[str, object],
) -> tuple[str, float | None]:
    if not isinstance(row, dict):
        raise ValueError(
            "Un diagnostic de convergence doit être "
            "représenté par un dictionnaire."
        )

    if "metric" not in row:
        raise ValueError(
            "Le diagnostic ne contient pas "
            "de nom de métrique."
        )

    metric = str(
        row["metric"]
    )

    structural_length = row.get(
        "structural_length"
    )

    if structural_length is None:
        length_value = None
    else:
        try:
            length_value = float(
                structural_length
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "La longueur structurelle du "
                "diagnostic doit être réelle."
            ) from error

        if not np.isfinite(length_value):
            raise ValueError(
                "La longueur structurelle du "
                "diagnostic doit être finie."
            )

    return metric, length_value


def convergence_error_is_estimable(
    row: dict[str, object],
) -> bool:
    status = str(
        row.get(
            "status",
            "",
        )
    )

    return status in (
        "resolved",
        "asymptotic",
    )


def combine_decoupled_convergence_rows(
    spatial_rows: object,
    temporal_rows: object,
    fine_match_tolerance: float = 1.0e-12,
) -> tuple[dict[str, object], ...]:
    """
    Combine deux études indépendantes :

    - raffinement spatial à grille temporelle fixe ;
    - raffinement temporel à grille spatiale fixe.

    Les deux études doivent partager exactement le
    même résultat fin.

    Le budget conservateur est :

        E_total <= E_spatial + E_temporal.
    """
    tolerance = (
        validate_convergence_tolerance(
            fine_match_tolerance
        )
    )

    try:
        spatial_tuple = tuple(
            spatial_rows
        )

        temporal_tuple = tuple(
            temporal_rows
        )
    except TypeError as error:
        raise ValueError(
            "Les diagnostics spatiaux et temporels "
            "doivent former des séquences."
        ) from error

    if not spatial_tuple:
        raise ValueError(
            "L'étude spatiale est vide."
        )

    if not temporal_tuple:
        raise ValueError(
            "L'étude temporelle est vide."
        )

    spatial_map: dict[
        tuple[str, float | None],
        dict[str, object],
    ] = {}

    temporal_map: dict[
        tuple[str, float | None],
        dict[str, object],
    ] = {}

    for row in spatial_tuple:
        key = convergence_row_key(
            row
        )

        if key in spatial_map:
            raise ValueError(
                "L'étude spatiale contient un "
                "diagnostic dupliqué."
            )

        spatial_map[key] = row

    for row in temporal_tuple:
        key = convergence_row_key(
            row
        )

        if key in temporal_map:
            raise ValueError(
                "L'étude temporelle contient un "
                "diagnostic dupliqué."
            )

        temporal_map[key] = row

    if spatial_map.keys() != temporal_map.keys():
        raise ValueError(
            "Les études spatiale et temporelle "
            "ne contiennent pas les mêmes métriques."
        )

    combined_rows: list[
        dict[str, object]
    ] = []

    for key in spatial_map:
        spatial = spatial_map[key]
        temporal = temporal_map[key]

        try:
            spatial_fine = float(
                spatial["fine"]
            )

            temporal_fine = float(
                temporal["fine"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Un diagnostic ne contient pas une "
                "valeur fine numérique."
            ) from error

        if not (
            np.isfinite(spatial_fine)
            and np.isfinite(temporal_fine)
        ):
            raise ValueError(
                "Les valeurs fines doivent être finies."
            )

        fine_scale = max(
            1.0,
            abs(spatial_fine),
            abs(temporal_fine),
        )

        fine_difference = abs(
            spatial_fine
            - temporal_fine
        )

        if (
            fine_difference
            > tolerance * fine_scale
        ):
            raise ValueError(
                "Les études spatiale et temporelle "
                "ne partagent pas le même calcul fin "
                f"pour {key!r}."
            )

        common_fine = spatial_fine

        spatial_estimable = (
            convergence_error_is_estimable(
                spatial
            )
        )

        temporal_estimable = (
            convergence_error_is_estimable(
                temporal
            )
        )

        spatial_error = (
            float(
                spatial[
                    "estimated_fine_error"
                ]
            )
            if spatial_estimable
            else None
        )

        temporal_error = (
            float(
                temporal[
                    "estimated_fine_error"
                ]
            )
            if temporal_estimable
            else None
        )

        if (
            spatial_error is not None
            and (
                not np.isfinite(spatial_error)
                or spatial_error < 0.0
            )
        ):
            raise ValueError(
                "L'erreur spatiale estimée doit être "
                "finie et positive ou nulle."
            )

        if (
            temporal_error is not None
            and (
                not np.isfinite(temporal_error)
                or temporal_error < 0.0
            )
        ):
            raise ValueError(
                "L'erreur temporelle estimée doit être "
                "finie et positive ou nulle."
            )

        if (
            spatial_estimable
            and temporal_estimable
        ):
            certification_status = (
                "certified"
            )

            combined_error = (
                spatial_error
                + temporal_error
            )

            combined_relative_error = (
                combined_error
                / max(
                    1.0e-15,
                    abs(common_fine),
                )
            )
        elif (
            spatial_estimable
            or temporal_estimable
        ):
            certification_status = (
                "partial"
            )

            combined_error = None
            combined_relative_error = None
        else:
            certification_status = (
                "uncertain"
            )

            combined_error = None
            combined_relative_error = None

        combined_rows.append(
            {
                "metric": key[0],
                "structural_length": key[1],
                "fine_value": common_fine,
                "fine_match_error": (
                    fine_difference
                ),
                "certification_status": (
                    certification_status
                ),
                "spatial_status": spatial.get(
                    "status"
                ),
                "spatial_observed_order": (
                    spatial.get(
                        "observed_order"
                    )
                ),
                "spatial_extrapolated_limit": (
                    spatial.get(
                        "extrapolated_limit"
                    )
                ),
                "spatial_estimated_fine_error": (
                    spatial_error
                ),
                "spatial_estimated_relative_fine_error": (
                    spatial.get(
                        "estimated_relative_fine_error"
                    )
                ),
                "temporal_status": temporal.get(
                    "status"
                ),
                "temporal_observed_order": (
                    temporal.get(
                        "observed_order"
                    )
                ),
                "temporal_extrapolated_limit": (
                    temporal.get(
                        "extrapolated_limit"
                    )
                ),
                "temporal_estimated_fine_error": (
                    temporal_error
                ),
                "temporal_estimated_relative_fine_error": (
                    temporal.get(
                        "estimated_relative_fine_error"
                    )
                ),
                "combined_estimated_fine_error": (
                    combined_error
                ),
                "combined_estimated_relative_fine_error": (
                    combined_relative_error
                ),
            }
        )

    return tuple(
        combined_rows
    )


def summarize_decoupled_convergence_rows(
    rows: object,
) -> dict[str, object]:
    """
    Résume une étude spatio-temporelle découplée.

    Un ordre observé n'est statistiquement publié
    que lorsque l'axe correspondant possède le statut
    "asymptotic".

    Les ordres associés aux statuts :

    - resolved ;
    - non_monotone ;
    - degenerate ;

    ne doivent pas entrer dans les minima et maxima.
    """
    try:
        row_tuple = tuple(rows)
    except TypeError as error:
        raise ValueError(
            "Les diagnostics découplés doivent "
            "former une séquence."
        ) from error

    if not row_tuple:
        raise ValueError(
            "Le résumé découplé exige au moins "
            "un diagnostic."
        )

    status_counts: dict[str, int] = {}
    spatial_status_counts: dict[str, int] = {}
    temporal_status_counts: dict[str, int] = {}

    spatial_orders: list[float] = []
    temporal_orders: list[float] = []

    combined_relative_errors: list[
        tuple[
            float,
            str,
            float | None,
        ]
    ] = []

    for row in row_tuple:
        if not isinstance(row, dict):
            raise ValueError(
                "Chaque diagnostic découplé doit "
                "être un dictionnaire."
            )

        certification_status = str(
            row.get(
                "certification_status",
                "missing",
            )
        )

        spatial_status = str(
            row.get(
                "spatial_status",
                "missing",
            )
        )

        temporal_status = str(
            row.get(
                "temporal_status",
                "missing",
            )
        )

        status_counts[
            certification_status
        ] = (
            status_counts.get(
                certification_status,
                0,
            )
            + 1
        )

        spatial_status_counts[
            spatial_status
        ] = (
            spatial_status_counts.get(
                spatial_status,
                0,
            )
            + 1
        )

        temporal_status_counts[
            temporal_status
        ] = (
            temporal_status_counts.get(
                temporal_status,
                0,
            )
            + 1
        )

        # Un ordre n'a de sens pour le résumé que
        # dans un régime asymptotique monotone.
        if spatial_status == "asymptotic":
            spatial_order = row.get(
                "spatial_observed_order"
            )

            if spatial_order is not None:
                value = float(
                    spatial_order
                )

                if (
                    np.isfinite(value)
                    and value > 0.0
                ):
                    spatial_orders.append(
                        value
                    )

        if temporal_status == "asymptotic":
            temporal_order = row.get(
                "temporal_observed_order"
            )

            if temporal_order is not None:
                value = float(
                    temporal_order
                )

                if (
                    np.isfinite(value)
                    and value > 0.0
                ):
                    temporal_orders.append(
                        value
                    )

        combined_relative_error = row.get(
            "combined_estimated_relative_fine_error"
        )

        if combined_relative_error is not None:
            value = float(
                combined_relative_error
            )

            if (
                np.isfinite(value)
                and value >= 0.0
            ):
                structural_length = row.get(
                    "structural_length"
                )

                if structural_length is not None:
                    structural_length = float(
                        structural_length
                    )

                combined_relative_errors.append(
                    (
                        value,
                        str(
                            row.get(
                                "metric",
                                "",
                            )
                        ),
                        structural_length,
                    )
                )

    if combined_relative_errors:
        worst = max(
            combined_relative_errors,
            key=lambda item: item[0],
        )

        maximum_combined_error = worst[0]
        worst_metric = worst[1]
        worst_structural_length = worst[2]
    else:
        maximum_combined_error = None
        worst_metric = None
        worst_structural_length = None

    return {
        "row_count": len(row_tuple),
        "status_counts": status_counts,
        "spatial_status_counts": (
            spatial_status_counts
        ),
        "temporal_status_counts": (
            temporal_status_counts
        ),
        "minimum_spatial_order": (
            min(spatial_orders)
            if spatial_orders
            else None
        ),
        "maximum_spatial_order": (
            max(spatial_orders)
            if spatial_orders
            else None
        ),
        "minimum_temporal_order": (
            min(temporal_orders)
            if temporal_orders
            else None
        ),
        "maximum_temporal_order": (
            max(temporal_orders)
            if temporal_orders
            else None
        ),
        "maximum_combined_estimated_relative_fine_error": (
            maximum_combined_error
        ),
        "worst_metric": worst_metric,
        "worst_structural_length": (
            worst_structural_length
        ),
    }



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


def validate_periodic_transport_mesh(
    x: object,
    y: object,
    geometry: object,
    boundary_mode: str,
) -> tuple[
    np.ndarray,
    np.ndarray,
    float,
    float,
]:
    """
    Valide une grille périodique cartésienne uniforme.

    La compensation de transport V21 ne possède
    volontairement aucune convention de remplissage
    aux frontières finies.
    """
    if boundary_mode != "periodic":
        raise ValueError(
            "La compensation de transport V21 "
            "exige le mode périodique."
        )

    normalized_geometry = (
        normalize_spatial_geometry(
            geometry
        )
    )

    if isinstance(
        normalized_geometry,
        RectilinearGeometry,
    ):
        if not normalized_geometry.uniform:
            raise ValueError(
                "La compensation de transport V21 "
                "exige une grille uniforme."
            )

        geometry_dx = float(
            normalized_geometry.dx
        )

        geometry_dy = float(
            normalized_geometry.dy
        )
    else:
        geometry_dx = float(
            normalized_geometry.dx
        )

        geometry_dy = float(
            normalized_geometry.dy
        )

    x_array = np.asarray(
        x,
        dtype=np.float64,
    )

    y_array = np.asarray(
        y,
        dtype=np.float64,
    )

    if (
        x_array.ndim != 2
        or y_array.ndim != 2
        or x_array.shape != y_array.shape
    ):
        raise ValueError(
            "Le maillage périodique doit être formé "
            "de deux tableaux 2D de même forme."
        )

    if min(x_array.shape) < 2:
        raise ValueError(
            "Le maillage périodique doit contenir "
            "au moins deux points par axe."
        )

    if not (
        np.all(np.isfinite(x_array))
        and np.all(np.isfinite(y_array))
    ):
        raise ValueError(
            "Le maillage périodique contient une "
            "valeur non finie."
        )

    (
        x_coordinates,
        coordinate_dx,
    ) = validate_uniform_axis_coordinates(
        x_array[0, :],
        "x",
    )

    (
        y_coordinates,
        coordinate_dy,
    ) = validate_uniform_axis_coordinates(
        y_array[:, 0],
        "y",
    )

    expected_x = np.broadcast_to(
        x_coordinates,
        x_array.shape,
    )

    expected_y = np.broadcast_to(
        y_coordinates[:, None],
        y_array.shape,
    )

    coordinate_scale = max(
        1.0,
        float(
            np.max(
                np.abs(x_array)
            )
        ),
        float(
            np.max(
                np.abs(y_array)
            )
        ),
    )

    tolerance = (
        128.0
        * np.finfo(np.float64).eps
        * coordinate_scale
    )

    if not np.allclose(
        x_array,
        expected_x,
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "Le maillage x n'est pas cartésien "
            "et rectiligne."
        )

    if not np.allclose(
        y_array,
        expected_y,
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "Le maillage y n'est pas cartésien "
            "et rectiligne."
        )

    spacing_scale = max(
        1.0,
        abs(coordinate_dx),
        abs(coordinate_dy),
        abs(geometry_dx),
        abs(geometry_dy),
    )

    spacing_tolerance = (
        128.0
        * np.finfo(np.float64).eps
        * spacing_scale
    )

    if not np.isclose(
        coordinate_dx,
        geometry_dx,
        rtol=1.0e-12,
        atol=spacing_tolerance,
    ):
        raise ValueError(
            "Le pas x du maillage ne correspond "
            "pas à la géométrie."
        )

    if not np.isclose(
        coordinate_dy,
        geometry_dy,
        rtol=1.0e-12,
        atol=spacing_tolerance,
    ):
        raise ValueError(
            "Le pas y du maillage ne correspond "
            "pas à la géométrie."
        )

    return (
        x_coordinates,
        y_coordinates,
        coordinate_dx,
        coordinate_dy,
    )


def periodic_bilinear_backtrace(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    transport_vx: object,
    transport_vy: object,
    delta_time: float,
) -> np.ndarray:
    """
    Transporte semi-lagrangiennement un champ scalaire
    du temps précédent vers le temps courant.

    Pour chaque nœud courant x :

        x_source = x - delta_time * u_transport.

    Les coordonnées sources sont rabattues
    périodiquement dans le domaine.
    """
    (
        x_axis,
        dx,
    ) = validate_uniform_axis_coordinates(
        x_coordinates,
        "x",
    )

    (
        y_axis,
        dy,
    ) = validate_uniform_axis_coordinates(
        y_coordinates,
        "y",
    )

    try:
        dt = float(
            delta_time
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Le pas temporel de transport doit "
            "être un nombre réel."
        ) from error

    if (
        not np.isfinite(dt)
        or dt <= 0.0
    ):
        raise ValueError(
            "Le pas temporel de transport doit "
            "être fini et strictement positif."
        )

    array = np.asarray(
        field,
        dtype=np.float64,
    )

    vx = np.asarray(
        transport_vx,
        dtype=np.float64,
    )

    vy = np.asarray(
        transport_vy,
        dtype=np.float64,
    )

    expected_shape = (
        y_axis.size,
        x_axis.size,
    )

    if array.shape != expected_shape:
        raise ValueError(
            "Le champ transporté doit avoir la "
            f"forme {expected_shape}, obtenue "
            f"{array.shape}."
        )

    if (
        vx.shape != expected_shape
        or vy.shape != expected_shape
    ):
        raise ValueError(
            "Le champ de transport doit avoir "
            "la forme de la grille."
        )

    if not (
        np.all(np.isfinite(array))
        and np.all(np.isfinite(vx))
        and np.all(np.isfinite(vy))
    ):
        raise ValueError(
            "Le transport contient une valeur "
            "non finie."
        )

    target_x, target_y = np.meshgrid(
        x_axis,
        y_axis,
        indexing="xy",
    )

    period_x = (
        dx * x_axis.size
    )

    period_y = (
        dy * y_axis.size
    )

    source_x = (
        target_x
        - dt * vx
    )

    source_y = (
        target_y
        - dt * vy
    )

    wrapped_x = (
        x_axis[0]
        + np.mod(
            source_x - x_axis[0],
            period_x,
        )
    )

    wrapped_y = (
        y_axis[0]
        + np.mod(
            source_y - y_axis[0],
            period_y,
        )
    )

    normalized_x = (
        wrapped_x - x_axis[0]
    ) / dx

    normalized_y = (
        wrapped_y - y_axis[0]
    ) / dy

    rounded_x = np.rint(
        normalized_x
    )

    rounded_y = np.rint(
        normalized_y
    )

    exact_tolerance = (
        512.0
        * np.finfo(np.float64).eps
        * max(
            x_axis.size,
            y_axis.size,
        )
    )

    snap_x = (
        np.abs(
            normalized_x - rounded_x
        )
        <= exact_tolerance
    )

    snap_y = (
        np.abs(
            normalized_y - rounded_y
        )
        <= exact_tolerance
    )

    if (
        np.all(snap_x)
        and np.all(snap_y)
    ):
        exact_ix = np.mod(
            rounded_x.astype(np.int64),
            x_axis.size,
        )

        exact_iy = np.mod(
            rounded_y.astype(np.int64),
            y_axis.size,
        )

        return array[
            exact_iy,
            exact_ix,
        ].copy()

    normalized_x = np.where(
        snap_x,
        np.mod(
            rounded_x,
            x_axis.size,
        ),
        normalized_x,
    )

    normalized_y = np.where(
        snap_y,
        np.mod(
            rounded_y,
            y_axis.size,
        ),
        normalized_y,
    )

    ix0 = np.floor(
        normalized_x
    ).astype(np.int64)

    iy0 = np.floor(
        normalized_y
    ).astype(np.int64)

    tx = (
        normalized_x
        - ix0
    )

    ty = (
        normalized_y
        - iy0
    )

    ix0 = np.mod(
        ix0,
        x_axis.size,
    )

    iy0 = np.mod(
        iy0,
        y_axis.size,
    )

    ix1 = np.mod(
        ix0 + 1,
        x_axis.size,
    )

    iy1 = np.mod(
        iy0 + 1,
        y_axis.size,
    )

    value_00 = array[
        iy0,
        ix0,
    ]

    value_10 = array[
        iy0,
        ix1,
    ]

    value_01 = array[
        iy1,
        ix0,
    ]

    value_11 = array[
        iy1,
        ix1,
    ]

    one_minus_tx = 1.0 - tx
    one_minus_ty = 1.0 - ty

    return (
        one_minus_tx
        * one_minus_ty
        * value_00
        + tx
        * one_minus_ty
        * value_10
        + one_minus_tx
        * ty
        * value_01
        + tx
        * ty
        * value_11
    )


def periodic_coordinate_geometry(
    coordinates: object,
    axis_name: str,
) -> tuple[np.ndarray, float, float]:
    values = np.asarray(
        coordinates,
        dtype=np.float64,
    )

    if (
        values.ndim != 1
        or values.size < 2
    ):
        raise ValueError(
            f"Les coordonnées périodiques {axis_name} "
            "doivent former un vecteur contenant "
            "au moins deux points."
        )

    if not np.all(
        np.isfinite(values)
    ):
        raise ValueError(
            f"Les coordonnées périodiques {axis_name} "
            "doivent être finies."
        )

    differences = np.diff(values)

    if not np.all(
        differences > 0.0
    ):
        raise ValueError(
            f"Les coordonnées périodiques {axis_name} "
            "doivent être strictement croissantes."
        )

    spacing = float(
        differences[0]
    )

    tolerance = (
        128.0
        * np.finfo(np.float64).eps
        * max(
            1.0,
            abs(spacing),
            float(
                np.max(
                    np.abs(values)
                )
            ),
        )
    )

    if not np.allclose(
        differences,
        spacing,
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "Le rétrotraçage périodique RK4 exige "
            "une grille uniforme."
        )

    period = float(
        spacing * values.size
    )

    if (
        not np.isfinite(period)
        or period <= 0.0
    ):
        raise ValueError(
            f"La période de l'axe {axis_name} "
            "est invalide."
        )

    return values, float(values[0]), period


def wrap_periodic_points(
    values: object,
    origin: float,
    period: float,
) -> np.ndarray:
    array = np.asarray(
        values,
        dtype=np.float64,
    )

    return (
        origin
        + np.mod(
            array - origin,
            period,
        )
    )


def evaluate_periodic_transport_velocity(
    transport_velocity_function: Callable,
    x: object,
    y: object,
    time: float,
    x_origin: float,
    x_period: float,
    y_origin: float,
    y_period: float,
) -> tuple[np.ndarray, np.ndarray]:
    wrapped_x = wrap_periodic_points(
        x,
        x_origin,
        x_period,
    )

    wrapped_y = wrap_periodic_points(
        y,
        y_origin,
        y_period,
    )

    result = transport_velocity_function(
        wrapped_x,
        wrapped_y,
        float(time),
    )

    if (
        not isinstance(
            result,
            (
                tuple,
                list,
            ),
        )
        or len(result) != 2
    ):
        raise ValueError(
            "Le champ de transport doit retourner "
            "exactement deux composantes."
        )

    target_shape = np.broadcast_shapes(
        np.shape(wrapped_x),
        np.shape(wrapped_y),
    )

    try:
        velocity_x = np.broadcast_to(
            np.asarray(
                result[0],
                dtype=np.float64,
            ),
            target_shape,
        )

        velocity_y = np.broadcast_to(
            np.asarray(
                result[1],
                dtype=np.float64,
            ),
            target_shape,
        )
    except ValueError as error:
        raise ValueError(
            "Les composantes du champ de transport "
            "ne sont pas compatibles avec la grille."
        ) from error

    if (
        not np.all(
            np.isfinite(velocity_x)
        )
        or not np.all(
            np.isfinite(velocity_y)
        )
    ):
        raise ValueError(
            "Le champ de transport doit rester fini "
            "sur toute la rétrotrajectoire."
        )

    return (
        np.asarray(
            velocity_x,
            dtype=np.float64,
        ),
        np.asarray(
            velocity_y,
            dtype=np.float64,
        ),
    )


def rk4_periodic_departure_points(
    x: object,
    y: object,
    x_coordinates: object,
    y_coordinates: object,
    previous_time: float,
    current_time: float,
    transport_velocity_function: Callable,
) -> tuple[np.ndarray, np.ndarray]:
    if not callable(
        transport_velocity_function
    ):
        raise ValueError(
            "Le champ de transport doit être "
            "appelable."
        )

    previous_time = float(
        previous_time
    )

    current_time = float(
        current_time
    )

    delta_time = (
        current_time
        - previous_time
    )

    if (
        not np.isfinite(previous_time)
        or not np.isfinite(current_time)
        or not np.isfinite(delta_time)
        or delta_time <= 0.0
    ):
        raise ValueError(
            "Les instants du rétrotraçage doivent "
            "être finis et strictement croissants."
        )

    _, x_origin, x_period = (
        periodic_coordinate_geometry(
            x_coordinates,
            "x",
        )
    )

    _, y_origin, y_period = (
        periodic_coordinate_geometry(
            y_coordinates,
            "y",
        )
    )

    current_x, current_y = np.broadcast_arrays(
        np.asarray(
            x,
            dtype=np.float64,
        ),
        np.asarray(
            y,
            dtype=np.float64,
        ),
    )

    if (
        not np.all(
            np.isfinite(current_x)
        )
        or not np.all(
            np.isfinite(current_y)
        )
    ):
        raise ValueError(
            "Les points d'arrivée doivent être finis."
        )

    step = -delta_time
    midpoint_time = 0.5 * (
        previous_time
        + current_time
    )

    k1_x, k1_y = (
        evaluate_periodic_transport_velocity(
            transport_velocity_function,
            current_x,
            current_y,
            current_time,
            x_origin,
            x_period,
            y_origin,
            y_period,
        )
    )

    k2_x, k2_y = (
        evaluate_periodic_transport_velocity(
            transport_velocity_function,
            current_x
            + 0.5 * step * k1_x,
            current_y
            + 0.5 * step * k1_y,
            midpoint_time,
            x_origin,
            x_period,
            y_origin,
            y_period,
        )
    )

    k3_x, k3_y = (
        evaluate_periodic_transport_velocity(
            transport_velocity_function,
            current_x
            + 0.5 * step * k2_x,
            current_y
            + 0.5 * step * k2_y,
            midpoint_time,
            x_origin,
            x_period,
            y_origin,
            y_period,
        )
    )

    k4_x, k4_y = (
        evaluate_periodic_transport_velocity(
            transport_velocity_function,
            current_x
            + step * k3_x,
            current_y
            + step * k3_y,
            previous_time,
            x_origin,
            x_period,
            y_origin,
            y_period,
        )
    )

    departure_x = (
        current_x
        + (
            step
            / 6.0
        )
        * (
            k1_x
            + 2.0 * k2_x
            + 2.0 * k3_x
            + k4_x
        )
    )

    departure_y = (
        current_y
        + (
            step
            / 6.0
        )
        * (
            k1_y
            + 2.0 * k2_y
            + 2.0 * k3_y
            + k4_y
        )
    )

    if (
        not np.all(
            np.isfinite(departure_x)
        )
        or not np.all(
            np.isfinite(departure_y)
        )
    ):
        raise ValueError(
            "Les points de départ RK4 doivent "
            "rester finis."
        )

    return departure_x, departure_y


def transport_previous_vorticity_periodic(
    previous_omega: object,
    x: object,
    y: object,
    x_coordinates: object,
    y_coordinates: object,
    previous_time: float,
    current_time: float,
    transport_velocity_function: Callable,
    transport_interpolation: str = (
        "bilinear_periodic"
    ),
    transport_trajectory_method: str = (
        "midpoint_time_velocity"
    ),
) -> np.ndarray:
    if not callable(
        transport_velocity_function
    ):
        raise ValueError(
            "Le champ de transport doit être "
            "appelable."
        )

    trajectory_method = (
        validate_transport_trajectory_method(
            transport_trajectory_method
        )
    )

    delta_time = float(
        current_time - previous_time
    )

    if (
        not np.isfinite(delta_time)
        or delta_time <= 0.0
    ):
        raise ValueError(
            "Les instants du transport doivent être "
            "finis et strictement croissants."
        )

    # Chemin historique V25-V28 conservé sans
    # modification numérique.
    if (
        trajectory_method
        == "midpoint_time_velocity"
    ):
        midpoint_time = 0.5 * (
            previous_time
            + current_time
        )

        transport_vx, transport_vy = (
            transport_velocity_function(
                x,
                y,
                midpoint_time,
            )
        )

        return periodic_backtrace(
            previous_omega,
            x_coordinates,
            y_coordinates,
            transport_vx,
            transport_vy,
            delta_time,
            interpolation=(
                transport_interpolation
            ),
        )

    departure_x, departure_y = (
        rk4_periodic_departure_points(
            x,
            y,
            x_coordinates,
            y_coordinates,
            previous_time,
            current_time,
            transport_velocity_function,
        )
    )

    # V29 : le rétrotraçage RK4 transmet désormais
    # directement les coordonnées de départ aux
    # interpolateurs. Aucun détour par une vitesse
    # effective n'est nécessaire.
    return periodic_sample_at_departures(
        previous_omega,
        x_coordinates,
        y_coordinates,
        departure_x,
        departure_y,
        interpolation=(
            transport_interpolation
        ),
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


def validate_galilean_frame_velocity(
    frame_velocity: object,
) -> np.ndarray:
    try:
        array = np.asarray(
            frame_velocity,
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "La vitesse du référentiel doit former "
            "un vecteur réel de dimension deux."
        ) from error

    if array.shape != (2,):
        raise ValueError(
            "La vitesse du référentiel doit former "
            "un vecteur de dimension deux."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "La vitesse du référentiel doit être finie."
        )

    copied = np.array(
        array,
        dtype=np.float64,
        copy=True,
    )

    copied.setflags(
        write=False
    )

    return copied


def validate_galilean_reference_time(
    reference_time: object,
) -> float:
    try:
        value = float(
            reference_time
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "L'instant de référence galiléen doit "
            "être un nombre réel."
        ) from error

    if not np.isfinite(value):
        raise ValueError(
            "L'instant de référence galiléen doit "
            "être fini."
        )

    return value


def galilean_source_coordinates(
    x: object,
    y: object,
    time: object,
    frame_velocity: object,
    reference_time: object = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcule les coordonnées de l'ancien référentiel :

        x = x' + c (t - t0).
    """
    velocity = validate_galilean_frame_velocity(
        frame_velocity
    )

    reference = validate_galilean_reference_time(
        reference_time
    )

    try:
        time_value = float(time)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "L'instant galiléen doit être réel."
        ) from error

    if not np.isfinite(time_value):
        raise ValueError(
            "L'instant galiléen doit être fini."
        )

    x_array = np.asarray(
        x,
        dtype=np.float64,
    )

    y_array = np.asarray(
        y,
        dtype=np.float64,
    )

    if x_array.shape != y_array.shape:
        raise ValueError(
            "Les coordonnées galiléennes x et y "
            "doivent avoir la même forme."
        )

    if not (
        np.all(np.isfinite(x_array))
        and np.all(np.isfinite(y_array))
    ):
        raise ValueError(
            "Les coordonnées galiléennes contiennent "
            "une valeur non finie."
        )

    elapsed = (
        time_value - reference
    )

    source_x = (
        x_array
        + velocity[0] * elapsed
    )

    source_y = (
        y_array
        + velocity[1] * elapsed
    )

    return source_x, source_y


def galilean_transform_scalar_function(
    scalar_function: Callable,
    frame_velocity: object,
    reference_time: object = 0.0,
) -> Callable:
    """
    Transforme un champ scalaire selon :

        f'(x',t) = f(x' + c(t-t0),t).
    """
    if not callable(scalar_function):
        raise ValueError(
            "Le champ scalaire galiléen doit être "
            "appelable."
        )

    velocity = validate_galilean_frame_velocity(
        frame_velocity
    )

    reference = validate_galilean_reference_time(
        reference_time
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> np.ndarray:
        source_x, source_y = (
            galilean_source_coordinates(
                x,
                y,
                time,
                velocity,
                reference,
            )
        )

        value = np.asarray(
            scalar_function(
                source_x,
                source_y,
                time,
            ),
            dtype=np.float64,
        )

        if value.shape != source_x.shape:
            raise ValueError(
                "Le champ scalaire transformé doit "
                "avoir la forme de la grille."
            )

        if not np.all(np.isfinite(value)):
            raise ValueError(
                "Le champ scalaire transformé contient "
                "une valeur non finie."
            )

        return value

    return transformed


def galilean_transform_velocity_function(
    velocity_function: Callable,
    frame_velocity: object,
    reference_time: object = 0.0,
) -> Callable:
    """
    Transforme un champ de vitesse selon :

        v'(x',t)
            = v(x' + c(t-t0),t) - c.
    """
    if not callable(velocity_function):
        raise ValueError(
            "Le champ de vitesse galiléen doit être "
            "appelable."
        )

    velocity = validate_galilean_frame_velocity(
        frame_velocity
    )

    reference = validate_galilean_reference_time(
        reference_time
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        source_x, source_y = (
            galilean_source_coordinates(
                x,
                y,
                time,
                velocity,
                reference,
            )
        )

        source_vx, source_vy = velocity_function(
            source_x,
            source_y,
            time,
        )

        source_vx = np.asarray(
            source_vx,
            dtype=np.float64,
        )

        source_vy = np.asarray(
            source_vy,
            dtype=np.float64,
        )

        if (
            source_vx.shape != source_x.shape
            or source_vy.shape != source_x.shape
        ):
            raise ValueError(
                "Le champ de vitesse transformé doit "
                "avoir la forme de la grille."
            )

        if not (
            np.all(np.isfinite(source_vx))
            and np.all(np.isfinite(source_vy))
        ):
            raise ValueError(
                "Le champ de vitesse transformé "
                "contient une valeur non finie."
            )

        return (
            source_vx - velocity[0],
            source_vy - velocity[1],
        )

    return transformed


def galilean_metadata(
    frame_velocity: object,
    reference_time: object = 0.0,
) -> dict[str, object]:
    velocity = validate_galilean_frame_velocity(
        frame_velocity
    )

    reference = validate_galilean_reference_time(
        reference_time
    )

    return {
        "transformation": "galilean",
        "frame_velocity_x": float(
            velocity[0]
        ),
        "frame_velocity_y": float(
            velocity[1]
        ),
        "reference_time": reference,
        "coordinate_law": (
            "x_prime = x - c * (t - t0)"
        ),
        "velocity_law": (
            "v_prime = v - c"
        ),
    }


def evaluate_translating_frame_vector(
    vector_function: Callable,
    time: object,
    quantity_name: str,
) -> np.ndarray:
    if not callable(vector_function):
        raise ValueError(
            f"La fonction de {quantity_name} du "
            "référentiel doit être appelable."
        )

    try:
        time_value = float(time)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "L'instant du référentiel doit être "
            "un nombre réel."
        ) from error

    if not np.isfinite(time_value):
        raise ValueError(
            "L'instant du référentiel doit être fini."
        )

    try:
        vector = np.asarray(
            vector_function(time_value),
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            f"La fonction de {quantity_name} doit "
            "retourner un vecteur réel."
        ) from error

    if vector.shape != (2,):
        raise ValueError(
            f"La fonction de {quantity_name} doit "
            "retourner un vecteur de dimension deux."
        )

    if not np.all(np.isfinite(vector)):
        raise ValueError(
            f"Le vecteur de {quantity_name} doit "
            "être fini."
        )

    copied = np.array(
        vector,
        dtype=np.float64,
        copy=True,
    )

    copied.setflags(
        write=False
    )

    return copied


def translating_frame_source_coordinates(
    x: object,
    y: object,
    time: object,
    displacement_function: Callable,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcule les coordonnées de l'ancien référentiel :

        x = x' + b(t).
    """
    displacement = (
        evaluate_translating_frame_vector(
            displacement_function,
            time,
            "déplacement",
        )
    )

    x_array = np.asarray(
        x,
        dtype=np.float64,
    )

    y_array = np.asarray(
        y,
        dtype=np.float64,
    )

    if x_array.shape != y_array.shape:
        raise ValueError(
            "Les coordonnées x et y doivent avoir "
            "la même forme."
        )

    if not (
        np.all(np.isfinite(x_array))
        and np.all(np.isfinite(y_array))
    ):
        raise ValueError(
            "Les coordonnées du référentiel "
            "contiennent une valeur non finie."
        )

    return (
        x_array + displacement[0],
        y_array + displacement[1],
    )


def translating_frame_transform_scalar_function(
    scalar_function: Callable,
    displacement_function: Callable,
) -> Callable:
    """
    Transforme un scalaire selon :

        f'(x',t) = f(x' + b(t),t).
    """
    if not callable(scalar_function):
        raise ValueError(
            "Le champ scalaire à transformer doit "
            "être appelable."
        )

    if not callable(displacement_function):
        raise ValueError(
            "La fonction de déplacement doit être "
            "appelable."
        )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> np.ndarray:
        source_x, source_y = (
            translating_frame_source_coordinates(
                x,
                y,
                time,
                displacement_function,
            )
        )

        values = np.asarray(
            scalar_function(
                source_x,
                source_y,
                time,
            ),
            dtype=np.float64,
        )

        if values.shape != source_x.shape:
            raise ValueError(
                "Le champ scalaire transformé doit "
                "avoir la forme de la grille."
            )

        if not np.all(np.isfinite(values)):
            raise ValueError(
                "Le champ scalaire transformé "
                "contient une valeur non finie."
            )

        return values

    return transformed


def translating_frame_transform_velocity_function(
    velocity_function: Callable,
    displacement_function: Callable,
    frame_velocity_function: Callable,
) -> Callable:
    """
    Transforme une vitesse sous une translation
    temporelle générale :

        v'(x',t)
            = v(x' + b(t),t) - db/dt.
    """
    if not callable(velocity_function):
        raise ValueError(
            "Le champ de vitesse à transformer doit "
            "être appelable."
        )

    if not callable(displacement_function):
        raise ValueError(
            "La fonction de déplacement doit être "
            "appelable."
        )

    if not callable(frame_velocity_function):
        raise ValueError(
            "La vitesse du référentiel doit être "
            "appelable."
        )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        source_x, source_y = (
            translating_frame_source_coordinates(
                x,
                y,
                time,
                displacement_function,
            )
        )

        frame_velocity = (
            evaluate_translating_frame_vector(
                frame_velocity_function,
                time,
                "vitesse",
            )
        )

        source_vx, source_vy = velocity_function(
            source_x,
            source_y,
            time,
        )

        source_vx = np.asarray(
            source_vx,
            dtype=np.float64,
        )

        source_vy = np.asarray(
            source_vy,
            dtype=np.float64,
        )

        if (
            source_vx.shape != source_x.shape
            or source_vy.shape != source_x.shape
        ):
            raise ValueError(
                "Le champ de vitesse transformé doit "
                "avoir la forme de la grille."
            )

        if not (
            np.all(np.isfinite(source_vx))
            and np.all(np.isfinite(source_vy))
        ):
            raise ValueError(
                "Le champ de vitesse transformé "
                "contient une valeur non finie."
            )

        return (
            source_vx - frame_velocity[0],
            source_vy - frame_velocity[1],
        )

    return transformed


def translating_frame_metadata(
    displacement_function: Callable,
    frame_velocity_function: Callable,
    reference_time: object = 0.0,
) -> dict[str, object]:
    displacement = (
        evaluate_translating_frame_vector(
            displacement_function,
            reference_time,
            "déplacement",
        )
    )

    velocity = (
        evaluate_translating_frame_vector(
            frame_velocity_function,
            reference_time,
            "vitesse",
        )
    )

    return {
        "transformation": (
            "time_dependent_translation"
        ),
        "reference_time": float(
            reference_time
        ),
        "reference_displacement_x": float(
            displacement[0]
        ),
        "reference_displacement_y": float(
            displacement[1]
        ),
        "reference_velocity_x": float(
            velocity[0]
        ),
        "reference_velocity_y": float(
            velocity[1]
        ),
        "coordinate_law": (
            "x_prime = x - b(t)"
        ),
        "velocity_law": (
            "v_prime = v - db/dt"
        ),
    }





def validate_transport_interpolation(
    interpolation: object,
) -> str:
    if not isinstance(
        interpolation,
        str,
    ):
        raise ValueError(
            "Le mode d'interpolation du transport "
            "doit être une chaîne."
        )

    normalized = (
        interpolation.strip().lower()
    )

    if (
        normalized
        not in TRANSPORT_INTERPOLATIONS
    ):
        allowed = ", ".join(
            TRANSPORT_INTERPOLATIONS
        )

        raise ValueError(
            "Interpolation de transport inconnue : "
            f"{interpolation!r}. "
            f"Modes autorisés : {allowed}."
        )

    return normalized

def validate_transport_trajectory_method(
    method: object,
) -> str:
    if not isinstance(method, str):
        raise ValueError(
            "La méthode de rétrotraçage doit être "
            "une chaîne."
        )

    if (
        method
        not in TRANSPORT_TRAJECTORY_METHODS
    ):
        allowed = ", ".join(
            TRANSPORT_TRAJECTORY_METHODS
        )

        raise ValueError(
            "Méthode de rétrotraçage inconnue : "
            f"{method!r}. Méthodes autorisées : "
            f"{allowed}."
        )

    return method



def periodic_cubic_lagrange_weights(
    fractional_coordinate: object,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Poids de Lagrange pour les quatre nœuds :

        -1, 0, 1, 2

    autour de l'indice inférieur de la cellule.
    """
    t = np.asarray(
        fractional_coordinate,
        dtype=np.float64,
    )

    if not np.all(np.isfinite(t)):
        raise ValueError(
            "La coordonnée fractionnaire contient "
            "une valeur non finie."
        )

    weight_minus_one = (
        -t
        * (t - 1.0)
        * (t - 2.0)
        / 6.0
    )

    weight_zero = (
        (t + 1.0)
        * (t - 1.0)
        * (t - 2.0)
        / 2.0
    )

    weight_one = (
        -(t + 1.0)
        * t
        * (t - 2.0)
        / 2.0
    )

    weight_two = (
        (t + 1.0)
        * t
        * (t - 1.0)
        / 6.0
    )

    return (
        weight_minus_one,
        weight_zero,
        weight_one,
        weight_two,
    )


def periodic_cubic_backtrace(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    transport_vx: object,
    transport_vy: object,
    delta_time: float,
) -> np.ndarray:
    """
    Rétrotraçage périodique avec interpolation
    cubique tensorielle à seize points.

    L'interpolation est d'ordre quatre pour un champ
    périodique suffisamment régulier.

    Aucun limiteur monotone n'est appliqué : cette
    interpolation vise la précision sur les champs
    lisses, et non la préservation d'extrema.
    """
    (
        x_axis,
        dx,
    ) = validate_uniform_axis_coordinates(
        x_coordinates,
        "x",
    )

    (
        y_axis,
        dy,
    ) = validate_uniform_axis_coordinates(
        y_coordinates,
        "y",
    )

    if (
        x_axis.size < 4
        or y_axis.size < 4
    ):
        raise ValueError(
            "L'interpolation cubique périodique "
            "exige au moins quatre points par axe."
        )

    try:
        dt = float(
            delta_time
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Le pas temporel de transport doit "
            "être un nombre réel."
        ) from error

    if (
        not np.isfinite(dt)
        or dt <= 0.0
    ):
        raise ValueError(
            "Le pas temporel de transport doit "
            "être fini et strictement positif."
        )

    array = np.asarray(
        field,
        dtype=np.float64,
    )

    vx = np.asarray(
        transport_vx,
        dtype=np.float64,
    )

    vy = np.asarray(
        transport_vy,
        dtype=np.float64,
    )

    expected_shape = (
        y_axis.size,
        x_axis.size,
    )

    if array.shape != expected_shape:
        raise ValueError(
            "Le champ transporté doit avoir la "
            f"forme {expected_shape}, obtenue "
            f"{array.shape}."
        )

    if (
        vx.shape != expected_shape
        or vy.shape != expected_shape
    ):
        raise ValueError(
            "Le champ de transport doit avoir "
            "la forme de la grille."
        )

    if not (
        np.all(np.isfinite(array))
        and np.all(np.isfinite(vx))
        and np.all(np.isfinite(vy))
    ):
        raise ValueError(
            "Le transport contient une valeur "
            "non finie."
        )

    target_x, target_y = np.meshgrid(
        x_axis,
        y_axis,
        indexing="xy",
    )

    period_x = (
        dx * x_axis.size
    )

    period_y = (
        dy * y_axis.size
    )

    source_x = (
        target_x
        - dt * vx
    )

    source_y = (
        target_y
        - dt * vy
    )

    wrapped_x = (
        x_axis[0]
        + np.mod(
            source_x - x_axis[0],
            period_x,
        )
    )

    wrapped_y = (
        y_axis[0]
        + np.mod(
            source_y - y_axis[0],
            period_y,
        )
    )

    normalized_x = (
        wrapped_x - x_axis[0]
    ) / dx

    normalized_y = (
        wrapped_y - y_axis[0]
    ) / dy

    rounded_x = np.rint(
        normalized_x
    )

    rounded_y = np.rint(
        normalized_y
    )

    exact_tolerance = (
        512.0
        * np.finfo(np.float64).eps
        * max(
            x_axis.size,
            y_axis.size,
        )
    )

    snap_x = (
        np.abs(
            normalized_x
            - rounded_x
        )
        <= exact_tolerance
    )

    snap_y = (
        np.abs(
            normalized_y
            - rounded_y
        )
        <= exact_tolerance
    )

    if (
        np.all(snap_x)
        and np.all(snap_y)
    ):
        exact_ix = np.mod(
            rounded_x.astype(np.int64),
            x_axis.size,
        )

        exact_iy = np.mod(
            rounded_y.astype(np.int64),
            y_axis.size,
        )

        return array[
            exact_iy,
            exact_ix,
        ].copy()

    normalized_x = np.where(
        snap_x,
        np.mod(
            rounded_x,
            x_axis.size,
        ),
        normalized_x,
    )

    normalized_y = np.where(
        snap_y,
        np.mod(
            rounded_y,
            y_axis.size,
        ),
        normalized_y,
    )

    base_x = np.floor(
        normalized_x
    ).astype(np.int64)

    base_y = np.floor(
        normalized_y
    ).astype(np.int64)

    fractional_x = (
        normalized_x - base_x
    )

    fractional_y = (
        normalized_y - base_y
    )

    weights_x = (
        periodic_cubic_lagrange_weights(
            fractional_x
        )
    )

    weights_y = (
        periodic_cubic_lagrange_weights(
            fractional_y
        )
    )

    offsets = (
        -1,
        0,
        1,
        2,
    )

    indices_x = tuple(
        np.mod(
            base_x + offset,
            x_axis.size,
        )
        for offset in offsets
    )

    indices_y = tuple(
        np.mod(
            base_y + offset,
            y_axis.size,
        )
        for offset in offsets
    )

    interpolated = np.zeros(
        expected_shape,
        dtype=np.float64,
    )

    for y_index in range(4):
        for x_index in range(4):
            interpolated += (
                weights_y[y_index]
                * weights_x[x_index]
                * array[
                    indices_y[y_index],
                    indices_x[x_index],
                ]
            )

    return interpolated

def periodic_bilinear_departure_bounds(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    transport_vx: object,
    transport_vy: object,
    delta_time: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Retourne les bornes des quatre nœuds entourant
    chaque point de départ périodique.
    """
    source = np.asarray(
        field,
        dtype=np.float64,
    )

    x_values, x_origin, x_period = (
        periodic_coordinate_geometry(
            x_coordinates,
            "x",
        )
    )

    y_values, y_origin, y_period = (
        periodic_coordinate_geometry(
            y_coordinates,
            "y",
        )
    )

    expected_shape = (
        y_values.size,
        x_values.size,
    )

    if source.shape != expected_shape:
        raise ValueError(
            "La forme du champ est incompatible "
            "avec les coordonnées périodiques."
        )

    delta_time = float(
        delta_time
    )

    if (
        not np.isfinite(delta_time)
        or delta_time <= 0.0
    ):
        raise ValueError(
            "Le pas temporel doit être fini et "
            "strictement positif."
        )

    grid_x, grid_y = np.meshgrid(
        x_values,
        y_values,
        indexing="xy",
    )

    try:
        velocity_x = np.broadcast_to(
            np.asarray(
                transport_vx,
                dtype=np.float64,
            ),
            source.shape,
        )

        velocity_y = np.broadcast_to(
            np.asarray(
                transport_vy,
                dtype=np.float64,
            ),
            source.shape,
        )
    except ValueError as error:
        raise ValueError(
            "Les vitesses du transport ne sont pas "
            "compatibles avec la grille."
        ) from error

    if (
        not np.all(
            np.isfinite(velocity_x)
        )
        or not np.all(
            np.isfinite(velocity_y)
        )
    ):
        raise ValueError(
            "Les vitesses du transport doivent "
            "être finies."
        )

    departure_x = wrap_periodic_points(
        grid_x
        - delta_time * velocity_x,
        x_origin,
        x_period,
    )

    departure_y = wrap_periodic_points(
        grid_y
        - delta_time * velocity_y,
        y_origin,
        y_period,
    )

    spacing_x = float(
        x_values[1] - x_values[0]
    )

    spacing_y = float(
        y_values[1] - y_values[0]
    )

    coordinate_x = (
        departure_x - x_origin
    ) / spacing_x

    coordinate_y = (
        departure_y - y_origin
    ) / spacing_y

    index_x0 = (
        np.floor(
            coordinate_x
        ).astype(np.int64)
        % x_values.size
    )

    index_y0 = (
        np.floor(
            coordinate_y
        ).astype(np.int64)
        % y_values.size
    )

    index_x1 = (
        index_x0 + 1
    ) % x_values.size

    index_y1 = (
        index_y0 + 1
    ) % y_values.size

    value_00 = source[
        index_y0,
        index_x0,
    ]

    value_10 = source[
        index_y0,
        index_x1,
    ]

    value_01 = source[
        index_y1,
        index_x0,
    ]

    value_11 = source[
        index_y1,
        index_x1,
    ]

    lower_bound = np.minimum.reduce(
        (
            value_00,
            value_10,
            value_01,
            value_11,
        )
    )

    upper_bound = np.maximum.reduce(
        (
            value_00,
            value_10,
            value_01,
            value_11,
        )
    )

    return (
        np.asarray(
            lower_bound,
            dtype=np.float64,
        ),
        np.asarray(
            upper_bound,
            dtype=np.float64,
        ),
    )


def normalize_periodic_departure_geometry(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Normalise un champ périodique et des coordonnées
    de départ explicites.

    Les coordonnées peuvent se trouver hors du
    domaine fondamental : elles sont repliées
    périodiquement.
    """
    source = np.asarray(
        field,
        dtype=np.float64,
    )

    x_values, x_origin, x_period = (
        periodic_coordinate_geometry(
            x_coordinates,
            "x",
        )
    )

    y_values, y_origin, y_period = (
        periodic_coordinate_geometry(
            y_coordinates,
            "y",
        )
    )

    expected_shape = (
        y_values.size,
        x_values.size,
    )

    if source.shape != expected_shape:
        raise ValueError(
            "La forme du champ est incompatible "
            "avec les coordonnées périodiques."
        )

    try:
        departure_x_array = np.broadcast_to(
            np.asarray(
                departure_x,
                dtype=np.float64,
            ),
            source.shape,
        )

        departure_y_array = np.broadcast_to(
            np.asarray(
                departure_y,
                dtype=np.float64,
            ),
            source.shape,
        )
    except ValueError as error:
        raise ValueError(
            "Les coordonnées de départ ne sont pas "
            "compatibles avec le champ."
        ) from error

    if (
        not np.all(
            np.isfinite(source)
        )
        or not np.all(
            np.isfinite(
                departure_x_array
            )
        )
        or not np.all(
            np.isfinite(
                departure_y_array
            )
        )
    ):
        raise ValueError(
            "Le champ et les coordonnées de départ "
            "doivent être finis."
        )

    wrapped_x = wrap_periodic_points(
        departure_x_array,
        x_origin,
        x_period,
    )

    wrapped_y = wrap_periodic_points(
        departure_y_array,
        y_origin,
        y_period,
    )

    spacing_x = float(
        x_values[1] - x_values[0]
    )

    spacing_y = float(
        y_values[1] - y_values[0]
    )

    coordinate_x = (
        wrapped_x - x_origin
    ) / spacing_x

    coordinate_y = (
        wrapped_y - y_origin
    ) / spacing_y

    index_x0 = (
        np.floor(
            coordinate_x
        ).astype(np.int64)
        % x_values.size
    )

    index_y0 = (
        np.floor(
            coordinate_y
        ).astype(np.int64)
        % y_values.size
    )

    fraction_x = (
        coordinate_x
        - np.floor(
            coordinate_x
        )
    )

    fraction_y = (
        coordinate_y
        - np.floor(
            coordinate_y
        )
    )

    return (
        source,
        x_values,
        y_values,
        index_x0,
        index_y0,
        np.asarray(
            fraction_x,
            dtype=np.float64,
        ),
        np.asarray(
            fraction_y,
            dtype=np.float64,
        ),
    )


def periodic_bilinear_sample_at_departures(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
) -> np.ndarray:
    """
    Échantillonne directement un champ aux points
    de départ périodiques par interpolation
    bilinéaire.
    """
    (
        source,
        x_values,
        y_values,
        index_x0,
        index_y0,
        fraction_x,
        fraction_y,
    ) = normalize_periodic_departure_geometry(
        field,
        x_coordinates,
        y_coordinates,
        departure_x,
        departure_y,
    )

    index_x1 = (
        index_x0 + 1
    ) % x_values.size

    index_y1 = (
        index_y0 + 1
    ) % y_values.size

    value_00 = source[
        index_y0,
        index_x0,
    ]

    value_10 = source[
        index_y0,
        index_x1,
    ]

    value_01 = source[
        index_y1,
        index_x0,
    ]

    value_11 = source[
        index_y1,
        index_x1,
    ]

    result = (
        (1.0 - fraction_x)
        * (1.0 - fraction_y)
        * value_00
        + fraction_x
        * (1.0 - fraction_y)
        * value_10
        + (1.0 - fraction_x)
        * fraction_y
        * value_01
        + fraction_x
        * fraction_y
        * value_11
    )

    return np.asarray(
        result,
        dtype=np.float64,
    )


def cubic_lagrange_weights_at_fraction(
    fraction: object,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Poids de Lagrange pour les nœuds relatifs
    -1, 0, 1 et 2.
    """
    value = np.asarray(
        fraction,
        dtype=np.float64,
    )

    weight_minus_one = (
        -value
        * (value - 1.0)
        * (value - 2.0)
        / 6.0
    )

    weight_zero = (
        (value + 1.0)
        * (value - 1.0)
        * (value - 2.0)
        / 2.0
    )

    weight_one = (
        -(value + 1.0)
        * value
        * (value - 2.0)
        / 2.0
    )

    weight_two = (
        (value + 1.0)
        * value
        * (value - 1.0)
        / 6.0
    )

    return (
        weight_minus_one,
        weight_zero,
        weight_one,
        weight_two,
    )


def periodic_cubic_sample_at_departures(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
) -> np.ndarray:
    """
    Échantillonne directement un champ aux points
    de départ périodiques avec le tenseur produit
    cubique de Lagrange à seize nœuds.
    """
    (
        source,
        x_values,
        y_values,
        index_x0,
        index_y0,
        fraction_x,
        fraction_y,
    ) = normalize_periodic_departure_geometry(
        field,
        x_coordinates,
        y_coordinates,
        departure_x,
        departure_y,
    )

    weights_x = (
        cubic_lagrange_weights_at_fraction(
            fraction_x
        )
    )

    weights_y = (
        cubic_lagrange_weights_at_fraction(
            fraction_y
        )
    )

    offsets = (
        -1,
        0,
        1,
        2,
    )

    result = np.zeros_like(
        source,
        dtype=np.float64,
    )

    for y_position, offset_y in enumerate(
        offsets
    ):
        index_y = (
            index_y0 + offset_y
        ) % y_values.size

        weight_y = weights_y[
            y_position
        ]

        for x_position, offset_x in enumerate(
            offsets
        ):
            index_x = (
                index_x0 + offset_x
            ) % x_values.size

            result += (
                weight_y
                * weights_x[x_position]
                * source[
                    index_y,
                    index_x,
                ]
            )

    return np.asarray(
        result,
        dtype=np.float64,
    )


def periodic_departure_bounds(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Retourne directement les bornes des quatre
    nœuds entourant chaque point de départ.
    """
    (
        source,
        x_values,
        y_values,
        index_x0,
        index_y0,
        _,
        _,
    ) = normalize_periodic_departure_geometry(
        field,
        x_coordinates,
        y_coordinates,
        departure_x,
        departure_y,
    )

    index_x1 = (
        index_x0 + 1
    ) % x_values.size

    index_y1 = (
        index_y0 + 1
    ) % y_values.size

    value_00 = source[
        index_y0,
        index_x0,
    ]

    value_10 = source[
        index_y0,
        index_x1,
    ]

    value_01 = source[
        index_y1,
        index_x0,
    ]

    value_11 = source[
        index_y1,
        index_x1,
    ]

    lower = np.minimum.reduce(
        (
            value_00,
            value_10,
            value_01,
            value_11,
        )
    )

    upper = np.maximum.reduce(
        (
            value_00,
            value_10,
            value_01,
            value_11,
        )
    )

    return (
        np.asarray(
            lower,
            dtype=np.float64,
        ),
        np.asarray(
            upper,
            dtype=np.float64,
        ),
    )


def periodic_cubic_local_bounded_sample_at_departures(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
) -> np.ndarray:
    bilinear = (
        periodic_bilinear_sample_at_departures(
            field,
            x_coordinates,
            y_coordinates,
            departure_x,
            departure_y,
        )
    )

    cubic = (
        periodic_cubic_sample_at_departures(
            field,
            x_coordinates,
            y_coordinates,
            departure_x,
            departure_y,
        )
    )

    lower, upper = periodic_departure_bounds(
        field,
        x_coordinates,
        y_coordinates,
        departure_x,
        departure_y,
    )

    return convex_local_bound_limiter(
        bilinear,
        cubic,
        lower,
        upper,
    )


def periodic_cubic_local_sum_preserving_sample_at_departures(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
) -> np.ndarray:
    bilinear = (
        periodic_bilinear_sample_at_departures(
            field,
            x_coordinates,
            y_coordinates,
            departure_x,
            departure_y,
        )
    )

    cubic = (
        periodic_cubic_sample_at_departures(
            field,
            x_coordinates,
            y_coordinates,
            departure_x,
            departure_y,
        )
    )

    lower, upper = periodic_departure_bounds(
        field,
        x_coordinates,
        y_coordinates,
        departure_x,
        departure_y,
    )

    bounded = convex_local_bound_limiter(
        bilinear,
        cubic,
        lower,
        upper,
    )

    activation_scale = max(
        1.0,
        float(
            np.max(
                np.abs(cubic)
            )
        ),
    )

    activation_tolerance = (
        256.0
        * np.finfo(np.float64).eps
        * activation_scale
    )

    seed_mask = (
        np.abs(
            bounded - cubic
        )
        > activation_tolerance
    )

    target_sum = precise_discrete_sum(
        cubic
    )

    return restore_sum_with_local_bounds(
        bounded,
        lower,
        upper,
        target_sum,
        seed_mask,
    )


def periodic_sample_at_departures(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    departure_x: object,
    departure_y: object,
    interpolation: object = (
        "bilinear_periodic"
    ),
) -> np.ndarray:
    """
    Point d'entrée direct pour toutes les
    interpolations périodiques.
    """
    mode = validate_transport_interpolation(
        interpolation
    )

    if mode == "bilinear_periodic":
        return (
            periodic_bilinear_sample_at_departures(
                field,
                x_coordinates,
                y_coordinates,
                departure_x,
                departure_y,
            )
        )

    if mode == "cubic_periodic":
        return (
            periodic_cubic_sample_at_departures(
                field,
                x_coordinates,
                y_coordinates,
                departure_x,
                departure_y,
            )
        )

    if (
        mode
        == "cubic_local_bounded_periodic"
    ):
        return (
            periodic_cubic_local_bounded_sample_at_departures(
                field,
                x_coordinates,
                y_coordinates,
                departure_x,
                departure_y,
            )
        )

    return (
        periodic_cubic_local_sum_preserving_sample_at_departures(
            field,
            x_coordinates,
            y_coordinates,
            departure_x,
            departure_y,
        )
    )



def convex_local_bound_limiter(
    low_order: object,
    high_order: object,
    lower_bound: object,
    upper_bound: object,
) -> np.ndarray:
    """
    Mélange localement une solution basse précision
    bornée et une solution haute précision.

        q = q_low + theta * (q_high - q_low)

    avec 0 <= theta <= 1.
    """
    low = np.asarray(
        low_order,
        dtype=np.float64,
    )

    high = np.asarray(
        high_order,
        dtype=np.float64,
    )

    lower = np.asarray(
        lower_bound,
        dtype=np.float64,
    )

    upper = np.asarray(
        upper_bound,
        dtype=np.float64,
    )

    try:
        low, high, lower, upper = (
            np.broadcast_arrays(
                low,
                high,
                lower,
                upper,
            )
        )
    except ValueError as error:
        raise ValueError(
            "Les données du limiteur local ne "
            "sont pas compatibles."
        ) from error

    if not all(
        np.all(
            np.isfinite(values)
        )
        for values in (
            low,
            high,
            lower,
            upper,
        )
    ):
        raise ValueError(
            "Le limiteur local exige des données "
            "finies."
        )

    scale = max(
        1.0,
        float(
            np.max(
                np.abs(lower)
            )
        ),
        float(
            np.max(
                np.abs(upper)
            )
        ),
    )

    tolerance = (
        512.0
        * np.finfo(np.float64).eps
        * scale
    )

    if (
        np.any(
            lower > upper + tolerance
        )
        or np.any(
            low < lower - tolerance
        )
        or np.any(
            low > upper + tolerance
        )
    ):
        raise RuntimeError(
            "La solution basse précision n'est "
            "pas comprise dans les bornes locales."
        )

    correction = (
        high - low
    )

    theta = np.ones_like(
        correction,
        dtype=np.float64,
    )

    upper_mask = (
        high > upper
    )

    lower_mask = (
        high < lower
    )

    theta_upper = np.ones_like(
        correction,
        dtype=np.float64,
    )

    theta_lower = np.ones_like(
        correction,
        dtype=np.float64,
    )

    safe_upper_mask = (
        upper_mask
        & (
            correction
            > tolerance
        )
    )

    safe_lower_mask = (
        lower_mask
        & (
            correction
            < -tolerance
        )
    )

    theta_upper[
        safe_upper_mask
    ] = (
        (
            upper - low
        )[
            safe_upper_mask
        ]
        / correction[
            safe_upper_mask
        ]
    )

    theta_lower[
        safe_lower_mask
    ] = (
        (
            lower - low
        )[
            safe_lower_mask
        ]
        / correction[
            safe_lower_mask
        ]
    )

    # Une violation portée par une correction trop
    # petite pour être divisée de façon sûre retombe
    # sur la solution basse précision bornée.
    theta_upper = np.where(
        upper_mask
        & ~safe_upper_mask,
        0.0,
        theta_upper,
    )

    theta_lower = np.where(
        lower_mask
        & ~safe_lower_mask,
        0.0,
        theta_lower,
    )

    theta = np.where(
        upper_mask,
        np.minimum(
            theta,
            theta_upper,
        ),
        theta,
    )

    theta = np.where(
        lower_mask,
        np.minimum(
            theta,
            theta_lower,
        ),
        theta,
    )

    theta = np.clip(
        theta,
        0.0,
        1.0,
    )

    result = (
        low + theta * correction
    )

    # Protection contre l'arrondi final seulement.
    result = np.minimum(
        np.maximum(
            result,
            lower,
        ),
        upper,
    )

    return np.asarray(
        result,
        dtype=np.float64,
    )


def periodic_cubic_local_bounded_backtrace(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    transport_vx: object,
    transport_vy: object,
    delta_time: float,
) -> np.ndarray:
    """
    Interpolation cubique limitée par mélange convexe
    avec l'interpolation bilinéaire.

    Le résultat respecte les bornes des quatre nœuds
    entourant chaque point de départ.

    La conservation exacte de la somme n'est pas
    revendiquée par cette version.
    """
    bilinear = periodic_bilinear_backtrace(
        field,
        x_coordinates,
        y_coordinates,
        transport_vx,
        transport_vy,
        delta_time,
    )

    cubic = periodic_cubic_backtrace(
        field,
        x_coordinates,
        y_coordinates,
        transport_vx,
        transport_vy,
        delta_time,
    )

    lower_bound, upper_bound = (
        periodic_bilinear_departure_bounds(
            field,
            x_coordinates,
            y_coordinates,
            transport_vx,
            transport_vy,
            delta_time,
        )
    )

    return convex_local_bound_limiter(
        bilinear,
        cubic,
        lower_bound,
        upper_bound,
    )

def precise_discrete_sum(
    values: object,
) -> np.longdouble:
    """
    Somme déterministe avec accumulateur étendu.

    Le tableau final reste en float64, mais le calcul
    du défaut de somme utilise longdouble.
    """
    array = np.asarray(
        values,
        dtype=np.longdouble,
    )

    if not np.all(
        np.isfinite(array)
    ):
        raise ValueError(
            "La somme précise exige des valeurs "
            "finies."
        )

    return np.sum(
        array,
        dtype=np.longdouble,
    )


def periodic_expand_mask(
    mask: object,
) -> np.ndarray:
    """
    Dilatation périodique d'une cellule dans le
    voisinage de Moore 3 x 3.
    """
    source = np.asarray(
        mask,
        dtype=bool,
    )

    if source.ndim != 2:
        raise ValueError(
            "Le masque périodique doit être "
            "bidimensionnel."
        )

    expanded = source.copy()

    for shift_y in (
        -1,
        0,
        1,
    ):
        for shift_x in (
            -1,
            0,
            1,
        ):
            expanded |= np.roll(
                np.roll(
                    source,
                    shift_y,
                    axis=0,
                ),
                shift_x,
                axis=1,
            )

    return expanded


def restore_sum_with_local_bounds(
    values: object,
    lower_bound: object,
    upper_bound: object,
    target_sum: object,
    seed_mask: object,
) -> np.ndarray:
    """
    Restaure une somme cible en modifiant seulement
    un voisinage périodique des cellules limitées.

    Les corrections sont distribuées suivant les
    capacités locales disponibles. Le voisinage est
    agrandi seulement lorsque cela est nécessaire.
    """
    result = np.asarray(
        values,
        dtype=np.float64,
    ).copy()

    lower = np.asarray(
        lower_bound,
        dtype=np.float64,
    )

    upper = np.asarray(
        upper_bound,
        dtype=np.float64,
    )

    seeds = np.asarray(
        seed_mask,
        dtype=bool,
    )

    try:
        result, lower, upper, seeds = (
            np.broadcast_arrays(
                result,
                lower,
                upper,
                seeds,
            )
        )
    except ValueError as error:
        raise ValueError(
            "Les tableaux de correction de somme "
            "ne sont pas compatibles."
        ) from error

    result = np.asarray(
        result,
        dtype=np.float64,
    ).copy()

    lower = np.asarray(
        lower,
        dtype=np.float64,
    )

    upper = np.asarray(
        upper,
        dtype=np.float64,
    )

    seeds = np.asarray(
        seeds,
        dtype=bool,
    )

    if result.ndim != 2:
        raise ValueError(
            "La correction localisée exige un "
            "champ bidimensionnel."
        )

    if not all(
        np.all(
            np.isfinite(array)
        )
        for array in (
            result,
            lower,
            upper,
        )
    ):
        raise ValueError(
            "La correction localisée exige des "
            "données finies."
        )

    value_scale = max(
        1.0,
        float(
            np.max(
                np.abs(lower)
            )
        ),
        float(
            np.max(
                np.abs(upper)
            )
        ),
    )

    tolerance = np.longdouble(
        4096.0
        * np.finfo(np.float64).eps
        * value_scale
    )

    if (
        np.any(
            lower > upper
        )
        or np.any(
            result < lower
            - float(tolerance)
        )
        or np.any(
            result > upper
            + float(tolerance)
        )
    ):
        raise RuntimeError(
            "Le champ initial de correction ne "
            "respecte pas les bornes locales."
        )

    target = np.longdouble(
        target_sum
    )

    if not np.isfinite(target):
        raise ValueError(
            "La somme cible doit être finie."
        )

    minimum_sum = precise_discrete_sum(
        lower
    )

    maximum_sum = precise_discrete_sum(
        upper
    )

    if (
        target < minimum_sum - tolerance
        or target > maximum_sum + tolerance
    ):
        raise ValueError(
            "La somme cible est incompatible avec "
            "les bornes locales disponibles."
        )

    residual = (
        target
        - precise_discrete_sum(
            result
        )
    )

    if abs(residual) <= tolerance:
        return result

    if not np.any(seeds):
        raise RuntimeError(
            "Un défaut de somme non résolu existe "
            "sans cellule limitée de départ."
        )

    support = seeds.copy()

    maximum_radius = max(
        result.shape
    )

    capacity = None

    for _ in range(
        maximum_radius + 1
    ):
        if residual > 0.0:
            candidate_capacity = np.where(
                support,
                np.maximum(
                    upper - result,
                    0.0,
                ),
                0.0,
            )
        else:
            candidate_capacity = np.where(
                support,
                np.maximum(
                    result - lower,
                    0.0,
                ),
                0.0,
            )

        capacity_sum = (
            precise_discrete_sum(
                candidate_capacity
            )
        )

        if (
            capacity_sum
            + tolerance
            >= abs(residual)
        ):
            capacity = candidate_capacity
            break

        expanded = periodic_expand_mask(
            support
        )

        if np.array_equal(
            expanded,
            support,
        ):
            break

        support = expanded

    if capacity is None:
        raise RuntimeError(
            "La capacité locale disponible est "
            "insuffisante pour restaurer la somme."
        )

    capacity_sum = precise_discrete_sum(
        capacity
    )

    fraction = float(
        abs(residual)
        / capacity_sum
    )

    fraction = min(
        1.0,
        max(
            0.0,
            fraction,
        ),
    )

    if residual > 0.0:
        result = (
            result
            + fraction * capacity
        )
    else:
        result = (
            result
            - fraction * capacity
        )

    result = np.minimum(
        np.maximum(
            result,
            lower,
        ),
        upper,
    )

    # Correction finale déterministe de l'arrondi.
    for _ in range(8):
        remaining = (
            target
            - precise_discrete_sum(
                result
            )
        )

        if abs(remaining) <= tolerance:
            break

        if remaining > 0.0:
            remaining_capacity = np.where(
                support,
                np.maximum(
                    upper - result,
                    0.0,
                ),
                0.0,
            )
        else:
            remaining_capacity = np.where(
                support,
                np.maximum(
                    result - lower,
                    0.0,
                ),
                0.0,
            )

        flat_capacity = (
            remaining_capacity.ravel()
        )

        eligible = np.flatnonzero(
            flat_capacity
            > float(tolerance)
        )

        if eligible.size == 0:
            raise RuntimeError(
                "Aucune capacité ne reste pour la "
                "correction finale de somme."
            )

        ordered = eligible[
            np.argsort(
                -flat_capacity[
                    eligible
                ],
                kind="mergesort",
            )
        ]

        for flat_index in ordered:
            remaining = (
                target
                - precise_discrete_sum(
                    result
                )
            )

            if abs(remaining) <= tolerance:
                break

            available = float(
                flat_capacity[
                    flat_index
                ]
            )

            correction = min(
                abs(
                    float(remaining)
                ),
                available,
            )

            if correction <= 0.0:
                continue

            if remaining > 0.0:
                result.flat[
                    flat_index
                ] += correction
            else:
                result.flat[
                    flat_index
                ] -= correction

            result.flat[
                flat_index
            ] = min(
                upper.flat[
                    flat_index
                ],
                max(
                    lower.flat[
                        flat_index
                    ],
                    result.flat[
                        flat_index
                    ],
                ),
            )

    final_residual = (
        target
        - precise_discrete_sum(
            result
        )
    )

    if abs(final_residual) > tolerance:
        raise RuntimeError(
            "La somme cible n'a pas été restaurée "
            "à la tolérance déclarée."
        )

    if (
        np.any(
            result < lower
            - float(tolerance)
        )
        or np.any(
            result > upper
            + float(tolerance)
        )
    ):
        raise RuntimeError(
            "La correction de somme viole les "
            "bornes locales."
        )

    return np.asarray(
        result,
        dtype=np.float64,
    )


def periodic_cubic_local_sum_preserving_backtrace(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    transport_vx: object,
    transport_vy: object,
    delta_time: float,
) -> np.ndarray:
    """
    Interpolation cubique localement bornée dont la
    somme discrète égale celle du candidat cubique
    non limité.

    Cette propriété n'est pas une formulation
    conservative en flux pour un écoulement général.
    """
    bilinear = periodic_bilinear_backtrace(
        field,
        x_coordinates,
        y_coordinates,
        transport_vx,
        transport_vy,
        delta_time,
    )

    cubic = periodic_cubic_backtrace(
        field,
        x_coordinates,
        y_coordinates,
        transport_vx,
        transport_vy,
        delta_time,
    )

    lower, upper = (
        periodic_bilinear_departure_bounds(
            field,
            x_coordinates,
            y_coordinates,
            transport_vx,
            transport_vy,
            delta_time,
        )
    )

    bounded = convex_local_bound_limiter(
        bilinear,
        cubic,
        lower,
        upper,
    )

    activation_scale = max(
        1.0,
        float(
            np.max(
                np.abs(cubic)
            )
        ),
    )

    activation_tolerance = (
        256.0
        * np.finfo(np.float64).eps
        * activation_scale
    )

    seed_mask = (
        np.abs(
            bounded - cubic
        )
        > activation_tolerance
    )

    target_sum = precise_discrete_sum(
        cubic
    )

    return restore_sum_with_local_bounds(
        bounded,
        lower,
        upper,
        target_sum,
        seed_mask,
    )




def periodic_backtrace(
    field: object,
    x_coordinates: object,
    y_coordinates: object,
    transport_vx: object,
    transport_vy: object,
    delta_time: float,
    interpolation: object = (
        "bilinear_periodic"
    ),
) -> np.ndarray:
    mode = validate_transport_interpolation(
        interpolation
    )

    if mode == "bilinear_periodic":
        return periodic_bilinear_backtrace(
            field,
            x_coordinates,
            y_coordinates,
            transport_vx,
            transport_vy,
            delta_time,
        )

    if mode == "cubic_periodic":
        return periodic_cubic_backtrace(
            field,
            x_coordinates,
            y_coordinates,
            transport_vx,
            transport_vy,
            delta_time,
        )

    if (
        mode
        == "cubic_local_bounded_periodic"
    ):
        return (
            periodic_cubic_local_bounded_backtrace(
                field,
                x_coordinates,
                y_coordinates,
                transport_vx,
                transport_vy,
                delta_time,
            )
        )

    return (
        periodic_cubic_local_sum_preserving_backtrace(
            field,
            x_coordinates,
            y_coordinates,
            transport_vx,
            transport_vy,
            delta_time,
        )
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
