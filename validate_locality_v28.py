#!/usr/bin/env python3

from __future__ import annotations

import gc
import json
import math
from pathlib import Path

import numpy as np

import itd_v28
import validate_cubic_transport_v25 as base
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

STRESS_GRID_SIZE = 256
STRESS_STEP_COUNT = 64

BOUND_TOLERANCE = 8.0e-12
SUM_TOLERANCE = 5.0e-10

OUTPUT_PATH = Path(
    "itd_v28_results"
    "/locality_audit_v28.json"
)


def precise_sum(
    values: object,
) -> np.longdouble:
    array = np.asarray(
        values,
        dtype=np.longdouble,
    )

    if not np.all(
        np.isfinite(array)
    ):
        raise ValueError(
            "La somme précise exige des données finies."
        )

    return np.sum(
        array,
        dtype=np.longdouble,
    )


def fitted_order(
    rows: list[dict[str, object]],
    key: str,
    tail_size: int = 3,
) -> float | None:
    tail = rows[-tail_size:]

    spacings = np.asarray(
        [
            float(row["spacing"])
            for row in tail
        ],
        dtype=np.float64,
    )

    values = np.asarray(
        [
            float(row[key])
            for row in tail
        ],
        dtype=np.float64,
    )

    if (
        not np.all(
            np.isfinite(values)
        )
        or np.any(values <= 0.0)
    ):
        return None

    slope, _ = np.polyfit(
        np.log(spacings),
        np.log(values),
        1,
    )

    return float(slope)


