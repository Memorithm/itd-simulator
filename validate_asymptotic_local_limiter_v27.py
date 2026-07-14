#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import validate_cubic_transport_v25 as base
import validate_local_bounded_v27 as local
import validate_shape_stability_v26 as shape


GRID_SIZES = (
    32,
    64,
    128,
    256,
    512,
    1024,
)

SHIFT_X_OVER_H = 0.371
SHIFT_Y_OVER_H = -0.283

BOUND_TOLERANCE = 5.0e-12

OUTPUT_PATH = Path(
    "itd_v27_results"
    "/local_limiter_asymptotics.json"
)


def observed_order(
    previous_error: float,
    current_error: float,
    previous_step: float,
    current_step: float,
) -> float:
    values = (
        previous_error,
        current_error,
        previous_step,
        current_step,
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
            previous_error
            / current_error
        )
        / math.log(
            previous_step
            / current_step
        )
    )


def error_norms(
    numerical: np.ndarray,
    exact: np.ndarray,
) -> dict[str, float]:
    difference = np.asarray(
        numerical - exact,
        dtype=np.float64,
    )

    return {
        "linf": float(
            np.max(
                np.abs(difference)
            )
        ),
        "l1_mean": float(
            np.mean(
                np.abs(difference)
            )
        ),
        "l2_rms": float(
            np.sqrt(
                np.mean(
                    difference * difference
                )
            )
        ),
    }


