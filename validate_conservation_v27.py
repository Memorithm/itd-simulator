#!/usr/bin/env python3

from __future__ import annotations

import gc
import json
import math
from pathlib import Path

import numpy as np

import itd_v27
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

STRESS_GRID_SIZE = 256

STRESS_STEP_COUNTS = (
    1,
    8,
    64,
)

BOUND_TOLERANCE = 8.0e-12

OUTPUT_PATH = Path(
    "itd_v27_results"
    "/conservation_audit_v27.json"
)


def observed_order(
    coarse_error: float,
    fine_error: float,
    coarse_spacing: float,
    fine_spacing: float,
) -> float:
    values = (
        coarse_error,
        fine_error,
        coarse_spacing,
        fine_spacing,
    )

    if not all(
        np.isfinite(value)
        and value > 0.0
        for value in values
    ):
        raise ValueError(
            "Les erreurs et les pas doivent être "
            "finis et strictement positifs."
        )

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

    errors = np.asarray(
        [
            float(row[key])
            for row in tail
        ],
        dtype=np.float64,
    )

    if (
        not np.all(
            np.isfinite(errors)
        )
        or np.any(errors <= 0.0)
    ):
        return None

    slope, _ = np.polyfit(
        np.log(spacings),
        np.log(errors),
        1,
    )

    return float(slope)


def pairwise_orders(
    rows: list[dict[str, object]],
    key: str,
) -> list[float | None]:
    orders: list[float | None] = []

    for index in range(
        1,
        len(rows),
    ):
        coarse = float(
            rows[index - 1][key]
        )

        fine = float(
            rows[index][key]
        )

        if (
            coarse <= 0.0
            or fine <= 0.0
        ):
            orders.append(None)
            continue

        orders.append(
            observed_order(
                coarse,
                fine,
                float(
                    rows[index - 1][
                        "spacing"
                    ]
                ),
                float(
                    rows[index][
                        "spacing"
                    ]
                ),
            )
        )

    return orders


def classify_order(
    order: float | None,
    expected: float,
) -> str:
    if order is None:
        return "roundoff_or_unresolved"

    distance = abs(
        order - expected
    )

    if distance <= 0.40:
        return (
            f"compatible_with_order_{expected:g}"
        )

    if distance <= 0.80:
        return (
            f"approaching_order_{expected:g}"
        )

    return "not_yet_compatible"


def transport_once(
    field: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    mode: str,
) -> np.ndarray:
    return local.transport_once(
        field,
        coordinates,
        displacement_x,
        displacement_y,
        mode,
    )


def conservation_defects(
    source: np.ndarray,
    result: np.ndarray,
) -> dict[str, float]:
    source_sum = float(
        np.sum(
            source,
            dtype=np.float64,
        )
    )

    result_sum = float(
        np.sum(
            result,
            dtype=np.float64,
        )
    )

    source_mean = float(
        np.mean(
            source,
            dtype=np.float64,
        )
    )

    result_mean = float(
        np.mean(
            result,
            dtype=np.float64,
        )
    )

    return {
        "source_sum": source_sum,
        "result_sum": result_sum,
        "absolute_sum_drift": abs(
            result_sum - source_sum
        ),
        "signed_sum_drift": (
            result_sum - source_sum
        ),
        "absolute_mean_drift": abs(
            result_mean - source_mean
        ),
        "signed_mean_drift": (
            result_mean - source_mean
        ),
    }


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
        itd_v27
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


