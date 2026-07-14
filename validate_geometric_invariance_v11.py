#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v10
import itd_v11
from compare_scenarios import (
    Config,
    coherent_vortex,
    curvature_field,
    multi_vortex_field,
    numerical_vorticity,
)


GRID_SIZE = 161
TIME_STEPS = 201

INVARIANCE_TOLERANCE = 2.0e-10
VORTICITY_TOLERANCE = 2.0e-11

TRANSFORMATIONS = (
    (
        "identite",
        np.asarray(
            (
                (1.0, 0.0),
                (0.0, 1.0),
            )
        ),
    ),
    (
        "rotation_90",
        np.asarray(
            (
                (0.0, -1.0),
                (1.0, 0.0),
            )
        ),
    ),
    (
        "rotation_180",
        np.asarray(
            (
                (-1.0, 0.0),
                (0.0, -1.0),
            )
        ),
    ),
    (
        "rotation_270",
        np.asarray(
            (
                (0.0, 1.0),
                (-1.0, 0.0),
            )
        ),
    ),
    (
        "reflexion_x",
        np.asarray(
            (
                (1.0, 0.0),
                (0.0, -1.0),
            )
        ),
    ),
    (
        "reflexion_y",
        np.asarray(
            (
                (-1.0, 0.0),
                (0.0, 1.0),
            )
        ),
    ),
    (
        "reflexion_diagonale",
        np.asarray(
            (
                (0.0, 1.0),
                (1.0, 0.0),
            )
        ),
    ),
    (
        "reflexion_antidiagonale",
        np.asarray(
            (
                (0.0, -1.0),
                (-1.0, 0.0),
            )
        ),
    ),
)

