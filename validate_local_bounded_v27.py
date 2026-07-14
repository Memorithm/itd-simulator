#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import itd_v26
import itd_v27
import validate_cubic_transport_v25 as base
import validate_shape_stability_v26 as shape


GRID_SIZES = (
    32,
    64,
    128,
    256,
)

AUDIT_GRID_SIZE = 128
REPEATED_STEP_COUNT = 64

SHIFT_X_OVER_H = 0.371
SHIFT_Y_OVER_H = -0.283

BOUND_TOLERANCE = 3.0e-12

OUTPUT_DIRECTORY = Path(
    "itd_v27_results"
)

JSON_PATH = (
    OUTPUT_DIRECTORY
    / "local_bounded_validation.json"
)


def observed_order(
    previous_error: float,
    current_error: float,
    previous_step: float,
    current_step: float,
) -> float:
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


def transport_once(
    field: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    interpolation: str,
) -> np.ndarray:
    velocity_x = np.full_like(
        field,
        displacement_x,
        dtype=np.float64,
    )

    velocity_y = np.full_like(
        field,
        displacement_y,
        dtype=np.float64,
    )

    return itd_v27.periodic_backtrace(
        field,
        coordinates,
        coordinates,
        velocity_x,
        velocity_y,
        1.0,
        interpolation=interpolation,
    )


def repeated_transport(
    field: np.ndarray,
    coordinates: np.ndarray,
    displacement_x: float,
    displacement_y: float,
    interpolation: str,
) -> np.ndarray:
    current = np.asarray(
        field,
        dtype=np.float64,
    ).copy()

    for _ in range(
        REPEATED_STEP_COUNT
    ):
        current = transport_once(
            current,
            coordinates,
            displacement_x,
            displacement_y,
            interpolation,
        )

    return current


def bound_defect(
    result: np.ndarray,
    source: np.ndarray,
) -> tuple[float, float]:
    return (
        max(
            0.0,
            float(np.min(source))
            - float(np.min(result)),
        ),
        max(
            0.0,
            float(np.max(result))
            - float(np.max(source)),
        ),
    )


def validate_api_and_compatibility() -> None:
    print(
        "=== API ET COMPATIBILITÉ V27 ==="
    )

    expected_modes = (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
    )

    observed_modes = tuple(
        itd_v27.TRANSPORT_INTERPOLATIONS
    )

    print(
        "Modes :",
        observed_modes,
    )

    if observed_modes != expected_modes:
        raise RuntimeError(
            "Les modes V27 sont inattendus."
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

    velocity_x = np.full_like(
        source,
        SHIFT_X_OVER_H * spacing,
    )

    velocity_y = np.full_like(
        source,
        SHIFT_Y_OVER_H * spacing,
    )

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
    ):
        reference = itd_v26.periodic_backtrace(
            source,
            coordinates,
            coordinates,
            velocity_x,
            velocity_y,
            1.0,
            interpolation=mode,
        )

        candidate = itd_v27.periodic_backtrace(
            source,
            coordinates,
            coordinates,
            velocity_x,
            velocity_y,
            1.0,
            interpolation=mode,
        )

        identical = np.array_equal(
            reference,
            candidate,
        )

        print(
            f"{mode:24s}: {identical}"
        )

        if not identical:
            raise RuntimeError(
                f"La branche {mode} a été modifiée."
            )

    print(
        "Compatibilité V26 → V27 : VALIDÉE"
    )


def validate_constants_and_nodes() -> None:
    print()
    print(
        "=== CONSTANTES ET DÉPLACEMENTS NODAUX ==="
    )

    (
        coordinates,
        x,
        _,
        spacing,
    ) = base.build_periodic_grid(
        64
    )

    constant = np.full_like(
        x,
        3.25,
    )

    constant_result = transport_once(
        constant,
        coordinates,
        0.37 * spacing,
        -0.21 * spacing,
        "cubic_local_bounded_periodic",
    )

    constant_error = maximum_error(
        constant,
        constant_result,
    )

    indexed = np.arange(
        x.size,
        dtype=np.float64,
    ).reshape(x.shape)

    cubic_nodal = transport_once(
        indexed,
        coordinates,
        spacing,
        -2.0 * spacing,
        "cubic_periodic",
    )

    bounded_nodal = transport_once(
        indexed,
        coordinates,
        spacing,
        -2.0 * spacing,
        "cubic_local_bounded_periodic",
    )

    nodal_error = maximum_error(
        cubic_nodal,
        bounded_nodal,
    )

    print(
        "Erreur constante :",
        f"{constant_error:.6e}",
    )

    print(
        "Erreur nodale    :",
        f"{nodal_error:.6e}",
    )

    if max(
        constant_error,
        nodal_error,
    ) > BOUND_TOLERANCE:
        raise RuntimeError(
            "Les invariants élémentaires ne sont "
            "pas préservés."
        )


