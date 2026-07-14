#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

import itd_v25
import validate_cubic_transport_v25 as base


OUTPUT_DIRECTORY = Path(
    "itd_v25_results"
)

CSV_PATH = (
    OUTPUT_DIRECTORY
    / "growth_family_certification.csv"
)

JSON_PATH = (
    OUTPUT_DIRECTORY
    / "growth_family_certification.json"
)


# Le temps des oracles est adimensionné.
#
# Dans une formulation dimensionnée, il faudrait écrire :
#
#     g = constante / tau_reference.
INTRINSIC_GROWTH_FAMILY = (
    {
        "name": "inverse_pi_factorial",
        "expression": (
            "1 / Gamma(pi + 1)"
        ),
        "value": (
            1.0
            / math.gamma(
                math.pi + 1.0
            )
        ),
    },
    {
        "name": "inverse_e",
        "expression": "1 / e",
        "value": (
            1.0 / math.e
        ),
    },
    {
        "name": "sqrt_two_over_ten",
        "expression": "sqrt(2) / 10",
        "value": (
            math.sqrt(2.0) / 10.0
        ),
    },
    {
        "name": "log_two_over_four",
        "expression": "log(2) / 4",
        "value": (
            math.log(2.0) / 4.0
        ),
    },
)

ZERO_GROWTH_CONTROL = 0.0

GRID_SIZES = (
    32,
    64,
    128,
    256,
)

DT_OVER_H_VALUES = (
    0.31,
    0.73,
)

RATE_ORDER_MINIMUM = 2.75
RATE_ORDER_MAXIMUM = 3.25

INCREMENT_ORDER_MINIMUM = 3.75
INCREMENT_ORDER_MAXIMUM = 4.25


def observed_order(
    previous_error: float,
    current_error: float,
    previous_step: float,
    current_step: float,
) -> float:
    if (
        previous_error <= 0.0
        or current_error <= 0.0
        or previous_step <= 0.0
        or current_step <= 0.0
    ):
        raise ValueError(
            "Les erreurs et les pas doivent être "
            "strictement positifs."
        )

    order = float(
        np.log(
            previous_error
            / current_error
        )
        / np.log(
            previous_step
            / current_step
        )
    )

    if not np.isfinite(order):
        raise ValueError(
            "L'ordre observé n'est pas fini."
        )

    return order


def validate_growth_family_definition() -> None:
    names = [
        str(item["name"])
        for item in INTRINSIC_GROWTH_FAMILY
    ]

    values = [
        float(item["value"])
        for item in INTRINSIC_GROWTH_FAMILY
    ]

    if len(set(names)) != len(names):
        raise RuntimeError(
            "Les noms des constantes de croissance "
            "ne sont pas uniques."
        )

    if len(set(values)) != len(values):
        raise RuntimeError(
            "Les valeurs des constantes de croissance "
            "ne sont pas uniques."
        )

    if not all(
        np.isfinite(value)
        and value > 0.0
        for value in values
    ):
        raise RuntimeError(
            "Chaque taux intrinsèque doit être fini "
            "et strictement positif."
        )

    print(
        "=== FAMILLE SYMBOLIQUE PRÉDÉCLARÉE ==="
    )

    for item in INTRINSIC_GROWTH_FAMILY:
        print(
            f"{item['name']:24s} | "
            f"{item['expression']:20s} | "
            f"{float(item['value']):.15f}"
        )

    print(
        f"{'zero_growth_control':24s} | "
        f"{'0':20s} | "
        f"{ZERO_GROWTH_CONTROL:.15f}"
    )

    print(
        "Définition de la famille : VALIDÉE"
    )


