#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v11
import itd_v12
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
PERIODIC_INVARIANCE_TOLERANCE = 2.0e-12

GRID_SIZES = (
    32,
    64,
    128,
    256,
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


def build_finite_environment() -> tuple[
    Config,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
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

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    spacing = float(
        coordinates[1] - coordinates[0]
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    return cfg, x, y, times, spacing


def periodic_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    amplitude = (
        1.0
        + 0.20 * np.sin(0.7 * time)
    )

    vx = amplitude * (
        np.sin(y)
        + 0.25 * np.sin(2.0 * x - y)
    )

    vy = amplitude * (
        np.sin(x)
        - 0.20 * np.cos(x + 2.0 * y)
    )

    return vx, vy


def periodic_exact_vorticity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    amplitude = (
        1.0
        + 0.20 * np.sin(0.7 * time)
    )

    return amplitude * (
        np.cos(x)
        - np.cos(y)
        + 0.20 * np.sin(x + 2.0 * y)
        + 0.25 * np.cos(2.0 * x - y)
    )


def periodic_curvature(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    return (
        0.30 * np.cos(
            x + y - 0.4 * time
        )
        + 0.10 * np.sin(
            2.0 * x - y + 0.2 * time
        )
    )


def validate_v11_compatibility() -> None:
    cfg, x, y, times, spacing = (
        build_finite_environment()
    )

    print(
        "=== COMPATIBILITÉ V11 → V12 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        old_result = extract_results(
            itd_v11.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        new_result = extract_results(
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

        scenario_error = max(
            scaled_error(
                new_result[key],
                old_result[key],
            )
            for key in old_result
        )

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
            "La convention finite de la V12 "
            "n'est pas compatible avec la V11."
        )

    print(
        "Convention finite historique : VALIDÉE"
    )


def validate_periodic_vorticity_convergence() -> None:
    print()
    print(
        "=== CONVERGENCE DE LA VORTICITÉ PÉRIODIQUE ==="
    )
    print(
        "grille | pas spatial     | erreur maximale | ordre"
    )

    errors: list[float] = []
    previous_error: float | None = None

    time = 1.3

    for grid_size in GRID_SIZES:
        coordinates = np.linspace(
            0.0,
            2.0 * np.pi,
            grid_size,
            endpoint=False,
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

        vx, vy = periodic_velocity(
            x,
            y,
            time,
        )

        numerical = (
            itd_v12.numerical_vorticity_with_boundary(
                vx,
                vy,
                spacing,
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
            f"{grid_size:6d} | "
            f"{spacing:15.12f} | "
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
            "L'erreur périodique ne décroît pas "
            "avec le raffinement."
        )

    final_orders = (
        np.log(errors[-3] / errors[-2])
        / np.log(2.0),
        np.log(errors[-2] / errors[-1])
        / np.log(2.0),
    )

    if min(final_orders) < 1.8:
        raise RuntimeError(
            "L'opérateur périodique ne présente pas "
            "la convergence attendue d'ordre deux."
        )

    if errors[-1] > 5.0e-4:
        raise RuntimeError(
            "L'erreur périodique finale est trop élevée."
        )

    print(
        "Différences centrées périodiques : VALIDÉES"
    )


def validate_periodic_translation_invariance() -> None:
    grid_size = 128

    cfg = Config(
        grid_size=grid_size,
        time_steps=161,
    )

    coordinates = np.linspace(
        0.0,
        2.0 * np.pi,
        grid_size,
        endpoint=False,
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

    shift_x = 7.0 * spacing
    shift_y = -11.0 * spacing

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

    baseline = extract_results(
        itd_v12.simulate(
            "periodique_reference",
            periodic_velocity,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=periodic_curvature,
            boundary_mode="periodic",
        )
    )

    shifted = extract_results(
        itd_v12.simulate(
            "periodique_translate",
            shifted_velocity,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=shifted_curvature,
            boundary_mode="periodic",
        )
    )

    errors = {
        key: scaled_error(
            shifted[key],
            baseline[key],
        )
        for key in baseline
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
        "=== INVARIANCE PAR TRANSLATION PÉRIODIQUE ==="
    )
    print(
        "Décalage x :",
        f"{shift_x / spacing:.0f} mailles",
    )
    print(
        "Décalage y :",
        f"{shift_y / spacing:.0f} mailles",
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
        > PERIODIC_INVARIANCE_TOLERANCE
    ):
        raise RuntimeError(
            "Le traitement périodique n'est pas "
            "invariant par translation de mailles."
        )

    print(
        "Invariance périodique par translation : "
        "VALIDÉE"
    )


def validate_spatial_mean_contract() -> None:
    finite_field = np.full(
        (41, 41),
        3.75,
        dtype=np.float64,
    )

    periodic_field = np.full(
        (40, 40),
        3.75,
        dtype=np.float64,
    )

    finite_mean = itd_v12.spatial_mean(
        finite_field,
        0.1,
        boundary_mode="finite",
    )

    periodic_mean = itd_v12.spatial_mean(
        periodic_field,
        0.1,
        boundary_mode="periodic",
    )

    print()
    print(
        "=== ORACLE DES MOYENNES SPATIALES ==="
    )
    print(
        "Moyenne domaine fini :",
        f"{finite_mean:.15f}",
    )
    print(
        "Moyenne périodique   :",
        f"{periodic_mean:.15f}",
    )

    if abs(finite_mean - 3.75) > 1.0e-14:
        raise RuntimeError(
            "La moyenne sur domaine fini est incorrecte."
        )

    if abs(periodic_mean - 3.75) > 1.0e-14:
        raise RuntimeError(
            "La moyenne périodique est incorrecte."
        )

    print(
        "Moyennes spatiales constantes : VALIDÉES"
    )


def validate_invalid_inputs() -> None:
    print()
    print(
        "=== REJET DES FRONTIÈRES INVALIDES ==="
    )

    for invalid_mode in (
        "",
        "open",
        "dirichlet",
        "periodique",
        42,
        None,
    ):
        try:
            itd_v12.validate_boundary_mode(
                invalid_mode
            )
        except ValueError as error:
            print(
                f"Rejet {invalid_mode!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un mode de frontière invalide "
                "n'a pas été rejeté."
            )

    small = np.zeros(
        (2, 2),
        dtype=np.float64,
    )

    try:
        itd_v12.numerical_vorticity_with_boundary(
            small,
            small,
            1.0,
            boundary_mode="periodic",
        )
    except ValueError as error:
        print(
            "Rejet grille périodique 2 × 2 : "
            f"RÉUSSI — {error}"
        )
    else:
        raise RuntimeError(
            "Une grille périodique trop petite "
            "n'a pas été rejetée."
        )

    print(
        "Contrôle des entrées de frontière : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DES CONDITIONS "
        "AUX LIMITES — ITD V12 ==="
    )

    validate_v11_compatibility()
    validate_periodic_vorticity_convergence()
    validate_periodic_translation_invariance()
    validate_spatial_mean_contract()
    validate_invalid_inputs()

    print()
    print(
        "Domaine fini historique       : VALIDÉ"
    )
    print(
        "Domaine périodique            : VALIDÉ"
    )
    print(
        "Convergence spatiale périodique: VALIDÉE"
    )
    print(
        "Invariance par translation    : VALIDÉE"
    )


if __name__ == "__main__":
    main()
