"""Géométries spatiales du simulateur ITD V29."""

from __future__ import annotations

import numpy as np

class SpatialGeometry:
    """
    Géométrie cartésienne uniforme bidimensionnelle.

    dx
        Pas spatial selon l'axe x, correspondant
        à l'axe 1 des tableaux NumPy.

    dy
        Pas spatial selon l'axe y, correspondant
        à l'axe 0 des tableaux NumPy.
    """

    __slots__ = (
        "dx",
        "dy",
    )

    def __init__(
        self,
        dx: float,
        dy: float,
    ) -> None:
        self.dx = validate_axis_spacing(
            dx,
            "dx",
        )

        self.dy = validate_axis_spacing(
            dy,
            "dy",
        )

    @property
    def cell_area(self) -> float:
        return self.dx * self.dy

    @property
    def isotropic(self) -> bool:
        return self.dx == self.dy

    def as_tuple(
        self,
    ) -> tuple[float, float]:
        return self.dx, self.dy

    def __iter__(self):
        yield self.dx
        yield self.dy

    def __repr__(self) -> str:
        return (
            "SpatialGeometry("
            f"dx={self.dx!r}, "
            f"dy={self.dy!r}"
            ")"
        )


def validate_axis_spacing(
    value: float,
    axis_name: str,
) -> float:
    try:
        spacing = float(value)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            f"Le pas {axis_name} doit être "
            "un nombre réel."
        ) from error

    if (
        not np.isfinite(spacing)
        or spacing <= 0.0
    ):
        raise ValueError(
            f"Le pas {axis_name} doit être fini "
            "et strictement positif."
        )

    return spacing


def validate_spacing(
    spacing: float,
) -> float:
    """
    API historique isotrope conservée pour compatibilité.
    """
    return validate_axis_spacing(
        spacing,
        "spatial",
    )


def validate_rectilinear_axis_coordinates(
    coordinates: object,
    axis_name: str,
) -> np.ndarray:
    """
    Valide un axe rectiligne strictement croissant.

    Contrairement à validate_uniform_axis_coordinates(),
    aucune uniformité du pas n'est exigée.
    """
    if isinstance(
        coordinates,
        (str, bytes),
    ):
        raise ValueError(
            f"Les coordonnées {axis_name} doivent "
            "former une séquence numérique."
        )

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

    if array.size < 3:
        raise ValueError(
            f"L'axe {axis_name} doit contenir "
            "au moins trois coordonnées."
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

    copied = np.array(
        array,
        dtype=np.float64,
        copy=True,
    )

    copied.setflags(
        write=False
    )

    return copied


class RectilinearGeometry:
    """
    Géométrie cartésienne rectiligne potentiellement
    non uniforme.

    Les lignes de la grille suivent y_coordinates.
    Les colonnes suivent x_coordinates.
    """

    __slots__ = (
        "x_coordinates",
        "y_coordinates",
        "nx",
        "ny",
        "shape",
        "width",
        "height",
        "domain_area",
        "dx_minimum",
        "dx_maximum",
        "dx_mean",
        "dy_minimum",
        "dy_maximum",
        "dy_mean",
        "uniform_x",
        "uniform_y",
        "dx",
        "dy",
        "minimum_cell_area",
        "maximum_cell_area",
    )

    def __init__(
        self,
        x_coordinates: object,
        y_coordinates: object,
    ) -> None:
        self.x_coordinates = (
            validate_rectilinear_axis_coordinates(
                x_coordinates,
                "x",
            )
        )

        self.y_coordinates = (
            validate_rectilinear_axis_coordinates(
                y_coordinates,
                "y",
            )
        )

        x_differences = np.diff(
            self.x_coordinates
        )

        y_differences = np.diff(
            self.y_coordinates
        )

        self.nx = int(
            self.x_coordinates.size
        )

        self.ny = int(
            self.y_coordinates.size
        )

        self.shape = (
            self.ny,
            self.nx,
        )

        self.width = float(
            self.x_coordinates[-1]
            - self.x_coordinates[0]
        )

        self.height = float(
            self.y_coordinates[-1]
            - self.y_coordinates[0]
        )

        self.domain_area = (
            self.width
            * self.height
        )

        self.dx_minimum = float(
            np.min(x_differences)
        )

        self.dx_maximum = float(
            np.max(x_differences)
        )

        self.dx_mean = float(
            self.width
            / (self.nx - 1)
        )

        self.dy_minimum = float(
            np.min(y_differences)
        )

        self.dy_maximum = float(
            np.max(y_differences)
        )

        self.dy_mean = float(
            self.height
            / (self.ny - 1)
        )

        x_tolerance = (
            64.0
            * np.finfo(np.float64).eps
            * max(
                1.0,
                abs(self.dx_mean),
            )
        )

        y_tolerance = (
            64.0
            * np.finfo(np.float64).eps
            * max(
                1.0,
                abs(self.dy_mean),
            )
        )

        self.uniform_x = bool(
            np.allclose(
                x_differences,
                self.dx_mean,
                rtol=1.0e-12,
                atol=x_tolerance,
            )
        )

        self.uniform_y = bool(
            np.allclose(
                y_differences,
                self.dy_mean,
                rtol=1.0e-12,
                atol=y_tolerance,
            )
        )

        self.dx = (
            self.dx_mean
            if self.uniform_x
            else None
        )

        self.dy = (
            self.dy_mean
            if self.uniform_y
            else None
        )

        self.minimum_cell_area = (
            self.dx_minimum
            * self.dy_minimum
        )

        self.maximum_cell_area = (
            self.dx_maximum
            * self.dy_maximum
        )

    @property
    def uniform(
        self,
    ) -> bool:
        return (
            self.uniform_x
            and self.uniform_y
        )

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "kind": "rectilinear",
            "nx": self.nx,
            "ny": self.ny,
            "width": self.width,
            "height": self.height,
            "domain_area": self.domain_area,
            "dx_minimum": self.dx_minimum,
            "dx_maximum": self.dx_maximum,
            "dx_mean": self.dx_mean,
            "dy_minimum": self.dy_minimum,
            "dy_maximum": self.dy_maximum,
            "dy_mean": self.dy_mean,
            "uniform_x": self.uniform_x,
            "uniform_y": self.uniform_y,
            "minimum_cell_area": (
                self.minimum_cell_area
            ),
            "maximum_cell_area": (
                self.maximum_cell_area
            ),
        }

    def __repr__(self) -> str:
        return (
            "RectilinearGeometry("
            f"nx={self.nx}, "
            f"ny={self.ny}, "
            f"uniform={self.uniform}"
            ")"
        )


