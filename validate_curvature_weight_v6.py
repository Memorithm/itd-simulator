#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable

import numpy as np

import itd_v6
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

GRID_SIZE = 161
TIME_STEPS = 401
CURVATURE_VALUES = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)

RELATIVE_TOLERANCE = 5.0e-12
STRUCTURE_TOLERANCE = 5.0e-12


def constant_curvature(
    curvature_value: float,
) -> Callable[
    [FloatArray, FloatArray, float],
    FloatArray,
]:
    def field(
        x: FloatArray,
        y: FloatArray,
        time: float,
    ) -> FloatArray:
        del y, time

        return np.full_like(
            x,
            curvature_value,
            dtype=np.float64,
        )

    return field


def relative_error(
    value: float,
    expected: float,
) -> float:
    if abs(expected) < 1.0e-15:
        return abs(value - expected)

    return abs(value - expected) / abs(expected)


def simulate_with_curvature(
    scenario_name: str,
    velocity_function: VelocityFunction,
    curvature_value: float,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> dict[str, float]:
    original_curvature_field = itd_v6.curvature_field

    try:
        itd_v6.curvature_field = constant_curvature(
            curvature_value
        )

        result = itd_v6.simulate(
            scenario_name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )
    finally:
        itd_v6.curvature_field = original_curvature_field

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


def validate_scenario(
    scenario_name: str,
    velocity_function: VelocityFunction,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> None:
    results = {
        curvature_value: simulate_with_curvature(
            scenario_name,
            velocity_function,
            curvature_value,
            x,
            y,
            times,
            spacing,
            cfg,
        )
        for curvature_value in CURVATURE_VALUES
    }

    reference = results[0.0]

    print()
    print("Scénario :", scenario_name)
    print(
        "R constant | facteur attendu | intensité       | "
        "erreur loi exp | structure        | erreur C"
    )

    maximum_intensity_error = 0.0
    maximum_structure_error = 0.0
    maximum_coupled_error = 0.0
    maximum_deformation_error = 0.0

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

        maximum_intensity_error = max(
            maximum_intensity_error,
            intensity_error,
        )

        maximum_structure_error = max(
            maximum_structure_error,
            structure_error,
        )

        maximum_coupled_error = max(
            maximum_coupled_error,
            coupled_error,
        )

        maximum_deformation_error = max(
            maximum_deformation_error,
            deformation_error,
        )

        print(
            f"{curvature_value:10.3f} | "
            f"{expected_factor:15.12f} | "
            f'{metrics["intensity"]:15.12f} | '
            f"{intensity_error:14.6e} | "
            f'{metrics["structure"]:15.12f} | '
            f"{structure_error:10.3e}"
        )

    print()
    print(
        "Erreur maximale intensité   :",
        f"{maximum_intensity_error:.6e}",
    )
    print(
        "Erreur maximale structure   :",
        f"{maximum_structure_error:.6e}",
    )
    print(
        "Erreur maximale diagnostic  :",
        f"{maximum_coupled_error:.6e}",
    )
    print(
        "Erreur maximale déformation :",
        f"{maximum_deformation_error:.6e}",
    )

    if maximum_intensity_error > RELATIVE_TOLERANCE:
        raise RuntimeError(
            "Le facteur de courbure ne suit pas "
            "la loi exponentielle attendue."
        )

    if maximum_structure_error > STRUCTURE_TOLERANCE:
        raise RuntimeError(
            "La structure dépend artificiellement "
            "d'une courbure constante."
        )

    if maximum_coupled_error > RELATIVE_TOLERANCE:
        raise RuntimeError(
            "Le diagnostic couplé ne suit pas "
            "la pondération exponentielle."
        )

    if maximum_deformation_error > STRUCTURE_TOLERANCE:
        raise RuntimeError(
            "La déformation dépend artificiellement "
            "d'une courbure constante."
        )

    print("Validation du scénario : RÉUSSIE")


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

    print(
        "=== VALIDATION DU FACTEUR DE COURBURE — ITD V6 ==="
    )
    print(
        "Longueur caractéristique :",
        cfg.characteristic_length,
    )
    print(
        "Loi attendue             :",
        "I(R) = exp(ell² R) I(0)",
    )

    validate_scenario(
        "vortex_coherent",
        coherent_vortex,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    validate_scenario(
        "multi_vortex_complexe",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    print()
    print(
        "Pondération exponentielle de R : VALIDÉE"
    )
    print(
        "Indépendance structure/courbure : VALIDÉE"
    )


if __name__ == "__main__":
    main()