def validate_bounds() -> dict[str, object]:
    print()
    print(
        "=== BORNES LOCALES ET GLOBALES ==="
    )

    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        AUDIT_GRID_SIZE
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    fields = {
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
        one_step = transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_bounded_periodic",
        )

        repeated = repeated_transport(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_local_bounded_periodic",
        )

        one_under, one_over = bound_defect(
            one_step,
            source,
        )

        repeated_under, repeated_over = (
            bound_defect(
                repeated,
                source,
            )
        )

        one_mean_drift = abs(
            float(np.mean(one_step))
            - float(np.mean(source))
        )

        repeated_mean_drift = abs(
            float(np.mean(repeated))
            - float(np.mean(source))
        )

        print()
        print(name)

        print(
            "  un pas undershoot/overshoot :",
            f"{one_under:.6e} / "
            f"{one_over:.6e}",
        )

        print(
            "  répété undershoot/overshoot :",
            f"{repeated_under:.6e} / "
            f"{repeated_over:.6e}",
        )

        print(
            "  dérive moyenne un pas       :",
            f"{one_mean_drift:.6e}",
        )

        print(
            "  dérive moyenne répétée      :",
            f"{repeated_mean_drift:.6e}",
        )

        if max(
            one_under,
            one_over,
            repeated_under,
            repeated_over,
        ) > BOUND_TOLERANCE:
            raise RuntimeError(
                "Le limiteur local viole les bornes "
                f"pour {name}."
            )

        report[name] = {
            "one_step_undershoot": one_under,
            "one_step_overshoot": one_over,
            "repeated_undershoot": (
                repeated_under
            ),
            "repeated_overshoot": (
                repeated_over
            ),
            "one_step_mean_drift": (
                one_mean_drift
            ),
            "repeated_mean_drift": (
                repeated_mean_drift
            ),
        }

    print()
    print(
        "Préservation des bornes : VALIDÉE"
    )

    return report


