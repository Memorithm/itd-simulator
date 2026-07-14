"""Transformations de référentiels pour le simulateur ITD V29."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


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
