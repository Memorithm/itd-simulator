"""Transport semi-lagrangien périodique du simulateur ITD V29."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from itd_v29_core.constants import (
    TRANSPORT_INTERPOLATIONS,
    TRANSPORT_TRAJECTORY_METHODS,
)
from itd_v29_core.geometric_transforms import (
    validate_uniform_axis_coordinates,
)
from itd_v29_core.spatial_geometry import (
    RectilinearGeometry,
    normalize_spatial_geometry,
)


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
    try:
        array = np.asarray(values, dtype=np.float64)
        origin_value = float(origin)
        period_value = float(period)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            "Les coordonnées périodiques doivent être réelles."
        ) from error

    if (
        not np.all(np.isfinite(array))
        or not np.isfinite(origin_value)
        or not np.isfinite(period_value)
        or period_value <= 0.0
    ):
        raise ValueError(
            "Les coordonnées et l'origine doivent être finies, "
            "et la période strictement positive."
        )

    return (
        origin_value
        + np.mod(
            array - origin_value,
            period_value,
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
