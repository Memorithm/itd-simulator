#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import itd_v29 as itd_v28
import validate_cubic_transport_v25 as base
import validate_shape_stability_v26 as shape


GRID_SIZES = (
    32,
    64,
    128,
    256,
    512,
)

TIME_INTERVALS = (
    (0.00, 0.07),
    (0.13, 0.31),
    (0.41, 0.73),
)

COORDINATE_TOLERANCE = 2.0e-13
BOUND_TOLERANCE = 2.0e-13
RESULT_BOUND_TOLERANCE = 5.0e-12
SUM_TOLERANCE = 5.0e-10

OUTPUT_PATH = Path(
    "itd_v29_results"
    "/rk4_departure_consistency.json"
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


def variable_periodic_velocity(
    x: object,
    y: object,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    x_values, y_values = np.broadcast_arrays(
        np.asarray(
            x,
            dtype=np.float64,
        ),
        np.asarray(
            y,
            dtype=np.float64,
        ),
    )

    length = float(
        base.DOMAIN_LENGTH
    )

    phase_x = (
        2.0 * np.pi * x_values
        / length
    )

    phase_y = (
        2.0 * np.pi * y_values
        / length
    )

    velocity_x = (
        0.37
        + 0.18 * np.sin(
            phase_y + 0.31 * time
        )
        + 0.07 * np.cos(
            phase_x - phase_y
        )
    )

    velocity_y = (
        -0.29
        + 0.14 * np.cos(
            phase_x - 0.27 * time
        )
        - 0.05 * np.sin(
            phase_x + phase_y
        )
    )

    return (
        np.asarray(
            velocity_x,
            dtype=np.float64,
        ),
        np.asarray(
            velocity_y,
            dtype=np.float64,
        ),
    )


def wrap(
    values: object,
    origin: float,
    period: float,
) -> np.ndarray:
    return (
        origin
        + np.mod(
            np.asarray(
                values,
                dtype=np.float64,
            )
            - origin,
            period,
        )
    )


def periodic_distance(
    left: object,
    right: object,
    period: float,
) -> np.ndarray:
    difference = np.abs(
        np.asarray(
            left,
            dtype=np.float64,
        )
        - np.asarray(
            right,
            dtype=np.float64,
        )
    )

    return np.minimum(
        difference,
        period - difference,
    )


def direct_departure_bounds(
    field: np.ndarray,
    x_coordinates: np.ndarray,
    y_coordinates: np.ndarray,
    departure_x: np.ndarray,
    departure_y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    x_values, x_origin, x_period = (
        itd_v28.periodic_coordinate_geometry(
            x_coordinates,
            "x",
        )
    )

    y_values, y_origin, y_period = (
        itd_v28.periodic_coordinate_geometry(
            y_coordinates,
            "y",
        )
    )

    wrapped_x = wrap(
        departure_x,
        x_origin,
        x_period,
    )

    wrapped_y = wrap(
        departure_y,
        y_origin,
        y_period,
    )

    spacing_x = float(
        x_values[1] - x_values[0]
    )

    spacing_y = float(
        y_values[1] - y_values[0]
    )

    coordinate_x = (
        wrapped_x - x_origin
    ) / spacing_x

    coordinate_y = (
        wrapped_y - y_origin
    ) / spacing_y

    index_x0 = (
        np.floor(
            coordinate_x
        ).astype(np.int64)
        % x_values.size
    )

    index_y0 = (
        np.floor(
            coordinate_y
        ).astype(np.int64)
        % y_values.size
    )

    index_x1 = (
        index_x0 + 1
    ) % x_values.size

    index_y1 = (
        index_y0 + 1
    ) % y_values.size

    value_00 = field[
        index_y0,
        index_x0,
    ]

    value_10 = field[
        index_y0,
        index_x1,
    ]

    value_01 = field[
        index_y1,
        index_x0,
    ]

    value_11 = field[
        index_y1,
        index_x1,
    ]

    lower = np.minimum.reduce(
        (
            value_00,
            value_10,
            value_01,
            value_11,
        )
    )

    upper = np.maximum.reduce(
        (
            value_00,
            value_10,
            value_01,
            value_11,
        )
    )

    return lower, upper


def direct_cell_indices(
    x_coordinates: np.ndarray,
    y_coordinates: np.ndarray,
    departure_x: np.ndarray,
    departure_y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    x_values, x_origin, x_period = (
        itd_v28.periodic_coordinate_geometry(
            x_coordinates,
            "x",
        )
    )

    y_values, y_origin, y_period = (
        itd_v28.periodic_coordinate_geometry(
            y_coordinates,
            "y",
        )
    )

    spacing_x = float(
        x_values[1] - x_values[0]
    )

    spacing_y = float(
        y_values[1] - y_values[0]
    )

    wrapped_x = wrap(
        departure_x,
        x_origin,
        x_period,
    )

    wrapped_y = wrap(
        departure_y,
        y_origin,
        y_period,
    )

    index_x = (
        np.floor(
            (
                wrapped_x - x_origin
            )
            / spacing_x
        ).astype(np.int64)
        % x_values.size
    )

    index_y = (
        np.floor(
            (
                wrapped_y - y_origin
            )
            / spacing_y
        ).astype(np.int64)
        % y_values.size
    )

    return index_x, index_y


def run_case(
    grid_size: int,
    previous_time: float,
    current_time: float,
) -> dict[str, object]:
    (
        coordinates,
        x,
        y,
        _,
    ) = base.build_periodic_grid(
        grid_size
    )

    field = shape.smooth_periodic_field(
        x,
        y,
    )

    delta_time = float(
        current_time - previous_time
    )

    departure_x, departure_y = (
        itd_v28.rk4_periodic_departure_points(
            x,
            y,
            coordinates,
            coordinates,
            previous_time,
            current_time,
            variable_periodic_velocity,
        )
    )

    effective_velocity_x = (
        x - departure_x
    ) / delta_time

    effective_velocity_y = (
        y - departure_y
    ) / delta_time

    reconstructed_x = (
        x
        - delta_time
        * effective_velocity_x
    )

    reconstructed_y = (
        y
        - delta_time
        * effective_velocity_y
    )

    _, x_origin, x_period = (
        itd_v28.periodic_coordinate_geometry(
            coordinates,
            "x",
        )
    )

    _, y_origin, y_period = (
        itd_v28.periodic_coordinate_geometry(
            coordinates,
            "y",
        )
    )

    wrapped_departure_x = wrap(
        departure_x,
        x_origin,
        x_period,
    )

    wrapped_departure_y = wrap(
        departure_y,
        y_origin,
        y_period,
    )

    wrapped_reconstructed_x = wrap(
        reconstructed_x,
        x_origin,
        x_period,
    )

    wrapped_reconstructed_y = wrap(
        reconstructed_y,
        y_origin,
        y_period,
    )

    coordinate_error_x = float(
        np.max(
            periodic_distance(
                wrapped_departure_x,
                wrapped_reconstructed_x,
                x_period,
            )
        )
    )

    coordinate_error_y = float(
        np.max(
            periodic_distance(
                wrapped_departure_y,
                wrapped_reconstructed_y,
                y_period,
            )
        )
    )

    direct_index_x, direct_index_y = (
        direct_cell_indices(
            coordinates,
            coordinates,
            departure_x,
            departure_y,
        )
    )

    reconstructed_index_x, reconstructed_index_y = (
        direct_cell_indices(
            coordinates,
            coordinates,
            reconstructed_x,
            reconstructed_y,
        )
    )

    index_mismatch_count = int(
        np.count_nonzero(
            (
                direct_index_x
                != reconstructed_index_x
            )
            |
            (
                direct_index_y
                != reconstructed_index_y
            )
        )
    )

    direct_lower, direct_upper = (
        direct_departure_bounds(
            field,
            coordinates,
            coordinates,
            departure_x,
            departure_y,
        )
    )

    module_lower, module_upper = (
        itd_v28.periodic_bilinear_departure_bounds(
            field,
            coordinates,
            coordinates,
            effective_velocity_x,
            effective_velocity_y,
            delta_time,
        )
    )

    lower_error = float(
        np.max(
            np.abs(
                direct_lower
                - module_lower
            )
        )
    )

    upper_error = float(
        np.max(
            np.abs(
                direct_upper
                - module_upper
            )
        )
    )

    cubic = (
        itd_v28
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            previous_time,
            current_time,
            variable_periodic_velocity,
            transport_interpolation=(
                "cubic_periodic"
            ),
            transport_trajectory_method=(
                "rk4_backtrace"
            ),
        )
    )

    bounded = (
        itd_v28
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            previous_time,
            current_time,
            variable_periodic_velocity,
            transport_interpolation=(
                "cubic_local_bounded_periodic"
            ),
            transport_trajectory_method=(
                "rk4_backtrace"
            ),
        )
    )

    sum_preserving = (
        itd_v28
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            previous_time,
            current_time,
            variable_periodic_velocity,
            transport_interpolation=(
                "cubic_local_sum_preserving_periodic"
            ),
            transport_trajectory_method=(
                "rk4_backtrace"
            ),
        )
    )

    bounded_defect = max(
        float(
            np.max(
                np.maximum(
                    direct_lower
                    - bounded,
                    0.0,
                )
            )
        ),
        float(
            np.max(
                np.maximum(
                    bounded
                    - direct_upper,
                    0.0,
                )
            )
        ),
    )

    sum_preserving_bound_defect = max(
        float(
            np.max(
                np.maximum(
                    direct_lower
                    - sum_preserving,
                    0.0,
                )
            )
        ),
        float(
            np.max(
                np.maximum(
                    sum_preserving
                    - direct_upper,
                    0.0,
                )
            )
        ),
    )

    sum_error = float(
        abs(
            precise_sum(
                sum_preserving
            )
            - precise_sum(
                cubic
            )
        )
    )

    return {
        "grid_size": grid_size,
        "previous_time": previous_time,
        "current_time": current_time,
        "delta_time": delta_time,
        "coordinate_error_x": (
            coordinate_error_x
        ),
        "coordinate_error_y": (
            coordinate_error_y
        ),
        "index_mismatch_count": (
            index_mismatch_count
        ),
        "lower_bound_error": (
            lower_error
        ),
        "upper_bound_error": (
            upper_error
        ),
        "bounded_result_defect": (
            bounded_defect
        ),
        "sum_preserving_result_defect": (
            sum_preserving_bound_defect
        ),
        "sum_preservation_error": (
            sum_error
        ),
    }


def main() -> None:
    print(
        "=== COHÉRENCE RK4 → INTERPOLATION "
        "→ BORNES — ITD V29.0-R1-RK4 ==="
    )

    print()
    print(
        "grille | intervalle | erreur coord. | "
        "cellules différentes | erreur bornes | "
        "défaut résultat | erreur somme"
    )

    rows: list[
        dict[str, object]
    ] = []

    for grid_size in GRID_SIZES:
        for (
            previous_time,
            current_time,
        ) in TIME_INTERVALS:
            row = run_case(
                grid_size,
                previous_time,
                current_time,
            )

            rows.append(row)

            coordinate_error = max(
                float(
                    row[
                        "coordinate_error_x"
                    ]
                ),
                float(
                    row[
                        "coordinate_error_y"
                    ]
                ),
            )

            bound_error = max(
                float(
                    row[
                        "lower_bound_error"
                    ]
                ),
                float(
                    row[
                        "upper_bound_error"
                    ]
                ),
            )

            result_defect = max(
                float(
                    row[
                        "bounded_result_defect"
                    ]
                ),
                float(
                    row[
                        "sum_preserving_result_defect"
                    ]
                ),
            )

            print(
                f"{grid_size:6d} | "
                f"[{previous_time:.2f},{current_time:.2f}] | "
                f"{coordinate_error:.3e} | "
                f"{int(
                    row[
                        'index_mismatch_count'
                    ]
                ):20d} | "
                f"{bound_error:.3e} | "
                f"{result_defect:.3e} | "
                f"{float(
                    row[
                        'sum_preservation_error'
                    ]
                ):.3e}"
            )

    maximum_coordinate_error = max(
        max(
            float(
                row[
                    "coordinate_error_x"
                ]
            ),
            float(
                row[
                    "coordinate_error_y"
                ]
            ),
        )
        for row in rows
    )

    total_index_mismatches = sum(
        int(
            row[
                "index_mismatch_count"
            ]
        )
        for row in rows
    )

    maximum_bound_error = max(
        max(
            float(
                row[
                    "lower_bound_error"
                ]
            ),
            float(
                row[
                    "upper_bound_error"
                ]
            ),
        )
        for row in rows
    )

    maximum_result_defect = max(
        max(
            float(
                row[
                    "bounded_result_defect"
                ]
            ),
            float(
                row[
                    "sum_preserving_result_defect"
                ]
            ),
        )
        for row in rows
    )

    maximum_sum_error = max(
        float(
            row[
                "sum_preservation_error"
            ]
        )
        for row in rows
    )

    checks = {
        "rk4_departures_reconstructed": (
            maximum_coordinate_error
            <= COORDINATE_TOLERANCE
        ),
        "departure_cells_identical": (
            total_index_mismatches == 0
        ),
        "direct_bounds_identical": (
            maximum_bound_error
            <= BOUND_TOLERANCE
        ),
        "bounded_modes_respect_direct_rk4_bounds": (
            maximum_result_defect
            <= RESULT_BOUND_TOLERANCE
        ),
        "sum_preserving_mode_matches_cubic_sum": (
            maximum_sum_error
            <= SUM_TOLERANCE
        ),
    }

    print()
    print(
        "=== CONCLUSION V28.2 ==="
    )

    for name, result in checks.items():
        print(
            f"{name:48s}: {result}"
        )

    print()
    print(
        "Erreur coordonnée maximale :",
        f"{maximum_coordinate_error:.9e}",
    )

    print(
        "Cellules différentes totales:",
        total_index_mismatches,
    )

    print(
        "Erreur de borne maximale    :",
        f"{maximum_bound_error:.9e}",
    )

    print(
        "Défaut de résultat maximal  :",
        f"{maximum_result_defect:.9e}",
    )

    print(
        "Erreur de somme maximale     :",
        f"{maximum_sum_error:.9e}",
    )

    report = {
        "version": "ITD V29.0-R1-RK4",
        "status": (
            "rk4_departure_path_certification"
        ),
        "grid_sizes": list(
            GRID_SIZES
        ),
        "time_intervals": [
            list(interval)
            for interval in TIME_INTERVALS
        ],
        "rows": rows,
        "summary": {
            "maximum_coordinate_error": (
                maximum_coordinate_error
            ),
            "total_index_mismatches": (
                total_index_mismatches
            ),
            "maximum_bound_error": (
                maximum_bound_error
            ),
            "maximum_result_defect": (
                maximum_result_defect
            ),
            "maximum_sum_error": (
                maximum_sum_error
            ),
        },
        "checks": checks,
        "claims": {
            "true_rk4_departure_points_used": (
                all(checks.values())
            ),
            "direct_departure_api_implemented": False,
            "floating_point_round_trip_measured": True,
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

    if not all(
        checks.values()
    ):
        raise RuntimeError(
            "Le chemin RK4 de V28 n'est pas "
            "entièrement cohérent."
        )


if __name__ == "__main__":
    main()