def run_smooth_phase_case(
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

    results: dict[
        str,
        dict[str, object],
    ] = {}

    cubic = transport_once(
        source,
        coordinates,
        displacement_x,
        displacement_y,
        "cubic_periodic",
    )

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
    ):
        result = transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            mode,
        )

        defects = conservation_defects(
            source,
            result,
        )

        mode_result: dict[str, object] = {
            **defects,
        }

        if (
            mode
            == "cubic_local_bounded_periodic"
        ):
            activation_tolerance = (
                256.0
                * np.finfo(np.float64).eps
                * max(
                    1.0,
                    float(
                        np.max(
                            np.abs(cubic)
                        )
                    ),
                )
            )

            active = (
                np.abs(
                    result - cubic
                )
                > activation_tolerance
            )

            mode_result[
                "active_count"
            ] = int(
                np.count_nonzero(active)
            )

            mode_result[
                "active_fraction"
            ] = float(
                np.mean(active)
            )

            mode_result[
                "local_bound_defect"
            ] = local_bound_defect(
                source,
                result,
                coordinates,
                displacement_x,
                displacement_y,
            )

        results[mode] = mode_result

    return {
        "grid_size": grid_size,
        "spacing": float(spacing),
        "phase_x": float(phase_x),
        "phase_y": float(phase_y),
        "modes": results,
    }


def aggregate_smooth_grid(
    grid_size: int,
    phases: list[
        tuple[float, float]
    ],
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
]:
    cases = [
        run_smooth_phase_case(
            grid_size,
            phase_x,
            phase_y,
        )
        for phase_x, phase_y in phases
    ]

    for case in cases:
        defect = float(
            case["modes"][
                "cubic_local_bounded_periodic"
            ][
                "local_bound_defect"
            ]
        )

        if defect > BOUND_TOLERANCE:
            raise RuntimeError(
                "Violation des bornes locales dans "
                "l'audit de conservation."
            )

    aggregate: dict[str, object] = {
        "grid_size": grid_size,
        "spacing": float(
            cases[0]["spacing"]
        ),
        "phase_count": len(cases),
    }

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
    ):
        aggregate[
            f"{mode}_worst_mean_drift"
        ] = max(
            float(
                case["modes"][mode][
                    "absolute_mean_drift"
                ]
            )
            for case in cases
        )

        aggregate[
            f"{mode}_worst_sum_drift"
        ] = max(
            float(
                case["modes"][mode][
                    "absolute_sum_drift"
                ]
            )
            for case in cases
        )

    bounded_mode = (
        "cubic_local_bounded_periodic"
    )

    aggregate[
        "maximum_active_count"
    ] = max(
        int(
            case["modes"][
                bounded_mode
            ][
                "active_count"
            ]
        )
        for case in cases
    )

    aggregate[
        "maximum_active_fraction"
    ] = max(
        float(
            case["modes"][
                bounded_mode
            ][
                "active_fraction"
            ]
        )
        for case in cases
    )

    aggregate[
        "maximum_local_bound_defect"
    ] = max(
        float(
            case["modes"][
                bounded_mode
            ][
                "local_bound_defect"
            ]
        )
        for case in cases
    )

    return aggregate, cases


def repeated_transport(
    source: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    step_count: int,
) -> np.ndarray:
    current = np.asarray(
        source,
        dtype=np.float64,
    ).copy()

    for _ in range(step_count):
        current = transport_once(
            current,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_bounded_periodic",
        )

    return current


def stress_phase_subset(
    phases: list[
        tuple[float, float]
    ],
) -> list[tuple[float, float]]:
    indices = (
        0,
        1,
        5,
        10,
        16,
    )

    return [
        phases[index]
        for index in indices
    ]


