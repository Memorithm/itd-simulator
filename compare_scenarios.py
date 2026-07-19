#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
VelocityFunction = Callable[
    [FloatArray, FloatArray, float],
    tuple[FloatArray, FloatArray],
]


@dataclass(frozen=True)
class Config:
    grid_size: int = 161
    domain_min: float = -2.0
    domain_max: float = 2.0
    duration: float = 10.0
    time_steps: int = 401
    characteristic_length: float = 0.5
    output_dir: str = "comparison_results"


def calm_field(
    x: FloatArray,
    y: FloatArray,
    t: float,
) -> tuple[FloatArray, FloatArray]:
    """
    Champ d'expansion pure :
        vx = a(t) x
        vy = a(t) y

    Son rotationnel analytique est nul.
    """
    amplitude = 0.35 + 0.05 * np.sin(0.4 * t)
    return amplitude * x, amplitude * y


def coherent_vortex(
    x: FloatArray,
    y: FloatArray,
    t: float,
) -> tuple[FloatArray, FloatArray]:
    """
    Rotation rigide cohérente.
    """
    amplitude = 1.0 + 0.35 * np.sin(0.6 * t)
    return -amplitude * y, amplitude * x


def multi_vortex_field(
    x: FloatArray,
    y: FloatArray,
    t: float,
) -> tuple[FloatArray, FloatArray]:
    """
    Superposition déterministe de quatre vortex gaussiens mobiles.
    """
    vx = np.zeros_like(x)
    vy = np.zeros_like(y)

    vortex_data = (
        (
            -0.85 + 0.15 * np.cos(0.37 * t),
            -0.65 + 0.12 * np.sin(0.43 * t),
            1.30,
            0.55,
        ),
        (
            0.80 + 0.13 * np.sin(0.31 * t),
            -0.55 + 0.14 * np.cos(0.47 * t),
            -1.05,
            0.48,
        ),
        (
            -0.45 + 0.12 * np.sin(0.53 * t),
            0.85 + 0.10 * np.cos(0.29 * t),
            0.90,
            0.62,
        ),
        (
            0.75 + 0.11 * np.cos(0.41 * t),
            0.70 + 0.13 * np.sin(0.35 * t),
            -1.20,
            0.52,
        ),
    )

    for center_x, center_y, strength, width in vortex_data:
        dx = x - center_x
        dy = y - center_y
        radius_squared = dx**2 + dy**2

        envelope = np.exp(
            -radius_squared / (2.0 * width**2)
        )

        temporal_strength = strength * (
            1.0 + 0.18 * np.sin(0.7 * t + strength)
        )

        vx += -temporal_strength * dy * envelope
        vy += temporal_strength * dx * envelope

    background = 0.08 * np.sin(0.5 * t)

    vx += background * np.sin(np.pi * y)
    vy += background * np.sin(np.pi * x)

    return vx, vy


def curvature_field(
    x: FloatArray,
    y: FloatArray,
    t: float,
) -> FloatArray:
    """
    Pondération synthétique commune aux trois scénarios.

    Ce champ n'est pas dérivé d'une métrique physique.
    """
    central = 0.42 * np.exp(
        -(x**2 + y**2) / 0.9**2
    )

    moving = 0.20 * np.exp(
        -(
            (x - 0.65 * np.cos(0.22 * t)) ** 2
            + (y - 0.65 * np.sin(0.22 * t)) ** 2
        )
        / 0.45**2
    )

    negative_region = -0.12 * np.exp(
        -(
            (x + 1.0) ** 2
            + (y - 0.75) ** 2
        )
        / 0.6**2
    )

    return central + moving + negative_region


def numerical_vorticity(
    vx: FloatArray,
    vy: FloatArray,
    spacing: float,
) -> FloatArray:
    dvy_dy, dvy_dx = np.gradient(
        vy,
        spacing,
        spacing,
        edge_order=2,
    )

    dvx_dy, dvx_dx = np.gradient(
        vx,
        spacing,
        spacing,
        edge_order=2,
    )

    del dvy_dy, dvx_dx

    return dvy_dx - dvx_dy


def normalized_spatial_integral(
    field: FloatArray,
    spacing: float,
) -> float:
    area = (
        field.shape[0]
        * field.shape[1]
        * spacing**2
    )

    return float(
        np.sum(field) * spacing**2 / area
    )


