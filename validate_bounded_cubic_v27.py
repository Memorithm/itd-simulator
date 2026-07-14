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

BOUND_TOLERANCE = 2.0e-12
SUM_TOLERANCE = 2.0e-11

OUTPUT_DIRECTORY = Path(
    "itd_v27_results"
)

JSON_PATH = (
    OUTPUT_DIRECTORY
    / "bounded_cubic_validation.json"
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
    step_count: int,
) -> np.ndarray:
    current = np.asarray(
        field,
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


def bound_defect(
    result: np.ndarray,
    source: np.ndarray,
) -> tuple[float, float]:
    lower = float(
        np.min(source)
    )

    upper = float(
        np.max(source)
    )

    minimum = float(
        np.min(result)
    )

    maximum = float(
        np.max(result)
    )

    return (
        max(
            0.0,
            lower - minimum,
        ),
        max(
            0.0,
            maximum - upper,
        ),
    )


def validate_api() -> None:
    print(
        "=== API D'INTERPOLATION V27 ==="
    )

    expected = (
        "bilinear_periodic",
        "cubic_periodic",
        "cubic_bounded_periodic",
    )

    observed = tuple(
        itd_v27.TRANSPORT_INTERPOLATIONS
    )

    print(
        "Modes disponibles :",
        observed,
    )

    if observed != expected:
        raise RuntimeError(
            "La liste des interpolations V27 "
            "est inattendue."
        )

    print(
        "API V27 : VALIDÉE"
    )


def validate_v26_compatibility() -> None:
    print()
    print(
        "=== COMPATIBILITÉ V26 → V27 ==="
    )

    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        96
    )

    field = shape.smooth_periodic_field(
        x,
        y,
    )

    displacement_x = (
        SHIFT_X_OVER_H * spacing
    )

    displacement_y = (
        SHIFT_Y_OVER_H * spacing
    )

    velocity_x = np.full_like(
        field,
        displacement_x,
    )

    velocity_y = np.full_like(
        field,
        displacement_y,
    )

    for mode in (
        "bilinear_periodic",
        "cubic_periodic",
    ):
        reference = itd_v26.periodic_backtrace(
            field,
            coordinates,
            coordinates,
            velocity_x,
            velocity_y,
            1.0,
            interpolation=mode,
        )

        candidate = itd_v27.periodic_backtrace(
            field,
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
                "Une branche historique V26 a été "
                f"modifiée : {mode}."
            )

    print(
        "Compatibilité V26 → V27 : VALIDÉE"
    )


def validate_constants_and_nodal_shift() -> None:
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

    transported_constant = transport_once(
        constant,
        coordinates,
        0.37 * spacing,
        -0.21 * spacing,
        "cubic_bounded_periodic",
    )

    constant_error = maximum_error(
        transported_constant,
        constant,
    )

    indexed = np.arange(
        constant.size,
        dtype=np.float64,
    ).reshape(
        constant.shape
    )

    unlimited_nodal = transport_once(
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
        "cubic_bounded_periodic",
    )

    nodal_error = maximum_error(
        bounded_nodal,
        unlimited_nodal,
    )

    print(
        "Erreur constante :",
        f"{constant_error:.6e}",
    )

    print(
        "Écart nodal      :",
        f"{nodal_error:.6e}",
    )

    if constant_error > BOUND_TOLERANCE:
        raise RuntimeError(
            "Le limiteur ne préserve pas "
            "les constantes."
        )

    if nodal_error > BOUND_TOLERANCE:
        raise RuntimeError(
            "Le limiteur altère une permutation "
            "nodale exacte."
        )

    print(
        "Constantes et nœuds : VALIDÉS"
    )


def validate_sharp_bounds() -> dict[str, object]:
    print()
    print(
        "=== PRINCIPE DU MAXIMUM GLOBAL ==="
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
        one_step_unlimited = transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_periodic",
        )

        one_step_bounded = transport_once(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_bounded_periodic",
        )

        repeated_bounded = repeated_transport(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            "cubic_bounded_periodic",
            REPEATED_STEP_COUNT,
        )

        one_under, one_over = bound_defect(
            one_step_bounded,
            source,
        )

        repeated_under, repeated_over = (
            bound_defect(
                repeated_bounded,
                source,
            )
        )

        unlimited_sum = float(
            np.sum(
                one_step_unlimited,
                dtype=np.float64,
            )
        )

        bounded_sum = float(
            np.sum(
                one_step_bounded,
                dtype=np.float64,
            )
        )

        one_sum_error = abs(
            bounded_sum
            - unlimited_sum
        )

        repeated_sum_error = abs(
            float(
                np.sum(
                    repeated_bounded,
                    dtype=np.float64,
                )
            )
            - float(
                np.sum(
                    source,
                    dtype=np.float64,
                )
            )
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
            "  erreur somme sur un pas     :",
            f"{one_sum_error:.6e}",
        )

        print(
            "  dérive somme répétée        :",
            f"{repeated_sum_error:.6e}",
        )

        if max(
            one_under,
            one_over,
            repeated_under,
            repeated_over,
        ) > BOUND_TOLERANCE:
            raise RuntimeError(
                "Le mode borné viole le principe "
                f"du maximum pour {name}."
            )

        if one_sum_error > SUM_TOLERANCE:
            raise RuntimeError(
                "Le limiteur ne préserve pas la "
                "somme cubique sur un pas."
            )

        if repeated_sum_error > SUM_TOLERANCE:
            raise RuntimeError(
                "La somme dérive après transports "
                f"répétés pour {name}."
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
            "one_step_sum_error": (
                one_sum_error
            ),
            "repeated_sum_error": (
                repeated_sum_error
            ),
        }

    print()
    print(
        "Principe du maximum global : VALIDÉ"
    )

    return report


