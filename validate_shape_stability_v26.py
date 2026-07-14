#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import itd_v26
import validate_cubic_transport_v25 as base


GRID_SIZE = 128

SHIFT_X_OVER_H = 0.371
SHIFT_Y_OVER_H = -0.283

REPEATED_STEP_COUNT = 64

CONSTANT_TOLERANCE = 2.0e-13
MEAN_TOLERANCE = 2.0e-13
BOUND_TOLERANCE = 2.0e-13

OUTPUT_DIRECTORY = Path(
    "itd_v26_results"
)

JSON_PATH = (
    OUTPUT_DIRECTORY
    / "shape_stability_v26.json"
)

TEXT_PATH = (
    OUTPUT_DIRECTORY
    / "shape_stability_v26.txt"
)


def periodic_total_variation(
    field: object,
) -> float:
    values = np.asarray(
        field,
        dtype=np.float64,
    )

    variation_x = np.mean(
        np.abs(
            np.roll(
                values,
                -1,
                axis=1,
            )
            - values
        )
    )

    variation_y = np.mean(
        np.abs(
            np.roll(
                values,
                -1,
                axis=0,
            )
            - values
        )
    )

    return float(
        variation_x + variation_y
    )


def field_statistics(
    field: object,
) -> dict[str, float]:
    values = np.asarray(
        field,
        dtype=np.float64,
    )

    if not np.all(
        np.isfinite(values)
    ):
        raise RuntimeError(
            "Le champ contient une valeur "
            "non finie."
        )

    return {
        "minimum": float(
            np.min(values)
        ),
        "maximum": float(
            np.max(values)
        ),
        "mean": float(
            np.mean(values)
        ),
        "l1_mean": float(
            np.mean(
                np.abs(values)
            )
        ),
        "l2_rms": float(
            np.sqrt(
                np.mean(
                    values * values
                )
            )
        ),
        "periodic_total_variation": (
            periodic_total_variation(
                values
            )
        ),
    }


def transport_once(
    field: object,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    interpolation: str,
) -> np.ndarray:
    values = np.asarray(
        field,
        dtype=np.float64,
    )

    velocity_x = np.full_like(
        values,
        displacement_x,
        dtype=np.float64,
    )

    velocity_y = np.full_like(
        values,
        displacement_y,
        dtype=np.float64,
    )

    return itd_v26.periodic_backtrace(
        values,
        coordinates,
        coordinates,
        velocity_x,
        velocity_y,
        1.0,
        interpolation=interpolation,
    )


