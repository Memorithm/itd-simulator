#!/usr/bin/env python3

from __future__ import annotations

import gc
import json
import math
from pathlib import Path

import numpy as np

import itd_v27
import itd_v28
import validate_cubic_transport_v25 as base
import validate_local_bounded_v27 as local
import validate_phase_robust_limiter_v27 as phase_validation
import validate_shape_stability_v26 as shape


GRID_SIZES = (
    64,
    128,
    256,
    512,
    1024,
)

SHIFT_X_OVER_H = 0.371
SHIFT_Y_OVER_H = -0.283

REPEATED_GRID_SIZE = 256
REPEATED_STEP_COUNT = 64

BOUND_TOLERANCE = 8.0e-12
SUM_TOLERANCE = 5.0e-10

OUTPUT_PATH = Path(
    "itd_v28_results"
    "/sum_preserving_validation.json"
)


def precise_sum(
    values: object,
) -> np.longdouble:
    return np.sum(
        np.asarray(
            values,
            dtype=np.longdouble,
        ),
        dtype=np.longdouble,
    )


def observed_order(
    coarse_error: float,
    fine_error: float,
    coarse_spacing: float,
    fine_spacing: float,
) -> float:
    return float(
        math.log(
            coarse_error
            / fine_error
        )
        / math.log(
            coarse_spacing
            / fine_spacing
        )
    )


def fitted_order(
    rows: list[dict[str, object]],
    key: str,
) -> float:
    tail = rows[-3:]

    spacings = np.asarray(
        [
            float(row["spacing"])
            for row in tail
        ],
        dtype=np.float64,
    )

    errors = np.asarray(
        [
            float(row[key])
            for row in tail
        ],
        dtype=np.float64,
    )

    slope, _ = np.polyfit(
        np.log(spacings),
        np.log(errors),
        1,
    )

    return float(slope)


def norms(
    numerical: np.ndarray,
    exact: np.ndarray,
) -> dict[str, float]:
    difference = np.asarray(
        numerical - exact,
        dtype=np.float64,
    )

    absolute = np.abs(
        difference
    )

    return {
        "linf": float(
            np.max(absolute)
        ),
        "l1_mean": float(
            np.mean(absolute)
        ),
        "l2_rms": float(
            np.sqrt(
                np.mean(
                    difference * difference
                )
            )
        ),
    }


def transport_once(
    module: object,
    source: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    mode: str,
) -> np.ndarray:
    velocity_x = np.full_like(
        source,
        displacement_x,
        dtype=np.float64,
    )

    velocity_y = np.full_like(
        source,
        displacement_y,
        dtype=np.float64,
    )

    return module.periodic_backtrace(
        source,
        coordinates,
        coordinates,
        velocity_x,
        velocity_y,
        1.0,
        interpolation=mode,
    )


def local_bound_defect(
    source: np.ndarray,
    result: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
) -> float:
    velocity_x = np.full_like(
        source,
        displacement_x,
        dtype=np.float64,
    )

    velocity_y = np.full_like(
        source,
        displacement_y,
        dtype=np.float64,
    )

    lower, upper = (
        itd_v28
        .periodic_bilinear_departure_bounds(
            source,
            coordinates,
            coordinates,
            velocity_x,
            velocity_y,
            1.0,
        )
    )

    return max(
        float(
            np.max(
                np.maximum(
                    lower - result,
                    0.0,
                )
            )
        ),
        float(
            np.max(
                np.maximum(
                    result - upper,
                    0.0,
                )
            )
        ),
    )


def validate_api_and_compatibility() -> None:
    print(
        "=== API ET COMPATIBILITÉ V28 ==="
    )

    expected = (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
        "cubic_local_sum_preserving_periodic",
    )

    observed = tuple(
        itd_v28.TRANSPORT_INTERPOLATIONS
    )

    print(
        "Modes :",
        observed,
    )

    if observed != expected:
        raise RuntimeError(
            "Les modes V28 sont inattendus."
        )

    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        96
    )

    source = shape.smooth_periodic_field(
        x,
        y,
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
    ):
        reference = transport_once(
            itd_v27,
            source,
            coordinates,
            displacement_x,
            displacement_y,
            mode,
        )

        candidate = transport_once(
            itd_v28,
            source,
            coordinates,
            displacement_x,
            displacement_y,
            mode,
        )

        identical = np.array_equal(
            reference,
            candidate,
        )

        print(
            f"{mode:38s}: {identical}"
        )

        if not identical:
            raise RuntimeError(
                "Une branche historique V27 a été "
                f"modifiée : {mode}."
            )

    print(
        "Compatibilité V27 → V28 : VALIDÉE"
    )