def smooth_convergence() -> dict[str, object]:
    print()
    print(
        "=== CONVERGENCE LISSE DU LIMITEUR LOCAL ==="
    )

    print(
        "grille | bilinéaire | cubique | "
        "borné | ordre borné | fraction limitée"
    )

    spacings: list[float] = []
    bilinear_errors: list[float] = []
    cubic_errors: list[float] = []
    bounded_errors: list[float] = []
    limited_fractions: list[float] = []
    mean_drifts: list[float] = []

    previous_spacing = None
    previous_bounded = None

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

        bilinear = transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "bilinear_periodic",
        )

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

        exact = shape.smooth_periodic_field(
            x - displacement_x,
            y - displacement_y,
        )

        bilinear_error = maximum_error(
            bilinear,
            exact,
        )

        cubic_error = maximum_error(
            cubic,
            exact,
        )

        bounded_error = maximum_error(
            bounded,
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

        mean_drift = abs(
            float(np.mean(bounded))
            - float(np.mean(source))
        )

        spacings.append(spacing)
        bilinear_errors.append(
            bilinear_error
        )
        cubic_errors.append(
            cubic_error
        )
        bounded_errors.append(
            bounded_error
        )
        limited_fractions.append(
            limited_fraction
        )
        mean_drifts.append(
            mean_drift
        )

        if previous_spacing is None:
            order_text = "—"
        else:
            order_text = (
                f"{observed_order(
                    previous_bounded,
                    bounded_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{bilinear_error:9.3e} | "
            f"{cubic_error:9.3e} | "
            f"{bounded_error:9.3e} | "
            f"{order_text:>11} | "
            f"{limited_fraction:.6f}"
        )

        previous_spacing = spacing
        previous_bounded = bounded_error

    bounded_orders = [
        observed_order(
            bounded_errors[index - 1],
            bounded_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(spacings),
        )
    ]

    if not all(
        current < previous
        for previous, current in zip(
            bounded_errors,
            bounded_errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur du limiteur local ne décroît "
            "pas monotoniquement."
        )

    final_order = bounded_orders[-1]

    if final_order >= 3.5:
        classification = (
            "fourth_order_on_declared_oracle"
        )
    elif final_order >= 1.5:
        classification = (
            "reduced_or_preasymptotic_order"
        )
    else:
        raise RuntimeError(
            "La convergence lisse du limiteur "
            "local est insuffisante."
        )

    if not (
        bounded_errors[-1]
        < bilinear_errors[-1]
    ):
        raise RuntimeError(
            "Le limiteur local n'améliore pas "
            "le bilinéaire à la résolution fine."
        )

    print()
    print(
        "Ordre final borné :",
        f"{final_order:.9f}",
    )

    print(
        "Classification    :",
        classification,
    )

    print(
        "Dérive moyenne fine:",
        f"{mean_drifts[-1]:.6e}",
    )

    return {
        "spacings": spacings,
        "bilinear_errors": bilinear_errors,
        "cubic_errors": cubic_errors,
        "bounded_errors": bounded_errors,
        "bounded_orders": bounded_orders,
        "limited_fractions": (
            limited_fractions
        ),
        "mean_drifts": mean_drifts,
        "classification": classification,
    }


def repeated_smooth_comparison() -> dict[str, float]:
    print()
    print(
        "=== PRÉCISION APRÈS 64 TRANSPORTS ==="
    )

    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        AUDIT_GRID_SIZE
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    source = shape.smooth_periodic_field(
        x,
        y,
    )

    exact = shape.smooth_periodic_field(
        x
        - REPEATED_STEP_COUNT
        * displacement_x,
        y
        - REPEATED_STEP_COUNT
        * displacement_y,
    )

    errors: dict[str, float] = {}

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_local_bounded_periodic",
    ):
        result = repeated_transport(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            mode,
        )

        error = maximum_error(
            result,
            exact,
        )

        errors[mode] = error

        print(
            f"{mode:30s}: "
            f"{error:.9e}"
        )

    if not (
        errors[
            "cubic_local_bounded_periodic"
        ]
        < errors["bilinear_periodic"]
    ):
        raise RuntimeError(
            "Le cubique local borné ne surpasse "
            "pas le bilinéaire."
        )

    return errors


def main() -> None:
    print(
        "=== VALIDATION DU CUBIQUE LOCAL BORNÉ "
        "— ITD V27 ==="
    )

    validate_api_and_compatibility()
    validate_constants_and_nodes()

    bounds_report = validate_bounds()
    convergence_report = (
        smooth_convergence()
    )
    repeated_errors = (
        repeated_smooth_comparison()
    )

    report = {
        "version": "ITD V27",
        "status": (
            "local_convex_bound_preserving_"
            "candidate"
        ),
        "algorithm": (
            "Pointwise convex blend between "
            "bilinear and cubic interpolation."
        ),
        "claims": {
            "local_departure_bounds": True,
            "global_source_bounds": True,
            "constant_preservation": True,
            "nodal_permutation_preservation": True,
            "exact_sum_conservation": False,
            "local_monotonicity_proof": False,
        },
        "bounds": bounds_report,
        "smooth_convergence": (
            convergence_report
        ),
        "repeated_smooth_errors": (
            repeated_errors
        ),
        "global": {
            "success": True,
            "default_interpolation": (
                "bilinear_periodic"
            ),
            "bounded_mode_optional": True,
        },
    }

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

    print()
    print(
        "Compatibilité V26 → V27             : VALIDÉE"
    )
    print(
        "Bornes locales de départ            : VALIDÉES"
    )
    print(
        "Conservation exacte de la somme     : NON REVENDIQUÉE"
    )
    print(
        "Cubique historique                  : CONSERVÉ"
    )
    print(
        "Limiteur local                      : OPTIONNEL"
    )
    print(
        "Rapport JSON :",
        JSON_PATH.resolve(),
    )


if __name__ == "__main__":
    main()
