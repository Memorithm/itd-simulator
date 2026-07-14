#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable

import numpy as np

import itd_v6
import itd_v7
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


FloatArray = np.ndarray
VelocityFunction = Callable[
    [FloatArray, FloatArray, float],
    tuple[FloatArray, FloatArray],
]
CurvatureFunction = Callable[
    [FloatArray, FloatArray, float],
    FloatArray,
]

GRID_SIZE = 161
TIME_STEPS = 401
CURVATURE_VALUES = (
    -2.0,
    -1.0,
    -0.5,
    0.0,
    0.5,
    1.0,
    2.0,
)

TOLERANCE = 5.0e-12


def constant_curvature(
    value: float,
) -> CurvatureFunction:
    def field(
        x: FloatArray,
        y: FloatArray,
        time: float,
    ) -> FloatArray:
        del y, time

        return np.full_like(
            x,
            value,
            dtype=np.float64,
        )

    return field


def relative_error(
    value: float,
    reference: float,
) -> float:
    if abs(reference) < 1.0e-15:
        return abs(value - reference)

    return abs(value - reference) / abs(reference)


def extract_metrics(
    result: dict[str, object],
) -> dict[str, float]:
    return {
        "intensity": float(
            result["intensity_index"]
        ),
        "structure": float(
            result["structure_index"]
        ),
        "coupled": float(
            result["coupled_index"]
        ),
        "deformation": float(
            result["temporal_deformation_index"]
        ),
    }


def validate_backward_compatibility(
    name: str,
    velocity_function: VelocityFunction,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> None:
    old_result = extract_metrics(
        itd_v6.simulate(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )
    )

    new_result = extract_metrics(
        itd_v7.simulate(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )
    )

    print()
    print(
        "Compatibilité V6 → V7 :",
        name,
    )

    maximum_error = 0.0

    for metric_name in (
        "intensity",
        "structure",
        "coupled",
        "deformation",
    ):
        error = relative_error(
            new_result[metric_name],
            old_result[metric_name],
        )

        maximum_error = max(
            maximum_error,
            error,
        )

        print(
            f"{metric_name:12s}: "
            f"V6={old_result[metric_name]:.15f}  "
            f"V7={new_result[metric_name]:.15f}  "
            f"erreur={error:.3e}"
        )

    if maximum_error > TOLERANCE:
        raise RuntimeError(
            "La V7 n'est pas compatible avec "
            "le comportement par défaut de la V6."
        )

    print("Compatibilité par défaut : RÉUSSIE")


def validate_constant_curvature(
    name: str,
    velocity_function: VelocityFunction,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> None:
    results: dict[float, dict[str, float]] = {}

    for curvature_value in CURVATURE_VALUES:
        result = itd_v7.simulate(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=constant_curvature(
                curvature_value
            ),
        )

        results[curvature_value] = extract_metrics(
            result
        )

    reference = results[0.0]

    print()
    print(
        "Injection de courbure :",
        name,
    )
    print(
        "R        | facteur attendu | intensité       | "
        "erreur I     | structure        | erreur C"
    )

    maximum_error = 0.0

    for curvature_value in CURVATURE_VALUES:
        metrics = results[curvature_value]

        expected_factor = np.exp(
            cfg.characteristic_length**2
            * curvature_value
        )

        expected_intensity = (
            reference["intensity"]
            * expected_factor
        )

        expected_coupled = (
            reference["coupled"]
            * expected_factor
        )

        intensity_error = relative_error(
            metrics["intensity"],
            expected_intensity,
        )

        structure_error = relative_error(
            metrics["structure"],
            reference["structure"],
        )

        coupled_error = relative_error(
            metrics["coupled"],
            expected_coupled,
        )

        deformation_error = relative_error(
            metrics["deformation"],
            reference["deformation"],
        )

        maximum_error = max(
            maximum_error,
            intensity_error,
            structure_error,
            coupled_error,
            deformation_error,
        )

        print(
            f"{curvature_value:8.3f} | "
            f"{expected_factor:15.12f} | "
            f'{metrics["intensity"]:15.12f} | '
            f"{intensity_error:11.3e} | "
            f'{metrics["structure"]:15.12f} | '
            f"{structure_error:11.3e}"
        )

    if maximum_error > TOLERANCE:
        raise RuntimeError(
            "Échec de validation du champ "
            "de courbure injecté."
        )

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )
    print("Injection explicite : RÉUSSIE")


def validate_rejections(
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> None:
    def wrong_shape(
        x_value: FloatArray,
        y_value: FloatArray,
        time: float,
    ) -> FloatArray:
        del y_value, time
        return np.zeros(
            (x_value.shape[0] - 1, x_value.shape[1]),
            dtype=np.float64,
        )

    def non_finite(
        x_value: FloatArray,
        y_value: FloatArray,
        time: float,
    ) -> FloatArray:
        del y_value, time
        result = np.zeros_like(x_value)
        result[0, 0] = np.nan
        return result

    for label, invalid_function in (
        ("forme incorrecte", wrong_shape),
        ("valeur non finie", non_finite),
    ):
        try:
            itd_v7.simulate(
                "validation_erreur",
                coherent_vortex,
                x,
                y,
                times[:2],
                spacing,
                cfg,
                curvature_function=invalid_function,
            )
        except ValueError as error:
            print(
                f"Rejet {label:16s}: RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                f"Le cas invalide « {label} » "
                "n'a pas été rejeté."
            )


def main() -> None:
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

    spacing = float(
        coordinates[1] - coordinates[0]
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    scenarios = (
        (
            "vortex_coherent",
            coherent_vortex,
        ),
        (
            "multi_vortex_complexe",
            multi_vortex_field,
        ),
    )

    print(
        "=== VALIDATION DE L'INJECTION "
        "DE COURBURE — ITD V7 ==="
    )

    for name, velocity_function in scenarios:
        validate_backward_compatibility(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )

        validate_constant_curvature(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )

    print()
    print("=== VALIDATION DES ERREURS D'ENTRÉE ===")

    validate_rejections(
        x,
        y,
        times,
        spacing,
        cfg,
    )

    print()
    print(
        "Compatibilité V6 → V7       : VALIDÉE"
    )
    print(
        "Injection de la courbure    : VALIDÉE"
    )
    print(
        "Contrôle des champs invalides: VALIDÉ"
    )


if __name__ == "__main__":
    main()
