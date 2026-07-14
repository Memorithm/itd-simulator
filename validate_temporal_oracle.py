#!/usr/bin/env python3

from __future__ import annotations

import numpy as np
from scipy.integrate import quad

from compare_scenarios import (
    Config,
    coherent_vortex,
)
from itd_v4 import simulate


GRID_SIZE = 161
TIME_STEPS = (101, 201, 401, 801, 1601)


def analytical_deformation(time: float) -> float:
    amplitude = (
        1.0
        + 0.35 * np.sin(0.6 * time)
    )

    amplitude_derivative = (
        0.21 * np.cos(0.6 * time)
    )

    return abs(amplitude_derivative) / amplitude


def relative_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / abs(reference)


def numerical_result(
    time_steps: int,
) -> float:
    cfg = Config(
        grid_size=GRID_SIZE,
        time_steps=time_steps,
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

    result = simulate(
        "vortex_coherent",
        coherent_vortex,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    deformation = np.asarray(
        result["temporal_deformation"],
        dtype=np.float64,
    )

    return float(
        np.trapezoid(
            deformation,
            times,
        )
        / cfg.duration
    )


def main() -> None:
    duration = 10.0

    analytical_integral, integration_error = quad(
        analytical_deformation,
        0.0,
        duration,
        epsabs=1.0e-13,
        epsrel=1.0e-13,
        limit=500,
        points=[
            np.pi / (2.0 * 0.6),
            3.0 * np.pi / (2.0 * 0.6),
        ],
    )

    analytical_mean = (
        analytical_integral / duration
    )

    print("=== ORACLE TEMPOREL DU VORTEX COHÉRENT ===")
    print(
        "Déformation analytique moyenne :",
        f"{analytical_mean:.15f}",
    )
    print(
        "Erreur estimée de quadrature    :",
        f"{integration_error:.3e}",
    )

    print()
    print(
        "pas  | dt         | valeur numérique   | "
        "erreur absolue | erreur relative"
    )

    previous_error: float | None = None

    for time_steps in TIME_STEPS:
        delta_time = duration / (
            time_steps - 1
        )

        value = numerical_result(time_steps)

        absolute_error = abs(
            value - analytical_mean
        )

        error = relative_error(
            value,
            analytical_mean,
        )

        convergence_ratio = (
            previous_error / error
            if previous_error is not None
            and error > 0.0
            else float("nan")
        )

        print(
            f"{time_steps:4d} | "
            f"{delta_time:10.7f} | "
            f"{value:18.15f} | "
            f"{absolute_error:13.6e} | "
            f"{100.0 * error:12.9f} %"
        )

        if previous_error is not None:
            print(
                "     rapport de réduction "
                f"de l'erreur : {convergence_ratio:.6f}"
            )

        previous_error = error

    print()
    print(
        "Un rapport proche de 2 lorsque dt est "
        "divisé par 2 indiquera un biais d'ordre 1."
    )


if __name__ == "__main__":
    main()