def transport_once(
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

    return itd_v28.periodic_backtrace(
        source,
        coordinates,
        coordinates,
        velocity_x,
        velocity_y,
        1.0,
        interpolation=mode,
    )


def activation_tolerance(
    reference: np.ndarray,
) -> float:
    return float(
        256.0
        * np.finfo(np.float64).eps
        * max(
            1.0,
            float(
                np.max(
                    np.abs(reference)
                )
            ),
        )
    )


def periodic_nearest_distances(
    source_mask: np.ndarray,
    target_mask: np.ndarray,
) -> np.ndarray:
    """
    Distance périodique de Chebyshev entre chaque
    cellule du masque cible et la cellule source
    la plus proche.
    """
    source = np.asarray(
        source_mask,
        dtype=bool,
    )

    target = np.asarray(
        target_mask,
        dtype=bool,
    )

    if (
        source.ndim != 2
        or target.ndim != 2
        or source.shape != target.shape
    ):
        raise ValueError(
            "Les masques de localité doivent être "
            "bidimensionnels et de même forme."
        )

    source_indices = np.argwhere(
        source
    )

    target_indices = np.argwhere(
        target
    )

    if target_indices.size == 0:
        return np.asarray(
            (),
            dtype=np.int64,
        )

    if source_indices.size == 0:
        raise RuntimeError(
            "Une correction existe sans cellule "
            "initialement limitée."
        )

    size_y, size_x = source.shape

    distances: list[np.ndarray] = []

    # Les supports sont normalement petits. Le
    # traitement par blocs évite néanmoins toute
    # matrice temporaire excessive.
    block_size = 4096

    for start in range(
        0,
        target_indices.shape[0],
        block_size,
    ):
        block = target_indices[
            start :
            start + block_size
        ]

        delta_y = np.abs(
            block[:, None, 0]
            - source_indices[None, :, 0]
        )

        delta_x = np.abs(
            block[:, None, 1]
            - source_indices[None, :, 1]
        )

        periodic_y = np.minimum(
            delta_y,
            size_y - delta_y,
        )

        periodic_x = np.minimum(
            delta_x,
            size_x - delta_x,
        )

        chebyshev = np.maximum(
            periodic_y,
            periodic_x,
        )

        distances.append(
            np.min(
                chebyshev,
                axis=1,
            )
        )

    return np.concatenate(
        distances
    ).astype(
        np.int64,
        copy=False,
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

    undershoot = float(
        np.max(
            np.maximum(
                lower - result,
                0.0,
            )
        )
    )

    overshoot = float(
        np.max(
            np.maximum(
                result - upper,
                0.0,
            )
        )
    )

    return max(
        undershoot,
        overshoot,
    )


def analyze_transport(
    source: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
) -> dict[str, object]:
    cubic = transport_once(
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_periodic",
    )

    bounded = transport_once(
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_local_bounded_periodic",
    )

    corrected = transport_once(
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_local_sum_preserving_periodic",
    )

    tolerance = activation_tolerance(
        cubic
    )

    seed_mask = (
        np.abs(
            bounded - cubic
        )
        > tolerance
    )

    correction_mask = (
        np.abs(
            corrected - bounded
        )
        > tolerance
    )

    seed_count = int(
        np.count_nonzero(
            seed_mask
        )
    )

    correction_count = int(
        np.count_nonzero(
            correction_mask
        )
    )

    distances = periodic_nearest_distances(
        seed_mask,
        correction_mask,
    )

    if distances.size == 0:
        maximum_radius = 0
        mean_radius = 0.0
        radius_histogram: dict[str, int] = {}
    else:
        maximum_radius = int(
            np.max(distances)
        )

        mean_radius = float(
            np.mean(distances)
        )

        unique, counts = np.unique(
            distances,
            return_counts=True,
        )

        radius_histogram = {
            str(int(radius)): int(count)
            for radius, count in zip(
                unique,
                counts,
            )
        }

    correction = (
        corrected - bounded
    )

    target_sum_error = abs(
        precise_sum(corrected)
        - precise_sum(cubic)
    )

    bounded_sum_defect = (
        precise_sum(cubic)
        - precise_sum(bounded)
    )

    applied_sum_correction = (
        precise_sum(corrected)
        - precise_sum(bounded)
    )

    bound_defect = local_bound_defect(
        source,
        corrected,
        coordinates,
        displacement_x,
        displacement_y,
    )

    if float(target_sum_error) > SUM_TOLERANCE:
        raise RuntimeError(
            "La somme cible n'est pas respectée."
        )

    if bound_defect > BOUND_TOLERANCE:
        raise RuntimeError(
            "Une correction viole les bornes locales."
        )

    if (
        correction_count > 0
        and seed_count == 0
    ):
        raise RuntimeError(
            "Une correction existe sans support limité."
        )

    return {
        "seed_count": seed_count,
        "correction_count": correction_count,
        "seed_fraction": float(
            seed_count / source.size
        ),
        "correction_fraction": float(
            correction_count
            / source.size
        ),
        "support_expansion_ratio": (
            float(
                correction_count
                / seed_count
            )
            if seed_count > 0
            else 0.0
        ),
        "maximum_periodic_radius": (
            maximum_radius
        ),
        "mean_periodic_radius": (
            mean_radius
        ),
        "radius_histogram": (
            radius_histogram
        ),
        "maximum_pointwise_correction": float(
            np.max(
                np.abs(correction)
            )
        ),
        "l1_mean_correction": float(
            np.mean(
                np.abs(correction)
            )
        ),
        "target_sum_error": float(
            target_sum_error
        ),
        "bounded_sum_defect": float(
            bounded_sum_defect
        ),
        "applied_sum_correction": float(
            applied_sum_correction
        ),
        "local_bound_defect": (
            bound_defect
        ),
    }


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

    analysis = analyze_transport(
        source,
        coordinates,
        displacement_x,
        displacement_y,
    )

    return {
        "grid_size": grid_size,
        "spacing": float(spacing),
        "phase_x": float(phase_x),
        "phase_y": float(phase_y),
        **analysis,
    }


def aggregate_grid(
    grid_size: int,
    phases: list[
        tuple[float, float]
    ],
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
]:
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
        "phase_count": len(cases),
        "maximum_seed_count": max(
            int(case["seed_count"])
            for case in cases
        ),
        "maximum_correction_count": max(
            int(case["correction_count"])
            for case in cases
        ),
        "maximum_seed_fraction": max(
            float(case["seed_fraction"])
            for case in cases
        ),
        "maximum_correction_fraction": max(
            float(
                case[
                    "correction_fraction"
                ]
            )
            for case in cases
        ),
        "maximum_support_expansion_ratio": max(
            float(
                case[
                    "support_expansion_ratio"
                ]
            )
            for case in cases
        ),
        "maximum_periodic_radius": max(
            int(
                case[
                    "maximum_periodic_radius"
                ]
            )
            for case in cases
        ),
        "maximum_mean_periodic_radius": max(
            float(
                case[
                    "mean_periodic_radius"
                ]
            )
            for case in cases
        ),
        "maximum_pointwise_correction": max(
            float(
                case[
                    "maximum_pointwise_correction"
                ]
            )
            for case in cases
        ),
        "maximum_l1_mean_correction": max(
            float(
                case[
                    "l1_mean_correction"
                ]
            )
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
        "maximum_local_bound_defect": max(
            float(
                case[
                    "local_bound_defect"
                ]
            )
            for case in cases
        ),
    }

    return aggregate, cases


def run_phase_audit() -> tuple[
    list[dict[str, object]],
    dict[str, list[dict[str, object]]],
]:
    phases = (
        phase_validation.phase_nodes()
    )

    print(
        "=== LOCALITÉ SUR LA FAMILLE DE PHASES ==="
    )

    print(
        "Nombre de phases :",
        len(phases),
    )

    print()
    print(
        "grille | graines max | corrigées max | "
        "rayon max | expansion max | "
        "fraction corrigée | correction max"
    )

    aggregates: list[
        dict[str, object]
    ] = []

    all_cases: dict[
        str,
        list[dict[str, object]],
    ] = {}

    for grid_size in GRID_SIZES:
        aggregate, cases = aggregate_grid(
            grid_size,
            phases,
        )

        aggregates.append(
            aggregate
        )

        all_cases[
            str(grid_size)
        ] = cases

        print(
            f"{grid_size:6d} | "
            f"{int(aggregate['maximum_seed_count']):11d} | "
            f"{int(aggregate['maximum_correction_count']):13d} | "
            f"{int(aggregate['maximum_periodic_radius']):9d} | "
            f"{float(
                aggregate[
                    'maximum_support_expansion_ratio'
                ]
            ):13.6f} | "
            f"{float(
                aggregate[
                    'maximum_correction_fraction'
                ]
            ):.9e} | "
            f"{float(
                aggregate[
                    'maximum_pointwise_correction'
                ]
            ):.9e}"
        )

        gc.collect()

    return aggregates, all_cases


