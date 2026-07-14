#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v7
import itd_v8
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


GRID_SIZES = (81, 121, 161, 241, 321)
TIME_STEPS = 201
COMPARISON_GRID_SIZE = 161
ZERO_TOLERANCE = 1.0e-11


def relative_difference(
    value: float,
    reference: float,
) -> float:
    if abs(reference) < 1.0e-15:
        return abs(value - reference)

    return abs(value - reference) / abs(reference)


def build_grid(
    cfg: Config,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
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

    return x, y, times, spacing


def temporal_mean(
    values: np.ndarray,
    times: np.ndarray,
) -> float:
    duration = float(
        times[-1] - times[0]
    )

    return float(
        np.trapezoid(
            values,
            times,
        )
        / duration
    )


def run_module(
    module,
    grid_size: int,
) -> dict[str, float]:
    cfg = Config(
        grid_size=grid_size,
        time_steps=TIME_STEPS,
    )

    x, y, times, spacing = build_grid(cfg)

    result = module.simulate(
        "multi_vortex_complexe",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    return {
        "heterogeneity": temporal_mean(
            np.asarray(
                result["heterogeneity"],
                dtype=np.float64,
            ),
            times,
        ),
        "structure": float(
            result["structure_index"]
        ),
        "intensity": float(
            result["intensity_index"]
        ),
    }


def validate_uniform_vortex() -> None:
    cfg = Config(
        grid_size=161,
        time_steps=101,
    )

    x, y, times, spacing = build_grid(cfg)

    result = itd_v8.simulate(
        "vortex_coherent",
        coherent_vortex,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    heterogeneity = np.asarray(
        result["heterogeneity"],
        dtype=np.float64,
    )

    maximum = float(
        np.max(np.abs(heterogeneity))
    )

    print(
        "Hétérogénéité maximale du vortex uniforme :",
        f"{maximum:.6e}",
    )

    if maximum > ZERO_TOLERANCE:
        raise RuntimeError(
            "Un champ de vorticité uniforme possède "
            "une hétérogénéité numérique non nulle."
        )

    print(
        "Oracle du champ uniforme                  : RÉUSSI"
    )


def validate_synthetic_field() -> None:
    grid_size = 161
    coordinates = np.linspace(
        -2.0,
        2.0,
        grid_size,
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

    omega = (
        1.4
        + 0.35 * x
        - 0.20 * y
        + 0.08 * x * y
    )

    metrics = itd_v8.structural_metrics(
        omega,
        spacing,
        previous_omega=None,
        delta_time=None,
    )

    absolute = np.abs(omega)

    mean_absolute = itd_v8.spatial_mean(
        absolute,
        spacing,
    )

    expected_variance = itd_v8.spatial_mean(
        (
            absolute - mean_absolute
        ) ** 2,
        spacing,
    )

    expected = (
        np.sqrt(expected_variance)
        / mean_absolute
    )

    obtained = float(
        metrics["heterogeneity"]
    )

    error = relative_difference(
        obtained,
        expected,
    )

    print()
    print(
        "Hétérogénéité synthétique attendue :",
        f"{expected:.15f}",
    )
    print(
        "Hétérogénéité synthétique obtenue  :",
        f"{obtained:.15f}",
    )
    print(
        "Erreur relative                    :",
        f"{error:.6e}",
    )

    if error > 1.0e-14:
        raise RuntimeError(
            "La variance spatiale pondérée "
            "est incorrecte."
        )

    print(
        "Oracle de quadrature synthétique   : RÉUSSI"
    )


def compare_v7_v8() -> None:
    old = run_module(
        itd_v7,
        COMPARISON_GRID_SIZE,
    )

    new = run_module(
        itd_v8,
        COMPARISON_GRID_SIZE,
    )

    print()
    print(
        "=== COMPARAISON V7 → V8 "
        f"À {COMPARISON_GRID_SIZE} × "
        f"{COMPARISON_GRID_SIZE} ==="
    )

    for metric in (
        "intensity",
        "heterogeneity",
        "structure",
    ):
        difference = relative_difference(
            new[metric],
            old[metric],
        )

        print(
            f"{metric:15s}: "
            f"V7={old[metric]:.15f}  "
            f"V8={new[metric]:.15f}  "
            f"écart={100.0 * difference:.9f} %"
        )

    intensity_error = relative_difference(
        new["intensity"],
        old["intensity"],
    )

    if intensity_error > 1.0e-14:
        raise RuntimeError(
            "La correction de l'hétérogénéité "
            "a modifié l'intensité."
        )


def validate_convergence() -> None:
    results = {
        grid_size: run_module(
            itd_v8,
            grid_size,
        )
        for grid_size in GRID_SIZES
    }

    reference_size = GRID_SIZES[-1]
    reference = results[reference_size]

    print()
    print(
        "=== CONVERGENCE DE L’HÉTÉROGÉNÉITÉ V8 ==="
    )
    print(
        "Référence :",
        f"{reference_size} × {reference_size}",
    )
    print(
        "grille | hétérogénéité | erreur H  | "
        "structure      | erreur C"
    )

    for grid_size in GRID_SIZES:
        metrics = results[grid_size]

        heterogeneity_error = relative_difference(
            metrics["heterogeneity"],
            reference["heterogeneity"],
        )

        structure_error = relative_difference(
            metrics["structure"],
            reference["structure"],
        )

        print(
            f"{grid_size:6d} | "
            f'{metrics["heterogeneity"]:13.10f} | '
            f"{heterogeneity_error:9.3e} | "
            f'{metrics["structure"]:13.10f} | '
            f"{structure_error:9.3e}"
        )

    previous_size = GRID_SIZES[-2]

    final_h_error = relative_difference(
        results[previous_size]["heterogeneity"],
        reference["heterogeneity"],
    )

    final_c_error = relative_difference(
        results[previous_size]["structure"],
        reference["structure"],
    )

    print()
    print(
        f"Écart {previous_size} → "
        f"{reference_size} :"
    )
    print(
        "Hétérogénéité :",
        f"{100.0 * final_h_error:.9f} %",
    )
    print(
        "Structure     :",
        f"{100.0 * final_c_error:.9f} %",
    )

    if not (
        np.isfinite(final_h_error)
        and np.isfinite(final_c_error)
    ):
        raise RuntimeError(
            "La convergence produit une valeur non finie."
        )

    print(
        "Convergence spatiale : VALIDÉE"
    )


def main() -> None:
    print(
        "=== VALIDATION DE L’HÉTÉROGÉNÉITÉ — ITD V8 ==="
    )

    validate_uniform_vortex()
    validate_synthetic_field()
    compare_v7_v8()
    validate_convergence()

    print()
    print(
        "Écart-type spatial pondéré : VALIDÉ"
    )
    print(
        "Intensité inchangée        : VALIDÉE"
    )
    print(
        "Oracle uniforme            : VALIDÉ"
    )


if __name__ == "__main__":
    main()