def run_repeated_stress(
    phases: list[
        tuple[float, float]
    ],
) -> list[dict[str, object]]:
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

    rows: list[
        dict[str, object]
    ] = []

    field_builders = {
        "smooth": (
            lambda phase_x, phase_y:
            shape.smooth_periodic_field(
                x + phase_x * spacing,
                y + phase_y * spacing,
            )
        ),
        "sharp": (
            lambda phase_x, phase_y:
            shape.sharp_periodic_field(
                x + phase_x * spacing,
                y + phase_y * spacing,
            )
        ),
        "positive_bump": (
            lambda phase_x, phase_y:
            shape.positive_periodic_bump(
                x + phase_x * spacing,
                y + phase_y * spacing,
            )
        ),
    }

    for field_name, builder in (
        field_builders.items()
    ):
        for phase_x, phase_y in (
            stress_phase_subset(phases)
        ):
            source = builder(
                phase_x,
                phase_y,
            )

            for step_count in (
                STRESS_STEP_COUNTS
            ):
                result = repeated_transport(
                    source,
                    coordinates,
                    displacement_x,
                    displacement_y,
                    step_count,
                )

                defects = conservation_defects(
                    source,
                    result,
                )

                global_undershoot = max(
                    0.0,
                    float(np.min(source))
                    - float(np.min(result)),
                )

                global_overshoot = max(
                    0.0,
                    float(np.max(result))
                    - float(np.max(source)),
                )

                if max(
                    global_undershoot,
                    global_overshoot,
                ) > BOUND_TOLERANCE:
                    raise RuntimeError(
                        "Les bornes globales sont "
                        "violées pendant le stress."
                    )

                rows.append(
                    {
                        "field": field_name,
                        "phase_x": phase_x,
                        "phase_y": phase_y,
                        "step_count": step_count,
                        **defects,
                        "global_undershoot": (
                            global_undershoot
                        ),
                        "global_overshoot": (
                            global_overshoot
                        ),
                    }
                )

    return rows