def repeated_field(
    name: str,
    source: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
) -> dict[str, object]:
    current = np.asarray(
        source,
        dtype=np.float64,
    ).copy()

    source_sum = precise_sum(
        source
    )

    step_rows: list[
        dict[str, object]
    ] = []

    for step in range(
        1,
        STRESS_STEP_COUNT + 1,
    ):
        analysis = analyze_transport(
            current,
            coordinates,
            displacement_x,
            displacement_y,
        )

        current = transport_once(
            current,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_sum_preserving_periodic",
        )

        step_rows.append(
            {
                "step": step,
                **analysis,
            }
        )

    final_sum_drift = abs(
        precise_sum(current)
        - source_sum
    )

    global_bound_defect = max(
        max(
            0.0,
            float(np.min(source))
            - float(np.min(current)),
        ),
        max(
            0.0,
            float(np.max(current))
            - float(np.max(source)),
        ),
    )

    return {
        "field": name,
        "step_count": (
            STRESS_STEP_COUNT
        ),
        "maximum_seed_count": max(
            int(row["seed_count"])
            for row in step_rows
        ),
        "maximum_correction_count": max(
            int(row["correction_count"])
            for row in step_rows
        ),
        "maximum_periodic_radius": max(
            int(
                row[
                    "maximum_periodic_radius"
                ]
            )
            for row in step_rows
        ),
        "maximum_support_expansion_ratio": max(
            float(
                row[
                    "support_expansion_ratio"
                ]
            )
            for row in step_rows
        ),
        "maximum_target_sum_error": max(
            float(
                row[
                    "target_sum_error"
                ]
            )
            for row in step_rows
        ),
        "final_sum_drift": float(
            final_sum_drift
        ),
        "global_bound_defect": (
            global_bound_defect
        ),
        "steps": step_rows,
    }


def run_repeated_audit() -> list[
    dict[str, object]
]:
    print()
    print(
        "=== LOCALITÉ SUR 64 TRANSPORTS ==="
    )

    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        STRESS_GRID_SIZE
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

    rows: list[
        dict[str, object]
    ] = []

    print(
        "champ | graines max | corrigées max | "
        "rayon max | expansion max | "
        "dérive somme finale"
    )

    for name, source in fields.items():
        result = repeated_field(
            name,
            source,
            coordinates,
            displacement_x,
            displacement_y,
        )

        rows.append(result)

        print(
            f"{name:14s} | "
            f"{int(result['maximum_seed_count']):11d} | "
            f"{int(result['maximum_correction_count']):13d} | "
            f"{int(result['maximum_periodic_radius']):9d} | "
            f"{float(
                result[
                    'maximum_support_expansion_ratio'
                ]
            ):13.6f} | "
            f"{float(
                result[
                    'final_sum_drift'
                ]
            ):.9e}"
        )

        if (
            float(
                result[
                    "final_sum_drift"
                ]
            )
            > SUM_TOLERANCE
        ):
            raise RuntimeError(
                "La somme dérive excessivement "
                f"pour {name}."
            )

        if (
            float(
                result[
                    "global_bound_defect"
                ]
            )
            > BOUND_TOLERANCE
        ):
            raise RuntimeError(
                "Les bornes globales sont violées "
                f"pour {name}."
            )

    return rows


