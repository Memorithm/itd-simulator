#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v12
import itd_v13
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
FINITE_ORACLE_TOLERANCE = 2.0e-12
PERIODIC_TRANSLATION_TOLERANCE = 3.0e-12

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)

SCALAR_RESULTS = (
    "intensity_index",
    "structure_index",
    "coupled_index",
    "temporal_deformation_index",
)

RECTANGULAR_GRIDS = (
    (32, 24),
    (64, 48),
    (128, 96),
    (256, 192),
)

LX = 2.0 * np.pi
LY = 3.0 * np.pi

KX = 2.0 * np.pi / LX
KY = 2.0 * np.pi / LY


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def extract_results(
    result: dict[str, object],
) -> dict[str, float]:
    extracted = {
        name: float(result[name])
        for name in SCALAR_RESULTS
    }

    components = {
        str(name): float(value)
        for name, value in dict(
            result["component_indices"]
        ).items()
    }

    for component in COMPONENTS:
        extracted[
            f"component:{component}"
        ] = components[component]

    return extracted


def validate_v12_compatibility() -> None:
    cfg = Config(
        grid_size=161,
        time_steps=201,
    )

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        endpoint=True,
        dtype=np.float64,
    )

    spacing = float(
        coordinates[1] - coordinates[0]
    )

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    print(
        "=== COMPATIBILITÉ V12 → V13 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        reference = extract_results(
            itd_v12.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        scalar_result = extract_results(
            itd_v13.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        object_result = extract_results(
            itd_v13.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                itd_v13.SpatialGeometry(
                    spacing,
                    spacing,
                ),
                cfg,
            )
        )

        tuple_result = extract_results(
            itd_v13.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                (spacing, spacing),
                cfg,
            )
        )

        errors = []

        for result in (
            scalar_result,
            object_result,
            tuple_result,
        ):
            errors.extend(
                scaled_error(
                    result[key],
                    reference[key],
                )
                for key in reference
            )

        scenario_error = max(errors)
        maximum_error = max(
            maximum_error,
            scenario_error,
        )

        print(
            f"{name:24s}: "
            f"erreur maximale={scenario_error:.6e}"
        )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V13 n'est pas compatible avec "
            "la géométrie isotrope de la V12."
        )

    print(
        "Compatibilité isotrope V12 → V13 : VALIDÉE"
    )