def main() -> None:
    print(
        "=== AUDIT DE CONSERVATION "
        "— ITD V27.3 ==="
    )

    phases = (
        phase_validation.phase_nodes()
    )

    print(
        "Phases déterministes :",
        len(phases),
    )

    print()
    print(
        "grille | dérive moyenne bornée | "
        "ordre | dérive somme bornée | ordre | "
        "actifs max"
    )

    aggregates: list[
        dict[str, object]
    ] = []

    all_cases: dict[
        str,
        list[dict[str, object]],
    ] = {}

    previous = None

    bounded_mean_key = (
        "cubic_local_bounded_periodic"
        "_worst_mean_drift"
    )

    bounded_sum_key = (
        "cubic_local_bounded_periodic"
        "_worst_sum_drift"
    )

    for grid_size in GRID_SIZES:
        aggregate, cases = (
            aggregate_smooth_grid(
                grid_size,
                phases,
            )
        )

        aggregates.append(
            aggregate
        )

        all_cases[
            str(grid_size)
        ] = cases

        if previous is None:
            mean_order_text = "—"
            sum_order_text = "—"
        else:
            coarse_mean = float(
                previous[
                    bounded_mean_key
                ]
            )

            fine_mean = float(
                aggregate[
                    bounded_mean_key
                ]
            )

            coarse_sum = float(
                previous[
                    bounded_sum_key
                ]
            )

            fine_sum = float(
                aggregate[
                    bounded_sum_key
                ]
            )

            mean_order_text = (
                "—"
                if (
                    coarse_mean <= 0.0
                    or fine_mean <= 0.0
                )
                else (
                    f"{observed_order(
                        coarse_mean,
                        fine_mean,
                        float(previous['spacing']),
                        float(aggregate['spacing']),
                    ):.6f}"
                )
            )

            sum_order_text = (
                "—"
                if (
                    coarse_sum <= 0.0
                    or fine_sum <= 0.0
                )
                else (
                    f"{observed_order(
                        coarse_sum,
                        fine_sum,
                        float(previous['spacing']),
                        float(aggregate['spacing']),
                    ):.6f}"
                )
            )

        print(
            f"{grid_size:6d} | "
            f"{float(
                aggregate[
                    bounded_mean_key
                ]
            ):.9e} | "
            f"{mean_order_text:>8} | "
            f"{float(
                aggregate[
                    bounded_sum_key
                ]
            ):.9e} | "
            f"{sum_order_text:>8} | "
            f"{int(
                aggregate[
                    'maximum_active_count'
                ]
            ):10d}"
        )

        previous = aggregate

        gc.collect()

    mean_order = fitted_order(
        aggregates,
        bounded_mean_key,
    )

    sum_order = fitted_order(
        aggregates,
        bounded_sum_key,
    )

    active_fraction_order = (
        fitted_order(
            aggregates,
            "maximum_active_fraction",
        )
    )

    mean_classification = (
        classify_order(
            mean_order,
            4.0,
        )
    )

    sum_classification = (
        classify_order(
            sum_order,
            2.0,
        )
    )

    repeated_rows = run_repeated_stress(
        phases
    )

    stress_summary: dict[
        str,
        dict[str, float],
    ] = {}

    for field_name in (
        "smooth",
        "sharp",
        "positive_bump",
    ):
        matching = [
            row
            for row in repeated_rows
            if row["field"] == field_name
        ]

        stress_summary[field_name] = {
            "maximum_absolute_mean_drift": max(
                float(
                    row[
                        "absolute_mean_drift"
                    ]
                )
                for row in matching
            ),
            "maximum_absolute_sum_drift": max(
                float(
                    row[
                        "absolute_sum_drift"
                    ]
                )
                for row in matching
            ),
            "maximum_global_bound_defect": max(
                max(
                    float(
                        row[
                            "global_undershoot"
                        ]
                    ),
                    float(
                        row[
                            "global_overshoot"
                        ]
                    ),
                )
                for row in matching
            ),
        }

    finest = aggregates[-1]

    print()
    print(
        "=== CLASSIFICATION DE LA DÉRIVE LISSE ==="
    )

    print(
        "Ordre ajusté dérive moyenne :",
        (
            "non résolu"
            if mean_order is None
            else f"{mean_order:.9f}"
        ),
        mean_classification,
    )

    print(
        "Ordre ajusté dérive somme   :",
        (
            "non résolu"
            if sum_order is None
            else f"{sum_order:.9f}"
        ),
        sum_classification,
    )

    print(
        "Ordre fraction active       :",
        (
            "non résolu"
            if active_fraction_order is None
            else (
                f"{active_fraction_order:.9f}"
            )
        ),
    )

    print()
    print(
        "=== RÉFÉRENCES NON LIMITÉES "
        "À LA RÉSOLUTION FINE ==="
    )

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
    ):
        print(
            f"{mode:30s} "
            "dérive moyenne pire : "
            f"{float(
                finest[
                    f'{mode}_worst_mean_drift'
                ]
            ):.9e}"
        )

    print()
    print(
        "=== STRESS DE TRANSPORTS RÉPÉTÉS ==="
    )

    for field_name, summary in (
        stress_summary.items()
    ):
        print(
            f"{field_name:16s} | "
            "dérive moyenne max="
            f"{summary[
                'maximum_absolute_mean_drift'
            ]:.9e} | "
            "défaut borne max="
            f"{summary[
                'maximum_global_bound_defect'
            ]:.3e}"
        )

    report = {
        "version": "ITD V27.3",
        "status": (
            "conservation_defect_audit"
        ),
        "phase_count": len(phases),
        "grid_sizes": list(
            GRID_SIZES
        ),
        "smooth_phase_aggregates": (
            aggregates
        ),
        "smooth_phase_cases": all_cases,
        "pairwise_orders": {
            "bounded_mean_drift": (
                pairwise_orders(
                    aggregates,
                    bounded_mean_key,
                )
            ),
            "bounded_sum_drift": (
                pairwise_orders(
                    aggregates,
                    bounded_sum_key,
                )
            ),
        },
        "fitted_orders": {
            "bounded_mean_drift": (
                mean_order
            ),
            "bounded_sum_drift": (
                sum_order
            ),
            "active_fraction": (
                active_fraction_order
            ),
        },
        "classifications": {
            "bounded_mean_drift": (
                mean_classification
            ),
            "bounded_sum_drift": (
                sum_classification
            ),
        },
        "repeated_stress": {
            "grid_size": (
                STRESS_GRID_SIZE
            ),
            "step_counts": list(
                STRESS_STEP_COUNTS
            ),
            "phase_count": len(
                stress_phase_subset(
                    phases
                )
            ),
            "rows": repeated_rows,
            "summary": stress_summary,
        },
        "claims": {
            "local_bounds_preserved": True,
            "exact_sum_conservation": False,
            "conservation_defect_measured": True,
            "corrective_scheme_implemented": False,
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
