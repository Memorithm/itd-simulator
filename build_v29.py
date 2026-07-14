#!/usr/bin/env python3

from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path("itd_v29.py")


def function_node(
    text: str,
    name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse(text)

    matches = [
        node
        for node in tree.body
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name == name
        )
    ]

    if len(matches) != 1:
        raise SystemExit(
            f"ERREUR : fonction {name}() "
            "introuvable ou ambiguë."
        )

    node = matches[0]

    if node.end_lineno is None:
        raise SystemExit(
            f"ERREUR : fin de {name}() indisponible."
        )

    return node


def insert_after_function(
    text: str,
    name: str,
    insertion: str,
) -> str:
    node = function_node(
        text,
        name,
    )

    lines = text.splitlines(
        keepends=True,
    )

    return (
        "".join(
            lines[:node.end_lineno]
        )
        + "\n"
        + insertion.rstrip()
        + "\n\n"
        + "".join(
            lines[node.end_lineno:]
        )
    )


def replace_function(
    text: str,
    name: str,
    replacement: str,
) -> str:
    node = function_node(
        text,
        name,
    )

    lines = text.splitlines(
        keepends=True,
    )

    return (
        "".join(
            lines[:node.lineno - 1]
        )
        + replacement.rstrip()
        + "\n\n"
        + "".join(
            lines[node.end_lineno:]
        )
    )


text = SOURCE.read_text(
    encoding="utf-8",
)

direct_departure_api = r'''
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
'''

text = insert_after_function(
    text,
    "periodic_bilinear_departure_bounds",
    direct_departure_api,
)

transport_function = r'''
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
'''

text = replace_function(
    text,
    "transport_previous_vorticity_periodic",
    transport_function,
)

if text.count(
    "=== SIMULATEUR ITD VERSION 28 ==="
) != 1:
    raise SystemExit(
        "ERREUR : bannière V28 introuvable."
    )

text = text.replace(
    "=== SIMULATEUR ITD VERSION 28 ===",
    "=== SIMULATEUR ITD VERSION 29 ===",
    1,
)

text = text.replace(
    "itd_v28_results",
    "itd_v29_results",
)

SOURCE.write_text(
    text,
    encoding="utf-8",
)

print(
    "itd_v29.py créé avec API directe "
    "en coordonnées de départ."
)
