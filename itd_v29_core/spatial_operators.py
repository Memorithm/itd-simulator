"""
Opérateurs spatiaux et conventions de frontière pour ITD V29.

Ce module regroupe les opérateurs numériques génériques utilisés
par le simulateur principal, les métriques structurelles et les
calculs de déformation matérielle.

L’interface publique historique reste exposée par itd_v29.py.
"""

from __future__ import annotations

import numpy as np

from compare_scenarios import numerical_vorticity
from itd_v29_core.constants import BOUNDARY_MODES
from itd_v29_core.spatial_geometry import (
    RectilinearGeometry,
    normalize_spatial_geometry,
    validate_field_shape_for_geometry,
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
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            "La grandeur à borner doit être un nombre réel."
        ) from error

    if not np.isfinite(value):
        raise ValueError(
            "La grandeur à borner doit être finie."
        )

    value = max(0.0, value)
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
