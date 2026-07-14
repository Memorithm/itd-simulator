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
import validate_shape_stability_v26 as shape


GRID_SIZES = (
    64,
    128,
    256,
    512,
    1024,
)

GAUSS_LEGENDRE_ORDER = 4

SHIFT_X_OVER_H = 0.371
SHIFT_Y_OVER_H = -0.283

BOUND_TOLERANCE = 8.0e-12

OUTPUT_PATH = Path(
    "itd_v27_results"
    "/phase_robust_asymptotics.json"
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
) -> float:
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
        raise ValueError(
            f"La séquence {key} ne peut pas "
            "être ajustée."
        )

    slope, _ = np.polyfit(
        np.log(spacings),
        np.log(errors),
        1,
    )

    return float(slope)


def phase_nodes() -> list[
    tuple[float, float]
]:
    """
    Phase nulle de référence, puis produit tensoriel
    des nœuds de Gauss-Legendre d'ordre quatre,
    translatés de [-1,1] vers [0,1].
    """
    nodes, _ = (
        np.polynomial.legendre.leggauss(
            GAUSS_LEGENDRE_ORDER
        )
    )

    mapped = (
        0.5
        * (
            nodes + 1.0
        )
    )

    phases = [
        (
            0.0,
            0.0,
        )
    ]

    phases.extend(
        (
            float(phase_x),
            float(phase_y),
        )
        for phase_x in mapped
        for phase_y in mapped
    )

    return phases


def error_norms(
    difference: np.ndarray,
) -> dict[str, float]:
    values = np.asarray(
        difference,
        dtype=np.float64,
    )

    absolute = np.abs(values)

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
                    values * values
                )
            )
        ),
    }