SCALAR_METRICS = (
    "intensity_index",
    "structure_index",
    "coupled_index",
    "temporal_deformation_index",
)

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def build_environment() -> tuple[
    Config,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
    cfg = Config(
        grid_size=GRID_SIZE,
        time_steps=TIME_STEPS,
    )

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        dtype=np.float64,
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

    spacing = float(
        coordinates[1] - coordinates[0]
    )

    return cfg, x, y, times, spacing


def extract_signature(
    result: dict[str, object],
) -> dict[str, float]:
    components = {
        str(name): float(value)
        for name, value in dict(
            result["component_indices"]
        ).items()
    }

    extracted = {
        metric: float(result[metric])
        for metric in SCALAR_METRICS
    }

    for component in COMPONENTS:
        extracted[
            f"component:{component}"
        ] = components[component]

    return extracted


def validate_v10_compatibility(
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    times: np.ndarray,
    spacing: float,
) -> None:
    print(
        "=== COMPATIBILITÉ V10 → V11 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        old = extract_signature(
            itd_v10.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        new = extract_signature(
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

        scenario_error = max(
            scaled_error(
                new[key],
                old[key],
            )
            for key in old
        )

        maximum_error = max(
            maximum_error,
            scenario_error,
        )

        print(
            f"{name:24s}: "
            f"erreur maximale={scenario_error:.6e}"
        )

    if maximum_error > INVARIANCE_TOLERANCE:
        raise RuntimeError(
            "La V11 n'est pas compatible avec la V10."
        )

    print(
        "Compatibilité V10 → V11 : RÉUSSIE"
    )


def validate_vorticity_orientation(
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
) -> None:
    print()
    print(
        "=== ORACLE DU SIGNE DE LA VORTICITÉ ==="
    )

    time = 2.3

    base_vx, base_vy = coherent_vortex(
        x,
        y,
        time,
    )

    base_omega = numerical_vorticity(
        base_vx,
        base_vy,
        spacing,
    )

    maximum_error = 0.0

    for name, matrix in TRANSFORMATIONS:
        transformed_velocity = (
            itd_v11.transform_velocity_function(
                coherent_vortex,
                matrix,
            )
        )

        transformed_vx, transformed_vy = (
            transformed_velocity(
                x,
                y,
                time,
            )
        )

        transformed_omega = numerical_vorticity(
            transformed_vx,
            transformed_vy,
            spacing,
        )

        determinant = float(
            np.linalg.det(matrix)
        )

        expected = determinant * base_omega

        error = float(
            np.max(
                np.abs(
                    transformed_omega
                    - expected
                )
            )
        )

        maximum_error = max(
            maximum_error,
            error,
        )

        print(
            f"{name:24s} "
            f"det={determinant:+.0f}  "
            f"erreur ω={error:.6e}"
        )

    if maximum_error > VORTICITY_TOLERANCE:
        raise RuntimeError(
            "La loi de transformation de la "
            "vorticité n'est pas respectée."
        )

    print(
        "Transformation pseudoscalaire de ω : RÉUSSIE"
    )


def validate_scenario(
    scenario_name: str,
    velocity_function,
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    times: np.ndarray,
    spacing: float,
) -> None:
    baseline = extract_signature(
        itd_v11.simulate(
            scenario_name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=curvature_field,
        )
    )

    print()
    print(
        "=== INVARIANCE GÉOMÉTRIQUE :",
        scenario_name,
        "===",
    )

    print(
        "transformation           | det | "
        "erreur maximale"
    )

    global_maximum = 0.0

    for transformation_name, matrix in TRANSFORMATIONS:
        transformed_velocity = (
            itd_v11.transform_velocity_function(
                velocity_function,
                matrix,
            )
        )

        transformed_curvature = (
            itd_v11.transform_scalar_function(
                curvature_field,
                matrix,
            )
        )

        result = extract_signature(
            itd_v11.simulate(
                (
                    f"{scenario_name}_"
                    f"{transformation_name}"
                ),
                transformed_velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=(
                    transformed_curvature
                ),
            )
        )

        metric_errors = {
            key: scaled_error(
                result[key],
                baseline[key],
            )
            for key in baseline
        }

        maximum_error = max(
            metric_errors.values()
        )

        global_maximum = max(
            global_maximum,
            maximum_error,
        )

        determinant = float(
            np.linalg.det(matrix)
        )

        print(
            f"{transformation_name:24s} | "
            f"{determinant:+.0f}  | "
            f"{maximum_error:.6e}"
        )

        if maximum_error > INVARIANCE_TOLERANCE:
            worst_metric = max(
                metric_errors,
                key=metric_errors.get,
            )

            raise RuntimeError(
                "Échec d'invariance pour "
                f"{scenario_name}, "
                f"{transformation_name}, "
                f"métrique {worst_metric}, "
                f"erreur {maximum_error:.6e}."
            )

    print(
        "Erreur maximale du scénario :",
        f"{global_maximum:.6e}",
    )
    print(
        "Invariance du scénario     : RÉUSSIE"
    )


def validate_invalid_matrices() -> None:
    print()
    print(
        "=== REJET DES MATRICES INVALIDES ==="
    )

    invalid_matrices = (
        np.eye(3),
        np.asarray(
            (
                (1.0, 1.0),
                (0.0, 1.0),
            )
        ),
        np.asarray(
            (
                (1.0, 0.0),
                (0.0, 2.0),
            )
        ),
        np.asarray(
            (
                (1.0, np.nan),
                (0.0, 1.0),
            )
        ),
    )

    for matrix in invalid_matrices:
        try:
            itd_v11.validate_orthogonal_matrix(
                matrix
            )
        except ValueError as error:
            print(
                "Rejet",
                repr(matrix.tolist()),
                "— RÉUSSI :",
                error,
            )
        else:
            raise RuntimeError(
                "Une matrice non orthogonale "
                "n'a pas été rejetée."
            )

    print(
        "Contrôle des matrices invalides : RÉUSSI"
    )


def main() -> None:
    cfg, x, y, times, spacing = (
        build_environment()
    )

    print(
        "=== VALIDATION GÉOMÉTRIQUE — ITD V11 ==="
    )

    validate_v10_compatibility(
        cfg,
        x,
        y,
        times,
        spacing,
    )

    validate_vorticity_orientation(
        x,
        y,
        spacing,
    )

    validate_scenario(
        "vortex_coherent",
        coherent_vortex,
        cfg,
        x,
        y,
        times,
        spacing,
    )

    validate_scenario(
        "multi_vortex_complexe",
        multi_vortex_field,
        cfg,
        x,
        y,
        times,
        spacing,
    )

    validate_invalid_matrices()

    print()
    print(
        "Compatibilité V10 → V11      : VALIDÉE"
    )
    print(
        "Rotations du système complet : VALIDÉES"
    )
    print(
        "Réflexions du système complet: VALIDÉES"
    )
    print(
        "Orientation de la vorticité  : VALIDÉE"
    )


if __name__ == "__main__":
    main()
