#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v14
import itd_v14_1
from compare_scenarios import (
    Config,
    coherent_vortex,
    curvature_field,
    multi_vortex_field,
)


MACHINE_TOLERANCE = 8.0e-13
SIGNATURE_TOLERANCE = 8.0e-13

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

D4_TRANSFORMATIONS = (
    (
        "identite",
        np.asarray(
            (
                (1.0, 0.0),
                (0.0, 1.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "rotation_90",
        np.asarray(
            (
                (0.0, -1.0),
                (1.0, 0.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "rotation_180",
        np.asarray(
            (
                (-1.0, 0.0),
                (0.0, -1.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "rotation_270",
        np.asarray(
            (
                (0.0, 1.0),
                (-1.0, 0.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "reflexion_x",
        np.asarray(
            (
                (1.0, 0.0),
                (0.0, -1.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "reflexion_y",
        np.asarray(
            (
                (-1.0, 0.0),
                (0.0, 1.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "reflexion_diagonale",
        np.asarray(
            (
                (0.0, 1.0),
                (1.0, 0.0),
            ),
            dtype=np.float64,
        ),
    ),
    (
        "reflexion_antidiagonale",
        np.asarray(
            (
                (0.0, -1.0),
                (-1.0, 0.0),
            ),
            dtype=np.float64,
        ),
    ),
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


def build_square_grid(
    grid_size: int,
    minimum: float = -2.0,
    maximum: float = 2.0,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
    coordinates = np.linspace(
        minimum,
        maximum,
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


def validate_v14_compatibility() -> None:
    cfg = Config(
        grid_size=65,
        time_steps=81,
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
        "=== COMPATIBILITÉ V14 → V14.1 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        reference = extract_results(
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

        candidate = extract_results(
            itd_v14_1.simulate(
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

    if maximum_error > MACHINE_TOLERANCE:
        raise RuntimeError(
            "La V14.1 modifie les résultats "
            "historiques de la V14."
        )

    print(
        "Compatibilité V14 → V14.1 : VALIDÉE"
    )


def validate_identity_bitwise() -> None:
    coordinates, _, _, _ = build_square_grid(
        65
    )

    rng = np.random.default_rng(
        141
    )

    scalar = rng.standard_normal(
        (65, 65)
    )

    vx = rng.standard_normal(
        (65, 65)
    )

    vy = rng.standard_normal(
        (65, 65)
    )

    plan = itd_v14_1.BilinearTransformPlan(
        coordinates,
        coordinates,
        np.eye(
            2,
            dtype=np.float64,
        ),
    )

    if not plan.uses_exact_node_map:
        raise RuntimeError(
            "L'identité n'a pas déclenché "
            "la permutation exacte."
        )

    transformed_scalar = (
        plan.transform_scalar(
            scalar
        )
    )

    transformed_vx, transformed_vy = (
        plan.transform_vector(
            vx,
            vy,
        )
    )

    print()
    print(
        "=== IDENTITÉ BIT À BIT ==="
    )

    print(
        "Scalaire :",
        np.array_equal(
            transformed_scalar,
            scalar,
        ),
    )

    print(
        "Vecteur x:",
        np.array_equal(
            transformed_vx,
            vx,
        ),
    )

    print(
        "Vecteur y:",
        np.array_equal(
            transformed_vy,
            vy,
        ),
    )

    if not np.array_equal(
        transformed_scalar,
        scalar,
    ):
        raise RuntimeError(
            "L'identité scalaire n'est pas "
            "exacte bit à bit."
        )

    if not np.array_equal(
        transformed_vx,
        vx,
    ):
        raise RuntimeError(
            "L'identité de vx n'est pas "
            "exacte bit à bit."
        )

    if not np.array_equal(
        transformed_vy,
        vy,
    ):
        raise RuntimeError(
            "L'identité de vy n'est pas "
            "exacte bit à bit."
        )

    print(
        "Identité bit à bit : VALIDÉE"
    )


def validate_d4_exact_roundtrip() -> None:
    coordinates, _, _, _ = build_square_grid(
        65
    )

    rng = np.random.default_rng(
        142
    )

    scalar = rng.standard_normal(
        (65, 65)
    )

    vx = rng.standard_normal(
        (65, 65)
    )

    vy = rng.standard_normal(
        (65, 65)
    )

    print()
    print(
        "=== GROUPE D4 : PERMUTATION ET INVERSE ==="
    )

    for name, matrix in D4_TRANSFORMATIONS:
        direct = itd_v14_1.BilinearTransformPlan(
            coordinates,
            coordinates,
            matrix,
        )

        inverse = itd_v14_1.BilinearTransformPlan(
            coordinates,
            coordinates,
            matrix.T,
        )

        if not direct.uses_exact_node_map:
            raise RuntimeError(
                f"{name} n'utilise pas le "
                "chemin exact."
            )

        if not inverse.uses_exact_node_map:
            raise RuntimeError(
                f"L'inverse de {name} n'utilise "
                "pas le chemin exact."
            )

        transformed_scalar = (
            direct.transform_scalar(
                scalar
            )
        )

        reconstructed_scalar = (
            inverse.transform_scalar(
                transformed_scalar
            )
        )

        transformed_vx, transformed_vy = (
            direct.transform_vector(
                vx,
                vy,
            )
        )

        reconstructed_vx, reconstructed_vy = (
            inverse.transform_vector(
                transformed_vx,
                transformed_vy,
            )
        )

        scalar_exact = np.array_equal(
            reconstructed_scalar,
            scalar,
        )

        vx_exact = np.array_equal(
            reconstructed_vx,
            vx,
        )

        vy_exact = np.array_equal(
            reconstructed_vy,
            vy,
        )

        print(
            f"{name:24s}: "
            f"scalaire={scalar_exact}  "
            f"vx={vx_exact}  "
            f"vy={vy_exact}"
        )

        if not (
            scalar_exact
            and vx_exact
            and vy_exact
        ):
            raise RuntimeError(
                f"La transformation {name} suivie "
                "de son inverse n'est pas exacte."
            )

    print(
        "Réversibilité bit à bit du groupe D4 : "
        "VALIDÉE"
    )


def bilinear_scalar(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    return (
        1.25
        - 0.70 * x
        + 0.45 * y
        + 0.30 * x * y
    )


def affine_vector(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    vx = (
        0.40
        + 0.75 * x
        - 0.20 * y
    )

    vy = (
        -0.35
        + 0.15 * x
        + 0.65 * y
    )

    return vx, vy


def validate_reproduction_space() -> None:
    coordinates, x, y, _ = build_square_grid(
        97,
        minimum=-3.0,
        maximum=3.0,
    )

    sampled_scalar = bilinear_scalar(
        x,
        y,
    )

    sampled_vx, sampled_vy = affine_vector(
        x,
        y,
    )

    angles = (
        13.0,
        37.0,
        71.0,
    )

    print()
    print(
        "=== ESPACE EXACT DE L'INTERPOLATEUR ==="
    )

    maximum_scalar_error = 0.0
    maximum_vector_error = 0.0

    for angle_degrees in angles:
        matrix = itd_v14_1.rotation_matrix(
            np.deg2rad(angle_degrees)
        )

        plan = itd_v14_1.BilinearTransformPlan(
            coordinates,
            coordinates,
            matrix,
        )

        if plan.uses_exact_node_map:
            raise RuntimeError(
                "Une rotation arbitraire a été "
                "classée à tort comme permutation."
            )

        interpolated_scalar = (
            plan.transform_scalar(
                sampled_scalar
            )
        )

        interpolated_vx, interpolated_vy = (
            plan.transform_vector(
                sampled_vx,
                sampled_vy,
            )
        )

        expected_scalar = bilinear_scalar(
            plan.source_x,
            plan.source_y,
        )

        source_vx, source_vy = affine_vector(
            plan.source_x,
            plan.source_y,
        )

        expected_vx = (
            matrix[0, 0] * source_vx
            + matrix[0, 1] * source_vy
        )

        expected_vy = (
            matrix[1, 0] * source_vx
            + matrix[1, 1] * source_vy
        )

        mask = plan.inside_mask

        scalar_error = float(
            np.max(
                np.abs(
                    interpolated_scalar[mask]
                    - expected_scalar[mask]
                )
            )
        )

        vector_error = float(
            np.max(
                np.sqrt(
                    (
                        interpolated_vx[mask]
                        - expected_vx[mask]
                    ) ** 2
                    + (
                        interpolated_vy[mask]
                        - expected_vy[mask]
                    ) ** 2
                )
            )
        )

        maximum_scalar_error = max(
            maximum_scalar_error,
            scalar_error,
        )

        maximum_vector_error = max(
            maximum_vector_error,
            vector_error,
        )

        print(
            f"{angle_degrees:6.1f} degrés : "
            f"scalaire={scalar_error:.6e}  "
            f"vecteur={vector_error:.6e}"
        )

    if maximum_scalar_error > MACHINE_TOLERANCE:
        raise RuntimeError(
            "L'interpolation ne reproduit pas "
            "correctement les champs bilinéaires."
        )

    if maximum_vector_error > MACHINE_TOLERANCE:
        raise RuntimeError(
            "L'interpolation ne reproduit pas "
            "correctement les champs vectoriels "
            "affines."
        )

    print(
        "Reproduction à l'arrondi machine : VALIDÉE"
    )


def validate_linearity() -> None:
    coordinates, x, y, _ = build_square_grid(
        81,
        minimum=-2.5,
        maximum=2.5,
    )

    matrix = itd_v14_1.rotation_matrix(
        np.deg2rad(37.0)
    )

    plan = itd_v14_1.BilinearTransformPlan(
        coordinates,
        coordinates,
        matrix,
    )

    first = (
        np.sin(0.7 * x)
        * np.cos(0.4 * y)
    )

    second = (
        np.cos(0.3 * x - 0.8 * y)
    )

    alpha = 1.75
    beta = -0.60

    left = plan.interpolate(
        alpha * first
        + beta * second
    )

    right = (
        alpha * plan.interpolate(first)
        + beta * plan.interpolate(second)
    )

    mask = plan.inside_mask

    error = float(
        np.max(
            np.abs(
                left[mask]
                - right[mask]
            )
        )
    )

    print()
    print(
        "=== LINÉARITÉ DE L'INTERPOLATION ==="
    )
    print(
        "Erreur maximale :",
        f"{error:.6e}",
    )

    if error > MACHINE_TOLERANCE:
        raise RuntimeError(
            "La linéarité de l'interpolation "
            "n'est pas respectée à l'arrondi machine."
        )

    print(
        "Linéarité : VALIDÉE"
    )


def validate_exact_signature_d4() -> None:
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

    print()
    print(
        "=== INVARIANCE EXACTE DE LA SIGNATURE D4 ==="
    )

    global_maximum = 0.0

    for scenario_name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        reference = extract_results(
            itd_v14_1.simulate(
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

        scenario_maximum = 0.0

        for transformation_name, matrix in (
            D4_TRANSFORMATIONS
        ):
            transformed_velocity = (
                itd_v14_1.make_sampled_transformed_velocity_function(
                    velocity_function,
                    coordinates,
                    coordinates,
                    matrix,
                )
            )

            transformed_curvature = (
                itd_v14_1.make_sampled_transformed_scalar_function(
                    curvature_field,
                    coordinates,
                    coordinates,
                    matrix,
                )
            )

            candidate = extract_results(
                itd_v14_1.simulate(
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

            error = max(
                scaled_error(
                    candidate[key],
                    reference[key],
                )
                for key in reference
            )

            scenario_maximum = max(
                scenario_maximum,
                error,
            )

            global_maximum = max(
                global_maximum,
                error,
            )

        print(
            f"{scenario_name:24s}: "
            f"erreur maximale={scenario_maximum:.6e}"
        )

    if global_maximum > SIGNATURE_TOLERANCE:
        raise RuntimeError(
            "La signature n'est pas invariante "
            "à l'arrondi machine sous le groupe D4."
        )

    print(
        "Signature D4 après permutation exacte : "
        "VALIDÉE"
    )


def validate_arbitrary_rotation_classification() -> None:
    coordinates, _, _, _ = build_square_grid(
        65
    )

    plan = itd_v14_1.BilinearTransformPlan(
        coordinates,
        coordinates,
        itd_v14_1.rotation_matrix(
            np.deg2rad(37.0)
        ),
    )

    print()
    print(
        "=== CLASSIFICATION D'UNE ROTATION ARBITRAIRE ==="
    )
    print(
        "Permutation exacte détectée :",
        plan.uses_exact_node_map,
    )

    if plan.uses_exact_node_map:
        raise RuntimeError(
            "Une rotation de 37 degrés ne doit "
            "pas être classée comme permutation "
            "exacte des nœuds."
        )

    print(
        "Séparation permutation/interpolation : "
        "VALIDÉE"
    )


def main() -> None:
    print(
        "=== VALIDATION D'EXACTITUDE "
        "DE L'INTERPOLATION — ITD V14.1 ==="
    )

    validate_v14_compatibility()
    validate_identity_bitwise()
    validate_d4_exact_roundtrip()
    validate_reproduction_space()
    validate_linearity()
    validate_exact_signature_d4()
    validate_arbitrary_rotation_classification()

    print()
    print(
        "Compatibilité V14 → V14.1        : VALIDÉE"
    )
    print(
        "Identité bit à bit               : VALIDÉE"
    )
    print(
        "Symétries D4 bit à bit           : VALIDÉES"
    )
    print(
        "Réversibilité D4 bit à bit       : VALIDÉE"
    )
    print(
        "Champs bilinéaires               : VALIDÉS"
    )
    print(
        "Champs vectoriels affines        : VALIDÉS"
    )
    print(
        "Linéarité à l'arrondi machine    : VALIDÉE"
    )
    print(
        "Signature D4 après échantillonnage: VALIDÉE"
    )


if __name__ == "__main__":
    main()