def pairwise_orders(
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


def classify_order(
    order: float,
    expected: float,
) -> str:
    distance = abs(
        order - expected
    )

    if distance <= 0.35:
        return (
            f"compatible_with_order_{expected:g}"
        )

    if distance <= 0.75:
        return (
            f"approaching_order_{expected:g}"
        )

    return (
        "not_yet_compatible"
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
        SHIFT_X_OVER_H
        * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H
        * spacing
    )

    # Les phases sont exprimées en fractions de maille.
    # La famille explore donc l'alignement sous-cellulaire
    # à chaque résolution.
    source = shape.smooth_periodic_field(
        x + phase_x * spacing,
        y + phase_y * spacing,
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

    exact = shape.smooth_periodic_field(
        x
        - displacement_x
        + phase_x * spacing,
        y
        - displacement_y
        + phase_y * spacing,
    )

    difference = (
        bounded - exact
    )

    cubic_difference = (
        cubic - exact
    )

    norms = error_norms(
        difference
    )

    cubic_norms = error_norms(
        cubic_difference
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

    active = (
        np.abs(
            bounded - cubic
        )
        > activation_tolerance
    )

    active_count = int(
        np.count_nonzero(active)
    )

    active_fraction = float(
        active_count
        / bounded.size
    )

    if active_count > 0:
        active_error_linf = float(
            np.max(
                np.abs(
                    difference[active]
                )
            )
        )
    else:
        active_error_linf = 0.0

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

    local_undershoot = float(
        np.max(
            np.maximum(
                lower - bounded,
                0.0,
            )
        )
    )

    local_overshoot = float(
        np.max(
            np.maximum(
                bounded - upper,
                0.0,
            )
        )
    )

    return {
        "grid_size": grid_size,
        "spacing": float(spacing),
        "phase_x": float(phase_x),
        "phase_y": float(phase_y),
        "linf": norms["linf"],
        "l1_mean": norms["l1_mean"],
        "l2_rms": norms["l2_rms"],
        "cubic_linf": (
            cubic_norms["linf"]
        ),
        "active_count": active_count,
        "active_fraction": (
            active_fraction
        ),
        "active_error_linf": (
            active_error_linf
        ),
        "mean_drift": abs(
            float(
                np.mean(bounded)
            )
            - float(
                np.mean(source)
            )
        ),
        "local_undershoot": (
            local_undershoot
        ),
        "local_overshoot": (
            local_overshoot
        ),
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
    cases: list[
        dict[str, object]
    ] = []

    for phase_x, phase_y in phases:
        case = run_phase_case(
            grid_size,
            phase_x,
            phase_y,
        )

        cases.append(case)

        if max(
            float(
                case[
                    "local_undershoot"
                ]
            ),
            float(
                case[
                    "local_overshoot"
                ]
            ),
        ) > BOUND_TOLERANCE:
            raise RuntimeError(
                "Les bornes locales sont violées "
                f"à N={grid_size}, "
                f"phase=({phase_x}, {phase_y})."
            )

    worst_linf_case = max(
        cases,
        key=lambda item: float(
            item["linf"]
        ),
    )

    worst_l2_case = max(
        cases,
        key=lambda item: float(
            item["l2_rms"]
        ),
    )

    worst_l1_case = max(
        cases,
        key=lambda item: float(
            item["l1_mean"]
        ),
    )

    aggregate = {
        "grid_size": grid_size,
        "spacing": float(
            cases[0]["spacing"]
        ),
        "phase_count": len(cases),
        "worst_linf": float(
            worst_linf_case["linf"]
        ),
        "worst_l2_rms": float(
            worst_l2_case["l2_rms"]
        ),
        "worst_l1_mean": float(
            worst_l1_case["l1_mean"]
        ),
        "median_linf": float(
            np.median(
                [
                    float(case["linf"])
                    for case in cases
                ]
            )
        ),
        "worst_cubic_linf": max(
            float(case["cubic_linf"])
            for case in cases
        ),
        "maximum_active_count": max(
            int(case["active_count"])
            for case in cases
        ),
        "minimum_active_count": min(
            int(case["active_count"])
            for case in cases
        ),
        "median_active_count": float(
            np.median(
                [
                    int(
                        case[
                            "active_count"
                        ]
                    )
                    for case in cases
                ]
            )
        ),
        "maximum_active_fraction": max(
            float(
                case[
                    "active_fraction"
                ]
            )
            for case in cases
        ),
        "worst_active_error_linf": max(
            float(
                case[
                    "active_error_linf"
                ]
            )
            for case in cases
        ),
        "maximum_mean_drift": max(
            float(case["mean_drift"])
            for case in cases
        ),
        "worst_linf_phase": {
            "x": float(
                worst_linf_case[
                    "phase_x"
                ]
            ),
            "y": float(
                worst_linf_case[
                    "phase_y"
                ]
            ),
        },
        "maximum_local_bound_defect": max(
            max(
                float(
                    case[
                        "local_undershoot"
                    ]
                ),
                float(
                    case[
                        "local_overshoot"
                    ]
                ),
            )
            for case in cases
        ),
    }

    return aggregate, cases


def main() -> None:
    print(
        "=== ENVELOPPE DE PHASE DU LIMITEUR "
        "LOCAL — ITD V27.2 ==="
    )

    phases = phase_nodes()

    print(
        "Famille de phases : référence nulle + "
        "Gauss-Legendre tensoriel"
    )

    print(
        "Ordre Gauss-Legendre :",
        GAUSS_LEGENDRE_ORDER,
    )

    print(
        "Nombre de phases     :",
        len(phases),
    )

    print()
    print(
        "grille | pire L∞ | ordre | pire L2 | "
        "ordre | pire L1 | ordre | "
        "actifs max | fraction max"
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
        aggregate, cases = (
            aggregate_grid(
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
            f"{int(aggregate['maximum_active_count']):10d} | "
            f"{float(aggregate['maximum_active_fraction']):.3e}"
        )

        previous = aggregate

        gc.collect()

    linf_orders = pairwise_orders(
        aggregates,
        "worst_linf",
    )

    l2_orders = pairwise_orders(
        aggregates,
        "worst_l2_rms",
    )

    l1_orders = pairwise_orders(
        aggregates,
        "worst_l1_mean",
    )

    active_amplitude_order = (
        fitted_order(
            aggregates,
            "worst_active_error_linf",
        )
    )

    active_fraction_order = (
        fitted_order(
            aggregates,
            "maximum_active_fraction",
        )
    )

    linf_fitted = fitted_order(
        aggregates,
        "worst_linf",
    )

    l2_fitted = fitted_order(
        aggregates,
        "worst_l2_rms",
    )

    l1_fitted = fitted_order(
        aggregates,
        "worst_l1_mean",
    )

    predicted_linf = (
        active_amplitude_order
    )

    predicted_l2 = (
        active_amplitude_order
        + 0.5
        * active_fraction_order
    )

    predicted_l1 = (
        active_amplitude_order
        + active_fraction_order
    )

    classifications = {
        "linf": classify_order(
            linf_fitted,
            2.0,
        ),
        "l2_rms": classify_order(
            l2_fitted,
            3.0,
        ),
        "l1_mean": classify_order(
            l1_fitted,
            4.0,
        ),
    }

    print()
    print(
        "=== AJUSTEMENT SUR LES TROIS "
        "RÉSOLUTIONS LES PLUS FINES ==="
    )

    print(
        "Ordre enveloppe L∞ :",
        f"{linf_fitted:.9f}",
        classifications["linf"],
    )

    print(
        "Ordre enveloppe L2 :",
        f"{l2_fitted:.9f}",
        classifications["l2_rms"],
    )

    print(
        "Ordre enveloppe L1 :",
        f"{l1_fitted:.9f}",
        classifications["l1_mean"],
    )

    print()
    print(
        "=== STRUCTURE DU SUPPORT LIMITÉ ==="
    )

    print(
        "Ordre amplitude active :",
        f"{active_amplitude_order:.9f}",
    )

    print(
        "Ordre fraction active  :",
        f"{active_fraction_order:.9f}",
    )

    print(
        "Prédiction structurelle L∞ :",
        f"{predicted_linf:.9f}",
    )

    print(
        "Prédiction structurelle L2 :",
        f"{predicted_l2:.9f}",
    )

    print(
        "Prédiction structurelle L1 :",
        f"{predicted_l1:.9f}",
    )

    finest = aggregates[-1]

    print()
    print(
        "Résolution fine :",
        finest["grid_size"],
    )

    print(
        "Cellules actives maximum :",
        finest[
            "maximum_active_count"
        ],
    )

    print(
        "Cellules actives médianes:",
        finest[
            "median_active_count"
        ],
    )

    print(
        "Défaut local maximal :",
        f"{float(
            finest[
                'maximum_local_bound_defect'
            ]
        ):.6e}",
    )

    report = {
        "version": "ITD V27.2",
        "status": (
            "phase_robust_asymptotic_diagnostic"
        ),
        "phase_family": {
            "reference_phase": [
                0.0,
                0.0,
            ],
            "construction": (
                "Tensor product of mapped "
                "Gauss-Legendre nodes."
            ),
            "gauss_legendre_order": (
                GAUSS_LEGENDRE_ORDER
            ),
            "phase_count": len(phases),
            "phases": [
                [
                    float(x),
                    float(y),
                ]
                for x, y in phases
            ],
        },
        "grid_sizes": list(
            GRID_SIZES
        ),
        "aggregates": aggregates,
        "cases": all_cases,
        "pairwise_orders": {
            "linf": linf_orders,
            "l2_rms": l2_orders,
            "l1_mean": l1_orders,
        },
        "fitted_orders": {
            "linf": linf_fitted,
            "l2_rms": l2_fitted,
            "l1_mean": l1_fitted,
            "active_amplitude": (
                active_amplitude_order
            ),
            "active_fraction": (
                active_fraction_order
            ),
        },
        "support_model_prediction": {
            "linf": predicted_linf,
            "l2_rms": predicted_l2,
            "l1_mean": predicted_l1,
        },
        "classifications": (
            classifications
        ),
        "claims": {
            "local_bounds_preserved": True,
            "phase_family_deterministic": True,
            "exact_sum_conservation": False,
            "continuous_phase_proof": False,
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