def sequence_orders(
    rows: list[dict[str, object]],
    key: str,
) -> list[float]:
    return [
        observed_order(
            float(
                rows[index - 1][key]
            ),
            float(
                rows[index][key]
            ),
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
        for index in range(
            1,
            len(rows),
        )
    ]


def classify_tail(
    orders: list[float],
) -> dict[str, object]:
    tail = orders[-2:]

    estimate = float(
        np.mean(tail)
    )

    spread = float(
        np.max(tail)
        - np.min(tail)
    )

    if min(tail) >= 3.5:
        classification = (
            "fourth_order_tail"
        )
    elif (
        min(tail) >= 1.5
        and spread <= 0.30
    ):
        classification = (
            "stable_reduced_order_tail"
        )
    else:
        classification = (
            "tail_not_yet_asymptotic"
        )

    return {
        "orders": orders,
        "tail_orders": tail,
        "tail_estimate": estimate,
        "tail_spread": spread,
        "classification": classification,
    }


def main() -> None:
    print(
        "=== ASYMPTOTIQUE DU LIMITEUR LOCAL "
        "— ITD V27.1 ==="
    )

    rows: list[
        dict[str, object]
    ] = []

    print()
    print(
        "grille | erreur L∞ | ordre | "
        "erreur L1 | ordre | erreur L2 | ordre | "
        "fraction limitée"
    )

    previous = None

    for grid_size in GRID_SIZES:
        (
            coordinates,
            x,
            y,
            spacing,
        ) = base.build_periodic_grid(
            grid_size
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

        cubic = local.transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_periodic",
        )

        bounded = local.transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_bounded_periodic",
        )

        bilinear = local.transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "bilinear_periodic",
        )

        exact = shape.smooth_periodic_field(
            x - displacement_x,
            y - displacement_y,
        )

        bounded_norms = error_norms(
            bounded,
            exact,
        )

        cubic_norms = error_norms(
            cubic,
            exact,
        )

        bilinear_norms = error_norms(
            bilinear,
            exact,
        )

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

        limited_fraction = float(
            np.mean(
                np.abs(
                    bounded - cubic
                )
                > activation_tolerance
            )
        )

        source_minimum = float(
            np.min(source)
        )

        source_maximum = float(
            np.max(source)
        )

        result_minimum = float(
            np.min(bounded)
        )

        result_maximum = float(
            np.max(bounded)
        )

        undershoot = max(
            0.0,
            source_minimum
            - result_minimum,
        )

        overshoot = max(
            0.0,
            result_maximum
            - source_maximum,
        )

        row = {
            "grid_size": grid_size,
            "spacing": float(spacing),
            "linf": bounded_norms[
                "linf"
            ],
            "l1_mean": bounded_norms[
                "l1_mean"
            ],
            "l2_rms": bounded_norms[
                "l2_rms"
            ],
            "cubic_linf": cubic_norms[
                "linf"
            ],
            "bilinear_linf": (
                bilinear_norms["linf"]
            ),
            "limited_fraction": (
                limited_fraction
            ),
            "mean_drift": abs(
                float(
                    np.mean(bounded)
                )
                - float(
                    np.mean(source)
                )
            ),
            "undershoot": undershoot,
            "overshoot": overshoot,
        }

        rows.append(row)

        if previous is None:
            linf_order = "—"
            l1_order = "—"
            l2_order = "—"
        else:
            linf_order = (
                f"{observed_order(
                    float(previous['linf']),
                    float(row['linf']),
                    float(previous['spacing']),
                    float(row['spacing']),
                ):.6f}"
            )

            l1_order = (
                f"{observed_order(
                    float(previous['l1_mean']),
                    float(row['l1_mean']),
                    float(previous['spacing']),
                    float(row['spacing']),
                ):.6f}"
            )

            l2_order = (
                f"{observed_order(
                    float(previous['l2_rms']),
                    float(row['l2_rms']),
                    float(previous['spacing']),
                    float(row['spacing']),
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{float(row['linf']):9.3e} | "
            f"{linf_order:>8} | "
            f"{float(row['l1_mean']):9.3e} | "
            f"{l1_order:>8} | "
            f"{float(row['l2_rms']):9.3e} | "
            f"{l2_order:>8} | "
            f"{limited_fraction:.8f}"
        )

        if max(
            undershoot,
            overshoot,
        ) > BOUND_TOLERANCE:
            raise RuntimeError(
                "Le limiteur viole les bornes "
                f"à N={grid_size}."
            )

        previous = row

    linf_analysis = classify_tail(
        sequence_orders(
            rows,
            "linf",
        )
    )

    l1_analysis = classify_tail(
        sequence_orders(
            rows,
            "l1_mean",
        )
    )

    l2_analysis = classify_tail(
        sequence_orders(
            rows,
            "l2_rms",
        )
    )

    bounded_errors = [
        float(row["linf"])
        for row in rows
    ]

    if not all(
        current < previous_error
        for previous_error, current
        in zip(
            bounded_errors,
            bounded_errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur L∞ ne décroît pas "
            "monotoniquement."
        )

    finest = rows[-1]

    if not (
        float(finest["linf"])
        < float(
            finest["bilinear_linf"]
        )
    ):
        raise RuntimeError(
            "Le limiteur local ne surpasse pas "
            "le bilinéaire à la résolution fine."
        )

    report = {
        "version": "ITD V27.1",
        "status": (
            "extended_asymptotic_diagnostic"
        ),
        "grid_sizes": list(
            GRID_SIZES
        ),
        "rows": rows,
        "linf_analysis": linf_analysis,
        "l1_analysis": l1_analysis,
        "l2_analysis": l2_analysis,
        "claims": {
            "bounds_preserved": True,
            "errors_monotone": True,
            "finer_than_bilinear": True,
            "exact_sum_conservation": False,
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
        "=== CLASSIFICATION ASYMPTOTIQUE ==="
    )

    for name, analysis in (
        (
            "L∞",
            linf_analysis,
        ),
        (
            "L1",
            l1_analysis,
        ),
        (
            "L2",
            l2_analysis,
        ),
    ):
        print(
            f"{name:3s} : "
            f"ordres finaux="
            f"{analysis['tail_orders']} ; "
            f"estimation="
            f"{analysis['tail_estimate']:.6f} ; "
            f"{analysis['classification']}"
        )

    print()
    print(
        "Erreur L∞ fine bornée :",
        f"{float(finest['linf']):.9e}",
    )

    print(
        "Erreur L∞ fine bilinéaire :",
        f"{float(finest['bilinear_linf']):.9e}",
    )

    print(
        "Fraction limitée fine :",
        f"{float(finest['limited_fraction']):.9e}",
    )

    print(
        "Dérive moyenne fine :",
        f"{float(finest['mean_drift']):.9e}",
    )

    print(
        "Rapport :",
        OUTPUT_PATH.resolve(),
    )


if __name__ == "__main__":
    main()