def run_phase_case(
    grid_size: int,
    phase_x: float,
    phase_y: float,
) -> dict[str, object]:
    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        grid_size
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    source = shape.smooth_periodic_field(
        x + phase_x * spacing,
        y + phase_y * spacing,
    )

    cubic = transport_once(
        itd_v28,
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_periodic",
    )

    bounded = transport_once(
        itd_v28,
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_local_bounded_periodic",
    )

    corrected = transport_once(
        itd_v28,
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_local_sum_preserving_periodic",
    )

    exact = shape.smooth_periodic_field(
        x
        - displacement_x
        + phase_x * spacing,
        y
        - displacement_y
        + phase_y * spacing,
    )

    error_norms = norms(
        corrected,
        exact,
    )

    activation_scale = max(
        1.0,
        float(
            np.max(
                np.abs(cubic)
            )
        ),
    )

    activation_tolerance = (
        256.0
        * np.finfo(np.float64).eps
        * activation_scale
    )

    limited_mask = (
        np.abs(
            bounded - cubic
        )
        > activation_tolerance
    )

    correction_mask = (
        np.abs(
            corrected - bounded
        )
        > activation_tolerance
    )

    target_sum_error = abs(
        precise_sum(corrected)
        - precise_sum(cubic)
    )

    source_sum_drift = abs(
        precise_sum(corrected)
        - precise_sum(source)
    )

    bound_defect = local_bound_defect(
        source,
        corrected,
        coordinates,
        displacement_x,
        displacement_y,
    )

    if (
        float(target_sum_error)
        > SUM_TOLERANCE
    ):
        raise RuntimeError(
            "La somme cubique cible n'est pas "
            "préservée."
        )

    if bound_defect > BOUND_TOLERANCE:
        raise RuntimeError(
            "Le mode V28 viole les bornes locales."
        )

    return {
        "grid_size": grid_size,
        "spacing": float(spacing),
        "phase_x": float(phase_x),
        "phase_y": float(phase_y),
        **error_norms,
        "limited_count": int(
            np.count_nonzero(
                limited_mask
            )
        ),
        "correction_count": int(
            np.count_nonzero(
                correction_mask
            )
        ),
        "target_sum_error": float(
            target_sum_error
        ),
        "source_sum_drift": float(
            source_sum_drift
        ),
        "local_bound_defect": (
            bound_defect
        ),
    }