def smooth_periodic_field(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    length = float(
        base.DOMAIN_LENGTH
    )

    phase_x = (
        2.0 * math.pi * x / length
    )

    phase_y = (
        2.0 * math.pi * y / length
    )

    return (
        1.25
        + 0.31 * np.sin(phase_x)
        - 0.23 * np.cos(2.0 * phase_y)
        + 0.17
        * np.sin(
            2.0 * phase_x
            - phase_y
        )
        + 0.09
        * np.cos(
            3.0 * phase_x
            + 2.0 * phase_y
        )
    )


def sharp_periodic_field(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    length = float(
        base.DOMAIN_LENGTH
    )

    normalized_x = np.mod(
        x / length,
        1.0,
    )

    normalized_y = np.mod(
        y / length,
        1.0,
    )

    rectangle = (
        (
            normalized_x >= 0.18
        )
        & (
            normalized_x <= 0.56
        )
        & (
            normalized_y >= 0.27
        )
        & (
            normalized_y <= 0.71
        )
    )

    return rectangle.astype(
        np.float64
    )


def positive_periodic_bump(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    length = float(
        base.DOMAIN_LENGTH
    )

    center_x = 0.41 * length
    center_y = 0.63 * length

    delta_x = (
        np.mod(
            x - center_x
            + 0.5 * length,
            length,
        )
        - 0.5 * length
    )

    delta_y = (
        np.mod(
            y - center_y
            + 0.5 * length,
            length,
        )
        - 0.5 * length
    )

    sigma = 0.075 * length

    return np.exp(
        -(
            delta_x * delta_x
            + delta_y * delta_y
        )
        / (
            2.0 * sigma * sigma
        )
    )


def bound_defects(
    result: object,
    source_minimum: float,
    source_maximum: float,
) -> dict[str, object]:
    values = np.asarray(
        result,
        dtype=np.float64,
    )

    result_minimum = float(
        np.min(values)
    )

    result_maximum = float(
        np.max(values)
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

    return {
        "source_minimum": (
            source_minimum
        ),
        "source_maximum": (
            source_maximum
        ),
        "result_minimum": (
            result_minimum
        ),
        "result_maximum": (
            result_maximum
        ),
        "undershoot": float(
            undershoot
        ),
        "overshoot": float(
            overshoot
        ),
        "maximum_principle_preserved": (
            undershoot
            <= BOUND_TOLERANCE
            and overshoot
            <= BOUND_TOLERANCE
        ),
    }


def repeated_transport(
    initial_field: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    interpolation: str,
    step_count: int,
) -> np.ndarray:
    current = np.asarray(
        initial_field,
        dtype=np.float64,
    ).copy()

    for _ in range(step_count):
        current = transport_once(
            current,
            coordinates,
            displacement_x,
            displacement_y,
            interpolation,
        )

    return current


def smooth_exact_after_steps(
    x: np.ndarray,
    y: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    step_count: int,
) -> np.ndarray:
    return smooth_periodic_field(
        x
        - step_count
        * displacement_x,
        y
        - step_count
        * displacement_y,
    )


def maximum_error(
    left: object,
    right: object,
) -> float:
    return float(
        np.max(
            np.abs(
                np.asarray(
                    left,
                    dtype=np.float64,
                )
                - np.asarray(
                    right,
                    dtype=np.float64,
                )
            )
        )
    )


def run_audit() -> dict[str, object]:
    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        GRID_SIZE
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    report: dict[str, object] = {
        "version": "ITD V26.2",
        "purpose": (
            "Shape-stability audit of periodic "
            "bilinear and cubic interpolation."
        ),
        "grid_size": GRID_SIZE,
        "spacing": float(spacing),
        "displacement": {
            "x": float(displacement_x),
            "y": float(displacement_y),
            "x_over_h": SHIFT_X_OVER_H,
            "y_over_h": SHIFT_Y_OVER_H,
        },
        "repeated_step_count": (
            REPEATED_STEP_COUNT
        ),
        "interpolations": {},
    }

    constant_field = np.full_like(
        x,
        3.25,
        dtype=np.float64,
    )

    smooth_field = smooth_periodic_field(
        x,
        y,
    )

    sharp_field = sharp_periodic_field(
        x,
        y,
    )

    positive_bump = positive_periodic_bump(
        x,
        y,
    )

    source_fields = {
        "constant": constant_field,
        "smooth": smooth_field,
        "sharp": sharp_field,
        "positive_bump": positive_bump,
    }

    source_statistics = {
        name: field_statistics(field)
        for name, field in source_fields.items()
    }

    report[
        "source_statistics"
    ] = source_statistics

    for interpolation in (
        "bilinear_periodic",
        "cubic_periodic",
    ):
        interpolation_report: dict[
            str,
            object,
        ] = {}

        one_step_results = {
            name: transport_once(
                field,
                coordinates,
                displacement_x,
                displacement_y,
                interpolation,
            )
            for name, field
            in source_fields.items()
        }

        constant_error = maximum_error(
            one_step_results["constant"],
            constant_field,
        )

        mean_errors = {
            name: abs(
                float(
                    np.mean(result)
                )
                - float(
                    np.mean(
                        source_fields[name]
                    )
                )
            )
            for name, result
            in one_step_results.items()
        }

        bounds = {
            name: bound_defects(
                result,
                float(
                    np.min(
                        source_fields[name]
                    )
                ),
                float(
                    np.max(
                        source_fields[name]
                    )
                ),
            )
            for name, result
            in one_step_results.items()
        }

        one_step_statistics = {
            name: field_statistics(
                result
            )
            for name, result
            in one_step_results.items()
        }

        repeated_smooth = repeated_transport(
            smooth_field,
            coordinates,
            displacement_x,
            displacement_y,
            interpolation,
            REPEATED_STEP_COUNT,
        )

        repeated_sharp = repeated_transport(
            sharp_field,
            coordinates,
            displacement_x,
            displacement_y,
            interpolation,
            REPEATED_STEP_COUNT,
        )

        repeated_bump = repeated_transport(
            positive_bump,
            coordinates,
            displacement_x,
            displacement_y,
            interpolation,
            REPEATED_STEP_COUNT,
        )

        exact_smooth = (
            smooth_exact_after_steps(
                x,
                y,
                displacement_x,
                displacement_y,
                REPEATED_STEP_COUNT,
            )
        )

        forward_smooth = transport_once(
            smooth_field,
            coordinates,
            displacement_x,
            displacement_y,
            interpolation,
        )

        reversed_smooth = transport_once(
            forward_smooth,
            coordinates,
            -displacement_x,
            -displacement_y,
            interpolation,
        )

        interpolation_report[
            "constant_error"
        ] = constant_error

        interpolation_report[
            "one_step_mean_errors"
        ] = mean_errors

        interpolation_report[
            "one_step_bounds"
        ] = bounds

        interpolation_report[
            "one_step_statistics"
        ] = one_step_statistics

        interpolation_report[
            "repeated_smooth"
        ] = {
            "statistics": (
                field_statistics(
                    repeated_smooth
                )
            ),
            "maximum_error_against_exact": (
                maximum_error(
                    repeated_smooth,
                    exact_smooth,
                )
            ),
            "mean_drift": abs(
                float(
                    np.mean(
                        repeated_smooth
                    )
                )
                - float(
                    np.mean(
                        smooth_field
                    )
                )
            ),
        }

        interpolation_report[
            "repeated_sharp"
        ] = {
            "statistics": (
                field_statistics(
                    repeated_sharp
                )
            ),
            "bounds": bound_defects(
                repeated_sharp,
                0.0,
                1.0,
            ),
            "mean_drift": abs(
                float(
                    np.mean(
                        repeated_sharp
                    )
                )
                - float(
                    np.mean(
                        sharp_field
                    )
                )
            ),
        }

        interpolation_report[
            "repeated_positive_bump"
        ] = {
            "statistics": (
                field_statistics(
                    repeated_bump
                )
            ),
            "bounds": bound_defects(
                repeated_bump,
                float(
                    np.min(
                        positive_bump
                    )
                ),
                float(
                    np.max(
                        positive_bump
                    )
                ),
            ),
            "mean_drift": abs(
                float(
                    np.mean(
                        repeated_bump
                    )
                )
                - float(
                    np.mean(
                        positive_bump
                    )
                )
            ),
        }

        interpolation_report[
            "forward_reverse_smooth_error"
        ] = maximum_error(
            reversed_smooth,
            smooth_field,
        )

        report["interpolations"][
            interpolation
        ] = interpolation_report

    bilinear = report[
        "interpolations"
    ][
        "bilinear_periodic"
    ]

    cubic = report[
        "interpolations"
    ][
        "cubic_periodic"
    ]

    required_checks = {
        "bilinear_constant_preserved": (
            float(
                bilinear[
                    "constant_error"
                ]
            )
            <= CONSTANT_TOLERANCE
        ),
        "cubic_constant_preserved": (
            float(
                cubic[
                    "constant_error"
                ]
            )
            <= CONSTANT_TOLERANCE
        ),
        "bilinear_means_preserved": all(
            float(error)
            <= MEAN_TOLERANCE
            for error in bilinear[
                "one_step_mean_errors"
            ].values()
        ),
        "cubic_means_preserved": all(
            float(error)
            <= MEAN_TOLERANCE
            for error in cubic[
                "one_step_mean_errors"
            ].values()
        ),
        "bilinear_sharp_maximum_principle": (
            bool(
                bilinear[
                    "one_step_bounds"
                ][
                    "sharp"
                ][
                    "maximum_principle_preserved"
                ]
            )
        ),
        "bilinear_positive_bump_preserved": (
            bool(
                bilinear[
                    "one_step_bounds"
                ][
                    "positive_bump"
                ][
                    "maximum_principle_preserved"
                ]
            )
        ),
    }

    diagnostic_classification = {
        "cubic_sharp_maximum_principle": (
            bool(
                cubic[
                    "one_step_bounds"
                ][
                    "sharp"
                ][
                    "maximum_principle_preserved"
                ]
            )
        ),
        "cubic_positive_bump_maximum_principle": (
            bool(
                cubic[
                    "one_step_bounds"
                ][
                    "positive_bump"
                ][
                    "maximum_principle_preserved"
                ]
            )
        ),
        "cubic_repeated_sharp_maximum_principle": (
            bool(
                cubic[
                    "repeated_sharp"
                ][
                    "bounds"
                ][
                    "maximum_principle_preserved"
                ]
            )
        ),
        "cubic_repeated_bump_maximum_principle": (
            bool(
                cubic[
                    "repeated_positive_bump"
                ][
                    "bounds"
                ][
                    "maximum_principle_preserved"
                ]
            )
        ),
    }

    report[
        "required_checks"
    ] = required_checks

    report[
        "diagnostic_classification"
    ] = diagnostic_classification

    report["global"] = {
        "audit_success": all(
            required_checks.values()
        ),
        "cubic_is_shape_preserving": all(
            diagnostic_classification.values()
        ),
        "recommendation": (
            "Keep cubic_periodic optional until "
            "a bounded or monotone limiter is "
            "implemented and certified."
        ),
    }

    return report


def print_audit(
    report: dict[str, object],
) -> None:
    print(
        "=== AUDIT DE STABILITÉ DE FORME "
        "— ITD V26.2 ==="
    )

    print(
        "Grille                  :",
        report["grid_size"],
    )

    print(
        "Nombre de transports    :",
        report[
            "repeated_step_count"
        ],
    )

    for interpolation in (
        "bilinear_periodic",
        "cubic_periodic",
    ):
        result = report[
            "interpolations"
        ][interpolation]

        sharp_bounds = result[
            "one_step_bounds"
        ]["sharp"]

        bump_bounds = result[
            "one_step_bounds"
        ][
            "positive_bump"
        ]

        repeated_sharp = result[
            "repeated_sharp"
        ]["bounds"]

        repeated_bump = result[
            "repeated_positive_bump"
        ]["bounds"]

        print()
        print(
            f"=== {interpolation} ==="
        )

        print(
            "Erreur champ constant       :",
            f"{float(result['constant_error']):.6e}",
        )

        print(
            "Dérive moyenne maximale     :",
            f"{max(
                float(value)
                for value in result[
                    'one_step_mean_errors'
                ].values()
            ):.6e}",
        )

        print(
            "Créneau après un pas        :",
            (
                f"min={float(
                    sharp_bounds[
                        'result_minimum'
                    ]
                ):.9e}, "
                f"max={float(
                    sharp_bounds[
                        'result_maximum'
                    ]
                ):.9e}"
            ),
        )

        print(
            "Créneau undershoot/overshoot:",
            (
                f"{float(
                    sharp_bounds[
                        'undershoot'
                    ]
                ):.6e} / "
                f"{float(
                    sharp_bounds[
                        'overshoot'
                    ]
                ):.6e}"
            ),
        )

        print(
            "Bosse après un pas          :",
            (
                f"min={float(
                    bump_bounds[
                        'result_minimum'
                    ]
                ):.9e}, "
                f"max={float(
                    bump_bounds[
                        'result_maximum'
                    ]
                ):.9e}"
            ),
        )

        print(
            "Après transports répétés    :"
        )

        print(
            "  créneau undershoot/overshoot :",
            (
                f"{float(
                    repeated_sharp[
                        'undershoot'
                    ]
                ):.6e} / "
                f"{float(
                    repeated_sharp[
                        'overshoot'
                    ]
                ):.6e}"
            ),
        )

        print(
            "  bosse undershoot/overshoot   :",
            (
                f"{float(
                    repeated_bump[
                        'undershoot'
                    ]
                ):.6e} / "
                f"{float(
                    repeated_bump[
                        'overshoot'
                    ]
                ):.6e}"
            ),
        )

        print(
            "Erreur lisse après répétition:",
            f"{float(
                result[
                    'repeated_smooth'
                ][
                    'maximum_error_against_exact'
                ]
            ):.6e}",
        )

        print(
            "Erreur aller-retour lisse   :",
            f"{float(
                result[
                    'forward_reverse_smooth_error'
                ]
            ):.6e}",
        )

    print()
    print(
        "=== CONTRÔLES OBLIGATOIRES ==="
    )

    for name, value in report[
        "required_checks"
    ].items():
        print(
            f"{name:42s}: {value}"
        )

    print()
    print(
        "=== CLASSIFICATION CUBIQUE ==="
    )

    for name, value in report[
        "diagnostic_classification"
    ].items():
        print(
            f"{name:42s}: {value}"
        )

    print()
    print(
        "Audit réussi               :",
        report["global"][
            "audit_success"
        ],
    )

    print(
        "Cubique préservateur de forme:",
        report["global"][
            "cubic_is_shape_preserving"
        ],
    )

    print(
        "Recommandation              :",
        report["global"][
            "recommendation"
        ],
    )


def main() -> None:
    report = run_audit()

    print_audit(report)

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    JSON_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    TEXT_PATH.write_text(
        (
            "ITD V26.2 shape-stability audit\n"
            "\n"
            f"Audit success: "
            f"{report['global']['audit_success']}\n"
            f"Cubic shape preserving: "
            f"{report['global']['cubic_is_shape_preserving']}\n"
            f"Recommendation: "
            f"{report['global']['recommendation']}\n"
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Rapport JSON :",
        JSON_PATH.resolve(),
    )

    print(
        "Rapport texte:",
        TEXT_PATH.resolve(),
    )

    if not report["global"][
        "audit_success"
    ]:
        raise RuntimeError(
            "Un invariant fondamental de "
            "l'interpolation a échoué."
        )


if __name__ == "__main__":
    main()
