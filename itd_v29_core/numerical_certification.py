"""Certification numérique et analyse de convergence du simulateur ITD V29."""

from __future__ import annotations

import numpy as np

from itd_v29_core.constants import (
    STRUCTURAL_COMPONENT_NAMES,
)


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



