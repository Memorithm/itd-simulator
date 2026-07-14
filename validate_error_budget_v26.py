#!/usr/bin/env python3

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

import itd_v26
import validate_cubic_transport_v25 as base


GRID_SIZES = (
    32,
    64,
    128,
    256,
)

DT_OVER_H = 0.47

INTERPOLATION_ORDER_RANGE = (
    3.75,
    4.25,
)

MIDPOINT_DISPLACEMENT_ORDER_RANGE = (
    2.75,
    3.25,
)

RK4_LOCAL_DISPLACEMENT_ORDER_RANGE = (
    4.70,
    5.30,
)

COMBINED_FIELD_ORDER_RANGE = (
    3.70,
    4.30,
)

COMBINED_RATE_ORDER_RANGE = (
    2.70,
    3.30,
)

OUTPUT_PATH = Path(
    "itd_v26_results"
    "/error_budget_v26.txt"
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


def sequence_orders(
    errors: list[float],
    steps: list[float],
) -> list[float]:
    return [
        observed_order(
            errors[index - 1],
            errors[index],
            steps[index - 1],
            steps[index],
        )
        for index in range(
            1,
            len(errors),
        )
    ]


def exact_periodic_interpolation_defect(
    grid_size: int,
) -> tuple[float, float]:
    (
        coordinates,
        x,
        y,
        spacing,
    ) = base.build_periodic_grid(
        grid_size
    )

    displacement_x = (
        0.371 * spacing
    )

    displacement_y = (
        -0.283 * spacing
    )

    previous_field = base.analytic_scalar(
        x,
        y,
    )

    # delta_time=1 permet d'utiliser directement
    # le déplacement comme vitesse effective.
    numerical = (
        itd_v26.periodic_cubic_backtrace(
            previous_field,
            coordinates,
            coordinates,
            np.full_like(
                previous_field,
                displacement_x,
            ),
            np.full_like(
                previous_field,
                displacement_y,
            ),
            1.0,
        )
    )

    exact = base.analytic_scalar(
        x - displacement_x,
        y - displacement_y,
    )

    error = float(
        np.max(
            np.abs(
                numerical - exact
            )
        )
    )

    return spacing, error


def midpoint_jerk_displacement_defect(
    delta_time: float,
) -> float:
    displacement, velocity = (
        base.make_jerk_frame()
    )

    exact = (
        np.asarray(
            displacement(delta_time),
            dtype=np.float64,
        )
        - np.asarray(
            displacement(0.0),
            dtype=np.float64,
        )
    )

    midpoint = (
        delta_time
        * np.asarray(
            velocity(
                0.5 * delta_time
            ),
            dtype=np.float64,
        )
    )

    return float(
        np.max(
            np.abs(
                midpoint - exact
            )
        )
    )


def make_quartic_time_velocity():
    constant = np.asarray(
        (
            0.31,
            -0.23,
        ),
        dtype=np.float64,
    )

    linear = np.asarray(
        (
            0.17,
            0.11,
        ),
        dtype=np.float64,
    )

    quadratic = np.asarray(
        (
            -0.09,
            0.07,
        ),
        dtype=np.float64,
    )

    cubic = np.asarray(
        (
            0.05,
            -0.04,
        ),
        dtype=np.float64,
    )

    quartic = np.asarray(
        (
            1.30,
            -0.90,
        ),
        dtype=np.float64,
    )

    def velocity(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ):
        value = (
            constant
            + linear * time
            + quadratic * time**2
            + cubic * time**3
            + quartic * time**4
        )

        return (
            np.full_like(
                x,
                value[0],
                dtype=np.float64,
            ),
            np.full_like(
                y,
                value[1],
                dtype=np.float64,
            ),
        )

    def exact_integral(
        previous_time: float,
        current_time: float,
    ) -> np.ndarray:
        def primitive(
            time: float,
        ) -> np.ndarray:
            return (
                constant * time
                + linear * time**2 / 2.0
                + quadratic * time**3 / 3.0
                + cubic * time**4 / 4.0
                + quartic * time**5 / 5.0
            )

        return (
            primitive(current_time)
            - primitive(previous_time)
        )

    return velocity, exact_integral


def rk4_local_displacement_defect(
    delta_time: float,
) -> float:
    coordinates = np.linspace(
        -4.0,
        4.0,
        64,
        endpoint=False,
        dtype=np.float64,
    )

    current_x = np.asarray(
        (
            (0.4, 0.7),
            (1.1, 1.4),
        ),
        dtype=np.float64,
    )

    current_y = np.asarray(
        (
            (-0.8, -0.5),
            (-0.2, 0.1),
        ),
        dtype=np.float64,
    )

    velocity, exact_integral = (
        make_quartic_time_velocity()
    )

    numerical_x, numerical_y = (
        itd_v26.rk4_periodic_departure_points(
            current_x,
            current_y,
            coordinates,
            coordinates,
            0.0,
            delta_time,
            velocity,
        )
    )

    exact_displacement = (
        exact_integral(
            0.0,
            delta_time,
        )
    )

    exact_x = (
        current_x
        - exact_displacement[0]
    )

    exact_y = (
        current_y
        - exact_displacement[1]
    )

    return float(
        max(
            np.max(
                np.abs(
                    numerical_x - exact_x
                )
            ),
            np.max(
                np.abs(
                    numerical_y - exact_y
                )
            ),
        )
    )


def combined_rk4_field_defect(
    grid_size: int,
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
        DT_OVER_H * spacing
    )

    previous_field = base.analytic_scalar(
        x,
        y,
    )

    velocity, exact_integral = (
        make_quartic_time_velocity()
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
            velocity,
            transport_interpolation=(
                "cubic_periodic"
            ),
            transport_trajectory_method=(
                "rk4_backtrace"
            ),
        )
    )

    exact_displacement = (
        exact_integral(
            0.0,
            delta_time,
        )
    )

    exact = base.analytic_scalar(
        x - exact_displacement[0],
        y - exact_displacement[1],
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
        field_error,
        rate_error,
    )


