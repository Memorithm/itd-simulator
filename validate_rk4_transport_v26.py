#!/usr/bin/env python3

from __future__ import annotations

import inspect
import math

import numpy as np

import itd_v25
import itd_v26
import validate_cubic_transport_v25 as base


GRID_SIZES = (
    32,
    64,
    128,
    256,
)

JERK_DT_OVER_H = 0.47

MIDPOINT_FIELD_ORDER_RANGE = (
    2.80,
    3.20,
)

MIDPOINT_RATE_ORDER_RANGE = (
    1.80,
    2.20,
)

RK4_FIELD_ORDER_RANGE = (
    3.70,
    4.30,
)

RK4_RATE_ORDER_RANGE = (
    2.70,
    3.30,
)

RK4_GLOBAL_ORDER_RANGE = (
    3.70,
    4.30,
)


def observed_order(
    previous_error: float,
    current_error: float,
    previous_step: float,
    current_step: float,
) -> float:
    return float(
        np.log(
            previous_error
            / current_error
        )
        / np.log(
            previous_step
            / current_step
        )
    )


def make_periodic_case(
    grid_size: int = 64,
    dt_over_h: float = 0.31,
):
    (
        coordinates,
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

    velocity = base.make_translating_velocity(
        base.PHYSICAL_TRANSPORT[0],
        base.PHYSICAL_TRANSPORT[1],
        growth_rate=(
            base.REFERENCE_GAMMA_GROWTH_RATE
        ),
    )

    transport = base.make_constant_velocity(
        base.PHYSICAL_TRANSPORT[0],
        base.PHYSICAL_TRANSPORT[1],
    )

    return (
        coordinates,
        x,
        y,
        spacing,
        times,
        cfg,
        velocity,
        transport,
    )


def validate_api() -> None:
    print(
        "=== API DE RÉTROTRAÇAGE V26 ==="
    )

    expected = (
        "midpoint_time_velocity",
        "rk4_backtrace",
    )

    observed = tuple(
        itd_v26
        .TRANSPORT_TRAJECTORY_METHODS
    )

    print(
        "Méthodes disponibles :",
        observed,
    )

    if observed != expected:
        raise RuntimeError(
            "Les méthodes V26 sont inattendues."
        )

    for function in (
        itd_v26
        .transport_previous_vorticity_periodic,
        itd_v26.simulate,
        itd_v26.simulate_multiscale,
    ):
        signature = inspect.signature(
            function
        )

        print(
            function.__name__,
            signature,
        )

        if (
            "transport_trajectory_method"
            not in signature.parameters
        ):
            raise RuntimeError(
                "Paramètre de trajectoire absent de "
                f"{function.__name__}()."
            )

    print(
        "API V26 : VALIDÉE"
    )


def validate_v25_compatibility() -> None:
    print()
    print(
        "=== COMPATIBILITÉ V25 → V26 ==="
    )

    (
        _,
        x,
        y,
        spacing,
        times,
        cfg,
        velocity,
        transport,
    ) = make_periodic_case()

    common = {
        "x": x,
        "y": y,
        "times": times,
        "spacing": spacing,
        "cfg": cfg,
        "curvature_function": (
            base.zero_curvature
        ),
        "boundary_mode": "periodic",
        "temporal_deformation_mode": (
            "transport_compensated"
        ),
        "transport_velocity_function": (
            transport
        ),
        "transport_interpolation": (
            "cubic_periodic"
        ),
    }

    historical = itd_v25.simulate(
        "v25_reference",
        velocity,
        **common,
    )

    default_v26 = itd_v26.simulate(
        "v26_default",
        velocity,
        **common,
    )

    explicit_midpoint = itd_v26.simulate(
        "v26_explicit_midpoint",
        velocity,
        transport_trajectory_method=(
            "midpoint_time_velocity"
        ),
        **common,
    )

    array_keys = (
        "temporal_deformation_compensated_interval",
    )

    scalar_keys = (
        "temporal_deformation_compensated_index",
    )

    for key in array_keys:
        reference = np.asarray(
            historical[key]
        )

        default = np.asarray(
            default_v26[key]
        )

        explicit = np.asarray(
            explicit_midpoint[key]
        )

        if not np.array_equal(
            reference,
            default,
        ):
            raise RuntimeError(
                f"Incompatibilité V25/V26 pour {key}."
            )

        if not np.array_equal(
            default,
            explicit,
        ):
            raise RuntimeError(
                "Le mode midpoint explicite diffère "
                f"du défaut pour {key}."
            )

    for key in scalar_keys:
        if historical[key] != default_v26[key]:
            raise RuntimeError(
                f"Incompatibilité V25/V26 pour {key}."
            )

        if (
            default_v26[key]
            != explicit_midpoint[key]
        ):
            raise RuntimeError(
                "Le mode midpoint explicite diffère "
                f"du défaut pour {key}."
            )

    metadata = default_v26[
        "transport_compensation"
    ]

    if (
        metadata["backtrace"]
        != "midpoint_time_velocity"
    ):
        raise RuntimeError(
            "La méthode historique n'est pas "
            "le défaut V26."
        )

    print(
        "Intervalles bit à bit : True"
    )

    print(
        "Indices bit à bit     : True"
    )

    print(
        "Défaut = midpoint explicite : True"
    )

    print(
        "Compatibilité V25 → V26 : VALIDÉE"
    )


def validate_constant_velocity_equivalence() -> None:
    print()
    print(
        "=== VITESSE CONSTANTE : MIDPOINT / RK4 ==="
    )

    (
        coordinates,
        x,
        y,
        spacing,
        _,
        _,
        _,
        transport,
    ) = make_periodic_case(
        grid_size=96,
        dt_over_h=0.47,
    )

    delta_time = (
        0.47 * spacing
    )

    field = base.analytic_scalar(
        x,
        y,
    )

    midpoint = (
        itd_v26
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            0.0,
            delta_time,
            transport,
            transport_interpolation=(
                "cubic_periodic"
            ),
            transport_trajectory_method=(
                "midpoint_time_velocity"
            ),
        )
    )

    rk4 = (
        itd_v26
        .transport_previous_vorticity_periodic(
            field,
            x,
            y,
            coordinates,
            coordinates,
            0.0,
            delta_time,
            transport,
            transport_interpolation=(
                "cubic_periodic"
            ),
            transport_trajectory_method=(
                "rk4_backtrace"
            ),
        )
    )

    error = float(
        np.max(
            np.abs(
                rk4 - midpoint
            )
        )
    )

    print(
        "Écart maximal :",
        f"{error:.6e}",
    )

    if error > 5.0e-13:
        raise RuntimeError(
            "RK4 ne reproduit pas le transport "
            "à vitesse constante."
        )

    print(
        "Équivalence constante : VALIDÉE"
    )