def run_phase_envelope() -> tuple[
    list[dict[str, object]],
    dict[str, list[dict[str, object]]],
]:
    phases = (
        phase_validation.phase_nodes()
    )

    print()
    print(
        "=== ENVELOPPE DE PHASE V28 ==="
    )

    print(
        "Nombre de phases :",
        len(phases),
    )

    print()
    print(
        "grille | pire L∞ | ordre | pire L2 | "
        "ordre | pire L1 | ordre | "
        "limités max | corrigés max | "
        "erreur somme max"
    )

    aggregates: list[
        dict[str, object]
    ] = []

    all_cases: dict[
        str,
        list[dict[str, object]],
    ] = {}

    previous = None

    for grid_size in GRID_SIZES:
        cases = [
            run_phase_case(
                grid_size,
                phase_x,
                phase_y,
            )
            for phase_x, phase_y in phases
        ]

        aggregate = {
            "grid_size": grid_size,
            "spacing": float(
                cases[0]["spacing"]
            ),
            "worst_linf": max(
                float(case["linf"])
                for case in cases
            ),
            "worst_l2_rms": max(
                float(case["l2_rms"])
                for case in cases
            ),
            "worst_l1_mean": max(
                float(case["l1_mean"])
                for case in cases
            ),
            "maximum_limited_count": max(
                int(case["limited_count"])
                for case in cases
            ),
            "maximum_correction_count": max(
                int(case["correction_count"])
                for case in cases
            ),
            "maximum_target_sum_error": max(
                float(
                    case[
                        "target_sum_error"
                    ]
                )
                for case in cases
            ),
            "maximum_source_sum_drift": max(
                float(
                    case[
                        "source_sum_drift"
                    ]
                )
                for case in cases
            ),
            "maximum_local_bound_defect": max(
                float(
                    case[
                        "local_bound_defect"
                    ]
                )
                for case in cases
            ),
        }

        aggregates.append(
            aggregate
        )

        all_cases[
            str(grid_size)
        ] = cases

        if previous is None:
            linf_order = "—"
            l2_order = "—"
            l1_order = "—"
        else:
            linf_order = (
                f"{observed_order(
                    float(previous['worst_linf']),
                    float(aggregate['worst_linf']),
                    float(previous['spacing']),
                    float(aggregate['spacing']),
                ):.6f}"
            )

            l2_order = (
                f"{observed_order(
                    float(previous['worst_l2_rms']),
                    float(aggregate['worst_l2_rms']),
                    float(previous['spacing']),
                    float(aggregate['spacing']),
                ):.6f}"
            )

            l1_order = (
                f"{observed_order(
                    float(previous['worst_l1_mean']),
                    float(aggregate['worst_l1_mean']),
                    float(previous['spacing']),
                    float(aggregate['spacing']),
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{float(aggregate['worst_linf']):9.3e} | "
            f"{linf_order:>8} | "
            f"{float(aggregate['worst_l2_rms']):9.3e} | "
            f"{l2_order:>8} | "
            f"{float(aggregate['worst_l1_mean']):9.3e} | "
            f"{l1_order:>8} | "
            f"{int(aggregate['maximum_limited_count']):11d} | "
            f"{int(aggregate['maximum_correction_count']):12d} | "
            f"{float(aggregate['maximum_target_sum_error']):.3e}"
        )

        previous = aggregate

        gc.collect()

    return aggregates, all_cases


def repeated_transport(
    source: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    mode: str,
) -> np.ndarray:
    current = np.asarray(
        source,
        dtype=np.float64,
    ).copy()

    for _ in range(
        REPEATED_STEP_COUNT
    ):
        current = transport_once(
            itd_v28,
            current,
            coordinates,
            displacement_x,
            displacement_y,
            mode,
        )

    return current


def repeated_stress() -> dict[str, object]:
    print()
    print(
        "=== TRANSPORTS RÉPÉTÉS V28 ==="
    )

    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        REPEATED_GRID_SIZE
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    fields = {
        "smooth": shape.smooth_periodic_field(
            x,
            y,
        ),
        "sharp": shape.sharp_periodic_field(
            x,
            y,
        ),
        "positive_bump": (
            shape.positive_periodic_bump(
                x,
                y,
            )
        ),
    }

    report: dict[str, object] = {}

    for name, source in fields.items():
        corrected = repeated_transport(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_sum_preserving_periodic",
        )

        bounded = repeated_transport(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_bounded_periodic",
        )

        sum_drift = abs(
            precise_sum(corrected)
            - precise_sum(source)
        )

        mean_drift = (
            float(sum_drift)
            / source.size
        )

        global_bound_defect = max(
            max(
                0.0,
                float(np.min(source))
                - float(np.min(corrected)),
            ),
            max(
                0.0,
                float(np.max(corrected))
                - float(np.max(source)),
            ),
        )

        corrected_bounded_difference = float(
            np.max(
                np.abs(
                    corrected - bounded
                )
            )
        )

        entry: dict[str, object] = {
            "sum_drift": float(
                sum_drift
            ),
            "mean_drift": mean_drift,
            "global_bound_defect": (
                global_bound_defect
            ),
            "maximum_difference_from_v27": (
                corrected_bounded_difference
            ),
        }

        if name == "smooth":
            exact = shape.smooth_periodic_field(
                x
                - REPEATED_STEP_COUNT
                * displacement_x,
                y
                - REPEATED_STEP_COUNT
                * displacement_y,
            )

            entry[
                "maximum_error_against_exact"
            ] = float(
                np.max(
                    np.abs(
                        corrected - exact
                    )
                )
            )

        print()
        print(name)

        print(
            "  dérive somme      :",
            f"{float(sum_drift):.9e}",
        )

        print(
            "  dérive moyenne    :",
            f"{mean_drift:.9e}",
        )

        print(
            "  défaut de borne   :",
            f"{global_bound_defect:.3e}",
        )

        print(
            "  écart maximal V27 :",
            f"{corrected_bounded_difference:.9e}",
        )

        if (
            float(sum_drift)
            > SUM_TOLERANCE
        ):
            raise RuntimeError(
                "La somme dérive après transports "
                f"répétés pour {name}."
            )

        if (
            global_bound_defect
            > BOUND_TOLERANCE
        ):
            raise RuntimeError(
                "Les bornes globales sont violées "
                f"pour {name}."
            )

        report[name] = entry

    return report


