#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)
from itd_v6 import simulate


FloatArray = np.ndarray
VelocityFunction = Callable[
    [FloatArray, FloatArray, float],
    tuple[FloatArray, FloatArray],
]

SCALES = (0.25, 0.5, 1.0, 2.0, 4.0)
GRID_SIZE = 161
TIME_STEPS = 401

INTENSITY_TOLERANCE = 2.0e-11
STRUCTURE_TOLERANCE = 2.0e-11
COUPLED_TOLERANCE = 2.0e-11


def scaled_velocity(
    velocity_function: VelocityFunction,
    scale: float,
) -> VelocityFunction:
    def field(
        x: FloatArray,
        y: FloatArray,
        time: float,
    ) -> tuple[FloatArray, FloatArray]:
        vx, vy = velocity_function(
            x,
            y,
            time,
        )

        return scale * vx, scale * vy

    return field


def relative_error(
    value: float,
    expected: float,
) -> float:
    if abs(expected) < 1.0e-15:
        return abs(value - expected)

    return abs(value - expected) / abs(expected)


def run_scenario(
    scenario_name: str,
    velocity_function: VelocityFunction,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> None:
    results: dict[float, dict[str, float]] = {}

    for scale in SCALES:
        result = simulate(
            f"{scenario_name}_scale_{scale}",
            scaled_velocity(
                velocity_function,
                scale,
            ),
            x,
            y,
            times,
            spacing,
            cfg,
        )

        results[scale] = {
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

    reference = results[1.0]

    print()
    print("Scénario :", scenario_name)
    print(
        "échelle | intensité       | erreur loi λ² | "
        "structure        | erreur structure | "
        "déformation"
    )

    maximum_intensity_error = 0.0
    maximum_structure_error = 0.0
    maximum_coupled_error = 0.0
    maximum_deformation_error = 0.0

    for scale in SCALES:
        metrics = results[scale]

        expected_intensity = (
            scale**2
            * reference["intensity"]
        )

        expected_coupled = (
            scale**2
            * reference["coupled"]
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
            f"{scale:7.2f} | "
            f'{metrics["intensity"]:15.12f} | '
            f"{intensity_error:13.6e} | "
            f'{metrics["structure"]:15.12f} | '
            f"{structure_error:15.6e} | "
            f'{metrics["deformation"]:.12f}'
        )

    print()
    print(
        "Erreur maximale intensité     :",
        f"{maximum_intensity_error:.6e}",
    )
    print(
        "Erreur maximale structure     :",
        f"{maximum_structure_error:.6e}",
    )
    print(
        "Erreur maximale diagnostic    :",
        f"{maximum_coupled_error:.6e}",
    )
    print(
        "Erreur maximale déformation   :",
        f"{maximum_deformation_error:.6e}",
    )

    if maximum_intensity_error > INTENSITY_TOLERANCE:
        raise RuntimeError(
            "Échec de la loi quadratique d'intensité."
        )

    if maximum_structure_error > STRUCTURE_TOLERANCE:
        raise RuntimeError(
            "L'indice structurel dépend artificiellement "
            "de l'amplitude."
        )

    if maximum_coupled_error > COUPLED_TOLERANCE:
        raise RuntimeError(
            "Le diagnostic couplé ne suit pas la loi λ²."
        )

    if maximum_deformation_error > STRUCTURE_TOLERANCE:
        raise RuntimeError(
            "La déformation normalisée dépend "
            "artificiellement de l'amplitude."
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

    print("=== VALIDATION DES LOIS D'ÉCHELLE — ITD V6 ===")
    print(
        "Grille          :",
        f"{GRID_SIZE} × {GRID_SIZE}",
    )
    print(
        "Instants        :",
        TIME_STEPS,
    )
    print(
        "Échelles testées:",
        SCALES,
    )

    run_scenario(
        "vortex_coherent",
        coherent_vortex,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    run_scenario(
        "multi_vortex_complexe",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    print()
    print("Loi I(λv) = λ² I(v)       : VALIDÉE")
    print("Invariance de C(λv)       : VALIDÉE")
    print("Invariance temporelle     : VALIDÉE")


if __name__ == "__main__":
    main()