def compute_growth_case(
    grid_size: int,
    dt_over_h: float,
    growth_rate: float,
) -> dict[str, float]:
    (
        _,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        grid_size
    )

    delta_time = (
        dt_over_h * spacing
    )

    times = np.asarray(
        (
            0.0,
            delta_time,
        ),
        dtype=np.float64,
    )

    cfg = base.Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=base.DOMAIN_LENGTH,
        duration=delta_time,
        time_steps=2,
        characteristic_length=0.5,
    )

    original_velocity = (
        base.make_translating_velocity(
            base.PHYSICAL_TRANSPORT[0],
            base.PHYSICAL_TRANSPORT[1],
            growth_rate=growth_rate,
        )
    )

    original_transport = (
        base.make_constant_velocity(
            base.PHYSICAL_TRANSPORT[0],
            base.PHYSICAL_TRANSPORT[1],
        )
    )

    transformed_velocity = (
        itd_v25.galilean_transform_velocity_function(
            original_velocity,
            base.FRAME_VELOCITY,
        )
    )

    transformed_transport = (
        itd_v25.galilean_transform_velocity_function(
            original_transport,
            base.FRAME_VELOCITY,
        )
    )

    original = itd_v25.simulate(
        (
            f"growth_original_"
            f"{grid_size}_{growth_rate:.12g}"
        ),
        original_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=base.zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            original_transport
        ),
        transport_interpolation=(
            "cubic_periodic"
        ),
    )

    transformed = itd_v25.simulate(
        (
            f"growth_transformed_"
            f"{grid_size}_{growth_rate:.12g}"
        ),
        transformed_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=base.zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            transformed_transport
        ),
        transport_interpolation=(
            "cubic_periodic"
        ),
    )

    original_interval = np.asarray(
        original[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    transformed_interval = np.asarray(
        transformed[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    interval_defect = float(
        np.max(
            np.abs(
                transformed_interval
                - original_interval
            )
        )
    )

    original_index = float(
        original[
            "temporal_deformation_compensated_index"
        ]
    )

    transformed_index = float(
        transformed[
            "temporal_deformation_compensated_index"
        ]
    )

    index_defect = abs(
        transformed_index
        - original_index
    )

    rate_defect = max(
        interval_defect,
        index_defect,
    )

    increment_defect = (
        delta_time
        * rate_defect
    )

    expected_intrinsic_rate = float(
        2.0
        * np.tanh(
            0.5
            * growth_rate
            * delta_time
        )
        / delta_time
    )

    return {
        "grid_size": float(grid_size),
        "spacing": float(spacing),
        "delta_time": float(delta_time),
        "dt_over_h": float(dt_over_h),
        "growth_rate": float(growth_rate),
        "rate_defect": float(rate_defect),
        "increment_defect": float(
            increment_defect
        ),
        "original_intrinsic_rate": float(
            original_index
        ),
        "transformed_intrinsic_rate": float(
            transformed_index
        ),
        "expected_intrinsic_rate": float(
            expected_intrinsic_rate
        ),
        "original_oracle_error": abs(
            original_index
            - expected_intrinsic_rate
        ),
        "transformed_oracle_error": abs(
            transformed_index
            - expected_intrinsic_rate
        ),
    }


def analyze_sequence(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    rate_orders: list[float] = []
    increment_orders: list[float] = []

    previous = None

    for row in rows:
        if previous is None:
            row["rate_order"] = None
            row["increment_order"] = None
        else:
            rate_order = observed_order(
                float(
                    previous["rate_defect"]
                ),
                float(
                    row["rate_defect"]
                ),
                float(
                    previous["spacing"]
                ),
                float(
                    row["spacing"]
                ),
            )

            increment_order = observed_order(
                float(
                    previous[
                        "increment_defect"
                    ]
                ),
                float(
                    row[
                        "increment_defect"
                    ]
                ),
                float(
                    previous["spacing"]
                ),
                float(
                    row["spacing"]
                ),
            )

            row["rate_order"] = rate_order
            row[
                "increment_order"
            ] = increment_order

            rate_orders.append(
                rate_order
            )

            increment_orders.append(
                increment_order
            )

        previous = row

    final_rate_orders = (
        rate_orders[-2:]
    )

    final_increment_orders = (
        increment_orders[-2:]
    )

    rate_valid = all(
        RATE_ORDER_MINIMUM
        <= order
        <= RATE_ORDER_MAXIMUM
        for order in final_rate_orders
    )

    increment_valid = all(
        INCREMENT_ORDER_MINIMUM
        <= order
        <= INCREMENT_ORDER_MAXIMUM
        for order in final_increment_orders
    )

    rate_errors = [
        float(row["rate_defect"])
        for row in rows
    ]

    increment_errors = [
        float(
            row["increment_defect"]
        )
        for row in rows
    ]

    return {
        "rate_orders": rate_orders,
        "increment_orders": (
            increment_orders
        ),
        "final_rate_orders": (
            final_rate_orders
        ),
        "final_increment_orders": (
            final_increment_orders
        ),
        "rate_order_three_valid": (
            rate_valid
        ),
        "increment_order_four_valid": (
            increment_valid
        ),
        "rate_monotone_decrease": all(
            current < previous
            for previous, current in zip(
                rate_errors,
                rate_errors[1:],
            )
        ),
        "increment_monotone_decrease": all(
            current < previous
            for previous, current in zip(
                increment_errors,
                increment_errors[1:],
            )
        ),
        "final_rate_defect": (
            rate_errors[-1]
        ),
        "final_increment_defect": (
            increment_errors[-1]
        ),
    }


def run_family_validation() -> tuple[
    list[dict[str, object]],
    dict[str, object],
]:
    all_rows: list[
        dict[str, object]
    ] = []

    summary: dict[str, object] = {
        "time_dimension": "dimensionless",
        "growth_family": [],
        "zero_growth_control": {
            "value": ZERO_GROWTH_CONTROL,
            "purpose": (
                "Isolation du transport et de la "
                "rétrotrajectoire."
            ),
        },
        "studies": {},
    }

    global_success = True

    for growth_item in (
        INTRINSIC_GROWTH_FAMILY
    ):
        growth_name = str(
            growth_item["name"]
        )

        growth_expression = str(
            growth_item["expression"]
        )

        growth_rate = float(
            growth_item["value"]
        )

        summary["growth_family"].append(
            {
                "name": growth_name,
                "expression": (
                    growth_expression
                ),
                "value": growth_rate,
            }
        )

        growth_summary: dict[
            str,
            object,
        ] = {}

        for dt_over_h in (
            DT_OVER_H_VALUES
        ):
            rows: list[
                dict[str, object]
            ] = []

            print()
            print(
                "=== "
                f"{growth_name} "
                f"({growth_expression}) — "
                f"Δt/h={dt_over_h:.2f} "
                "==="
            )

            print(
                "grille | défaut taux | ordre | "
                "défaut incrément | ordre | "
                "taux intrinsèque"
            )

            for grid_size in GRID_SIZES:
                row = compute_growth_case(
                    grid_size,
                    dt_over_h,
                    growth_rate,
                )

                row["growth_name"] = (
                    growth_name
                )

                row[
                    "growth_expression"
                ] = growth_expression

                rows.append(row)

            analysis = analyze_sequence(
                rows
            )

            for row in rows:
                rate_order = row.get(
                    "rate_order"
                )

                increment_order = row.get(
                    "increment_order"
                )

                rate_order_text = (
                    "—"
                    if rate_order is None
                    else (
                        f"{float(rate_order):.6f}"
                    )
                )

                increment_order_text = (
                    "—"
                    if increment_order is None
                    else (
                        f"{float(increment_order):.6f}"
                    )
                )

                print(
                    f"{int(float(row['grid_size'])):6d} | "
                    f"{float(row['rate_defect']):11.4e} | "
                    f"{rate_order_text:>8} | "
                    f"{float(row['increment_defect']):16.6e} | "
                    f"{increment_order_text:>8} | "
                    f"{float(row['original_intrinsic_rate']):.9f}"
                )

            sequence_success = all(
                (
                    bool(
                        analysis[
                            "rate_order_three_valid"
                        ]
                    ),
                    bool(
                        analysis[
                            "increment_order_four_valid"
                        ]
                    ),
                    bool(
                        analysis[
                            "rate_monotone_decrease"
                        ]
                    ),
                    bool(
                        analysis[
                            "increment_monotone_decrease"
                        ]
                    ),
                )
            )

            print(
                "Taux cubique d'ordre trois :",
                analysis[
                    "rate_order_three_valid"
                ],
            )

            print(
                "Incrément d'ordre quatre    :",
                analysis[
                    "increment_order_four_valid"
                ],
            )

            print(
                "Décroissance monotone        :",
                (
                    analysis[
                        "rate_monotone_decrease"
                    ]
                    and analysis[
                        "increment_monotone_decrease"
                    ]
                ),
            )

            analysis["success"] = (
                sequence_success
            )

            growth_summary[
                f"{dt_over_h:.2f}"
            ] = analysis

            all_rows.extend(rows)

            global_success = (
                global_success
                and sequence_success
            )

        summary["studies"][
            growth_name
        ] = growth_summary

    summary["global"] = {
        "success": global_success,
        "all_growth_rates_tested": (
            len(
                INTRINSIC_GROWTH_FAMILY
            )
        ),
        "all_dt_over_h_values_tested": (
            len(
                DT_OVER_H_VALUES
            )
        ),
        "expected_rate_order": 3,
        "expected_increment_order": 4,
    }

    return all_rows, summary


def write_reports(
    rows: list[dict[str, object]],
    summary: dict[str, object],
) -> None:
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    field_names = (
        "growth_name",
        "growth_expression",
        "growth_rate",
        "dt_over_h",
        "grid_size",
        "spacing",
        "delta_time",
        "rate_defect",
        "rate_order",
        "increment_defect",
        "increment_order",
        "original_intrinsic_rate",
        "transformed_intrinsic_rate",
        "expected_intrinsic_rate",
        "original_oracle_error",
        "transformed_oracle_error",
    )

    with CSV_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=field_names,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    name: row.get(name)
                    for name in field_names
                }
            )

    JSON_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    print(
        "=== CERTIFICATION MULTIPARAMÉTRIQUE "
        "DES CROISSANCES — ITD V25.1 ==="
    )

    validate_growth_family_definition()

    rows, summary = (
        run_family_validation()
    )

    write_reports(
        rows,
        summary,
    )

    print()
    print(
        "=== CONCLUSION GLOBALE ==="
    )

    print(
        "Nombre de constantes testées :",
        len(
            INTRINSIC_GROWTH_FAMILY
        ),
    )

    print(
        "Nombre de rapports Δt/h      :",
        len(
            DT_OVER_H_VALUES
        ),
    )

    print(
        "Taux cubique ordre trois pour "
        "toute la famille :",
        summary["global"]["success"],
    )

    print(
        "Rapport CSV :",
        CSV_PATH.resolve(),
    )

    print(
        "Rapport JSON:",
        JSON_PATH.resolve(),
    )

    if not summary["global"][
        "success"
    ]:
        raise RuntimeError(
            "La robustesse multiparamétrique "
            "de V25 n'est pas validée."
        )


if __name__ == "__main__":
    main()