def validate_rk4_global_order() -> None:
    print()
    print(
        "=== ORDRE GLOBAL RK4 SUR ODE SPATIALE ==="
    )

    coordinates = np.linspace(
        -10.0,
        10.0,
        128,
        endpoint=False,
        dtype=np.float64,
    )

    final_x = np.asarray(
        (
            (1.20, 1.55),
            (1.90, 2.30),
        ),
        dtype=np.float64,
    )

    final_y = np.asarray(
        (
            (1.10, 1.40),
            (1.75, 2.05),
        ),
        dtype=np.float64,
    )

    coefficient_x = 0.23
    coefficient_y = -0.17
    duration = 0.8

    def velocity(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ):
        del time

        return (
            coefficient_x * x,
            coefficient_y * y,
        )

    exact_x = (
        final_x
        * math.exp(
            -coefficient_x
            * duration
        )
    )

    exact_y = (
        final_y
        * math.exp(
            -coefficient_y
            * duration
        )
    )

    step_counts = (
        4,
        8,
        16,
        32,
    )

    errors: list[float] = []
    steps: list[float] = []

    print(
        "pas | delta_t | erreur | ordre"
    )

    previous_error = None
    previous_step = None

    for step_count in step_counts:
        delta_time = (
            duration / step_count
        )

        current_x = final_x.copy()
        current_y = final_y.copy()

        for index in range(
            step_count,
            0,
            -1,
        ):
            current_time = (
                index * delta_time
            )

            previous_time = (
                (index - 1)
                * delta_time
            )

            current_x, current_y = (
                itd_v26
                .rk4_periodic_departure_points(
                    current_x,
                    current_y,
                    coordinates,
                    coordinates,
                    previous_time,
                    current_time,
                    velocity,
                )
            )

        error = float(
            max(
                np.max(
                    np.abs(
                        current_x - exact_x
                    )
                ),
                np.max(
                    np.abs(
                        current_y - exact_y
                    )
                ),
            )
        )

        errors.append(error)
        steps.append(delta_time)

        if previous_error is None:
            order_text = "—"
        else:
            order_text = (
                f"{observed_order(
                    previous_error,
                    error,
                    previous_step,
                    delta_time,
                ):.6f}"
            )

        print(
            f"{step_count:3d} | "
            f"{delta_time:.6e} | "
            f"{error:.6e} | "
            f"{order_text:>8}"
        )

        previous_error = error
        previous_step = delta_time

    final_order = observed_order(
        errors[-2],
        errors[-1],
        steps[-2],
        steps[-1],
    )

    if not (
        RK4_GLOBAL_ORDER_RANGE[0]
        <= final_order
        <= RK4_GLOBAL_ORDER_RANGE[1]
    ):
        raise RuntimeError(
            "Le rétrotraçage RK4 n'atteint pas "
            "l'ordre global quatre."
        )

    print(
        "Rétrotraçage RK4 global ordre 4 : VALIDÉ"
    )


