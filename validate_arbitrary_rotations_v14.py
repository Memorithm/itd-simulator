#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v13
import itd_v14
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


DOMAIN_MIN = -2.5
DOMAIN_MAX = 2.5

INTERPOLATION_GRID_SIZES = (
    33,
    65,
    129,
    257,
)

SIGNATURE_GRID_SIZES = (
    33,
    65,
    129,
)

ANGLES_DEGREES = (
    17.0,
    37.0,
    73.0,
)

COMPATIBILITY_TOLERANCE = 2.0e-13

FINAL_SCALAR_INTERPOLATION_TOLERANCE = 3.0e-4
FINAL_VECTOR_INTERPOLATION_TOLERANCE = 1.0e-3
FINAL_VORTICITY_EQUIVARIANCE_TOLERANCE = 3.0e-3

FINAL_ANALYTIC_SIGNATURE_TOLERANCE = 1.0e-4
FINAL_SAMPLED_SIGNATURE_TOLERANCE = 3.0e-3

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


def convergence_order(
    previous_error: float,
    current_error: float,
) -> float:
    return float(
        np.log(previous_error / current_error)
        / np.log(2.0)
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


def build_grid(
    grid_size: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
    coordinates = np.linspace(
        DOMAIN_MIN,
        DOMAIN_MAX,
        grid_size,
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

    return coordinates, x, y, spacing


def smooth_compact_bump(
    x: np.ndarray,
    y: np.ndarray,
    radius: float,
) -> np.ndarray:
    normalized_radius = (
        x**2 + y**2
    ) / radius**2

    result = np.zeros_like(
        normalized_radius,
        dtype=np.float64,
    )

    inside = normalized_radius < 1.0

    result[inside] = np.exp(
        1.0
        - 1.0
        / (
            1.0
            - normalized_radius[inside]
        )
    )

    return result


def compact_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    bump = smooth_compact_bump(
        x,
        y,
        radius=1.6,
    )

    amplitude = (
        1.0
        + 0.15 * np.sin(0.8 * time)
    )

    coupling = (
        0.20 * np.cos(0.6 * time)
    )

    vx = bump * (
        amplitude
        * (
            -0.80 * y
            + 0.25 * x
        )
        + coupling * x * y
    )

    vy = bump * (
        amplitude
        * (
            0.95 * x
            + 0.15 * y
        )
        + 0.12
        * np.sin(0.9 * time)
        * (
            x**2 - y**2
        )
    )

    return vx, vy


def compact_curvature(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    bump = smooth_compact_bump(
        x,
        y,
        radius=1.8,
    )

    return bump * (
        0.35
        + 0.08 * x
        - 0.06 * y
        + 0.04
        * np.cos(0.5 * time)
        * x
        * y
    )


def validate_v13_compatibility() -> None:
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
        "=== COMPATIBILITÉ V13 → V14 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        reference = extract_results(
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

        candidate = extract_results(
            itd_v14.simulate(
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
            "La V14 n'est pas compatible "
            "avec la V13."
        )

    print(
        "Compatibilité V13 → V14 : VALIDÉE"
    )


def validate_bilinear_interpolation() -> None:
    print()
    print(
        "=== CONVERGENCE DE L'INTERPOLATION "
        "BILINÉAIRE ==="
    )

    print(
        "grille | erreur scalaire | ordre  | "
        "erreur vectorielle | ordre"
    )

    scalar_errors: list[float] = []
    vector_errors: list[float] = []

    previous_scalar: float | None = None
    previous_vector: float | None = None

    time = 0.7

    for grid_size in INTERPOLATION_GRID_SIZES:
        coordinates, x, y, _ = build_grid(
            grid_size
        )

        base_scalar = compact_curvature(
            x,
            y,
            time,
        )

        base_vx, base_vy = compact_velocity(
            x,
            y,
            time,
        )

        worst_scalar = 0.0
        worst_vector = 0.0

        for angle_degrees in ANGLES_DEGREES:
            matrix = itd_v14.rotation_matrix(
                np.deg2rad(angle_degrees)
            )

            plan = itd_v14.BilinearTransformPlan(
                coordinates,
                coordinates,
                matrix,
            )

            sampled_scalar = (
                plan.transform_scalar(
                    base_scalar
                )
            )

            sampled_vx, sampled_vy = (
                plan.transform_vector(
                    base_vx,
                    base_vy,
                )
            )

            exact_scalar_function = (
                itd_v14.transform_scalar_function(
                    compact_curvature,
                    matrix,
                )
            )

            exact_velocity_function = (
                itd_v14.transform_velocity_function(
                    compact_velocity,
                    matrix,
                )
            )

            exact_scalar = exact_scalar_function(
                x,
                y,
                time,
            )

            exact_vx, exact_vy = (
                exact_velocity_function(
                    x,
                    y,
                    time,
                )
            )

            scalar_error = float(
                np.max(
                    np.abs(
                        sampled_scalar
                        - exact_scalar
                    )
                )
            )

            vector_error = float(
                np.max(
                    np.sqrt(
                        (
                            sampled_vx
                            - exact_vx
                        ) ** 2
                        + (
                            sampled_vy
                            - exact_vy
                        ) ** 2
                    )
                )
            )

            worst_scalar = max(
                worst_scalar,
                scalar_error,
            )

            worst_vector = max(
                worst_vector,
                vector_error,
            )

        scalar_errors.append(worst_scalar)
        vector_errors.append(worst_vector)

        if previous_scalar is None:
            scalar_order_text = "—"
            vector_order_text = "—"
        else:
            scalar_order_text = (
                f"{convergence_order(previous_scalar, worst_scalar):.5f}"
            )

            vector_order_text = (
                f"{convergence_order(previous_vector, worst_vector):.5f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{worst_scalar:15.6e} | "
            f"{scalar_order_text:6s} | "
            f"{worst_vector:17.6e} | "
            f"{vector_order_text}"
        )

        previous_scalar = worst_scalar
        previous_vector = worst_vector

    if not all(
        current < previous
        for previous, current in zip(
            scalar_errors,
            scalar_errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur d'interpolation scalaire "
            "ne décroît pas."
        )

    if not all(
        current < previous
        for previous, current in zip(
            vector_errors,
            vector_errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur d'interpolation vectorielle "
            "ne décroît pas."
        )

    scalar_final_orders = (
        convergence_order(
            scalar_errors[-3],
            scalar_errors[-2],
        ),
        convergence_order(
            scalar_errors[-2],
            scalar_errors[-1],
        ),
    )

    vector_final_orders = (
        convergence_order(
            vector_errors[-3],
            vector_errors[-2],
        ),
        convergence_order(
            vector_errors[-2],
            vector_errors[-1],
        ),
    )

    if min(scalar_final_orders) < 1.7:
        raise RuntimeError(
            "L'interpolation scalaire n'atteint "
            "pas l'ordre attendu."
        )

    if min(vector_final_orders) < 1.7:
        raise RuntimeError(
            "L'interpolation vectorielle n'atteint "
            "pas l'ordre attendu."
        )

    if (
        scalar_errors[-1]
        > FINAL_SCALAR_INTERPOLATION_TOLERANCE
    ):
        raise RuntimeError(
            "L'erreur scalaire finale "
            "est trop élevée."
        )

    if (
        vector_errors[-1]
        > FINAL_VECTOR_INTERPOLATION_TOLERANCE
    ):
        raise RuntimeError(
            "L'erreur vectorielle finale "
            "est trop élevée."
        )

    print(
        "Interpolation bilinéaire convergente : "
        "VALIDÉE"
    )


def validate_vorticity_equivariance() -> None:
    print()
    print(
        "=== ÉQUIVARIANCE APPROCHÉE "
        "DE LA VORTICITÉ ==="
    )

    print(
        "grille | erreur RMS maximale | ordre"
    )

    errors: list[float] = []
    previous_error: float | None = None

    time = 0.7

    for grid_size in INTERPOLATION_GRID_SIZES:
        (
            coordinates,
            x,
            y,
            spacing,
        ) = build_grid(grid_size)

        base_vx, base_vy = compact_velocity(
            x,
            y,
            time,
        )

        base_omega = (
            itd_v14.numerical_vorticity_with_boundary(
                base_vx,
                base_vy,
                spacing,
                boundary_mode="finite",
            )
        )

        comparison_mask = (
            x**2 + y**2
        ) < 1.95**2

        worst_error = 0.0

        for angle_degrees in ANGLES_DEGREES:
            matrix = itd_v14.rotation_matrix(
                np.deg2rad(angle_degrees)
            )

            plan = itd_v14.BilinearTransformPlan(
                coordinates,
                coordinates,
                matrix,
            )

            rotated_vx, rotated_vy = (
                plan.transform_vector(
                    base_vx,
                    base_vy,
                )
            )

            rotated_omega = (
                itd_v14.numerical_vorticity_with_boundary(
                    rotated_vx,
                    rotated_vy,
                    spacing,
                    boundary_mode="finite",
                )
            )

            expected_omega = (
                plan.transform_scalar(
                    base_omega
                )
            )

            error_field = (
                rotated_omega
                - expected_omega
            )

            rms_error = float(
                np.sqrt(
                    np.mean(
                        error_field[
                            comparison_mask
                        ] ** 2
                    )
                )
            )

            worst_error = max(
                worst_error,
                rms_error,
            )

        errors.append(worst_error)

        if previous_error is None:
            order_text = "—"
        else:
            order_text = (
                f"{convergence_order(previous_error, worst_error):.5f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{worst_error:19.6e} | "
            f"{order_text}"
        )

        previous_error = worst_error

    if not all(
        current < previous
        for previous, current in zip(
            errors,
            errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur d'équivariance de la "
            "vorticité ne décroît pas."
        )

    final_orders = (
        convergence_order(
            errors[-3],
            errors[-2],
        ),
        convergence_order(
            errors[-2],
            errors[-1],
        ),
    )

    if min(final_orders) < 1.0:
        raise RuntimeError(
            "La composition interpolation-dérivation "
            "ne converge pas suffisamment."
        )

    if (
        errors[-1]
        > FINAL_VORTICITY_EQUIVARIANCE_TOLERANCE
    ):
        raise RuntimeError(
            "L'erreur finale d'équivariance "
            "de la vorticité est trop élevée."
        )

    print(
        "Équivariance de la vorticité sous "
        "raffinement : VALIDÉE"
    )


def validate_signature_rotation_convergence() -> None:
    print()
    print(
        "=== CONVERGENCE DE LA SIGNATURE "
        "SOUS ROTATION ARBITRAIRE ==="
    )

    print(
        "grille | erreur analytique | "
        "erreur après interpolation"
    )

    analytic_errors: list[float] = []
    sampled_errors: list[float] = []

    for grid_size in SIGNATURE_GRID_SIZES:
        (
            coordinates,
            x,
            y,
            spacing,
        ) = build_grid(grid_size)

        cfg = Config(
            grid_size=grid_size,
            time_steps=41,
        )

        times = np.linspace(
            0.0,
            cfg.duration,
            cfg.time_steps,
            dtype=np.float64,
        )

        reference = extract_results(
            itd_v14.simulate(
                "compact_reference",
                compact_velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=compact_curvature,
                boundary_mode="finite",
            )
        )

        worst_analytic = 0.0
        worst_sampled = 0.0

        for angle_degrees in ANGLES_DEGREES:
            matrix = itd_v14.rotation_matrix(
                np.deg2rad(angle_degrees)
            )

            analytic_velocity = (
                itd_v14.transform_velocity_function(
                    compact_velocity,
                    matrix,
                )
            )

            analytic_curvature = (
                itd_v14.transform_scalar_function(
                    compact_curvature,
                    matrix,
                )
            )

            sampled_velocity = (
                itd_v14.make_sampled_transformed_velocity_function(
                    compact_velocity,
                    coordinates,
                    coordinates,
                    matrix,
                )
            )

            sampled_curvature = (
                itd_v14.make_sampled_transformed_scalar_function(
                    compact_curvature,
                    coordinates,
                    coordinates,
                    matrix,
                )
            )

            analytic_result = extract_results(
                itd_v14.simulate(
                    (
                        "compact_analytic_"
                        f"{angle_degrees:g}"
                    ),
                    analytic_velocity,
                    x,
                    y,
                    times,
                    spacing,
                    cfg,
                    curvature_function=analytic_curvature,
                    boundary_mode="finite",
                )
            )

            sampled_result = extract_results(
                itd_v14.simulate(
                    (
                        "compact_sampled_"
                        f"{angle_degrees:g}"
                    ),
                    sampled_velocity,
                    x,
                    y,
                    times,
                    spacing,
                    cfg,
                    curvature_function=sampled_curvature,
                    boundary_mode="finite",
                )
            )

            analytic_error = max(
                scaled_error(
                    analytic_result[key],
                    reference[key],
                )
                for key in reference
            )

            sampled_error = max(
                scaled_error(
                    sampled_result[key],
                    reference[key],
                )
                for key in reference
            )

            worst_analytic = max(
                worst_analytic,
                analytic_error,
            )

            worst_sampled = max(
                worst_sampled,
                sampled_error,
            )

        analytic_errors.append(
            worst_analytic
        )

        sampled_errors.append(
            worst_sampled
        )

        print(
            f"{grid_size:6d} | "
            f"{worst_analytic:17.6e} | "
            f"{worst_sampled:25.6e}"
        )

    if not all(
        current < previous
        for previous, current in zip(
            analytic_errors,
            analytic_errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur de rotation analytique "
            "de la signature ne décroît pas."
        )

    if not all(
        current < previous
        for previous, current in zip(
            sampled_errors,
            sampled_errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur de la signature interpolée "
            "ne décroît pas."
        )

    if (
        analytic_errors[-1]
        > FINAL_ANALYTIC_SIGNATURE_TOLERANCE
    ):
        raise RuntimeError(
            "L'erreur analytique finale de la "
            "signature est trop élevée."
        )

    if (
        sampled_errors[-1]
        > FINAL_SAMPLED_SIGNATURE_TOLERANCE
    ):
        raise RuntimeError(
            "L'erreur finale de la signature "
            "interpolée est trop élevée."
        )

    print(
        "Signature sous rotation arbitraire : "
        "VALIDÉE PAR CONVERGENCE"
    )


def validate_invalid_inputs() -> None:
    print()
    print(
        "=== REJET DES PARAMÈTRES INVALIDES ==="
    )

    for invalid_angle in (
        np.nan,
        np.inf,
        -np.inf,
        "rotation",
        None,
    ):
        try:
            itd_v14.rotation_matrix(
                invalid_angle
            )
        except ValueError as error:
            print(
                f"Angle {invalid_angle!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un angle invalide n'a pas été rejeté."
            )

    invalid_axes = (
        [0.0],
        [0.0, 1.0, 0.5],
        [0.0, 1.0, 2.1],
        [0.0, np.nan, 2.0],
        [[0.0, 1.0]],
    )

    for invalid_axis in invalid_axes:
        try:
            itd_v14.validate_uniform_axis_coordinates(
                invalid_axis,
                "test",
            )
        except ValueError as error:
            print(
                f"Axe {invalid_axis!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un axe invalide n'a pas été rejeté."
            )

    coordinates = np.linspace(
        -1.0,
        1.0,
        9,
        dtype=np.float64,
    )

    try:
        itd_v14.BilinearTransformPlan(
            coordinates,
            coordinates,
            (
                (1.0, 0.5),
                (0.0, 1.0),
            ),
        )
    except ValueError as error:
        print(
            "Matrice non orthogonale : "
            f"RÉUSSI — {error}"
        )
    else:
        raise RuntimeError(
            "Une matrice non orthogonale "
            "n'a pas été rejetée."
        )

    plan = itd_v14.BilinearTransformPlan(
        coordinates,
        coordinates,
        np.eye(2),
    )

    try:
        plan.interpolate(
            np.zeros(
                (8, 9),
                dtype=np.float64,
            )
        )
    except ValueError as error:
        print(
            "Forme de champ invalide : "
            f"RÉUSSI — {error}"
        )
    else:
        raise RuntimeError(
            "Une forme de champ invalide "
            "n'a pas été rejetée."
        )

    print(
        "Contrôle des paramètres V14 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DES ROTATIONS "
        "ARBITRAIRES — ITD V14 ==="
    )

    validate_v13_compatibility()
    validate_bilinear_interpolation()
    validate_vorticity_equivariance()
    validate_signature_rotation_convergence()
    validate_invalid_inputs()

    print()
    print(
        "Compatibilité V13 → V14          : VALIDÉE"
    )
    print(
        "Interpolation bilinéaire          : VALIDÉE"
    )
    print(
        "Rotations arbitraires analytiques : VALIDÉES"
    )
    print(
        "Rotations de champs échantillonnés: VALIDÉES"
    )
    print(
        "Erreur d'interpolation séparée    : VALIDÉE"
    )


if __name__ == "__main__":
    main()
