#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import itd_v28
import itd_v29
import validate_cubic_transport_v25 as base
import validate_shape_stability_v26 as shape


GRID_SIZES = (
    32,
    64,
    128,
    256,
)

TIME_INTERVALS = (
    (0.00, 0.07),
    (0.13, 0.31),
    (0.41, 0.73),
)

MODES = (
    "bilinear_periodic",
    "cubic_periodic",
    "cubic_local_bounded_periodic",
    "cubic_local_sum_preserving_periodic",
)

ROUND_OFF_TOLERANCE = 5.0e-13
BOUND_TOLERANCE = 8.0e-12
SUM_TOLERANCE = 5.0e-10

OUTPUT_PATH = Path(
    "itd_v29_results"
    "/direct_departure_validation.json"
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


def midpoint_transport(
    module: object,
    field: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    coordinates: np.ndarray,
    previous_time: float,
    current_time: float,
    mode: str,
) -> np.ndarray:
    return (
        module
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            previous_time,
            current_time,
            variable_periodic_velocity,
            transport_interpolation=mode,
            transport_trajectory_method=(
                "midpoint_time_velocity"
            ),
        )
    )


def rk4_transport(
    module: object,
    field: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    coordinates: np.ndarray,
    previous_time: float,
    current_time: float,
    mode: str,
) -> np.ndarray:
    return (
        module
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            previous_time,
            current_time,
            variable_periodic_velocity,
            transport_interpolation=mode,
            transport_trajectory_method=(
                "rk4_backtrace"
            ),
        )
    )