def smooth_convergence() -> dict[str, object]:
    print()
    print(
        "=== CONVERGENCE SUR CHAMP LISSE ==="
    )

    print(
        "grille | erreur cubique | ordre | "
        "erreur bornée | ordre | fraction limitée"
    )

    spacings: list[float] = []
    cubic_errors: list[float] = []
    bounded_errors: list[float] = []
    limited_fractions: list[float] = []

    previous_spacing = None
    previous_cubic = None
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
            "cubic_bounded_periodic",
        )

        exact = shape.smooth_periodic_field(
            x - displacement_x,
            y - displacement_y,
        )

        cubic_error = maximum_error(
            cubic,
            exact,
        )

        bounded_error = maximum_error(
            bounded,
            exact,
        )

        difference = np.abs(
            bounded - cubic
        )

        activation_tolerance = (
            128.0
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
                difference
                > activation_tolerance
            )
        )

        spacings.append(spacing)
        cubic_errors.append(cubic_error)
        bounded_errors.append(bounded_error)
        limited_fractions.append(
            limited_fraction
        )

        if previous_spacing is None:
            cubic_order_text = "—"
            bounded_order_text = "—"
        else:
            cubic_order_text = (
                f"{observed_order(
                    previous_cubic,
                    cubic_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

            bounded_order_text = (
                f"{observed_order(
                    previous_bounded,
                    bounded_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{cubic_error:13.6e} | "
            f"{cubic_order_text:>8} | "
            f"{bounded_error:12.6e} | "
            f"{bounded_order_text:>8} | "
            f"{limited_fraction:.6f}"
        )

        previous_spacing = spacing
        previous_cubic = cubic_error
        previous_bounded = bounded_error

    cubic_orders = [
        observed_order(
            cubic_errors[index - 1],
            cubic_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(spacings),
        )
    ]

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
            "L'erreur bornée ne décroît pas "
            "monotoniquement."
        )

    final_order = (
        bounded_orders[-1]
    )

    if final_order >= 3.5:
        classification = (
            "fourth_order_on_declared_smooth_oracle"
        )
    elif final_order >= 1.5:
        classification = (
            "bounded_with_reduced_smooth_order"
        )
    else:
        classification = (
            "insufficient_smooth_convergence"
        )

    if classification == (
        "insufficient_smooth_convergence"
    ):
        raise RuntimeError(
            "Le limiteur ne présente pas une "
            "convergence lisse suffisante."
        )

    print()
    print(
        "Ordre final cubique :",
        f"{cubic_orders[-1]:.9f}",
    )

    print(
        "Ordre final borné   :",
        f"{bounded_orders[-1]:.9f}",
    )

    print(
        "Classification      :",
        classification,
    )

    return {
        "spacings": spacings,
        "cubic_errors": cubic_errors,
        "bounded_errors": bounded_errors,
        "limited_fractions": (
            limited_fractions
        ),
        "cubic_orders": cubic_orders,
        "bounded_orders": bounded_orders,
        "classification": classification,
    }


def repeated_smooth_comparison() -> dict[str, float]:
    print()
    print(
        "=== PRÉCISION LISSE APRÈS 64 TRANSPORTS ==="
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
        "cubic_bounded_periodic",
    ):
        result = repeated_transport(
            source,
            coordinates,
            displacement_x,
            displacement_y,
            mode,
            REPEATED_STEP_COUNT,
        )

        error = maximum_error(
            result,
            exact,
        )

        errors[mode] = error

        print(
            f"{mode:24s}: "
            f"{error:.9e}"
        )

    if not (
        errors["cubic_bounded_periodic"]
        < errors["bilinear_periodic"]
    ):
        raise RuntimeError(
            "Le cubique borné n'améliore pas "
            "la précision bilinéaire."
        )

    return errors


def validate_invalid_mode() -> None:
    print()
    print(
        "=== REJET D'UN MODE INVALIDE ==="
    )

    try:
        itd_v27.validate_transport_interpolation(
            "bounded"
        )
    except ValueError as error:
        print(
            "Mode 'bounded' : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Un alias d'interpolation invalide "
            "a été accepté."
        )


def main() -> None:
    print(
        "=== VALIDATION DU CUBIQUE BORNÉ "
        "— ITD V27 ==="
    )

    validate_api()
    validate_v26_compatibility()
    validate_constants_and_nodal_shift()

    sharp_report = (
        validate_sharp_bounds()
    )

    convergence_report = (
        smooth_convergence()
    )

    repeated_errors = (
        repeated_smooth_comparison()
    )

    validate_invalid_mode()

    report = {
        "version": "ITD V27",
        "status": (
            "global_bound_preserving_"
            "cubic_candidate"
        ),
        "scope": (
            "Global source bounds and unlimited "
            "cubic sum are preserved. Local "
            "monotonicity is not claimed."
        ),
        "sharp_bounds": sharp_report,
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
            "historical_cubic_preserved": True,
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
        "Principe du maximum global          : VALIDÉ"
    )

    print(
        "Somme cubique de référence          : CONSERVÉE"
    )

    print(
        "Monotonie locale                    : NON REVENDIQUÉE"
    )

    print(
        "Cubique historique non limité       : CONSERVÉ"
    )

    print(
        "Mode borné                          : OPTIONNEL"
    )

    print(
        "Rapport JSON :",
        JSON_PATH.resolve(),
    )


if __name__ == "__main__":
    main()
