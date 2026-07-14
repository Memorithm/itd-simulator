#!/usr/bin/env python3

from __future__ import annotations

import numpy as np
from scipy.integrate import quad

from compare_scenarios import (
    Config,
    coherent_vortex,
)
from itd_v6 import simulate


GRID_SIZE = 81
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


def run_simulation(
    time_steps: int,
) -> tuple[float, float]:
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

    interval_values = np.asarray(
        result["temporal_deformation_interval"],
        dtype=np.float64,
    )

    interval_dt = np.asarray(
        result["temporal_interval_dt"],
        dtype=np.float64,
    )

    if len(interval_values) != time_steps - 1:
        raise RuntimeError(
            "Nombre incorrect de valeurs d'intervalle."
        )

    direct_mean = float(
        np.sum(
            interval_values * interval_dt
        )
        / np.sum(interval_dt)
    )

    stored_mean = float(
        result["temporal_deformation_index"]
    )

    return direct_mean, stored_mean


def main() -> None:
    duration = 10.0

    analytical_integral, quadrature_error = quad(
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

    oracle = analytical_integral / duration

    print("=== VALIDATION TEMPORELLE ITD V6 ===")
    print(
        "Oracle analytique       :",
        f"{oracle:.15f}",
    )
    print(
        "Erreur quadrature oracle:",
        f"{quadrature_error:.3e}",
    )

    print()
    print(
        "pas  | dt         | moyenne intervalles | "
        "erreur relative"
    )

    for time_steps in TIME_STEPS:
        direct_mean, stored_mean = run_simulation(
            time_steps
        )

        consistency_error = abs(
            direct_mean - stored_mean
        )

        if consistency_error > 1.0e-14:
            raise RuntimeError(
                "L'indice enregistré diffère de "
                "l'intégration directe."
            )

        relative_error = (
            abs(direct_mean - oracle)
            / abs(oracle)
        )

        delta_time = duration / (
            time_steps - 1
        )

        print(
            f"{time_steps:4d} | "
            f"{delta_time:10.7f} | "
            f"{direct_mean:19.15f} | "
            f"{100.0 * relative_error:12.9f} %"
        )

    print()
    print(
        "Intégration par intervalles : VALIDÉE"
    )
    print(
        "Remarque : sur une grille temporelle uniforme, "
        "les valeurs restent proches de la V5, ce qui "
        "est attendu."
    )


if __name__ == "__main__":
    main()