def jerk_defect(
    grid_size: int,
    method: str,
) -> tuple[
    float,
    float,
    float,
]:
    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        grid_size
    )

    delta_time = (
        JERK_DT_OVER_H
        * spacing
    )

    previous_field = base.analytic_scalar(
        x,
        y,
    )

    displacement, frame_velocity = (
        base.make_jerk_frame()
    )

    def transformed_transport(
        point_x: np.ndarray,
        point_y: np.ndarray,
        time: float,
    ):
        frame = np.asarray(
            frame_velocity(time),
            dtype=np.float64,
        )

        return (
            np.full_like(
                point_x,
                base.PHYSICAL_TRANSPORT[0]
                - frame[0],
                dtype=np.float64,
            ),
            np.full_like(
                point_y,
                base.PHYSICAL_TRANSPORT[1]
                - frame[1],
                dtype=np.float64,
            ),
        )

    numerical = (
        itd_v26
        .transport_previous_vorticity_periodic(
            previous_field,
            x,
            y,
            coordinates,
            coordinates,
            0.0,
            delta_time,
            transformed_transport,
            transport_interpolation=(
                "cubic_periodic"
            ),
            transport_trajectory_method=(
                method
            ),
        )
    )

    previous_displacement = np.asarray(
        displacement(0.0),
        dtype=np.float64,
    )

    current_displacement = np.asarray(
        displacement(delta_time),
        dtype=np.float64,
    )

    exact_source_x = (
        x
        - base.PHYSICAL_TRANSPORT[0]
        * delta_time
        + current_displacement[0]
        - previous_displacement[0]
    )

    exact_source_y = (
        y
        - base.PHYSICAL_TRANSPORT[1]
        * delta_time
        + current_displacement[1]
        - previous_displacement[1]
    )

    exact = base.analytic_scalar(
        exact_source_x,
        exact_source_y,
    )

    field_error = float(
        np.max(
            np.abs(
                numerical - exact
            )
        )
    )

    rate_error = (
        field_error / delta_time
    )

    return (
        spacing,
        rate_error,
        field_error,
    )


