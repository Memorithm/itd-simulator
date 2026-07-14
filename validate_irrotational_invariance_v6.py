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

GRID_SIZE = 161
TIME_STEPS = 401

RELATIVE_TOLERANCE = 2.0e-10
ABSOLUTE_TOLERANCE = 2.0e-12


def uniform_translation(
    base_field: VelocityFunction,
) -> VelocityFunction:
    """
    Ajoute une translation uniforme dépendant du temps.

    Son rotationnel est exactement nul :
        curl(c(t)) = 0.
    """
    def transformed(
        x: FloatArray,
        y: FloatArray,
        time: float,
    ) -> tuple[FloatArray, FloatArray]:
        vx, vy = base_field(x, y, time)

        translation_x = (
            2.5 * np.sin(0.37 * time)
            + 0.8 * np.cos(0.91 * time)
        )

        translation_y = (
            -1.7 * np.cos(0.43 * time)
            + 0.6 * np.sin(0.79 * time)
        )

        return (
            vx + translation_x,
            vy + translation_y,
        )

    return transformed


def add_potential_flow(
    base_field: VelocityFunction,
) -> VelocityFunction:
    """
    Ajoute le gradient d'un potentiel polynomial :

        phi = A(t) [
            0.30 x²
            - 0.20 y²
            + 0.15 xy
            + 0.04 x³
            - 0.03 y³
        ]

    Par construction :
        curl(grad(phi)) = 0.
    """
    def transformed(
        x: FloatArray,
        y: FloatArray,
        time: float,
    ) -> tuple[FloatArray, FloatArray]:
        vx, vy = base_field(x, y, time)

        amplitude = (
            1.2
            + 0.4 * np.sin(0.53 * time)
        )

        gradient_x = amplitude * (
            0.60 * x
            + 0.15 * y
            + 0.12 * x**2
        )

        gradient_y = amplitude * (
            -0.40 * y
            + 0.15 * x
            - 0.09 * y**2
        )

        return (
            vx + gradient_x,
            vy + gradient_y,
        )

    return transformed


def relative_error(
    value: float,
    reference: float,
) -> float:
    if abs(reference) < ABSOLUTE_TOLERANCE:
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


def run_case(
    scenario_name: str,
    base_field: VelocityFunction,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> None:
    fields = (
        ("original", base_field),
        (
            "translation_uniforme",
            uniform_translation(base_field),
        ),
        (
            "flux_potentiel",
            add_potential_flow(base_field),
        ),
    )

    results: dict[str, dict[str, float]] = {}

    for transformation_name, velocity_field in fields:
        result = simulate(
            f"{scenario_name}_{transformation_name}",
            velocity_field,
            x,
            y,
            times,
            spacing,
            cfg,
        )

        results[transformation_name] = extract_metrics(
            result
        )

    reference = results["original"]

    print()
    print("Scénario :", scenario_name)
    print(
        "transformation       | intensité       | erreur I     | "
        "structure        | erreur C     | déformation     | erreur D"
    )

    maximum_error = 0.0

    for transformation_name, _ in fields:
        metrics = results[transformation_name]

        intensity_error = relative_error(
            metrics["intensity"],
            reference["intensity"],
        )

        structure_error = relative_error(
            metrics["structure"],
            reference["structure"],
        )

        coupled_error = relative_error(
            metrics["coupled"],
            reference["coupled"],
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
            f"{transformation_name:20s} | "
            f'{metrics["intensity"]:15.12f} | '
            f"{intensity_error:11.4e} | "
            f'{metrics["structure"]:15.12f} | '
            f"{structure_error:11.4e} | "
            f'{metrics["deformation"]:15.12f} | '
            f"{deformation_error:11.4e}"
        )

    print(
        "Erreur relative maximale :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > RELATIVE_TOLERANCE:
        raise RuntimeError(
            "L'indice varie après l'ajout "
            "d'un champ irrotationnel."
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
        "=== INVARIANCE AUX CHAMPS "
        "IRROTATIONNELS — ITD V6 ==="
    )
    print(
        "Grille   :",
        f"{GRID_SIZE} × {GRID_SIZE}",
    )
    print(
        "Instants :",
        TIME_STEPS,
    )

    run_case(
        "vortex_coherent",
        coherent_vortex,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    run_case(
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
        "Invariance par translation uniforme : VALIDÉE"
    )
    print(
        "Invariance par flux potentiel        : VALIDÉE"
    )
    print(
        "Dépendance à la seule vorticité      : VALIDÉE"
    )


if __name__ == "__main__":
    main()