def main() -> None:
    print(
        "=== VALIDATION DU CUBIQUE LOCAL "
        "À SOMME PRÉSERVÉE — ITD V28 ==="
    )

    validate_api_and_compatibility()

    aggregates, cases = (
        run_phase_envelope()
    )

    linf_order = fitted_order(
        aggregates,
        "worst_linf",
    )

    l2_order = fitted_order(
        aggregates,
        "worst_l2_rms",
    )

    l1_order = fitted_order(
        aggregates,
        "worst_l1_mean",
    )

    print()
    print(
        "=== ORDRES AJUSTÉS SUR LES "
        "TROIS RÉSOLUTIONS FINES ==="
    )

    print(
        "L∞ :",
        f"{linf_order:.9f}",
    )

    print(
        "L2 :",
        f"{l2_order:.9f}",
    )

    print(
        "L1 :",
        f"{l1_order:.9f}",
    )

    if linf_order < 1.5:
        raise RuntimeError(
            "L'ordre L∞ de V28 est insuffisant."
        )

    if l2_order < 2.5:
        raise RuntimeError(
            "L'ordre L2 de V28 est insuffisant."
        )

    if l1_order < 3.5:
        raise RuntimeError(
            "L'ordre L1 de V28 est insuffisant."
        )

    repeated_report = repeated_stress()

    finest = aggregates[-1]

    report = {
        "version": "ITD V28",
        "status": (
            "local_bound_preserving_"
            "cubic_sum_preserving_candidate"
        ),
        "algorithm": (
            "Local convex limiting followed by "
            "periodically expanding localized "
            "capacity redistribution."
        ),
        "target": (
            "Discrete sum of the unlimited cubic "
            "interpolant."
        ),
        "grid_sizes": list(
            GRID_SIZES
        ),
        "phase_count": len(
            phase_validation.phase_nodes()
        ),
        "phase_aggregates": aggregates,
        "phase_cases": cases,
        "fitted_orders": {
            "linf": linf_order,
            "l2_rms": l2_order,
            "l1_mean": l1_order,
        },
        "repeated_stress": (
            repeated_report
        ),
        "claims": {
            "local_departure_bounds": True,
            "cubic_candidate_sum_preserved": True,
            "constant_translation_source_sum": True,
            "localized_correction": True,
            "flux_form_conservation": False,
            "compressible_flow_mass_conservation": False,
        },
        "global": {
            "success": True,
            "maximum_fine_target_sum_error": (
                finest[
                    "maximum_target_sum_error"
                ]
            ),
            "maximum_fine_correction_count": (
                finest[
                    "maximum_correction_count"
                ]
            ),
            "historical_modes_preserved": True,
            "new_mode_optional": True,
        },
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "Compatibilité V27 → V28             : VALIDÉE"
    )

    print(
        "Bornes locales                      : VALIDÉES"
    )

    print(
        "Somme du candidat cubique           : PRÉSERVÉE"
    )

    print(
        "Correction globale                  : ABSENTE"
    )

    print(
        "Conservation en forme flux          : NON REVENDIQUÉE"
    )

    print(
        "Mode V28                            : OPTIONNEL"
    )

    print(
        "Rapport :",
        OUTPUT_PATH.resolve(),
    )


if __name__ == "__main__":
    main()