def run_jerk_study(
    method: str,
    title: str,
) -> tuple[
    list[float],
    list[float],
]:
    print()
    print(title)
    print(
        "grille | défaut taux | ordre | "
        "défaut champ | ordre"
    )

    spacings: list[float] = []
    rate_errors: list[float] = []
    field_errors: list[float] = []

    previous_spacing = None
    previous_rate = None
    previous_field = None

    for grid_size in GRID_SIZES:
        (
            spacing,
            rate_error,
            field_error,
        ) = jerk_defect(
            grid_size,
            method,
        )

        spacings.append(spacing)
        rate_errors.append(rate_error)
        field_errors.append(field_error)

        if previous_spacing is None:
            rate_order_text = "—"
            field_order_text = "—"
        else:
            rate_order_text = (
                f"{observed_order(
                    previous_rate,
                    rate_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

            field_order_text = (
                f"{observed_order(
                    previous_field,
                    field_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{rate_error:11.4e} | "
            f"{rate_order_text:>8} | "
            f"{field_error:12.6e} | "
            f"{field_order_text:>8}"
        )

        previous_spacing = spacing
        previous_rate = rate_error
        previous_field = field_error

    rate_orders = [
        observed_order(
            rate_errors[index - 1],
            rate_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(spacings),
        )
    ]

    field_orders = [
        observed_order(
            field_errors[index - 1],
            field_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(spacings),
        )
    ]

    return rate_orders, field_orders


def validate_jerk_orders() -> None:
    midpoint_rate, midpoint_field = (
        run_jerk_study(
            "midpoint_time_velocity",
            (
                "=== JERK — POINT MILIEU "
                "HISTORIQUE ==="
            ),
        )
    )

    rk4_rate, rk4_field = (
        run_jerk_study(
            "rk4_backtrace",
            (
                "=== JERK — "
                "RÉTROTRAÇAGE RK4 ==="
            ),
        )
    )

    if not (
        MIDPOINT_RATE_ORDER_RANGE[0]
        <= midpoint_rate[-1]
        <= MIDPOINT_RATE_ORDER_RANGE[1]
    ):
        raise RuntimeError(
            "Le taux midpoint ne conserve pas "
            "l'ordre deux attendu."
        )

    if not (
        MIDPOINT_FIELD_ORDER_RANGE[0]
        <= midpoint_field[-1]
        <= MIDPOINT_FIELD_ORDER_RANGE[1]
    ):
        raise RuntimeError(
            "Le champ midpoint ne conserve pas "
            "l'ordre trois attendu."
        )

    if not (
        RK4_RATE_ORDER_RANGE[0]
        <= rk4_rate[-1]
        <= RK4_RATE_ORDER_RANGE[1]
    ):
        raise RuntimeError(
            "Le taux RK4 n'atteint pas "
            "l'ordre trois attendu."
        )

    if not (
        RK4_FIELD_ORDER_RANGE[0]
        <= rk4_field[-1]
        <= RK4_FIELD_ORDER_RANGE[1]
    ):
        raise RuntimeError(
            "Le champ RK4 n'atteint pas "
            "l'ordre quatre attendu."
        )

    print()
    print(
        "Point milieu : champ ordre 3 : VALIDÉ"
    )

    print(
        "Point milieu : taux ordre 2  : VALIDÉ"
    )

    print(
        "RK4 : champ ordre 4          : VALIDÉ"
    )

    print(
        "RK4 : taux ordre 3           : VALIDÉ"
    )


def validate_multiscale_forwarding() -> None:
    print()
    print(
        "=== TRANSMISSION MULTI-ÉCHELLE RK4 ==="
    )

    (
        _,
        x,
        y,
        spacing,
        times,
        cfg,
        velocity,
        transport,
    ) = make_periodic_case(
        grid_size=32,
        dt_over_h=0.31,
    )

    result = itd_v26.simulate_multiscale(
        "rk4_multiscale",
        velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=(
            0.25,
            0.5,
            1.0,
        ),
        curvature_function=(
            base.zero_curvature
        ),
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            transport
        ),
        transport_interpolation=(
            "cubic_periodic"
        ),
        transport_trajectory_method=(
            "rk4_backtrace"
        ),
    )

    metadata = result[
        "transport_compensation"
    ]

    print(
        "Méthode transmise :",
        metadata["backtrace"],
    )

    if (
        metadata["backtrace"]
        != "rk4_backtrace"
    ):
        raise RuntimeError(
            "La méthode RK4 n'est pas transmise "
            "au profil multi-échelle."
        )

    print(
        "Transmission multi-échelle : VALIDÉE"
    )


def validate_invalid_methods() -> None:
    print()
    print(
        "=== REJET DES MÉTHODES INVALIDES ==="
    )

    invalid_values = (
        "midpoint",
        "rk4",
        "",
        None,
        17,
    )

    for value in invalid_values:
        try:
            itd_v26.validate_transport_trajectory_method(
                value
            )
        except ValueError as error:
            print(
                f"{value!r}: RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Méthode invalide acceptée : "
                f"{value!r}."
            )

    print(
        "Rejet des méthodes invalides : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DU RÉTROTRAÇAGE RK4 "
        "— ITD V26 ==="
    )

    validate_api()
    validate_v25_compatibility()
    validate_constant_velocity_equivalence()
    validate_rk4_global_order()
    validate_jerk_orders()
    validate_multiscale_forwarding()
    validate_invalid_methods()

    print()
    print(
        "Compatibilité V25 → V26              : VALIDÉE"
    )

    print(
        "Défaut midpoint historique           : CONSERVÉ"
    )

    print(
        "RK4 global sur trajectoire spatiale   : ORDRE 4"
    )

    print(
        "Jerk midpoint : champ/taux            : ORDRES 3/2"
    )

    print(
        "Jerk RK4 : champ/taux                 : ORDRES 4/3"
    )

    print(
        "Transmission multi-échelle RK4        : VALIDÉE"
    )


if __name__ == "__main__":
    main()