def local_bound_defect(
    result: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> float:
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


def validate_api() -> None:
    print(
        "=== API DIRECTE V29 ==="
    )

    names = (
        "periodic_bilinear_sample_at_departures",
        "periodic_cubic_sample_at_departures",
        "periodic_departure_bounds",
        "periodic_cubic_local_bounded_sample_at_departures",
        "periodic_cubic_local_sum_preserving_sample_at_departures",
        "periodic_sample_at_departures",
    )

    for name in names:
        exists = callable(
            getattr(
                itd_v29,
                name,
                None,
            )
        )

        print(
            f"{name:62s}: {exists}"
        )

        if not exists:
            raise RuntimeError(
                f"API V29 absente : {name}."
            )

    try:
        itd_v29.periodic_sample_at_departures(
            np.zeros(
                (4, 4),
                dtype=np.float64,
            ),
            np.arange(
                4,
                dtype=np.float64,
            ),
            np.arange(
                4,
                dtype=np.float64,
            ),
            np.zeros(
                (4, 4),
                dtype=np.float64,
            ),
            np.zeros(
                (4, 4),
                dtype=np.float64,
            ),
            interpolation=(
                "mode_invalide"
            ),
        )
    except ValueError:
        print(
            "Mode invalide rejeté : True"
        )
    else:
        raise RuntimeError(
            "Un mode d'interpolation invalide "
            "a été accepté."
        )


def validate_midpoint_bitwise() -> None:
    print()
    print(
        "=== COMPATIBILITÉ BIT À BIT "
        "DU CHEMIN HISTORIQUE ==="
    )

    (
        coordinates,
        x,
        y,
        _,
    ) = base.build_periodic_grid(
        96
    )

    field = shape.smooth_periodic_field(
        x,
        y,
    )

    for mode in MODES:
        reference = midpoint_transport(
            itd_v28,
            field,
            x,
            y,
            coordinates,
            0.13,
            0.31,
            mode,
        )

        candidate = midpoint_transport(
            itd_v29,
            field,
            x,
            y,
            coordinates,
            0.13,
            0.31,
            mode,
        )

        identical = np.array_equal(
            reference,
            candidate,
        )

        print(
            f"{mode:42s}: {identical}"
        )

        if not identical:
            raise RuntimeError(
                "Le chemin historique au point "
                f"milieu a changé pour {mode}."
            )


def validate_direct_wrappers() -> dict[str, float]:
    print()
    print(
        "=== COHÉRENCE API DIRECTE "
        "ET ADAPTATEURS V28 ==="
    )

    maxima = {
        mode: 0.0
        for mode in MODES
    }

    maximum_bound_error = 0.0
    maximum_bound_defect = 0.0
    maximum_sum_error = 0.0

    print(
        "grille | mode | écart direct/adaptateur | "
        "erreur bornes | défaut bornes"
    )

    for grid_size in GRID_SIZES:
        (
            coordinates,
            x,
            y,
            spacing,
        ) = base.build_periodic_grid(
            grid_size
        )

        field = shape.smooth_periodic_field(
            x + 0.173 * spacing,
            y - 0.291 * spacing,
        )

        departure_x = (
            x
            - 0.371 * spacing
            - 0.083
            * spacing
            * np.sin(
                2.0
                * np.pi
                * y
                / float(
                    base.DOMAIN_LENGTH
                )
            )
        )

        departure_y = (
            y
            + 0.283 * spacing
            + 0.061
            * spacing
            * np.cos(
                2.0
                * np.pi
                * x
                / float(
                    base.DOMAIN_LENGTH
                )
            )
        )

        delta_time = 0.37

        effective_velocity_x = (
            x - departure_x
        ) / delta_time

        effective_velocity_y = (
            y - departure_y
        ) / delta_time

        direct_lower, direct_upper = (
            itd_v29.periodic_departure_bounds(
                field,
                coordinates,
                coordinates,
                departure_x,
                departure_y,
            )
        )

        wrapper_lower, wrapper_upper = (
            itd_v28
            .periodic_bilinear_departure_bounds(
                field,
                coordinates,
                coordinates,
                effective_velocity_x,
                effective_velocity_y,
                delta_time,
            )
        )

        bound_error = max(
            float(
                np.max(
                    np.abs(
                        direct_lower
                        - wrapper_lower
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        direct_upper
                        - wrapper_upper
                    )
                )
            ),
        )

        maximum_bound_error = max(
            maximum_bound_error,
            bound_error,
        )

        cubic_direct = (
            itd_v29
            .periodic_cubic_sample_at_departures(
                field,
                coordinates,
                coordinates,
                departure_x,
                departure_y,
            )
        )

        for mode in MODES:
            direct = (
                itd_v29
                .periodic_sample_at_departures(
                    field,
                    coordinates,
                    coordinates,
                    departure_x,
                    departure_y,
                    interpolation=mode,
                )
            )

            wrapper = (
                itd_v28.periodic_backtrace(
                    field,
                    coordinates,
                    coordinates,
                    effective_velocity_x,
                    effective_velocity_y,
                    delta_time,
                    interpolation=mode,
                )
            )

            difference = float(
                np.max(
                    np.abs(
                        direct - wrapper
                    )
                )
            )

            maxima[mode] = max(
                maxima[mode],
                difference,
            )

            defect = 0.0

            if mode in (
                "cubic_local_bounded_periodic",
                "cubic_local_sum_preserving_periodic",
            ):
                defect = local_bound_defect(
                    direct,
                    direct_lower,
                    direct_upper,
                )

                maximum_bound_defect = max(
                    maximum_bound_defect,
                    defect,
                )

            if (
                mode
                == "cubic_local_sum_preserving_periodic"
            ):
                sum_error = float(
                    abs(
                        precise_sum(
                            direct
                        )
                        - precise_sum(
                            cubic_direct
                        )
                    )
                )

                maximum_sum_error = max(
                    maximum_sum_error,
                    sum_error,
                )

            print(
                f"{grid_size:6d} | "
                f"{mode:42s} | "
                f"{difference:.3e} | "
                f"{bound_error:.3e} | "
                f"{defect:.3e}"
            )

    if (
        max(maxima.values())
        > ROUND_OFF_TOLERANCE
    ):
        raise RuntimeError(
            "L'API directe diffère excessivement "
            "des adaptateurs historiques."
        )

    if (
        maximum_bound_error
        > ROUND_OFF_TOLERANCE
    ):
        raise RuntimeError(
            "Les bornes directes diffèrent des "
            "bornes historiques."
        )

    if (
        maximum_bound_defect
        > BOUND_TOLERANCE
    ):
        raise RuntimeError(
            "Une interpolation directe limitée "
            "viole les bornes locales."
        )

    if (
        maximum_sum_error
        > SUM_TOLERANCE
    ):
        raise RuntimeError(
            "Le mode direct à somme préservée "
            "ne respecte pas sa somme cible."
        )

    return {
        "maximum_wrapper_difference": max(
            maxima.values()
        ),
        "maximum_bound_error": (
            maximum_bound_error
        ),
        "maximum_bound_defect": (
            maximum_bound_defect
        ),
        "maximum_sum_error": (
            maximum_sum_error
        ),
    }


def validate_rk4_path() -> dict[str, float]:
    print()
    print(
        "=== ÉQUIVALENCE DU CHEMIN RK4 "
        "V28 → V29 ==="
    )

    maximum_difference = 0.0
    maximum_bound_defect = 0.0
    maximum_sum_error = 0.0

    print(
        "grille | intervalle | mode | "
        "écart V28/V29 | défaut bornes | "
        "erreur somme"
    )

    for grid_size in GRID_SIZES:
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

        for (
            previous_time,
            current_time,
        ) in TIME_INTERVALS:
            departure_x, departure_y = (
                itd_v29
                .rk4_periodic_departure_points(
                    x,
                    y,
                    coordinates,
                    coordinates,
                    previous_time,
                    current_time,
                    variable_periodic_velocity,
                )
            )

            lower, upper = (
                itd_v29.periodic_departure_bounds(
                    field,
                    coordinates,
                    coordinates,
                    departure_x,
                    departure_y,
                )
            )

            cubic_direct = (
                itd_v29
                .periodic_cubic_sample_at_departures(
                    field,
                    coordinates,
                    coordinates,
                    departure_x,
                    departure_y,
                )
            )

            for mode in MODES:
                reference = rk4_transport(
                    itd_v28,
                    field,
                    x,
                    y,
                    coordinates,
                    previous_time,
                    current_time,
                    mode,
                )

                candidate = rk4_transport(
                    itd_v29,
                    field,
                    x,
                    y,
                    coordinates,
                    previous_time,
                    current_time,
                    mode,
                )

                difference = float(
                    np.max(
                        np.abs(
                            candidate
                            - reference
                        )
                    )
                )

                maximum_difference = max(
                    maximum_difference,
                    difference,
                )

                defect = 0.0
                sum_error = 0.0

                if mode in (
                    "cubic_local_bounded_periodic",
                    "cubic_local_sum_preserving_periodic",
                ):
                    defect = local_bound_defect(
                        candidate,
                        lower,
                        upper,
                    )

                    maximum_bound_defect = max(
                        maximum_bound_defect,
                        defect,
                    )

                if (
                    mode
                    == "cubic_local_sum_preserving_periodic"
                ):
                    sum_error = float(
                        abs(
                            precise_sum(
                                candidate
                            )
                            - precise_sum(
                                cubic_direct
                            )
                        )
                    )

                    maximum_sum_error = max(
                        maximum_sum_error,
                        sum_error,
                    )

                print(
                    f"{grid_size:6d} | "
                    f"[{previous_time:.2f},{current_time:.2f}] | "
                    f"{mode:42s} | "
                    f"{difference:.3e} | "
                    f"{defect:.3e} | "
                    f"{sum_error:.3e}"
                )

    if (
        maximum_difference
        > ROUND_OFF_TOLERANCE
    ):
        raise RuntimeError(
            "Le chemin RK4 direct de V29 diffère "
            "excessivement de V28."
        )

    if (
        maximum_bound_defect
        > BOUND_TOLERANCE
    ):
        raise RuntimeError(
            "Le chemin RK4 direct viole les "
            "bornes locales."
        )

    if (
        maximum_sum_error
        > SUM_TOLERANCE
    ):
        raise RuntimeError(
            "Le chemin RK4 direct ne préserve pas "
            "la somme cubique."
        )

    return {
        "maximum_rk4_difference": (
            maximum_difference
        ),
        "maximum_rk4_bound_defect": (
            maximum_bound_defect
        ),
        "maximum_rk4_sum_error": (
            maximum_sum_error
        ),
    }


def validate_constants() -> None:
    print()
    print(
        "=== CONSTANTES ET IDENTITÉ ==="
    )

    (
        coordinates,
        x,
        y,
        _,
    ) = base.build_periodic_grid(
        64
    )

    constant = np.full_like(
        x,
        3.25,
        dtype=np.float64,
    )

    for mode in MODES:
        result = (
            itd_v29
            .periodic_sample_at_departures(
                constant,
                coordinates,
                coordinates,
                x,
                y,
                interpolation=mode,
            )
        )

        error = float(
            np.max(
                np.abs(
                    result - constant
                )
            )
        )

        print(
            f"{mode:42s}: {error:.3e}"
        )

        if error > ROUND_OFF_TOLERANCE:
            raise RuntimeError(
                "Une constante ou l'identité "
                "n'est pas reproduite à la "
                f"tolérance déclarée pour {mode}."
            )


def main() -> None:
    print(
        "=== VALIDATION DE L'API DIRECTE "
        "— ITD V29.0 ==="
    )

    validate_api()
    validate_midpoint_bitwise()
    validate_constants()

    wrapper_summary = (
        validate_direct_wrappers()
    )

    rk4_summary = (
        validate_rk4_path()
    )

    summary = {
        **wrapper_summary,
        **rk4_summary,
    }

    checks = {
        "historical_midpoint_bitwise": True,
        "direct_api_available": True,
        "direct_wrapper_roundoff_equivalence": (
            summary[
                "maximum_wrapper_difference"
            ]
            <= ROUND_OFF_TOLERANCE
        ),
        "rk4_roundoff_equivalence": (
            summary[
                "maximum_rk4_difference"
            ]
            <= ROUND_OFF_TOLERANCE
        ),
        "local_bounds_preserved": (
            max(
                summary[
                    "maximum_bound_defect"
                ],
                summary[
                    "maximum_rk4_bound_defect"
                ],
            )
            <= BOUND_TOLERANCE
        ),
        "cubic_sum_preserved": (
            max(
                summary[
                    "maximum_sum_error"
                ],
                summary[
                    "maximum_rk4_sum_error"
                ],
            )
            <= SUM_TOLERANCE
        ),
    }

    print()
    print(
        "=== CONCLUSION V29.0 ==="
    )

    for name, result in checks.items():
        print(
            f"{name:48s}: {result}"
        )

    print()
    print(
        "Écart direct/adaptateur maximal :",
        f"{summary[
            'maximum_wrapper_difference'
        ]:.9e}",
    )

    print(
        "Écart RK4 V28/V29 maximal       :",
        f"{summary[
            'maximum_rk4_difference'
        ]:.9e}",
    )

    print(
        "Erreur de borne maximale        :",
        f"{summary[
            'maximum_bound_error'
        ]:.9e}",
    )

    print(
        "Défaut de borne maximal         :",
        f"{max(
            summary[
                'maximum_bound_defect'
            ],
            summary[
                'maximum_rk4_bound_defect'
            ],
        ):.9e}",
    )

    print(
        "Erreur de somme maximale        :",
        f"{max(
            summary[
                'maximum_sum_error'
            ],
            summary[
                'maximum_rk4_sum_error'
            ],
        ):.9e}",
    )

    report = {
        "version": "ITD V29.0",
        "status": (
            "direct_departure_api_candidate"
        ),
        "grid_sizes": list(
            GRID_SIZES
        ),
        "time_intervals": [
            list(interval)
            for interval in TIME_INTERVALS
        ],
        "modes": list(
            MODES
        ),
        "summary": summary,
        "checks": checks,
        "claims": {
            "new_scientific_quantity": False,
            "historical_midpoint_path_changed": False,
            "rk4_effective_velocity_round_trip_removed": True,
            "direct_departure_coordinates_used": True,
            "v28_archive_modified": False,
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
            "La validation V29.0 n'est pas "
            "entièrement réussie."
        )


if __name__ == "__main__":
    main()
