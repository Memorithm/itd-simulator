"""Covariance et redimensionnement spatial du simulateur ITD V29."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from itd_v29_core.geometric_transforms import (
    validate_transform_origin,
)
from itd_v29_core.spatial_geometry import (
    RectilinearGeometry,
    SpatialGeometry,
    normalize_spatial_geometry,
)


def validate_spatial_scale_factor(
    scale_factor: float,
) -> float:
    try:
        factor = float(scale_factor)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Le facteur d'échelle spatiale doit "
            "être un nombre réel."
        ) from error

    if (
        not np.isfinite(factor)
        or factor <= 0.0
    ):
        raise ValueError(
            "Le facteur d'échelle spatiale doit "
            "être fini et strictement positif."
        )

    return factor


def validate_nonnegative_length(
    length: float,
    name: str,
) -> float:
    try:
        value = float(length)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            f"La longueur {name} doit être "
            "un nombre réel."
        ) from error

    if (
        not np.isfinite(value)
        or value < 0.0
    ):
        raise ValueError(
            f"La longueur {name} doit être finie "
            "et positive ou nulle."
        )

    return value


def scale_length(
    length: float,
    scale_factor: float,
    name: str = "spatiale",
) -> float:
    factor = validate_spatial_scale_factor(
        scale_factor
    )

    value = validate_nonnegative_length(
        length,
        name,
    )

    return factor * value


def inverse_scale_coordinates(
    x: object,
    y: object,
    scale_factor: float,
    origin: object = (0.0, 0.0),
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcule les coordonnées sources associées à :

        x' = o + a (x - o).

    Donc :

        x = o + (x' - o) / a.
    """
    factor = validate_spatial_scale_factor(
        scale_factor
    )

    origin_array = validate_transform_origin(
        origin
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
            "Les coordonnées contiennent une "
            "valeur non finie."
        )

    source_x = (
        origin_array[0]
        + (
            x_array
            - origin_array[0]
        ) / factor
    )

    source_y = (
        origin_array[1]
        + (
            y_array
            - origin_array[1]
        ) / factor
    )

    return source_x, source_y


def scale_velocity_function(
    velocity_function: Callable,
    scale_factor: float,
    origin: object = (0.0, 0.0),
) -> Callable:
    """
    Construit le champ :

        v_a(x',t) = a v(x,t),

    avec :

        x = o + (x' - o) / a.

    Le temps n'est pas redimensionné.
    """
    if not callable(velocity_function):
        raise ValueError(
            "Le champ de vitesse doit être appelable."
        )

    factor = validate_spatial_scale_factor(
        scale_factor
    )

    origin_array = validate_transform_origin(
        origin
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        source_x, source_y = (
            inverse_scale_coordinates(
                x,
                y,
                factor,
                origin_array,
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
                "Le champ de vitesse redimensionné "
                "doit avoir la forme de la grille."
            )

        if not (
            np.all(np.isfinite(source_vx))
            and np.all(np.isfinite(source_vy))
        ):
            raise ValueError(
                "Le champ de vitesse redimensionné "
                "contient une valeur non finie."
            )

        return (
            factor * source_vx,
            factor * source_vy,
        )

    return transformed


def scale_curvature_function(
    curvature_function: Callable,
    scale_factor: float,
    origin: object = (0.0, 0.0),
) -> Callable:
    """
    Construit un champ de courbure transformé selon :

        R_a(x',t) = R(x,t) / a².
    """
    if not callable(curvature_function):
        raise ValueError(
            "Le champ de courbure doit être appelable."
        )

    factor = validate_spatial_scale_factor(
        scale_factor
    )

    inverse_square = 1.0 / (
        factor**2
    )

    origin_array = validate_transform_origin(
        origin
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> np.ndarray:
        source_x, source_y = (
            inverse_scale_coordinates(
                x,
                y,
                factor,
                origin_array,
            )
        )

        source_curvature = np.asarray(
            curvature_function(
                source_x,
                source_y,
                time,
            ),
            dtype=np.float64,
        )

        if source_curvature.shape != source_x.shape:
            raise ValueError(
                "Le champ de courbure redimensionné "
                "doit avoir la forme de la grille."
            )

        if not np.all(
            np.isfinite(source_curvature)
        ):
            raise ValueError(
                "Le champ de courbure redimensionné "
                "contient une valeur non finie."
            )

        return (
            inverse_square
            * source_curvature
        )

    return transformed


def scale_spatial_geometry(
    geometry: object,
    scale_factor: float,
    origin: object = (0.0, 0.0),
) -> SpatialGeometry | RectilinearGeometry:
    """
    Redimensionne une géométrie uniforme ou rectiligne.

    Pour une géométrie uniforme, seuls dx et dy
    sont nécessaires.

    Pour une géométrie rectiligne, les coordonnées
    sont dilatées autour de origin.
    """
    factor = validate_spatial_scale_factor(
        scale_factor
    )

    normalized = normalize_spatial_geometry(
        geometry
    )

    if isinstance(
        normalized,
        SpatialGeometry,
    ):
        return SpatialGeometry(
            factor * normalized.dx,
            factor * normalized.dy,
        )

    origin_array = validate_transform_origin(
        origin
    )

    scaled_x = (
        origin_array[0]
        + factor
        * (
            normalized.x_coordinates
            - origin_array[0]
        )
    )

    scaled_y = (
        origin_array[1]
        + factor
        * (
            normalized.y_coordinates
            - origin_array[1]
        )
    )

    return RectilinearGeometry(
        scaled_x,
        scaled_y,
    )