def finite_polynomial_velocity(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    vx = (
        0.50 * y**2
        + 0.25 * x * y
        - 0.30 * x
    )

    vy = (
        x**2
        - 0.40 * x * y
        + 0.20 * y
    )

    return vx, vy


def finite_exact_vorticity(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    return (
        1.75 * x
        - 1.40 * y
    )


def validate_finite_rectangular_oracle() -> None:
    nx = 91
    ny = 57

    x_coordinates = np.linspace(
        -2.5,
        4.0,
        nx,
        endpoint=True,
        dtype=np.float64,
    )

    y_coordinates = np.linspace(
        -1.25,
        3.75,
        ny,
        endpoint=True,
        dtype=np.float64,
    )

    dx = float(
        x_coordinates[1]
        - x_coordinates[0]
    )

    dy = float(
        y_coordinates[1]
        - y_coordinates[0]
    )

    x, y = np.meshgrid(
        x_coordinates,
        y_coordinates,
        indexing="xy",
    )

    vx, vy = finite_polynomial_velocity(
        x,
        y,
    )

    numerical = (
        itd_v13.numerical_vorticity_with_boundary(
            vx,
            vy,
            itd_v13.SpatialGeometry(
                dx,
                dy,
            ),
            boundary_mode="finite",
        )
    )

    exact = finite_exact_vorticity(
        x,
        y,
    )

    error = float(
        np.max(
            np.abs(
                numerical - exact
            )
        )
    )

    print()
    print(
        "=== ORACLE RECTANGULAIRE FINI ==="
    )
    print(
        "Forme de la grille :",
        f"{ny} × {nx}",
    )
    print(
        "dx                :",
        f"{dx:.15f}",
    )
    print(
        "dy                :",
        f"{dy:.15f}",
    )
    print(
        "Erreur maximale   :",
        f"{error:.6e}",
    )

    if error > FINITE_ORACLE_TOLERANCE:
        raise RuntimeError(
            "L'oracle polynomial rectangulaire "
            "n'est pas respecté."
        )

    print(
        "Vorticité rectangulaire finie : VALIDÉE"
    )


def periodic_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    amplitude = (
        1.0
        + 0.17 * np.sin(0.6 * time)
    )

    vx = amplitude * (
        np.sin(KY * y)
        + 0.25 * np.sin(
            2.0 * KX * x
            - KY * y
        )
    )

    vy = amplitude * (
        np.sin(KX * x)
        - 0.20 * np.cos(
            KX * x
            + 2.0 * KY * y
        )
    )

    return vx, vy


def periodic_exact_vorticity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    amplitude = (
        1.0
        + 0.17 * np.sin(0.6 * time)
    )

    return amplitude * (
        KX * np.cos(KX * x)
        + 0.20 * KX * np.sin(
            KX * x
            + 2.0 * KY * y
        )
        - KY * np.cos(KY * y)
        + 0.25 * KY * np.cos(
            2.0 * KX * x
            - KY * y
        )
    )


def periodic_curvature(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    return (
        0.25 * np.cos(
            KX * x
            + KY * y
            - 0.30 * time
        )
        + 0.08 * np.sin(
            2.0 * KX * x
            - KY * y
            + 0.20 * time
        )
    )


def build_periodic_grid(
    nx: int,
    ny: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    itd_v13.SpatialGeometry,
]:
    x_coordinates = np.linspace(
        0.0,
        LX,
        nx,
        endpoint=False,
        dtype=np.float64,
    )

    y_coordinates = np.linspace(
        0.0,
        LY,
        ny,
        endpoint=False,
        dtype=np.float64,
    )

    geometry = itd_v13.SpatialGeometry(
        LX / nx,
        LY / ny,
    )

    x, y = np.meshgrid(
        x_coordinates,
        y_coordinates,
        indexing="xy",
    )

    return x, y, geometry


def validate_periodic_rectangular_convergence() -> None:
    print()
    print(
        "=== CONVERGENCE PÉRIODIQUE RECTANGULAIRE ==="
    )
    print(
        "nx × ny   | dx             | dy             | "
        "erreur maximale | ordre"
    )

    errors: list[float] = []
    previous_error: float | None = None

    time = 1.4

    for nx, ny in RECTANGULAR_GRIDS:
        x, y, geometry = build_periodic_grid(
            nx,
            ny,
        )

        vx, vy = periodic_velocity(
            x,
            y,
            time,
        )

        numerical = (
            itd_v13.numerical_vorticity_with_boundary(
                vx,
                vy,
                geometry,
                boundary_mode="periodic",
            )
        )

        exact = periodic_exact_vorticity(
            x,
            y,
            time,
        )

        error = float(
            np.max(
                np.abs(
                    numerical - exact
                )
            )
        )

        errors.append(error)

        if previous_error is None:
            order_text = "—"
        else:
            order = float(
                np.log(previous_error / error)
                / np.log(2.0)
            )

            order_text = f"{order:.6f}"

        print(
            f"{nx:3d} × {ny:<3d} | "
            f"{geometry.dx:14.11f} | "
            f"{geometry.dy:14.11f} | "
            f"{error:15.6e} | "
            f"{order_text}"
        )

        previous_error = error

    if not all(
        current < previous
        for previous, current in zip(
            errors,
            errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur rectangulaire périodique "
            "ne décroît pas."
        )

    final_orders = (
        np.log(errors[-3] / errors[-2])
        / np.log(2.0),
        np.log(errors[-2] / errors[-1])
        / np.log(2.0),
    )

    if min(final_orders) < 1.8:
        raise RuntimeError(
            "La convergence rectangulaire n'atteint "
            "pas l'ordre deux attendu."
        )

    if errors[-1] > 5.0e-4:
        raise RuntimeError(
            "L'erreur finale rectangulaire "
            "est trop élevée."
        )

    print(
        "Convergence rectangulaire d'ordre deux : "
        "VALIDÉE"
    )


def validate_rectangular_spatial_mean() -> None:
    nx = 73
    ny = 41

    x_coordinates = np.linspace(
        -1.0,
        5.0,
        nx,
        endpoint=True,
        dtype=np.float64,
    )

    y_coordinates = np.linspace(
        2.0,
        7.5,
        ny,
        endpoint=True,
        dtype=np.float64,
    )

    geometry = itd_v13.SpatialGeometry(
        float(
            x_coordinates[1]
            - x_coordinates[0]
        ),
        float(
            y_coordinates[1]
            - y_coordinates[0]
        ),
    )

    x, y = np.meshgrid(
        x_coordinates,
        y_coordinates,
        indexing="xy",
    )

    constant_field = np.full_like(
        x,
        3.75,
        dtype=np.float64,
    )

    linear_field = (
        2.0
        + 3.0 * x
        - 0.50 * y
    )

    constant_mean = itd_v13.spatial_mean(
        constant_field,
        geometry,
        boundary_mode="finite",
    )

    linear_mean = itd_v13.spatial_mean(
        linear_field,
        geometry,
        boundary_mode="finite",
    )

    center_x = 0.5 * (
        x_coordinates[0]
        + x_coordinates[-1]
    )

    center_y = 0.5 * (
        y_coordinates[0]
        + y_coordinates[-1]
    )

    expected_linear_mean = (
        2.0
        + 3.0 * center_x
        - 0.50 * center_y
    )

    print()
    print(
        "=== QUADRATURE RECTANGULAIRE ==="
    )
    print(
        "Moyenne constante :",
        f"{constant_mean:.15f}",
    )
    print(
        "Moyenne linéaire   :",
        f"{linear_mean:.15f}",
    )
    print(
        "Valeur attendue    :",
        f"{expected_linear_mean:.15f}",
    )

    if abs(
        constant_mean - 3.75
    ) > 2.0e-14:
        raise RuntimeError(
            "La moyenne constante rectangulaire "
            "est incorrecte."
        )

    if abs(
        linear_mean
        - expected_linear_mean
    ) > 2.0e-13:
        raise RuntimeError(
            "La quadrature rectangulaire ne calcule "
            "pas exactement le champ linéaire."
        )

    print(
        "Quadrature rectangulaire : VALIDÉE"
    )


def validate_periodic_translation_invariance() -> None:
    nx = 128
    ny = 96

    x, y, geometry = build_periodic_grid(
        nx,
        ny,
    )

    cfg = Config(
        grid_size=max(nx, ny),
        time_steps=121,
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    shift_x_cells = 9
    shift_y_cells = -13

    shift_x = (
        shift_x_cells
        * geometry.dx
    )

    shift_y = (
        shift_y_cells
        * geometry.dy
    )

    def shifted_velocity(
        x_value: np.ndarray,
        y_value: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        return periodic_velocity(
            x_value - shift_x,
            y_value - shift_y,
            time,
        )

    def shifted_curvature(
        x_value: np.ndarray,
        y_value: np.ndarray,
        time: float,
    ) -> np.ndarray:
        return periodic_curvature(
            x_value - shift_x,
            y_value - shift_y,
            time,
        )

    reference = extract_results(
        itd_v13.simulate(
            "rectangulaire_reference",
            periodic_velocity,
            x,
            y,
            times,
            geometry,
            cfg,
            curvature_function=periodic_curvature,
            boundary_mode="periodic",
        )
    )

    translated = extract_results(
        itd_v13.simulate(
            "rectangulaire_translate",
            shifted_velocity,
            x,
            y,
            times,
            geometry,
            cfg,
            curvature_function=shifted_curvature,
            boundary_mode="periodic",
        )
    )

    errors = {
        key: scaled_error(
            translated[key],
            reference[key],
        )
        for key in reference
    }

    maximum_error = max(
        errors.values()
    )

    worst_metric = max(
        errors,
        key=errors.get,
    )

    print()
    print(
        "=== TRANSLATION PÉRIODIQUE RECTANGULAIRE ==="
    )
    print(
        "Décalage x :",
        f"{shift_x_cells} mailles",
    )
    print(
        "Décalage y :",
        f"{shift_y_cells} mailles",
    )
    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )
    print(
        "Métrique la plus sensible :",
        worst_metric,
    )

    if (
        maximum_error
        > PERIODIC_TRANSLATION_TOLERANCE
    ):
        raise RuntimeError(
            "La signature rectangulaire périodique "
            "n'est pas invariante par translation."
        )

    print(
        "Translation périodique rectangulaire : "
        "VALIDÉE"
    )


def validate_geometry_metadata() -> None:
    nx = 48
    ny = 32

    x, y, geometry = build_periodic_grid(
        nx,
        ny,
    )

    cfg = Config(
        grid_size=max(nx, ny),
        time_steps=21,
    )

    times = np.linspace(
        0.0,
        1.0,
        cfg.time_steps,
        dtype=np.float64,
    )

    result = itd_v13.simulate(
        "metadata",
        periodic_velocity,
        x,
        y,
        times,
        geometry,
        cfg,
        curvature_function=periodic_curvature,
        boundary_mode="periodic",
    )

    metadata = dict(
        result["spatial_geometry"]
    )

    print()
    print(
        "=== MÉTADONNÉES GÉOMÉTRIQUES ==="
    )
    print(
        "dx        :",
        f"{float(metadata['dx']):.15f}",
    )
    print(
        "dy        :",
        f"{float(metadata['dy']):.15f}",
    )
    print(
        "aire cellule:",
        f"{float(metadata['cell_area']):.15f}",
    )

    if float(metadata["dx"]) != geometry.dx:
        raise RuntimeError(
            "La métadonnée dx est incorrecte."
        )

    if float(metadata["dy"]) != geometry.dy:
        raise RuntimeError(
            "La métadonnée dy est incorrecte."
        )

    if float(
        metadata["cell_area"]
    ) != geometry.cell_area:
        raise RuntimeError(
            "La métadonnée cell_area est incorrecte."
        )

    print(
        "Métadonnées géométriques : VALIDÉES"
    )


def validate_invalid_geometries() -> None:
    print()
    print(
        "=== REJET DES GÉOMÉTRIES INVALIDES ==="
    )

    invalid_values = (
        0.0,
        -1.0,
        np.nan,
        np.inf,
        "",
        "0.1",
        (),
        (0.1,),
        (0.1, 0.2, 0.3),
        (0.1, 0.0),
        (-0.1, 0.2),
        (np.nan, 0.2),
        None,
    )

    for invalid in invalid_values:
        try:
            itd_v13.normalize_spatial_geometry(
                invalid
            )
        except ValueError as error:
            print(
                f"Rejet {invalid!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une géométrie invalide n'a pas "
                "été rejetée."
            )

    print(
        "Contrôle des géométries invalides : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE LA GÉOMÉTRIE "
        "RECTANGULAIRE — ITD V13 ==="
    )

    validate_v12_compatibility()
    validate_finite_rectangular_oracle()
    validate_periodic_rectangular_convergence()
    validate_rectangular_spatial_mean()
    validate_periodic_translation_invariance()
    validate_geometry_metadata()
    validate_invalid_geometries()

    print()
    print(
        "Compatibilité isotrope V12 → V13 : VALIDÉE"
    )
    print(
        "Grilles rectangulaires finies    : VALIDÉES"
    )
    print(
        "Grilles rectangulaires périodiques: VALIDÉES"
    )
    print(
        "Convergence spatiale d'ordre deux : VALIDÉE"
    )
    print(
        "Quadrature avec dx différent de dy: VALIDÉE"
    )
    print(
        "Translations indépendantes x et y : VALIDÉES"
    )


if __name__ == "__main__":
    main()
