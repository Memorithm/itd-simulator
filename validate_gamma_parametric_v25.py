#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from validate_growth_family_v25 import (
    compute_growth_case,
    observed_order,
)


OUTPUT_DIRECTORY = Path(
    "itd_v25_results"
)

CSV_PATH = (
    OUTPUT_DIRECTORY
    / "gamma_parametric_certification.csv"
)

JSON_PATH = (
    OUTPUT_DIRECTORY
    / "gamma_parametric_certification.json"
)


# Loi officielle de croissance synthétique :
#
#     g(alpha) = 1 / Gamma(alpha + 1)
#
# Le temps est adimensionné dans ces oracles.
#
# Pour un temps dimensionné :
#
#     g(alpha) =
#         1 / (
#             tau_reference
#             * Gamma(alpha + 1)
#         )
REFERENCE_ALPHA = math.pi

ALPHA_MINIMUM = 3.0
ALPHA_MAXIMUM = 4.0

# Nœuds de Chebyshev-Lobatto, bornes incluses.
CHEBYSHEV_NODE_COUNT = 9

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


def gamma_growth_rate(
    alpha: float,
) -> float:
    alpha = float(alpha)

    if not np.isfinite(alpha):
        raise ValueError(
            "L'ordre Gamma doit être fini."
        )

    if alpha <= 0.0:
        raise ValueError(
            "L'ordre Gamma doit être "
            "strictement positif."
        )

    value = float(
        1.0
        / math.gamma(
            alpha + 1.0
        )
    )

    if (
        not np.isfinite(value)
        or value <= 0.0
    ):
        raise ValueError(
            "Le taux Gamma obtenu doit être "
            "fini et strictement positif."
        )

    return value


def chebyshev_lobatto_nodes(
    minimum: float,
    maximum: float,
    count: int,
) -> list[float]:
    minimum = float(minimum)
    maximum = float(maximum)

    if count < 2:
        raise ValueError(
            "Au moins deux nœuds sont requis."
        )

    if not minimum < maximum:
        raise ValueError(
            "L'intervalle Alpha est invalide."
        )

    midpoint = (
        0.5
        * (
            minimum + maximum
        )
    )

    half_width = (
        0.5
        * (
            maximum - minimum
        )
    )

    nodes = [
        midpoint
        + half_width
        * math.cos(
            math.pi
            * index
            / (
                count - 1
            )
        )
        for index in range(count)
    ]

    return sorted(
        float(node)
        for node in nodes
    )


def declared_alpha_nodes() -> list[float]:
    nodes = chebyshev_lobatto_nodes(
        ALPHA_MINIMUM,
        ALPHA_MAXIMUM,
        CHEBYSHEV_NODE_COUNT,
    )

    nodes.append(
        REFERENCE_ALPHA
    )

    # Déduplication déterministe à une précision
    # très supérieure à celle des rapports.
    unique = {
        round(
            float(node),
            15,
        ): float(node)
        for node in nodes
    }

    return sorted(
        unique.values()
    )


def validate_definition(
    nodes: list[float],
) -> None:
    if not (
        ALPHA_MINIMUM
        < REFERENCE_ALPHA
        < ALPHA_MAXIMUM
    ):
        raise RuntimeError(
            "Pi doit appartenir strictement à "
            "l'intervalle Gamma déclaré."
        )

    if len(nodes) != (
        CHEBYSHEV_NODE_COUNT + 1
    ):
        raise RuntimeError(
            "Le nombre de points Alpha est "
            "inattendu."
        )

    if not any(
        math.isclose(
            node,
            REFERENCE_ALPHA,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        )
        for node in nodes
    ):
        raise RuntimeError(
            "Le point de référence alpha=pi "
            "est absent."
        )

    print(
        "=== LOI GAMMA DÉCLARÉE ==="
    )

    print(
        "g(alpha) = 1 / Gamma(alpha + 1)"
    )

    print(
        "Intervalle alpha : "
        f"[{ALPHA_MINIMUM:.1f}, "
        f"{ALPHA_MAXIMUM:.1f}]"
    )

    print(
        "Référence alpha  : pi"
    )

    print(
        "Référence g(pi) : "
        f"{gamma_growth_rate(REFERENCE_ALPHA):.15f}"
    )

    print(
        "Points testés    :",
        len(nodes),
    )

    print()
    print(
        "index | alpha             | "
        "g(alpha)"
    )

    for index, alpha in enumerate(nodes):
        marker = (
            "  <- pi"
            if math.isclose(
                alpha,
                REFERENCE_ALPHA,
                rel_tol=0.0,
                abs_tol=1.0e-15,
            )
            else ""
        )

        print(
            f"{index:5d} | "
            f"{alpha:17.15f} | "
            f"{gamma_growth_rate(alpha):.15f}"
            f"{marker}"
        )


