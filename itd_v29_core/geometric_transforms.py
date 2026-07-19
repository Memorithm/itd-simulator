"""Transformations géométriques cartésiennes du simulateur ITD V29."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def validate_orthogonal_matrix(
    matrix: object,
    tolerance: float = 1.0e-12,
) -> np.ndarray:
    """
    Valide une transformation orthogonale réelle 2 × 2.

    Les rotations ont un déterminant +1.
    Les réflexions ont un déterminant -1.
    """
    array = np.asarray(
        matrix,
        dtype=np.float64,
    )

    if array.shape != (2, 2):
        raise ValueError(
            "La transformation géométrique doit être "
            "une matrice 2 × 2."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "La transformation géométrique doit "
            "contenir uniquement des valeurs finies."
        )

    gram = array.T @ array

    if not np.allclose(
        gram,
        np.eye(2, dtype=np.float64),
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "La matrice doit être orthogonale : "
            "QᵀQ = I."
        )

    determinant = float(
        np.linalg.det(array)
    )

    if not np.isclose(
        abs(determinant),
        1.0,
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "Le déterminant d'une transformation "
            "orthogonale doit valoir +1 ou -1."
        )

    return array


def transform_coordinates(
    x: np.ndarray,
    y: np.ndarray,
    matrix: object,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcule les coordonnées sources Qᵀx.
    """
    orthogonal = validate_orthogonal_matrix(matrix)

    x_array = np.asarray(x, dtype=np.float64)
    y_array = np.asarray(y, dtype=np.float64)

    if x_array.shape != y_array.shape:
        raise ValueError(
            "Les coordonnées x et y doivent avoir la même forme."
        )

    if not (
        np.all(np.isfinite(x_array))
        and np.all(np.isfinite(y_array))
    ):
        raise ValueError(
            "Les coordonnées transformées doivent être finies."
        )

    source_x = (
        orthogonal[0, 0] * x_array
        + orthogonal[1, 0] * y_array
    )

    source_y = (
        orthogonal[0, 1] * x_array
        + orthogonal[1, 1] * y_array
    )

    return source_x, source_y


