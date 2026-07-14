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
TIME_COUNTS = (101, 201, 401, 801)
DURATION = 10.0


def analytical_deformation(time: float) -> float:
    amplitude = (
        1.0
        + 0.35 * np.sin(0.6 * time)
    )

    amplitude_derivative = (
        0.21 * np.cos(0.6 * time)
    )

    return abs(amplitude_derivative) / amplitude


def create_time_grid(
    count: int,
    mode: str,
) -> np.ndarray:
    parameter = np.linspace(
        0.0,
        1.0,
        count,
        dtype=np.float64,
    )

    if mode == "uniform":
        times = DURATION * parameter

    elif mode == "quadratic_start":
        times = DURATION * parameter**2

    elif mode == "quadratic_end":
        times = DURATION * (
            1.0 - (1.0 - parameter) ** 2
        )

    elif mode == "smooth_warp":
        warp = (
            parameter
            + 0.12
            * np.sin(2.0 * np.pi * parameter)
            / (2.0 * np.pi)
        )

        times = DURATION * warp

    elif mode == "cusp_focused":
        cusp_times = np.array(
            [
                0.0,
                np.pi / (2.0 * 0.6),
                3.0 * np.pi / (2.0 * 0.6),
                DURATION,
            ],
            dtype=np.float64,
        )

        segment_lengths = np.diff(cusp_times)

        raw_counts = (
            count - 1
        ) * segment_lengths / DURATION

        interval_counts = np.maximum(
            2,
            np.floor(raw_counts).astype(int),
        )

        missing = (
            count - 1 - int(np.sum(interval_counts))
        )

        order = np.argsort(
            raw_counts - np.floor(raw_counts)
        )[::-1]

        index = 0

        while missing > 0:
            interval_counts[order[index % len(order)]] += 1
            missing -= 1
            index += 1

        while missing < 0:
            candidate = order[::-1][index % len(order)]

            if interval_counts[candidate] > 2:
                interval_counts[candidate] -= 1
                missing += 1

            index += 1

        pieces: list[np.ndarray] = []

        for segment_index, intervals in enumerate(
            interval_counts
        ):
            local = np.linspace(
                cusp_times[segment_index],
                cusp_times[segment_index + 1],
                intervals + 1,
                dtype=np.float64,
            )

            if segment_index > 0:
                local = local[1:]

            pieces.append(local)

        times = np.concatenate(pieces)

    else:
        raise ValueError(
            f"Mode temporel inconnu : {mode}"
        )

    if len(times) != count:
        raise RuntimeError(
            f"Nombre incorrect d'instants pour {mode}: "
            f"{len(times)} au lieu de {count}."
        )

    if times[0] != 0.0:
        raise RuntimeError(
            "Le premier instant doit être zéro."
        )

    if not np.isclose(
        times[-1],
        DURATION,
        rtol=0.0,
        atol=1.0e-14,
    ):
        raise RuntimeError(
            "Le dernier instant doit être la durée totale."
        )

    if np.any(np.diff(times) <= 0.0):
        raise RuntimeError(
            "La grille temporelle n'est pas "
            "strictement croissante."
        )

    return times


def run_simulation(
    times: np.ndarray,
) -> tuple[float, float, float]:
    cfg = Config(
        grid_size=GRID_SIZE,
        time_steps=len(times),
        duration=DURATION,
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

    result = simulate(
        "vortex_coherent",
        coherent_vortex,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    deformation_index = float(
        result["temporal_deformation_index"]
    )

    interval_values = np.asarray(
        result["temporal_deformation_interval"],
        dtype=np.float64,
    )

    interval_dt = np.asarray(
        result["temporal_interval_dt"],
        dtype=np.float64,
    )

    direct_index = float(
        np.sum(
            interval_values * interval_dt
        )
        / np.sum(interval_dt)
    )

    consistency_error = abs(
        deformation_index - direct_index
    )

    return (
        deformation_index,
        float(np.min(interval_dt)),
        float(np.max(interval_dt)),
    )


def main() -> None:
    analytical_integral, quadrature_error = quad(
        analytical_deformation,
        0.0,
        DURATION,
        epsabs=1.0e-13,
        epsrel=1.0e-13,
        limit=500,
        points=[
            np.pi / (2.0 * 0.6),
            3.0 * np.pi / (2.0 * 0.6),
        ],
    )

    oracle = analytical_integral / DURATION

    modes = (
        "uniform",
        "quadratic_start",
        "quadratic_end",
        "smooth_warp",
        "cusp_focused",
    )

    print("=== TEST TEMPOREL NON UNIFORME — ITD V6 ===")
    print(
        "Oracle analytique :",
        f"{oracle:.15f}",
    )
    print(
        "Erreur quadrature  :",
        f"{quadrature_error:.3e}",
    )

    for count in TIME_COUNTS:
        print()
        print(
            f"Nombre d'instants : {count}"
        )
        print(
            "mode             | dt min     | dt max     | "
            "déformation       | erreur relative"
        )

        for mode in modes:
            times = create_time_grid(
                count,
                mode,
            )

            value, dt_min, dt_max = run_simulation(
                times
            )

            relative_error = (
                abs(value - oracle)
                / abs(oracle)
            )

            print(
                f"{mode:16s} | "
                f"{dt_min:10.7f} | "
                f"{dt_max:10.7f} | "
                f"{value:17.15f} | "
                f"{100.0 * relative_error:12.9f} %"
            )

            if not np.isfinite(value):
                raise RuntimeError(
                    f"Valeur non finie pour {mode}."
                )

    print()
    print(
        "Grilles non uniformes : VALIDÉES"
    )


if __name__ == "__main__":
    main()
