#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v8
import itd_v9
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


GRID_SIZE = 161
TIME_STEPS = 201

STRUCTURAL_LENGTHS = (
    0.0,
    0.10,
    0.25,
    0.50,
    1.00,
    2.00,
)

TOLERANCE = 2.0e-12


def relative_error(
    value: float,
    expected: float,
) -> float:
    if abs(expected) < 1.0e-15:
        return abs(value - expected)

    return abs(value - expected) / abs(expected)


def temporal_mean(
    values: np.ndarray,
    times: np.ndarray,
) -> float:
    return float(
        np.trapezoid(values, times)
        / float(times[-1] - times[0])
    )


def extract(
    result: dict[str, object],
    times: np.ndarray,
) -> dict[str, float]:
    return {
        "intensity": float(
            result["intensity_index"]
        ),
        "structure": float(
            result["structure_index"]
        ),
        "roughness": temporal_mean(
            np.asarray(
                result["roughness"],
                dtype=np.float64,
            ),
            times,
        ),
        "heterogeneity": temporal_mean(
            np.asarray(
                result["heterogeneity"],
                dtype=np.float64,
            ),
            times,
        ),
        "localization": temporal_mean(
            np.asarray(
                result["localization"],
                dtype=np.float64,
            ),
            times,
        ),
        "sign_mixing": temporal_mean(
            np.asarray(
                result["sign_mixing"],
                dtype=np.float64,
            ),
            times,
        ),
        "deformation": float(
            result["temporal_deformation_index"]
        ),
    }


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
        "=== SENSIBILITÉ À LA LONGUEUR "
        "STRUCTURELLE — ITD V9 ==="
    )

    old_result = extract(
        itd_v8.simulate(
            "multi_vortex_v8",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
        ),
        times,
    )

    default_result = extract(
        itd_v9.simulate(
            "multi_vortex_v9",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
        ),
        times,
    )

    print()
    print("=== COMPATIBILITÉ V8 → V9 ===")

    maximum_compatibility_error = 0.0

    for metric_name in old_result:
        error = relative_error(
            default_result[metric_name],
            old_result[metric_name],
        )

        maximum_compatibility_error = max(
            maximum_compatibility_error,
            error,
        )

        print(
            f"{metric_name:15s}: "
            f"V8={old_result[metric_name]:.15f}  "
            f"V9={default_result[metric_name]:.15f}  "
            f"erreur={error:.3e}"
        )

    if maximum_compatibility_error > TOLERANCE:
        raise RuntimeError(
            "La V9 n'est pas compatible avec "
            "la V8 pour ell_s = 0,5."
        )

    results: dict[float, dict[str, float]] = {}

    for structural_length in STRUCTURAL_LENGTHS:
        result = itd_v9.simulate(
            f"multi_vortex_L_{structural_length}",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            structural_length=structural_length,
        )

        results[structural_length] = extract(
            result,
            times,
        )

    reference = results[0.50]

    print()
    print("=== MULTI-VORTEX ===")
    print(
        "ell_s  | rugosité        | erreur loi linéaire | "
        "structure        | intensité"
    )

    previous_structure: float | None = None
    maximum_roughness_error = 0.0
    maximum_invariant_error = 0.0

    invariant_names = (
        "intensity",
        "heterogeneity",
        "localization",
        "sign_mixing",
        "deformation",
    )

    for structural_length in STRUCTURAL_LENGTHS:
        metrics = results[structural_length]

        expected_roughness = (
            0.0
            if structural_length == 0.0
            else reference["roughness"]
            * structural_length
            / 0.50
        )

        roughness_error = relative_error(
            metrics["roughness"],
            expected_roughness,
        )

        maximum_roughness_error = max(
            maximum_roughness_error,
            roughness_error,
        )

        for metric_name in invariant_names:
            invariant_error = relative_error(
                metrics[metric_name],
                reference[metric_name],
            )

            maximum_invariant_error = max(
                maximum_invariant_error,
                invariant_error,
            )

        if (
            previous_structure is not None
            and metrics["structure"]
            < previous_structure - TOLERANCE
        ):
            raise RuntimeError(
                "La structure n'est pas monotone "
                "avec la longueur structurelle."
            )

        previous_structure = metrics["structure"]

        print(
            f"{structural_length:5.2f} | "
            f'{metrics["roughness"]:15.12f} | '
            f"{roughness_error:19.6e} | "
            f'{metrics["structure"]:15.12f} | '
            f'{metrics["intensity"]:.12f}'
        )

    print()
    print(
        "Erreur maximale loi Q ∝ ell_s :",
        f"{maximum_roughness_error:.6e}",
    )
    print(
        "Erreur maximale autres mesures:",
        f"{maximum_invariant_error:.6e}",
    )

    if maximum_roughness_error > TOLERANCE:
        raise RuntimeError(
            "La rugosité ne suit pas la loi "
            "linéaire en ell_s."
        )

    if maximum_invariant_error > TOLERANCE:
        raise RuntimeError(
            "Une mesure indépendante de ell_s "
            "a été modifiée."
        )

    print()
    print("=== VORTEX COHÉRENT ===")

    coherent_structures: list[float] = []

    for structural_length in STRUCTURAL_LENGTHS:
        result = itd_v9.simulate(
            f"vortex_L_{structural_length}",
            coherent_vortex,
            x,
            y,
            times,
            spacing,
            cfg,
            structural_length=structural_length,
        )

        metrics = extract(result, times)
        coherent_structures.append(
            metrics["structure"]
        )

        print(
            f"ell_s={structural_length:5.2f}  "
            f"rugosité={metrics['roughness']:.6e}  "
            f"structure={metrics['structure']:.12f}"
        )

    coherent_spread = (
        max(coherent_structures)
        - min(coherent_structures)
    )

    if coherent_spread > TOLERANCE:
        raise RuntimeError(
            "Le vortex uniforme dépend artificiellement "
            "de la longueur structurelle."
        )

    for invalid_value in (
        -0.1,
        float("nan"),
        float("inf"),
    ):
        try:
            itd_v9.simulate(
                "invalid_structural_length",
                coherent_vortex,
                x,
                y,
                times[:2],
                spacing,
                cfg,
                structural_length=invalid_value,
            )
        except ValueError as error:
            print(
                f"Rejet ell_s={invalid_value!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une longueur structurelle invalide "
                "n'a pas été rejetée."
            )

    print()
    print("Compatibilité V8 → V9       : VALIDÉE")
    print("Loi Q(ell_s) ∝ ell_s        : VALIDÉE")
    print("Intensité indépendante      : VALIDÉE")
    print("Sensibilité explicite de C  : MESURÉE")


if __name__ == "__main__":
    main()