def analyze_rows(
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

            row["rate_order"] = (
                rate_order
            )

            row["increment_order"] = (
                increment_order
            )

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

    monotone = (
        all(
            current < previous_error
            for previous_error, current
            in zip(
                rate_errors,
                rate_errors[1:],
            )
        )
        and all(
            current < previous_error
            for previous_error, current
            in zip(
                increment_errors,
                increment_errors[1:],
            )
        )
    )

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
        "monotone_decrease": monotone,
        "success": (
            rate_valid
            and increment_valid
            and monotone
        ),
        "final_rate_defect": (
            rate_errors[-1]
        ),
        "final_increment_defect": (
            increment_errors[-1]
        ),
    }


def run_certification(
    alpha_nodes: list[float],
) -> tuple[
    list[dict[str, object]],
    dict[str, object],
]:
    all_rows: list[
        dict[str, object]
    ] = []

    studies: list[
        dict[str, object]
    ] = []

    global_success = True

    for alpha_index, alpha in enumerate(
        alpha_nodes
    ):
        growth_rate = gamma_growth_rate(
            alpha
        )

        alpha_is_reference = (
            math.isclose(
                alpha,
                REFERENCE_ALPHA,
                rel_tol=0.0,
                abs_tol=1.0e-15,
            )
        )

        for dt_over_h in (
            DT_OVER_H_VALUES
        ):
            rows: list[
                dict[str, object]
            ] = []

            print()
            print(
                "=== "
                f"alpha={alpha:.15f} "
                f"g={growth_rate:.15f} "
                f"Δt/h={dt_over_h:.2f}"
                + (
                    " — RÉFÉRENCE PI"
                    if alpha_is_reference
                    else ""
                )
                + " ==="
            )

            print(
                "grille | défaut taux | ordre | "
                "défaut incrément | ordre"
            )

            for grid_size in GRID_SIZES:
                row = compute_growth_case(
                    grid_size,
                    dt_over_h,
                    growth_rate,
                )

                row["alpha_index"] = (
                    alpha_index
                )

                row["alpha"] = alpha
                row["alpha_is_pi"] = (
                    alpha_is_reference
                )

                row[
                    "gamma_expression"
                ] = (
                    "1 / Gamma(alpha + 1)"
                )

                rows.append(row)

            analysis = analyze_rows(
                rows
            )

            for row in rows:
                rate_order = row.get(
                    "rate_order"
                )

                increment_order = row.get(
                    "increment_order"
                )

                rate_text = (
                    "—"
                    if rate_order is None
                    else (
                        f"{float(rate_order):.6f}"
                    )
                )

                increment_text = (
                    "—"
                    if increment_order is None
                    else (
                        f"{float(increment_order):.6f}"
                    )
                )

                print(
                    f"{int(float(row['grid_size'])):6d} | "
                    f"{float(row['rate_defect']):11.4e} | "
                    f"{rate_text:>8} | "
                    f"{float(row['increment_defect']):16.6e} | "
                    f"{increment_text:>8}"
                )

            print(
                "Taux d'ordre trois      :",
                analysis[
                    "rate_order_three_valid"
                ],
            )

            print(
                "Incrément d'ordre quatre:",
                analysis[
                    "increment_order_four_valid"
                ],
            )

            print(
                "Décroissance monotone    :",
                analysis[
                    "monotone_decrease"
                ],
            )

            study = {
                "alpha_index": alpha_index,
                "alpha": alpha,
                "alpha_is_pi": (
                    alpha_is_reference
                ),
                "growth_rate": (
                    growth_rate
                ),
                "dt_over_h": (
                    dt_over_h
                ),
                **analysis,
            }

            studies.append(study)
            all_rows.extend(rows)

            global_success = (
                global_success
                and bool(
                    analysis["success"]
                )
            )

    all_rate_orders = [
        float(order)
        for study in studies
        for order in study[
            "final_rate_orders"
        ]
    ]

    all_increment_orders = [
        float(order)
        for study in studies
        for order in study[
            "final_increment_orders"
        ]
    ]

    summary = {
        "version": "ITD V25.2",
        "status": (
            "gamma_parametric_numerical_"
            "certification"
        ),
        "time_dimension": (
            "dimensionless"
        ),
        "law": (
            "g(alpha) = "
            "1 / Gamma(alpha + 1)"
        ),
        "alpha_interval": {
            "minimum": ALPHA_MINIMUM,
            "maximum": ALPHA_MAXIMUM,
            "justification": (
                "Smallest interval with integer "
                "endpoints containing pi."
            ),
        },
        "reference": {
            "alpha": REFERENCE_ALPHA,
            "growth_rate": (
                gamma_growth_rate(
                    REFERENCE_ALPHA
                )
            ),
        },
        "sampling": {
            "method": (
                "Chebyshev-Lobatto nodes "
                "plus explicit alpha=pi"
            ),
            "chebyshev_node_count": (
                CHEBYSHEV_NODE_COUNT
            ),
            "total_alpha_count": (
                len(alpha_nodes)
            ),
            "alpha_nodes": alpha_nodes,
        },
        "grid_sizes": list(
            GRID_SIZES
        ),
        "dt_over_h_values": list(
            DT_OVER_H_VALUES
        ),
        "studies": studies,
        "global": {
            "success": global_success,
            "study_count": len(studies),
            "minimum_final_rate_order": min(
                all_rate_orders
            ),
            "maximum_final_rate_order": max(
                all_rate_orders
            ),
            "minimum_final_increment_order": min(
                all_increment_orders
            ),
            "maximum_final_increment_order": max(
                all_increment_orders
            ),
            "expected_rate_order": 3,
            "expected_increment_order": 4,
        },
        "scope_note": (
            "This is a deterministic numerical "
            "coverage of declared alpha nodes, "
            "not a proof for every real alpha "
            "in the interval."
        ),
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
        "alpha_index",
        "alpha",
        "alpha_is_pi",
        "gamma_expression",
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
                    field: row.get(field)
                    for field in field_names
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
        "=== CERTIFICATION GAMMA "
        "PARAMÉTRIQUE — ITD V25.2 ==="
    )

    alpha_nodes = (
        declared_alpha_nodes()
    )

    validate_definition(
        alpha_nodes
    )

    rows, summary = run_certification(
        alpha_nodes
    )

    write_reports(
        rows,
        summary,
    )

    global_summary = summary[
        "global"
    ]

    print()
    print(
        "=== CONCLUSION V25.2 ==="
    )

    print(
        "Points alpha testés :",
        len(alpha_nodes),
    )

    print(
        "Études alpha × Δt/h :",
        global_summary[
            "study_count"
        ],
    )

    print(
        "Ordre taux minimal  :",
        f"{global_summary[
            'minimum_final_rate_order'
        ]:.9f}",
    )

    print(
        "Ordre taux maximal  :",
        f"{global_summary[
            'maximum_final_rate_order'
        ]:.9f}",
    )

    print(
        "Ordre incr. minimal :",
        f"{global_summary[
            'minimum_final_increment_order'
        ]:.9f}",
    )

    print(
        "Ordre incr. maximal :",
        f"{global_summary[
            'maximum_final_increment_order'
        ]:.9f}",
    )

    print(
        "Certification globale:",
        global_summary["success"],
    )

    print(
        "Rapport CSV :",
        CSV_PATH.resolve(),
    )

    print(
        "Rapport JSON:",
        JSON_PATH.resolve(),
    )

    if not global_summary["success"]:
        raise RuntimeError(
            "La certification Gamma paramétrique "
            "V25.2 a échoué."
        )


if __name__ == "__main__":
    main()
