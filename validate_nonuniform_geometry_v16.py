#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v15
import itd_v16
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
UNIFORM_RECTILINEAR_TOLERANCE = 2.0e-11
QUADRATURE_TOLERANCE = 3.0e-13
TRANSLATION_TOLERANCE = 2.0e-11

FINAL_CONVERGENCE_TOLERANCE = 2.0e-4

GRID_SIZES = (
    33,
    65,
    129,
    257,
)

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


def validate_v15_compatibility() -> None:
    cfg = Config(
        grid_size=81,
        time_steps=101,
    )

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        endpoint=True,
        dtype=np.float64,
    )

    spacing = float(
        coordinates[1]
        - coordinates[0]
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
        "=== COMPATIBILITÉ V15 → V16 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        reference = extract_results(
            itd_v15.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        candidate = extract_results(
            itd_v16.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        error = max(
            scaled_error(
                candidate[key],
                reference[key],
            )
            for key in reference
        )

        maximum_error = max(
            maximum_error,
            error,
        )

        print(
            f"{name:24s}: "
            f"erreur maximale={error:.6e}"
        )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V16 n'est pas compatible "
            "avec la V15."
        )

    print(
        "Compatibilité V15 → V16 : VALIDÉE"
    )


def validate_uniform_rectilinear_equivalence() -> None:
    cfg = Config(
        grid_size=65,
        time_steps=61,
    )

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        endpoint=True,
        dtype=np.float64,
    )

    spacing = float(
        coordinates[1]
        - coordinates[0]
    )

    geometry = itd_v16.RectilinearGeometry(
        coordinates,
        coordinates,
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

    reference = extract_results(
        itd_v16.simulate(
            "uniforme_reference",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
        )
    )

    candidate = extract_results(
        itd_v16.simulate(
            "uniforme_rectiligne",
            multi_vortex_field,
            x,
            y,
            times,
            geometry,
            cfg,
        )
    )

    errors = {
        key: scaled_error(
            candidate[key],
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
        "=== ÉQUIVALENCE RECTILIGNE UNIFORME ==="
    )

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    print(
        "Métrique sensible:",
        worst_metric,
    )

    if (
        maximum_error
        > UNIFORM_RECTILINEAR_TOLERANCE
    ):
        raise RuntimeError(
            "Une géométrie rectiligne uniforme "
            "diffère excessivement de la géométrie "
            "uniforme historique."
        )

    print(
        "Équivalence uniforme : VALIDÉE"
    )


def build_stretched_grid(
    grid_size: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    itd_v16.RectilinearGeometry,
]:
    parameter = np.linspace(
        0.0,
        1.0,
        grid_size,
        endpoint=True,
        dtype=np.float64,
    )

    x_coordinates = (
        -1.5
        + 3.0 * parameter**1.3
    )

    y_coordinates = (
        -1.0
        + 2.0 * parameter**1.7
    )

    x, y = np.meshgrid(
        x_coordinates,
        y_coordinates,
        indexing="xy",
    )

    geometry = itd_v16.RectilinearGeometry(
        x_coordinates,
        y_coordinates,
    )

    return (
        x_coordinates,
        y_coordinates,
        x,
        y,
        geometry,
    )


def analytic_velocity(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    vx = (
        np.sin(y)
        + 0.20 * x * y
    )

    vy = (
        np.cos(x)
        + 0.30 * x**2 * y
    )

    return vx, vy


def analytic_vorticity(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    return (
        -np.sin(x)
        + 0.60 * x * y
        - np.cos(y)
        - 0.20 * x
    )


def validate_nonuniform_convergence() -> None:
    print()
    print(
        "=== CONVERGENCE SUR GRILLES NON UNIFORMES ==="
    )

    print(
        "grille | max(dx)       | max(dy)       | "
        "erreur maximale | ordre"
    )

    errors: list[float] = []
    steps: list[float] = []

    previous_error: float | None = None
    previous_step: float | None = None

    for grid_size in GRID_SIZES:
        (
            _,
            _,
            x,
            y,
            geometry,
        ) = build_stretched_grid(
            grid_size
        )

        vx, vy = analytic_velocity(
            x,
            y,
        )

        numerical = (
            itd_v16.numerical_vorticity_with_boundary(
                vx,
                vy,
                geometry,
                boundary_mode="finite",
            )
        )

        exact = analytic_vorticity(
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

        step = max(
            geometry.dx_maximum,
            geometry.dy_maximum,
        )

        errors.append(error)
        steps.append(step)

        if previous_error is None:
            order_text = "—"
        else:
            order = float(
                np.log(
                    previous_error / error
                )
                / np.log(
                    previous_step / step
                )
            )

            order_text = f"{order:.6f}"

        print(
            f"{grid_size:6d} | "
            f"{geometry.dx_maximum:13.10f} | "
            f"{geometry.dy_maximum:13.10f} | "
            f"{error:15.6e} | "
            f"{order_text}"
        )

        previous_error = error
        previous_step = step

    if not all(
        current < previous
        for previous, current in zip(
            errors,
            errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur non uniforme ne décroît pas."
        )

    final_orders = []

    for index in (
        len(errors) - 2,
        len(errors) - 1,
    ):
        final_orders.append(
            float(
                np.log(
                    errors[index - 1]
                    / errors[index]
                )
                / np.log(
                    steps[index - 1]
                    / steps[index]
                )
            )
        )

    if min(final_orders) < 1.8:
        raise RuntimeError(
            "La convergence non uniforme n'atteint "
            "pas l'ordre deux attendu."
        )

    if (
        errors[-1]
        > FINAL_CONVERGENCE_TOLERANCE
    ):
        raise RuntimeError(
            "L'erreur finale non uniforme "
            "est trop élevée."
        )

    print(
        "Convergence non uniforme d'ordre deux : "
        "VALIDÉE"
    )


def validate_nonuniform_quadrature() -> None:
    (
        x_coordinates,
        y_coordinates,
        x,
        y,
        geometry,
    ) = build_stretched_grid(
        73
    )

    field = (
        2.0
        + 3.0 * x
        - 0.50 * y
        + 0.20 * x * y
    )

    numerical_mean = itd_v16.spatial_mean(
        field,
        geometry,
        boundary_mode="finite",
    )

    mean_x = 0.5 * (
        x_coordinates[0]
        + x_coordinates[-1]
    )

    mean_y = 0.5 * (
        y_coordinates[0]
        + y_coordinates[-1]
    )

    expected_mean = (
        2.0
        + 3.0 * mean_x
        - 0.50 * mean_y
        + 0.20 * mean_x * mean_y
    )

    constant_mean = itd_v16.spatial_mean(
        np.full_like(
            field,
            3.75,
        ),
        geometry,
        boundary_mode="finite",
    )

    print()
    print(
        "=== QUADRATURE NON UNIFORME ==="
    )

    print(
        "Moyenne bilinéaire obtenue :",
        f"{numerical_mean:.15f}",
    )

    print(
        "Moyenne bilinéaire attendue:",
        f"{expected_mean:.15f}",
    )

    print(
        "Moyenne constante           :",
        f"{constant_mean:.15f}",
    )

    if abs(
        numerical_mean
        - expected_mean
    ) > QUADRATURE_TOLERANCE:
        raise RuntimeError(
            "La quadrature non uniforme ne reproduit "
            "pas exactement le champ bilinéaire."
        )

    if abs(
        constant_mean - 3.75
    ) > QUADRATURE_TOLERANCE:
        raise RuntimeError(
            "La moyenne constante non uniforme "
            "est incorrecte."
        )

    print(
        "Quadrature non uniforme : VALIDÉE"
    )


def dynamic_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    vx = (
        np.sin(y)
        + 0.15 * x * y
        + 0.05 * time * x
    )

    vy = (
        np.cos(x)
        - 0.12 * x * y
        + 0.03 * time * y
    )

    return vx, vy


def dynamic_curvature(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    return (
        0.15 * np.cos(x - 0.2 * time)
        + 0.08 * np.sin(y + 0.1 * time)
        + 0.02 * x * y
    )


def validate_coordinate_translation() -> None:
    (
        x_coordinates,
        y_coordinates,
        x,
        y,
        geometry,
    ) = build_stretched_grid(
        65
    )

    shift_x = 7.25
    shift_y = -4.50

    shifted_x_coordinates = (
        x_coordinates + shift_x
    )

    shifted_y_coordinates = (
        y_coordinates + shift_y
    )

    shifted_x, shifted_y = np.meshgrid(
        shifted_x_coordinates,
        shifted_y_coordinates,
        indexing="xy",
    )

    shifted_geometry = (
        itd_v16.RectilinearGeometry(
            shifted_x_coordinates,
            shifted_y_coordinates,
        )
    )

    times = np.asarray(
        (
            0.0,
            0.125,
            0.40,
            0.85,
            1.50,
            2.25,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=65,
        time_steps=times.size,
    )

    def translated_velocity(
        x_value: np.ndarray,
        y_value: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        return dynamic_velocity(
            x_value - shift_x,
            y_value - shift_y,
            time,
        )

    def translated_curvature(
        x_value: np.ndarray,
        y_value: np.ndarray,
        time: float,
    ) -> np.ndarray:
        return dynamic_curvature(
            x_value - shift_x,
            y_value - shift_y,
            time,
        )

    reference = extract_results(
        itd_v16.simulate(
            "translation_reference",
            dynamic_velocity,
            x,
            y,
            times,
            geometry,
            cfg,
            curvature_function=dynamic_curvature,
            boundary_mode="finite",
        )
    )

    translated = extract_results(
        itd_v16.simulate(
            "translation_coordonnees",
            translated_velocity,
            shifted_x,
            shifted_y,
            times,
            shifted_geometry,
            cfg,
            curvature_function=translated_curvature,
            boundary_mode="finite",
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
        "=== TRANSLATION DES COORDONNÉES ==="
    )

    print(
        "Décalage x      :",
        shift_x,
    )

    print(
        "Décalage y      :",
        shift_y,
    )

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    print(
        "Métrique sensible:",
        worst_metric,
    )

    if maximum_error > TRANSLATION_TOLERANCE:
        raise RuntimeError(
            "La description dépend de l'origine "
            "absolue des coordonnées."
        )

    print(
        "Translation des coordonnées : VALIDÉE"
    )


def validate_metadata() -> None:
    (
        _,
        _,
        x,
        y,
        geometry,
    ) = build_stretched_grid(
        33
    )

    times = np.asarray(
        (
            0.0,
            0.25,
            0.75,
            1.5,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=33,
        time_steps=times.size,
    )

    result = itd_v16.simulate(
        "metadata_non_uniforme",
        dynamic_velocity,
        x,
        y,
        times,
        geometry,
        cfg,
        curvature_function=dynamic_curvature,
    )

    metadata = dict(
        result["spatial_geometry"]
    )

    print()
    print(
        "=== MÉTADONNÉES NON UNIFORMES ==="
    )

    for key, value in metadata.items():
        print(
            f"{key:20s}: {value}"
        )

    if metadata != geometry.as_dict():
        raise RuntimeError(
            "Les métadonnées spatiales exportées "
            "sont incorrectes."
        )

    if metadata["uniform_x"]:
        raise RuntimeError(
            "L'axe x étiré a été classé uniforme."
        )

    if metadata["uniform_y"]:
        raise RuntimeError(
            "L'axe y étiré a été classé uniforme."
        )

    print(
        "Métadonnées non uniformes : VALIDÉES"
    )


def validate_periodic_rejection() -> None:
    (
        _,
        _,
        x,
        y,
        geometry,
    ) = build_stretched_grid(
        33
    )

    vx, vy = analytic_velocity(
        x,
        y,
    )

    print()
    print(
        "=== REJET DU PÉRIODIQUE NON UNIFORME ==="
    )

    try:
        itd_v16.numerical_vorticity_with_boundary(
            vx,
            vy,
            geometry,
            boundary_mode="periodic",
        )
    except ValueError as error:
        print(
            "Vorticité : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Une dérivation périodique non uniforme "
            "a été acceptée sans méthode validée."
        )

    try:
        itd_v16.spatial_mean(
            vx,
            geometry,
            boundary_mode="periodic",
        )
    except ValueError as error:
        print(
            "Moyenne   : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Une moyenne périodique non uniforme "
            "a été acceptée sans convention validée."
        )

    print(
        "Périodique non uniforme refusé : VALIDÉ"
    )


def validate_invalid_geometries() -> None:
    invalid_axes = (
        (
            (0.0, 1.0),
            (0.0, 0.5, 1.0),
        ),
        (
            (0.0, 1.0, 0.5),
            (0.0, 0.5, 1.0),
        ),
        (
            (0.0, 0.5, 1.0),
            (0.0, 0.5, 0.5),
        ),
        (
            (0.0, np.nan, 1.0),
            (0.0, 0.5, 1.0),
        ),
        (
            [[0.0, 0.5, 1.0]],
            (0.0, 0.5, 1.0),
        ),
        (
            "0,1,2",
            (0.0, 0.5, 1.0),
        ),
    )

    print()
    print(
        "=== REJET DES GÉOMÉTRIES "
        "RECTILIGNES INVALIDES ==="
    )

    for x_coordinates, y_coordinates in invalid_axes:
        try:
            itd_v16.RectilinearGeometry(
                x_coordinates,
                y_coordinates,
            )
        except ValueError as error:
            print(
                "Rejet : RÉUSSI —",
                error,
            )
        else:
            raise RuntimeError(
                "Une géométrie rectiligne invalide "
                "n'a pas été rejetée."
            )

    (
        x_coordinates,
        y_coordinates,
        x,
        y,
        geometry,
    ) = build_stretched_grid(
        17
    )

    del x_coordinates
    del y_coordinates

    mismatched_x = x.copy()
    mismatched_x[0, 0] += 0.01

    times = np.asarray(
        (
            0.0,
            0.5,
            1.0,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=17,
        time_steps=times.size,
    )

    try:
        itd_v16.simulate(
            "maillage_incoherent",
            dynamic_velocity,
            mismatched_x,
            y,
            times,
            geometry,
            cfg,
            curvature_function=dynamic_curvature,
        )
    except ValueError as error:
        print(
            "Maillage incohérent : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Un maillage incohérent avec sa "
            "géométrie n'a pas été rejeté."
        )

    print(
        "Contrôle des géométries invalides : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DES GRILLES "
        "NON UNIFORMES — ITD V16 ==="
    )

    validate_v15_compatibility()
    validate_uniform_rectilinear_equivalence()
    validate_nonuniform_convergence()
    validate_nonuniform_quadrature()
    validate_coordinate_translation()
    validate_metadata()
    validate_periodic_rejection()
    validate_invalid_geometries()

    print()
    print(
        "Compatibilité V15 → V16            : VALIDÉE"
    )
    print(
        "Rectiligne uniforme                : VALIDÉ"
    )
    print(
        "Rectiligne non uniforme            : VALIDÉ"
    )
    print(
        "Convergence spatiale d'ordre deux  : VALIDÉE"
    )
    print(
        "Quadrature non uniforme            : VALIDÉE"
    )
    print(
        "Translation des coordonnées        : VALIDÉE"
    )
    print(
        "Métadonnées spatiales explicites   : VALIDÉES"
    )
    print(
        "Périodique non uniforme non supporté: EXPLICITE"
    )


if __name__ == "__main__":
    main()