def normalize_spatial_geometry(
    spacing: object,
) -> SpatialGeometry | RectilinearGeometry:
    """
    Formes acceptées :

    - scalaire : dx = dy ;
    - couple (dx, dy) ;
    - SpatialGeometry ;
    - RectilinearGeometry.
    """
    if isinstance(
        spacing,
        (
            SpatialGeometry,
            RectilinearGeometry,
        ),
    ):
        return spacing

    if isinstance(
        spacing,
        (str, bytes),
    ):
        raise ValueError(
            "La géométrie spatiale ne peut pas "
            "être une chaîne."
        )

    try:
        array = np.asarray(
            spacing,
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "La géométrie spatiale doit être un "
            "scalaire, un couple (dx, dy) ou une "
            "géométrie rectiligne."
        ) from error

    if array.ndim == 0:
        value = validate_axis_spacing(
            float(array),
            "spatial",
        )

        return SpatialGeometry(
            value,
            value,
        )

    if array.shape == (2,):
        return SpatialGeometry(
            float(array[0]),
            float(array[1]),
        )

    raise ValueError(
        "La géométrie spatiale doit être un "
        "scalaire ou un couple de deux valeurs "
        "(dx, dy)."
    )


def spatial_geometry_metadata(
    geometry: SpatialGeometry | RectilinearGeometry,
) -> dict[str, object]:
    if isinstance(
        geometry,
        RectilinearGeometry,
    ):
        return geometry.as_dict()

    return {
        "kind": "uniform",
        "dx": geometry.dx,
        "dy": geometry.dy,
        "cell_area": geometry.cell_area,
        "isotropic": geometry.isotropic,
    }


def validate_field_shape_for_geometry(
    field: np.ndarray,
    geometry: SpatialGeometry | RectilinearGeometry,
) -> None:
    if (
        isinstance(
            geometry,
            RectilinearGeometry,
        )
        and field.shape != geometry.shape
    ):
        raise ValueError(
            "La forme du champ ne correspond pas "
            "à la géométrie rectiligne : "
            f"{field.shape} contre {geometry.shape}."
        )


def validate_mesh_geometry(
    x: object,
    y: object,
    geometry: SpatialGeometry | RectilinearGeometry,
) -> None:
    if not isinstance(
        geometry,
        RectilinearGeometry,
    ):
        return

    x_array = np.asarray(
        x,
        dtype=np.float64,
    )

    y_array = np.asarray(
        y,
        dtype=np.float64,
    )

    if (
        x_array.shape != geometry.shape
        or y_array.shape != geometry.shape
    ):
        raise ValueError(
            "La grille spatiale ne correspond pas "
            "à la forme de la géométrie rectiligne."
        )

    if not (
        np.all(np.isfinite(x_array))
        and np.all(np.isfinite(y_array))
    ):
        raise ValueError(
            "La grille spatiale contient une "
            "valeur non finie."
        )

    expected_x = np.broadcast_to(
        geometry.x_coordinates,
        geometry.shape,
    )

    expected_y = np.broadcast_to(
        geometry.y_coordinates[:, None],
        geometry.shape,
    )

    coordinate_scale = max(
        1.0,
        float(
            np.max(
                np.abs(
                    geometry.x_coordinates
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    geometry.y_coordinates
                )
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
            "Les coordonnées x ne correspondent pas "
            "à la géométrie rectiligne."
        )

    if not np.allclose(
        y_array,
        expected_y,
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "Les coordonnées y ne correspondent pas "
            "à la géométrie rectiligne."
        )