def main() -> None:
    print(
        "=== AUDIT DE LOCALITÉ DE LA "
        "CORRECTION — ITD V28.1 ==="
    )

    aggregates, cases = (
        run_phase_audit()
    )

    repeated = run_repeated_audit()

    correction_fraction_order = (
        fitted_order(
            aggregates,
            "maximum_correction_fraction",
        )
    )

    correction_amplitude_order = (
        fitted_order(
            aggregates,
            "maximum_pointwise_correction",
        )
    )

    correction_l1_order = (
        fitted_order(
            aggregates,
            "maximum_l1_mean_correction",
        )
    )

    maximum_radius = max(
        int(
            row[
                "maximum_periodic_radius"
            ]
        )
        for row in aggregates
    )

    fine_radius = int(
        aggregates[-1][
            "maximum_periodic_radius"
        ]
    )

    maximum_correction_count = max(
        int(
            row[
                "maximum_correction_count"
            ]
        )
        for row in aggregates
    )

    fine_correction_count = int(
        aggregates[-1][
            "maximum_correction_count"
        ]
    )

    print()
    print(
        "=== STRUCTURE ASYMPTOTIQUE "
        "DE LA CORRECTION ==="
    )

    print(
        "Ordre fraction corrigée :",
        (
            "non résolu"
            if correction_fraction_order is None
            else (
                f"{correction_fraction_order:.9f}"
            )
        ),
    )

    print(
        "Ordre amplitude correction:",
        (
            "non résolu"
            if correction_amplitude_order is None
            else (
                f"{correction_amplitude_order:.9f}"
            )
        ),
    )

    print(
        "Ordre correction L1      :",
        (
            "non résolu"
            if correction_l1_order is None
            else (
                f"{correction_l1_order:.9f}"
            )
        ),
    )

    print(
        "Rayon maximal observé    :",
        maximum_radius,
    )

    print(
        "Rayon à N=1024           :",
        fine_radius,
    )

    print(
        "Support maximal observé  :",
        maximum_correction_count,
    )

    print(
        "Support à N=1024         :",
        fine_correction_count,
    )

    if any(
        float(
            row[
                "maximum_target_sum_error"
            ]
        )
        > SUM_TOLERANCE
        for row in aggregates
    ):
        raise RuntimeError(
            "La conservation par pas a échoué."
        )

    if any(
        float(
            row[
                "maximum_local_bound_defect"
            ]
        )
        > BOUND_TOLERANCE
        for row in aggregates
    ):
        raise RuntimeError(
            "Les bornes locales ont été violées."
        )

    report = {
        "version": "ITD V28.1",
        "status": (
            "localized_correction_support_audit"
        ),
        "grid_sizes": list(
            GRID_SIZES
        ),
        "phase_count": len(
            phase_validation.phase_nodes()
        ),
        "phase_aggregates": (
            aggregates
        ),
        "phase_cases": cases,
        "repeated_transport": repeated,
        "fitted_orders": {
            "correction_fraction": (
                correction_fraction_order
            ),
            "correction_amplitude": (
                correction_amplitude_order
            ),
            "correction_l1_mean": (
                correction_l1_order
            ),
        },
        "summary": {
            "maximum_observed_radius": (
                maximum_radius
            ),
            "fine_grid_radius": (
                fine_radius
            ),
            "maximum_observed_correction_count": (
                maximum_correction_count
            ),
            "fine_grid_correction_count": (
                fine_correction_count
            ),
        },
        "claims": {
            "local_bounds_preserved": True,
            "cubic_candidate_sum_preserved": True,
            "correction_support_measured": True,
            "grid_independent_locality_proof": False,
            "flux_form_conservation": False,
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
        "Rapport :",
        OUTPUT_PATH.resolve(),
    )


if __name__ == "__main__":
    main()