def print_sequence(
    title: str,
    label: str,
    steps: list[float],
    errors: list[float],
) -> list[float]:
    orders = sequence_orders(
        errors,
        steps,
    )

    print()
    print(title)

    print(
        f"niveau | pas | {label} | ordre"
    )

    for index, (
        step,
        error,
    ) in enumerate(
        zip(
            steps,
            errors,
        )
    ):
        order_text = (
            "—"
            if index == 0
            else f"{orders[index - 1]:.6f}"
        )

        print(
            f"{index:6d} | "
            f"{step:.6e} | "
            f"{error:.6e} | "
            f"{order_text:>8}"
        )

    return orders


def main() -> None:
    print(
        "=== BUDGET D'ERREUR SÉPARÉ "
        "— ITD V26.1 ==="
    )

    interpolation_steps: list[float] = []
    interpolation_errors: list[float] = []

    for grid_size in GRID_SIZES:
        step, error = (
            exact_periodic_interpolation_defect(
                grid_size
            )
        )

        interpolation_steps.append(step)
        interpolation_errors.append(error)

    interpolation_orders = print_sequence(
        (
            "=== INTERPOLATION CUBIQUE "
            "SEULE ==="
        ),
        "erreur champ",
        interpolation_steps,
        interpolation_errors,
    )

    temporal_steps = [
        0.20,
        0.10,
        0.05,
        0.025,
    ]

    midpoint_errors = [
        midpoint_jerk_displacement_defect(
            step
        )
        for step in temporal_steps
    ]

    midpoint_orders = print_sequence(
        (
            "=== TRAJECTOIRE POINT MILIEU "
            "SEULE ==="
        ),
        "erreur déplacement",
        temporal_steps,
        midpoint_errors,
    )

    rk4_errors = [
        rk4_local_displacement_defect(
            step
        )
        for step in temporal_steps
    ]

    rk4_orders = print_sequence(
        (
            "=== TRAJECTOIRE RK4 "
            "SEULE ==="
        ),
        "erreur déplacement",
        temporal_steps,
        rk4_errors,
    )

    combined_steps: list[float] = []
    combined_field_errors: list[float] = []
    combined_rate_errors: list[float] = []

    for grid_size in GRID_SIZES:
        (
            step,
            field_error,
            rate_error,
        ) = combined_rk4_field_defect(
            grid_size
        )

        combined_steps.append(step)
        combined_field_errors.append(
            field_error
        )

        combined_rate_errors.append(
            rate_error
        )

    combined_field_orders = print_sequence(
        (
            "=== ERREUR COMBINÉE "
            "RK4 + CUBIQUE : CHAMP ==="
        ),
        "erreur champ",
        combined_steps,
        combined_field_errors,
    )

    combined_rate_orders = print_sequence(
        (
            "=== ERREUR COMBINÉE "
            "RK4 + CUBIQUE : TAUX ==="
        ),
        "erreur taux",
        combined_steps,
        combined_rate_errors,
    )

    checks = {
        "interpolation_cubic_order_four": (
            INTERPOLATION_ORDER_RANGE[0]
            <= interpolation_orders[-1]
            <= INTERPOLATION_ORDER_RANGE[1]
        ),
        "midpoint_displacement_order_three": (
            MIDPOINT_DISPLACEMENT_ORDER_RANGE[0]
            <= midpoint_orders[-1]
            <= MIDPOINT_DISPLACEMENT_ORDER_RANGE[1]
        ),
        "rk4_local_displacement_order_five": (
            RK4_LOCAL_DISPLACEMENT_ORDER_RANGE[0]
            <= rk4_orders[-1]
            <= RK4_LOCAL_DISPLACEMENT_ORDER_RANGE[1]
        ),
        "combined_field_order_four": (
            COMBINED_FIELD_ORDER_RANGE[0]
            <= combined_field_orders[-1]
            <= COMBINED_FIELD_ORDER_RANGE[1]
        ),
        "combined_rate_order_three": (
            COMBINED_RATE_ORDER_RANGE[0]
            <= combined_rate_orders[-1]
            <= COMBINED_RATE_ORDER_RANGE[1]
        ),
    }

    print()
    print(
        "=== CONCLUSION V26.1 ==="
    )

    for name, result in checks.items():
        print(
            f"{name:42s}: {result}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n".join(
            (
                "ITD V26.1 error budget",
                "",
                (
                    "Interpolation final order: "
                    f"{interpolation_orders[-1]:.12f}"
                ),
                (
                    "Midpoint displacement final order: "
                    f"{midpoint_orders[-1]:.12f}"
                ),
                (
                    "RK4 local displacement final order: "
                    f"{rk4_orders[-1]:.12f}"
                ),
                (
                    "Combined field final order: "
                    f"{combined_field_orders[-1]:.12f}"
                ),
                (
                    "Combined rate final order: "
                    f"{combined_rate_orders[-1]:.12f}"
                ),
                "",
                f"Success: {all(checks.values())}",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Rapport :",
        OUTPUT_PATH.resolve(),
    )

    if not all(
        checks.values()
    ):
        raise RuntimeError(
            "Le budget d'erreur séparé V26.1 "
            "n'est pas validé."
        )


if __name__ == "__main__":
    main()