def simulate_scenario(
    name: str,
    velocity_function: VelocityFunction,
    x: FloatArray,
    y: FloatArray,
    times: FloatArray,
    spacing: float,
    cfg: Config,
) -> dict[str, FloatArray | float | str]:
    psi_rate = np.empty_like(times)
    enstrophy = np.empty_like(times)
    mean_absolute_vorticity = np.empty_like(times)

    final_vorticity = np.zeros_like(x)
    final_density = np.zeros_like(x)

    for index, time in enumerate(times):
        vx, vy = velocity_function(
            x,
            y,
            float(time),
        )

        omega = numerical_vorticity(
            vx,
            vy,
            spacing,
        )

        curvature = curvature_field(
            x,
            y,
            float(time),
        )

        weight = np.exp(
            cfg.characteristic_length**2
            * curvature
        )

        density = omega**2 * weight

        psi_rate[index] = normalized_spatial_integral(
            density,
            spacing,
        )

        enstrophy[index] = normalized_spatial_integral(
            omega**2,
            spacing,
        )

        mean_absolute_vorticity[index] = float(
            np.mean(np.abs(omega))
        )

        if index == len(times) - 1:
            final_vorticity = omega.copy()
            final_density = density.copy()

    psi_accumulated = np.zeros_like(times)

    psi_accumulated[1:] = np.cumsum(
        0.5
        * (
            psi_rate[:-1]
            + psi_rate[1:]
        )
        * np.diff(times)
    )

    psi_normalized = float(
        np.trapezoid(
            psi_rate,
            times,
        )
        / cfg.duration
    )

    return {
        "name": name,
        "psi_rate": psi_rate,
        "psi_accumulated": psi_accumulated,
        "psi_normalized": psi_normalized,
        "enstrophy": enstrophy,
        "mean_absolute_vorticity": mean_absolute_vorticity,
        "final_vorticity": final_vorticity,
        "final_density": final_density,
    }


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    cfg = Config()

    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
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
            "calme_irrotationnel",
            calm_field,
        ),
        (
            "vortex_coherent",
            coherent_vortex,
        ),
        (
            "multi_vortex_complexe",
            multi_vortex_field,
        ),
    )

    results = [
        simulate_scenario(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )
        for name, velocity_function in scenarios
    ]

    summary_rows: list[list[float | str]] = []

    for result in results:
        name = str(result["name"])
        psi_rate = np.asarray(result["psi_rate"])
        enstrophy = np.asarray(result["enstrophy"])
        mean_abs_omega = np.asarray(
            result["mean_absolute_vorticity"]
        )

        summary_rows.append(
            [
                name,
                float(result["psi_normalized"]),
                float(np.min(psi_rate)),
                float(np.max(psi_rate)),
                float(np.mean(enstrophy)),
                float(np.mean(mean_abs_omega)),
            ]
        )

        table = np.column_stack(
            (
                times,
                psi_rate,
                np.asarray(
                    result["psi_accumulated"]
                ),
                enstrophy,
                mean_abs_omega,
            )
        )

        np.savetxt(
            output_dir / f"{name}.csv",
            table,
            delimiter=",",
            header=(
                "time,"
                "psi_rate,"
                "psi_accumulated,"
                "mean_squared_vorticity,"
                "mean_absolute_vorticity"
            ),
            comments="",
        )

        for field_name, title_suffix in (
            (
                "final_vorticity",
                "vorticité finale",
            ),
            (
                "final_density",
                "densité ITD finale",
            ),
        ):
            field = np.asarray(result[field_name])

            plt.figure(figsize=(8, 7))
            image = plt.pcolormesh(
                x,
                y,
                field,
                shading="auto",
            )
            plt.colorbar(image)
            plt.xlabel("x")
            plt.ylabel("y")
            plt.title(
                f"{name} — {title_suffix}"
            )
            plt.axis("equal")
            plt.tight_layout()
            plt.savefig(
                output_dir
                / f"{name}_{field_name}.png",
                dpi=160,
            )
            plt.close()

    plt.figure(figsize=(10, 6))

    for result in results:
        plt.plot(
            times,
            np.asarray(result["psi_rate"]),
            label=str(result["name"]),
        )

    plt.xlabel("Temps")
    plt.ylabel("Taux instantané de l'ITD")
    plt.title("Comparaison des taux ITD")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir / "comparison_psi_rate.png",
        dpi=160,
    )
    plt.close()

    plt.figure(figsize=(10, 6))

    for result in results:
        plt.plot(
            times,
            np.asarray(
                result["psi_accumulated"]
            ),
            label=str(result["name"]),
        )

    plt.xlabel("Temps")
    plt.ylabel("ITD accumulé")
    plt.title("Comparaison des ITD accumulés")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir
        / "comparison_psi_accumulated.png",
        dpi=160,
    )
    plt.close()

    with (
        output_dir / "summary.csv"
    ).open(
        "w",
        encoding="utf-8",
    ) as summary_file:
        summary_file.write(
            "scenario,"
            "psi_normalized,"
            "psi_rate_min,"
            "psi_rate_max,"
            "mean_enstrophy,"
            "mean_absolute_vorticity\n"
        )

        for row in summary_rows:
            summary_file.write(
                ",".join(str(value) for value in row)
                + "\n"
            )

    calm_result = results[0]
    calm_psi = float(
        calm_result["psi_normalized"]
    )

    if calm_psi > 1.0e-24:
        raise RuntimeError(
            "Le champ calme devrait avoir un ITD "
            f"quasi nul, valeur obtenue : {calm_psi}"
        )

    print("=== COMPARAISON DES SCÉNARIOS ===")

    for row in summary_rows:
        print()
        print(f"Scénario             : {row[0]}")
        print(f"ITD normalisé        : {float(row[1]):.12f}")
        print(f"Taux ITD minimal     : {float(row[2]):.12f}")
        print(f"Taux ITD maximal     : {float(row[3]):.12f}")
        print(f"Enstrophie moyenne   : {float(row[4]):.12f}")
        print(f"|vorticité| moyenne  : {float(row[5]):.12f}")

    print()
    print(
        "Validation champ calme : RÉUSSIE"
    )
    print(
        "Résultats              :",
        output_dir.resolve(),
    )


if __name__ == "__main__":
    main()