def transform_velocity_function(
    velocity_function: Callable,
    matrix: object,
) -> Callable:
    """
    Construit le champ vectoriel transformé :

        v_Q(x,t) = Q v(Qᵀx,t).
    """
    orthogonal = validate_orthogonal_matrix(
        matrix
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        source_x, source_y = transform_coordinates(
            x,
            y,
            orthogonal,
        )

        source_vx, source_vy = velocity_function(
            source_x,
            source_y,
            time,
        )

        transformed_vx = (
            orthogonal[0, 0] * source_vx
            + orthogonal[0, 1] * source_vy
        )

        transformed_vy = (
            orthogonal[1, 0] * source_vx
            + orthogonal[1, 1] * source_vy
        )

        return transformed_vx, transformed_vy

    return transformed


def transform_scalar_function(
    scalar_function: Callable,
    matrix: object,
) -> Callable:
    """
    Construit le champ scalaire transformé :

        f_Q(x,t) = f(Qᵀx,t).
    """
    orthogonal = validate_orthogonal_matrix(
        matrix
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> np.ndarray:
        source_x, source_y = transform_coordinates(
            x,
            y,
            orthogonal,
        )

        return np.asarray(
            scalar_function(
                source_x,
                source_y,
                time,
            ),
            dtype=np.float64,
        )

    return transformed


def validate_rotation_angle(
    angle_radians: float,
) -> float:
    try:
        angle = float(angle_radians)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "L'angle de rotation doit être "
            "un nombre réel."
        ) from error

    if not np.isfinite(angle):
        raise ValueError(
            "L'angle de rotation doit être fini."
        )

    return angle


def rotation_matrix(
    angle_radians: float,
) -> np.ndarray:
    """
    Retourne la matrice de rotation directe :

        Q = [[cos(theta), -sin(theta)],
             [sin(theta),  cos(theta)]]
    """
    angle = validate_rotation_angle(
        angle_radians
    )

    cosine = float(np.cos(angle))
    sine = float(np.sin(angle))

    return np.asarray(
        (
            (cosine, -sine),
            (sine, cosine),
        ),
        dtype=np.float64,
    )


def validate_uniform_axis_coordinates(
    coordinates: object,
    axis_name: str,
) -> tuple[np.ndarray, float]:
    try:
        array = np.asarray(
            coordinates,
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            f"Les coordonnées {axis_name} doivent "
            "être numériques."
        ) from error

    if array.ndim != 1:
        raise ValueError(
            f"Les coordonnées {axis_name} doivent "
            "former un tableau unidimensionnel."
        )

    if array.size < 2:
        raise ValueError(
            f"L'axe {axis_name} doit contenir "
            "au moins deux coordonnées."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            f"Les coordonnées {axis_name} "
            "contiennent une valeur non finie."
        )

    differences = np.diff(array)

    if not np.all(differences > 0.0):
        raise ValueError(
            f"Les coordonnées {axis_name} doivent "
            "être strictement croissantes."
        )

    spacing = float(differences[0])

    absolute_tolerance = (
        64.0
        * np.finfo(np.float64).eps
        * max(1.0, abs(spacing))
    )

    if not np.allclose(
        differences,
        spacing,
        rtol=1.0e-12,
        atol=absolute_tolerance,
    ):
        raise ValueError(
            f"L'axe {axis_name} doit être "
            "uniformément échantillonné."
        )

    return array.copy(), spacing


def validate_transform_origin(
    origin: object,
) -> np.ndarray:
    try:
        array = np.asarray(
            origin,
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "L'origine doit être un couple réel."
        ) from error

    if array.shape != (2,):
        raise ValueError(
            "L'origine doit contenir exactement "
            "deux coordonnées."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "L'origine doit contenir uniquement "
            "des valeurs finies."
        )

    return array.copy()


class BilinearTransformPlan:
    """
    Plan déterministe de transformation d'un champ
    échantillonné sur une grille cartésienne uniforme.

    La transformation géométrique est :

        f_Q(x) = f(Q^T (x - o) + o)

    Pour un champ vectoriel :

        v_Q(x) = Q v(Q^T (x - o) + o)

    Les points sources situés hors du domaine reçoivent
    fill_value. Cette convention n'est scientifiquement
    neutre que si le champ s'annule avant la frontière.
    """

    __slots__ = (
        "x_coordinates",
        "y_coordinates",
        "dx",
        "dy",
        "matrix",
        "origin",
        "fill_value",
        "shape",
        "target_x",
        "target_y",
        "source_x",
        "source_y",
        "_inside",
        "_ix0",
        "_iy0",
        "_tx",
        "_ty",
        "_exact_node_map",
        "_exact_ix",
        "_exact_iy",
    )

    def __init__(
        self,
        x_coordinates: object,
        y_coordinates: object,
        matrix: object,
        origin: object = (0.0, 0.0),
        fill_value: float = 0.0,
    ) -> None:
        (
            self.x_coordinates,
            self.dx,
        ) = validate_uniform_axis_coordinates(
            x_coordinates,
            "x",
        )

        (
            self.y_coordinates,
            self.dy,
        ) = validate_uniform_axis_coordinates(
            y_coordinates,
            "y",
        )

        self.matrix = (
            validate_orthogonal_matrix(
                matrix
            ).copy()
        )

        self.origin = validate_transform_origin(
            origin
        )

        try:
            self.fill_value = float(
                fill_value
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "La valeur de remplissage doit "
                "être un nombre réel."
            ) from error

        if not np.isfinite(self.fill_value):
            raise ValueError(
                "La valeur de remplissage doit "
                "être finie."
            )

        self.target_x, self.target_y = np.meshgrid(
            self.x_coordinates,
            self.y_coordinates,
            indexing="xy",
        )

        self.shape = self.target_x.shape

        relative_x = (
            self.target_x
            - self.origin[0]
        )

        relative_y = (
            self.target_y
            - self.origin[1]
        )

        self.source_x = (
            self.origin[0]
            + self.matrix[0, 0] * relative_x
            + self.matrix[1, 0] * relative_y
        )

        self.source_y = (
            self.origin[1]
            + self.matrix[0, 1] * relative_x
            + self.matrix[1, 1] * relative_y
        )

        normalized_x = (
            self.source_x
            - self.x_coordinates[0]
        ) / self.dx

        normalized_y = (
            self.source_y
            - self.y_coordinates[0]
        ) / self.dy

        tolerance = (
            64.0
            * np.finfo(np.float64).eps
            * max(
                self.x_coordinates.size,
                self.y_coordinates.size,
            )
        )

        self._inside = (
            (normalized_x >= -tolerance)
            & (
                normalized_x
                <= self.x_coordinates.size
                - 1
                + tolerance
            )
            & (normalized_y >= -tolerance)
            & (
                normalized_y
                <= self.y_coordinates.size
                - 1
                + tolerance
            )
        )

        clipped_x = np.clip(
            normalized_x,
            0.0,
            self.x_coordinates.size - 1,
        )

        clipped_y = np.clip(
            normalized_y,
            0.0,
            self.y_coordinates.size - 1,
        )

        self._ix0 = np.floor(
            clipped_x
        ).astype(np.int64)

        self._iy0 = np.floor(
            clipped_y
        ).astype(np.int64)

        self._ix0 = np.minimum(
            self._ix0,
            self.x_coordinates.size - 2,
        )

        self._iy0 = np.minimum(
            self._iy0,
            self.y_coordinates.size - 2,
        )

        self._tx = (
            clipped_x
            - self._ix0
        )

        self._ty = (
            clipped_y
            - self._iy0
        )

        # Certaines transformations orthogonales
        # envoient exactement chaque nœud de la grille
        # vers un autre nœud :
        #
        # - identité ;
        # - rotations de 90 degrés ;
        # - réflexions du carré.
        #
        # Dans ce cas, l'interpolation bilinéaire est
        # remplacée par une permutation directe afin
        # d'éviter toute erreur d'arrondi ou diffusion.
        rounded_x = np.rint(
            normalized_x
        )

        rounded_y = np.rint(
            normalized_y
        )

        exact_tolerance = (
            256.0
            * np.finfo(np.float64).eps
            * max(
                self.x_coordinates.size,
                self.y_coordinates.size,
            )
        )

        node_aligned = (
            np.all(self._inside)
            and np.all(
                np.abs(
                    normalized_x - rounded_x
                )
                <= exact_tolerance
            )
            and np.all(
                np.abs(
                    normalized_y - rounded_y
                )
                <= exact_tolerance
            )
        )

        self._exact_node_map = bool(
            node_aligned
        )

        if self._exact_node_map:
            self._exact_ix = (
                rounded_x.astype(np.int64)
            )

            self._exact_iy = (
                rounded_y.astype(np.int64)
            )

            if (
                np.any(self._exact_ix < 0)
                or np.any(
                    self._exact_ix
                    >= self.x_coordinates.size
                )
                or np.any(self._exact_iy < 0)
                or np.any(
                    self._exact_iy
                    >= self.y_coordinates.size
                )
            ):
                raise RuntimeError(
                    "Le plan exact contient un indice "
                    "situé hors de la grille."
                )
        else:
            self._exact_ix = np.empty(
                (0, 0),
                dtype=np.int64,
            )

            self._exact_iy = np.empty(
                (0, 0),
                dtype=np.int64,
            )

    @property
    def uses_exact_node_map(
        self,
    ) -> bool:
        return self._exact_node_map

    @property
    def inside_mask(
        self,
    ) -> np.ndarray:
        return self._inside.copy()

    def interpolate(
        self,
        field: object,
    ) -> np.ndarray:
        array = np.asarray(
            field,
            dtype=np.float64,
        )

        if array.shape != self.shape:
            raise ValueError(
                "Le champ à interpoler doit avoir "
                f"la forme {self.shape}, obtenue "
                f"{array.shape}."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(
                "Le champ à interpoler contient "
                "une valeur non finie."
            )

        if self._exact_node_map:
            return array[
                self._exact_iy,
                self._exact_ix,
            ].copy()

        ix1 = self._ix0 + 1
        iy1 = self._iy0 + 1

        value_00 = array[
            self._iy0,
            self._ix0,
        ]

        value_10 = array[
            self._iy0,
            ix1,
        ]

        value_01 = array[
            iy1,
            self._ix0,
        ]

        value_11 = array[
            iy1,
            ix1,
        ]

        one_minus_tx = 1.0 - self._tx
        one_minus_ty = 1.0 - self._ty

        interpolated = (
            one_minus_tx
            * one_minus_ty
            * value_00
            + self._tx
            * one_minus_ty
            * value_10
            + one_minus_tx
            * self._ty
            * value_01
            + self._tx
            * self._ty
            * value_11
        )

        return np.where(
            self._inside,
            interpolated,
            self.fill_value,
        )

    def transform_scalar(
        self,
        field: object,
    ) -> np.ndarray:
        return self.interpolate(field)

    def transform_vector(
        self,
        vx: object,
        vy: object,
    ) -> tuple[np.ndarray, np.ndarray]:
        source_vx = self.interpolate(vx)
        source_vy = self.interpolate(vy)

        transformed_vx = (
            self.matrix[0, 0] * source_vx
            + self.matrix[0, 1] * source_vy
        )

        transformed_vy = (
            self.matrix[1, 0] * source_vx
            + self.matrix[1, 1] * source_vy
        )

        return transformed_vx, transformed_vy


def make_sampled_transformed_velocity_function(
    velocity_function: Callable,
    x_coordinates: object,
    y_coordinates: object,
    matrix: object,
    origin: object = (0.0, 0.0),
    fill_value: float = 0.0,
) -> Callable:
    """
    Transforme un champ continu après l'avoir
    échantillonné sur la grille source.

    Cette fonction simule le cas réaliste où seules
    les valeurs discrètes du champ sont disponibles.
    """
    plan = BilinearTransformPlan(
        x_coordinates,
        y_coordinates,
        matrix,
        origin=origin,
        fill_value=fill_value,
    )

    source_x, source_y = np.meshgrid(
        plan.x_coordinates,
        plan.y_coordinates,
        indexing="xy",
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        if (
            np.asarray(x).shape != plan.shape
            or np.asarray(y).shape != plan.shape
        ):
            raise ValueError(
                "La grille fournie à la fonction "
                "transformée ne correspond pas au plan."
            )

        source_vx, source_vy = velocity_function(
            source_x,
            source_y,
            time,
        )

        return plan.transform_vector(
            source_vx,
            source_vy,
        )

    return transformed


def make_sampled_transformed_scalar_function(
    scalar_function: Callable,
    x_coordinates: object,
    y_coordinates: object,
    matrix: object,
    origin: object = (0.0, 0.0),
    fill_value: float = 0.0,
) -> Callable:
    plan = BilinearTransformPlan(
        x_coordinates,
        y_coordinates,
        matrix,
        origin=origin,
        fill_value=fill_value,
    )

    source_x, source_y = np.meshgrid(
        plan.x_coordinates,
        plan.y_coordinates,
        indexing="xy",
    )

    def transformed(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> np.ndarray:
        if (
            np.asarray(x).shape != plan.shape
            or np.asarray(y).shape != plan.shape
        ):
            raise ValueError(
                "La grille fournie à la fonction "
                "transformée ne correspond pas au plan."
            )

        source_field = scalar_function(
            source_x,
            source_y,
            time,
        )

        return plan.transform_scalar(
            source_field
        )

    return transformed

