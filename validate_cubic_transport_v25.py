#!/usr/bin/env python3

from __future__ import annotations

import math

import numpy as np

import itd_v24
import itd_v25
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
INTERPOLATION_ORDER_MINIMUM = 3.80
CUBIC_RATE_ORDER_MINIMUM = 2.65
CUBIC_INCREMENT_ORDER_MINIMUM = 3.65
REFERENCE_GAMMA_ALPHA = math.pi
REFERENCE_GAMMA_GROWTH_RATE = (
    1.0
    / math.gamma(
        REFERENCE_GAMMA_ALPHA + 1.0
    )
)

JERK_RATE_ORDER_MINIMUM = 1.80
JERK_RATE_ORDER_MAXIMUM = 2.20
JERK_FIELD_ORDER_MINIMUM = 2.80
JERK_FIELD_ORDER_MAXIMUM = 3.20
MULTISCALE_TOLERANCE = 5.0e-13

DOMAIN_LENGTH = 2.0 * np.pi
AMPLITUDE = 0.75

GRID_SIZES = (
    32,
    64,
    128,
    256,
)

PHYSICAL_TRANSPORT = np.asarray(
    (
        0.82,
        -0.57,
    ),
    dtype=np.float64,
)

FRAME_VELOCITY = np.asarray(
    (
        0.413,
        -0.287,
    ),
    dtype=np.float64,
)


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def zero_curvature(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    del time

    return np.zeros_like(
        x + y,
        dtype=np.float64,
    )


def build_periodic_grid(
    grid_size: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
    coordinates = np.linspace(
        0.0,
        DOMAIN_LENGTH,
        grid_size,
        endpoint=False,
        dtype=np.float64,
    )

    spacing = (
        DOMAIN_LENGTH
        / grid_size
    )

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    return coordinates, x, y, spacing


def analytic_scalar(
    x: np.ndarray,
    y: np.ndarray,
) -> np.ndarray:
    return (
        np.sin(x)
        + 0.31 * np.cos(2.0 * y)
        + 0.17 * np.sin(x + y)
        - 0.09 * np.cos(2.0 * x - y)
    )


def make_translating_velocity(
    transport_x: float,
    transport_y: float,
    growth_rate: float = 0.0,
):
    def velocity(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        amplitude = (
            AMPLITUDE
            * np.exp(
                growth_rate * time
            )
        )

        phase_x = (
            x - transport_x * time
        )

        phase_y = (
            y - transport_y * time
        )

        rotational_vx = (
            amplitude
            * np.sin(phase_x)
            * np.cos(phase_y)
        )

        rotational_vy = (
            -amplitude
            * np.cos(phase_x)
            * np.sin(phase_y)
        )

        return (
            transport_x + rotational_vx,
            transport_y + rotational_vy,
        )

    return velocity


def make_constant_velocity(
    velocity_x: float,
    velocity_y: float,
):
    def velocity(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        del time

        return (
            np.full_like(
                x,
                velocity_x,
                dtype=np.float64,
            ),
            np.full_like(
                y,
                velocity_y,
                dtype=np.float64,
            ),
        )

    return velocity


def observed_order(
    previous_error: float,
    current_error: float,
    previous_step: float,
    current_step: float,
) -> float:
    return float(
        np.log(
            previous_error / current_error
        )
        / np.log(
            previous_step / current_step
        )
    )


def validate_v24_compatibility() -> None:
    cfg = Config(
        grid_size=49,
        domain_min=-2.0,
        domain_max=2.0,
        duration=2.0,
        time_steps=31,
        characteristic_length=0.5,
    )

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        dtype=np.float64,
    )

    spacing = float(
        coordinates[1]
        - coordinates[0]
    )

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    print(
        "=== COMPATIBILITÉ V24 → V25 ==="
    )

    reference = (
        itd_v24.extract_single_scale_diagnostics(
            itd_v24.simulate(
                "compatibilite_v24",
                multi_vortex_field,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=curvature_field,
                structural_length=0.5,
            )
        )
    )

    candidate = (
        itd_v25.extract_single_scale_diagnostics(
            itd_v25.simulate(
                "compatibilite_v25",
                multi_vortex_field,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=curvature_field,
                structural_length=0.5,
            )
        )
    )

    maximum_error = max(
        scaled_error(
            candidate[key],
            reference[key],
        )
        for key in reference
    )

    print(
        "Erreur maximale eulérienne :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V25 modifie les résultats "
            "historiques de la V24."
        )

    print(
        "Compatibilité V24 → V25 : VALIDÉE"
    )


def validate_bilinear_branch_compatibility() -> None:
    grid_size = 48

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    times = np.linspace(
        0.0,
        0.8,
        7,
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=0.8,
        time_steps=times.size,
        characteristic_length=0.5,
    )

    velocity = make_translating_velocity(
        PHYSICAL_TRANSPORT[0],
        PHYSICAL_TRANSPORT[1],
        growth_rate=0.11,
    )

    transport = make_constant_velocity(
        PHYSICAL_TRANSPORT[0],
        PHYSICAL_TRANSPORT[1],
    )

    reference = itd_v24.simulate(
        "bilineaire_v24",
        velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=transport,
    )

    candidate = itd_v25.simulate(
        "bilineaire_v25",
        velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=transport,
        transport_interpolation=(
            "bilinear_periodic"
        ),
    )

    interval_exact = np.array_equal(
        np.asarray(
            reference[
                "temporal_deformation_compensated_interval"
            ]
        ),
        np.asarray(
            candidate[
                "temporal_deformation_compensated_interval"
            ]
        ),
    )

    scalar_exact = all(
        reference[key] == candidate[key]
        for key in (
            "intensity_index",
            "structure_index",
            "coupled_index",
            "temporal_deformation_compensated_index",
        )
    )

    print()
    print(
        "=== COMPATIBILITÉ DE LA BRANCHE BILINÉAIRE ==="
    )

    print(
        "Intervalles bit à bit :",
        interval_exact,
    )

    print(
        "Indices bit à bit     :",
        scalar_exact,
    )

    if not (
        interval_exact
        and scalar_exact
    ):
        raise RuntimeError(
            "La branche bilinéaire V25 diffère "
            "de la branche historique V24."
        )

    if (
        candidate[
            "transport_compensation"
        ]["interpolation"]
        != "bilinear_periodic"
    ):
        raise RuntimeError(
            "La métadonnée bilinéaire est incorrecte."
        )

    print(
        "Branche bilinéaire historique : VALIDÉE"
    )


def validate_exact_node_transport() -> None:
    grid_size = 32

    coordinates, _, _, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    rng = np.random.default_rng(
        20260714
    )

    field = rng.normal(
        size=(
            grid_size,
            grid_size,
        )
    )

    delta_time = 0.20

    shift_x = 3
    shift_y = -2

    transport_vx = np.full_like(
        field,
        shift_x
        * spacing
        / delta_time,
    )

    transport_vy = np.full_like(
        field,
        shift_y
        * spacing
        / delta_time,
    )

    expected = np.roll(
        np.roll(
            field,
            shift=shift_x,
            axis=1,
        ),
        shift=shift_y,
        axis=0,
    )

    bilinear = itd_v25.periodic_backtrace(
        field,
        coordinates,
        coordinates,
        transport_vx,
        transport_vy,
        delta_time,
        interpolation="bilinear_periodic",
    )

    cubic = itd_v25.periodic_backtrace(
        field,
        coordinates,
        coordinates,
        transport_vx,
        transport_vy,
        delta_time,
        interpolation="cubic_periodic",
    )

    bilinear_exact = np.array_equal(
        bilinear,
        expected,
    )

    cubic_exact = np.array_equal(
        cubic,
        expected,
    )

    print()
    print(
        "=== TRANSPORT NODAL EXACT ==="
    )

    print(
        "Bilinéaire exact :",
        bilinear_exact,
    )

    print(
        "Cubique exact    :",
        cubic_exact,
    )

    if not (
        bilinear_exact
        and cubic_exact
    ):
        raise RuntimeError(
            "Un déplacement nodal n'est pas "
            "une permutation exacte."
        )

    print(
        "Permutation périodique exacte : VALIDÉE"
    )


def validate_interpolation_orders() -> None:
    shift_x_cells = 0.37
    shift_y_cells = -0.41

    bilinear_errors = []
    cubic_errors = []
    spacings = []

    print()
    print(
        "=== ORDRE DE L'INTERPOLATION PÉRIODIQUE ==="
    )

    print(
        "grille | erreur bilinéaire | ordre | "
        "erreur cubique | ordre"
    )

    previous_bilinear = None
    previous_cubic = None
    previous_spacing = None

    for grid_size in GRID_SIZES:
        coordinates, x, y, spacing = (
            build_periodic_grid(
                grid_size
            )
        )

        field = analytic_scalar(
            x,
            y,
        )

        delta_time = 1.0

        transport_vx = np.full_like(
            field,
            shift_x_cells
            * spacing,
        )

        transport_vy = np.full_like(
            field,
            shift_y_cells
            * spacing,
        )

        expected = analytic_scalar(
            x
            - shift_x_cells
            * spacing,
            y
            - shift_y_cells
            * spacing,
        )

        bilinear = (
            itd_v25.periodic_bilinear_backtrace(
                field,
                coordinates,
                coordinates,
                transport_vx,
                transport_vy,
                delta_time,
            )
        )

        cubic = (
            itd_v25.periodic_cubic_backtrace(
                field,
                coordinates,
                coordinates,
                transport_vx,
                transport_vy,
                delta_time,
            )
        )

        bilinear_error = float(
            np.max(
                np.abs(
                    bilinear - expected
                )
            )
        )

        cubic_error = float(
            np.max(
                np.abs(
                    cubic - expected
                )
            )
        )

        bilinear_errors.append(
            bilinear_error
        )

        cubic_errors.append(
            cubic_error
        )

        spacings.append(spacing)

        if previous_bilinear is None:
            bilinear_order_text = "—"
            cubic_order_text = "—"
        else:
            bilinear_order_text = (
                f"{observed_order(
                    previous_bilinear,
                    bilinear_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

            cubic_order_text = (
                f"{observed_order(
                    previous_cubic,
                    cubic_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{bilinear_error:17.6e} | "
            f"{bilinear_order_text:>8} | "
            f"{cubic_error:13.6e} | "
            f"{cubic_order_text:>8}"
        )

        previous_bilinear = bilinear_error
        previous_cubic = cubic_error
        previous_spacing = spacing

    cubic_orders = [
        observed_order(
            cubic_errors[index - 1],
            cubic_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(cubic_errors),
        )
    ]

    if min(
        cubic_orders[-2:]
    ) < INTERPOLATION_ORDER_MINIMUM:
        raise RuntimeError(
            "L'interpolation cubique n'atteint "
            "pas l'ordre quatre attendu."
        )

    print(
        "Interpolation cubique d'ordre quatre : "
        "VALIDÉE"
    )


def make_jerk_frame():
    initial_velocity = np.asarray(
        (
            0.413,
            -0.287,
        ),
        dtype=np.float64,
    )

    acceleration = np.asarray(
        (
            0.271,
            -0.183,
        ),
        dtype=np.float64,
    )

    jerk = np.asarray(
        (
            12.0,
            -9.0,
        ),
        dtype=np.float64,
    )

    def displacement(
        time: float,
    ) -> np.ndarray:
        return (
            initial_velocity * time
            + 0.5
            * acceleration
            * time**2
            + (
                jerk
                * time**3
                / 6.0
            )
        )

    def velocity(
        time: float,
    ) -> np.ndarray:
        return (
            initial_velocity
            + acceleration * time
            + 0.5 * jerk * time**2
        )

    return displacement, velocity


def compute_objectivity_defect(
    grid_size: int,
    dt_over_h: float,
    interpolation: str,
    frame_kind: str,
) -> tuple[
    float,
    float,
    float,
]:
    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
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

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=delta_time,
        time_steps=2,
        characteristic_length=0.5,
    )

    original_velocity = (
        make_translating_velocity(
            PHYSICAL_TRANSPORT[0],
            PHYSICAL_TRANSPORT[1],
            growth_rate=REFERENCE_GAMMA_GROWTH_RATE,
        )
    )

    original_transport = (
        make_constant_velocity(
            PHYSICAL_TRANSPORT[0],
            PHYSICAL_TRANSPORT[1],
        )
    )

    if frame_kind == "galilean":
        transformed_velocity = (
            itd_v25.galilean_transform_velocity_function(
                original_velocity,
                FRAME_VELOCITY,
            )
        )

        transformed_transport = (
            itd_v25.galilean_transform_velocity_function(
                original_transport,
                FRAME_VELOCITY,
            )
        )
    elif frame_kind == "jerk":
        displacement, frame_velocity = (
            make_jerk_frame()
        )

        transformed_velocity = (
            itd_v25.translating_frame_transform_velocity_function(
                original_velocity,
                displacement,
                frame_velocity,
            )
        )

        transformed_transport = (
            itd_v25.translating_frame_transform_velocity_function(
                original_transport,
                displacement,
                frame_velocity,
            )
        )
    else:
        raise ValueError(
            f"Référentiel inconnu : {frame_kind}."
        )

    original = itd_v25.simulate(
        f"original_{frame_kind}_{grid_size}",
        original_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            original_transport
        ),
        transport_interpolation=interpolation,
    )

    transformed = itd_v25.simulate(
        f"transformed_{frame_kind}_{grid_size}",
        transformed_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            transformed_transport
        ),
        transport_interpolation=interpolation,
    )

    original_intervals = np.asarray(
        original[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    transformed_intervals = np.asarray(
        transformed[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    rate_defect = max(
        float(
            np.max(
                np.abs(
                    transformed_intervals
                    - original_intervals
                )
            )
        ),
        abs(
            float(
                transformed[
                    "temporal_deformation_compensated_index"
                ]
            )
            - float(
                original[
                    "temporal_deformation_compensated_index"
                ]
            )
        ),
    )

    increment_defect = (
        delta_time * rate_defect
    )

    return (
        spacing,
        rate_defect,
        increment_defect,
    )


def run_objectivity_study(
    title: str,
    interpolation: str,
    frame_kind: str,
    dt_over_h: float,
) -> tuple[
    list[float],
    list[float],
]:
    rate_errors = []
    increment_errors = []
    spacings = []

    print()
    print(title)

    print(
        "grille | défaut taux | ordre | "
        "défaut incrément | ordre"
    )

    previous_rate = None
    previous_increment = None
    previous_spacing = None

    for grid_size in GRID_SIZES:
        (
            spacing,
            rate_error,
            increment_error,
        ) = compute_objectivity_defect(
            grid_size,
            dt_over_h,
            interpolation,
            frame_kind,
        )

        rate_errors.append(
            rate_error
        )

        increment_errors.append(
            increment_error
        )

        spacings.append(spacing)

        if previous_rate is None:
            rate_order_text = "—"
            increment_order_text = "—"
        else:
            rate_order_text = (
                f"{observed_order(
                    previous_rate,
                    rate_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

            increment_order_text = (
                f"{observed_order(
                    previous_increment,
                    increment_error,
                    previous_spacing,
                    spacing,
                ):.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{rate_error:11.4e} | "
            f"{rate_order_text:>8} | "
            f"{increment_error:16.6e} | "
            f"{increment_order_text:>8}"
        )

        previous_rate = rate_error
        previous_increment = increment_error
        previous_spacing = spacing

    rate_orders = [
        observed_order(
            rate_errors[index - 1],
            rate_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(rate_errors),
        )
    ]

    increment_orders = [
        observed_order(
            increment_errors[index - 1],
            increment_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(increment_errors),
        )
    ]

    return rate_orders, increment_orders


def compute_jerk_trajectory_defect(
    grid_size: int,
    dt_over_h: float,
) -> tuple[
    float,
    float,
    float,
]:
    """
    Mesure directement l'erreur de rétrotrajectoire
    produite par la vitesse au point milieu.

    Pour une trajectoire cubique b(t), l'erreur de
    déplacement est O(delta_t^3). Le défaut du champ
    doit donc être d'ordre trois lorsque delta_t est
    proportionnel à h, et le défaut du taux obtenu
    après division par delta_t doit être d'ordre deux.

    Cette comparaison porte sur le champ transporté,
    et non sur la différence de deux normes L2 pouvant
    masquer le terme dominant par orthogonalité.
    """
    coordinates, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    delta_time = (
        dt_over_h * spacing
    )

    previous_field = analytic_scalar(
        x,
        y,
    )

    displacement, frame_velocity = (
        make_jerk_frame()
    )

    previous_displacement = np.asarray(
        displacement(0.0),
        dtype=np.float64,
    )

    current_displacement = np.asarray(
        displacement(delta_time),
        dtype=np.float64,
    )

    midpoint_velocity = np.asarray(
        frame_velocity(
            0.5 * delta_time
        ),
        dtype=np.float64,
    )

    transformed_transport = (
        PHYSICAL_TRANSPORT
        - midpoint_velocity
    )

    transport_vx = np.full_like(
        previous_field,
        transformed_transport[0],
        dtype=np.float64,
    )

    transport_vy = np.full_like(
        previous_field,
        transformed_transport[1],
        dtype=np.float64,
    )

    numerical = (
        itd_v25.periodic_cubic_backtrace(
            previous_field,
            coordinates,
            coordinates,
            transport_vx,
            transport_vy,
            delta_time,
        )
    )

    # Coordonnée exacte, dans le référentiel mobile,
    # du point source au début de l'intervalle :
    #
    # x'_0 = x'_1 - u * dt + b(t_1) - b(t_0).
    exact_source_x = (
        x
        - PHYSICAL_TRANSPORT[0]
        * delta_time
        + current_displacement[0]
        - previous_displacement[0]
    )

    exact_source_y = (
        y
        - PHYSICAL_TRANSPORT[1]
        * delta_time
        + current_displacement[1]
        - previous_displacement[1]
    )

    exact = analytic_scalar(
        exact_source_x,
        exact_source_y,
    )

    field_defect = float(
        np.max(
            np.abs(
                numerical - exact
            )
        )
    )

    rate_defect = (
        field_defect
        / delta_time
    )

    return (
        spacing,
        rate_defect,
        field_defect,
    )


def run_jerk_trajectory_study(
    dt_over_h: float,
) -> tuple[
    list[float],
    list[float],
]:
    rate_errors: list[float] = []
    field_errors: list[float] = []
    spacings: list[float] = []

    print()
    print(
        "=== CUBIQUE — ORACLE DIRECT DE "
        "RÉTROTRAJECTOIRE À JERK ==="
    )

    print(
        "grille | défaut taux | ordre | "
        "défaut champ | ordre"
    )

    previous_rate = None
    previous_field = None
    previous_spacing = None

    for grid_size in GRID_SIZES:
        (
            spacing,
            rate_error,
            field_error,
        ) = compute_jerk_trajectory_defect(
            grid_size,
            dt_over_h,
        )

        rate_errors.append(
            rate_error
        )

        field_errors.append(
            field_error
        )

        spacings.append(
            spacing
        )

        if previous_rate is None:
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

        previous_rate = rate_error
        previous_field = field_error
        previous_spacing = spacing

    rate_orders = [
        observed_order(
            rate_errors[index - 1],
            rate_errors[index],
            spacings[index - 1],
            spacings[index],
        )
        for index in range(
            1,
            len(rate_errors),
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
            len(field_errors),
        )
    ]

    return (
        rate_orders,
        field_orders,
    )


def validate_rate_orders() -> None:
    bilinear_rate, _ = run_objectivity_study(
        "=== CONTRÔLE BILINÉAIRE GALILÉEN ===",
        "bilinear_periodic",
        "galilean",
        0.47,
    )

    cubic_rate_031, cubic_increment_031 = (
        run_objectivity_study(
            "=== CUBIQUE GALILÉEN — Δt/h=0.31 ===",
            "cubic_periodic",
            "galilean",
            0.31,
        )
    )

    cubic_rate_073, cubic_increment_073 = (
        run_objectivity_study(
            "=== CUBIQUE GALILÉEN — Δt/h=0.73 ===",
            "cubic_periodic",
            "galilean",
            0.73,
        )
    )

    jerk_rate, jerk_field = (
        run_jerk_trajectory_study(
            0.47
        )
    )

    if not (
        0.90
        <= bilinear_rate[-1]
        <= 1.10
    ):
        raise RuntimeError(
            "Le contrôle bilinéaire ne retrouve "
            "pas l'ordre un certifié en V24."
        )

    for orders in (
        cubic_rate_031,
        cubic_rate_073,
    ):
        if min(
            orders[-2:]
        ) < CUBIC_RATE_ORDER_MINIMUM:
            raise RuntimeError(
                "Le taux cubique galiléen n'atteint "
                "pas l'ordre trois attendu."
            )

    for orders in (
        cubic_increment_031,
        cubic_increment_073,
    ):
        if min(
            orders[-2:]
        ) < CUBIC_INCREMENT_ORDER_MINIMUM:
            raise RuntimeError(
                "L'incrément cubique n'atteint pas "
                "l'ordre quatre attendu."
            )

    if not (
        JERK_RATE_ORDER_MINIMUM
        <= jerk_rate[-1]
        <= JERK_RATE_ORDER_MAXIMUM
    ):
        raise RuntimeError(
            "Le défaut de taux du rétrotraçage à "
            "jerk n'atteint pas l'ordre deux."
        )

    if not (
        JERK_FIELD_ORDER_MINIMUM
        <= jerk_field[-1]
        <= JERK_FIELD_ORDER_MAXIMUM
    ):
        raise RuntimeError(
            "Le défaut de champ du rétrotraçage à "
            "jerk n'atteint pas l'ordre trois."
        )

    print()
    print(
        "Bilinéaire : taux d'ordre un       : VALIDÉ"
    )

    print(
        "Cubique : incrément d'ordre quatre : VALIDÉ"
    )

    print(
        "Cubique : taux d'ordre trois       : VALIDÉ"
    )

    print(
        "Jerk : défaut du champ ordre trois : VALIDÉ"
    )

    print(
        "Jerk : défaut du taux ordre deux   : VALIDÉ"
    )


def validate_multiscale_cubic() -> None:
    grid_size = 48

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    times = np.linspace(
        0.0,
        0.75,
        7,
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=0.75,
        time_steps=times.size,
        characteristic_length=0.5,
    )

    velocity = make_translating_velocity(
        PHYSICAL_TRANSPORT[0],
        PHYSICAL_TRANSPORT[1],
        growth_rate=0.12,
    )

    transport = make_constant_velocity(
        PHYSICAL_TRANSPORT[0],
        PHYSICAL_TRANSPORT[1],
    )

    lengths = np.asarray(
        (
            0.0,
            0.5,
            1.0,
        ),
        dtype=np.float64,
    )

    profile = itd_v25.simulate_multiscale(
        "profil_cubique",
        velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=lengths,
        curvature_function=zero_curvature,
        boundary_mode="periodic",
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=transport,
        transport_interpolation=(
            "cubic_periodic"
        ),
    )

    signatures = np.asarray(
        profile[
            "structural_signatures"
        ],
        dtype=np.float64,
    )

    structures = np.asarray(
        profile[
            "structure_indices"
        ],
        dtype=np.float64,
    )

    coupled = np.asarray(
        profile[
            "coupled_indices"
        ],
        dtype=np.float64,
    )

    maximum_error = 0.0

    for index, length in enumerate(
        lengths
    ):
        direct = itd_v25.simulate(
            f"direct_cubique_{length:g}",
            velocity,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
            structural_length=float(length),
            boundary_mode="periodic",
            temporal_deformation_mode=(
                "transport_compensated"
            ),
            transport_velocity_function=transport,
            transport_interpolation=(
                "cubic_periodic"
            ),
        )

        components = dict(
            direct[
                "component_indices"
            ]
        )

        direct_signature = np.asarray(
            tuple(
                float(
                    components[name]
                )
                for name in (
                    itd_v25.STRUCTURAL_COMPONENT_NAMES
                )
            ),
            dtype=np.float64,
        )

        maximum_error = max(
            maximum_error,
            float(
                np.max(
                    np.abs(
                        signatures[index]
                        - direct_signature
                    )
                )
            ),
            abs(
                structures[index]
                - float(
                    direct[
                        "structure_index"
                    ]
                )
            ),
            abs(
                coupled[index]
                - float(
                    direct[
                        "coupled_index"
                    ]
                )
            ),
        )

    print()
    print(
        "=== PROFIL MULTI-ÉCHELLE CUBIQUE ==="
    )

    print(
        "Erreur maximale profil/direct :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > MULTISCALE_TOLERANCE:
        raise RuntimeError(
            "Le profil multi-échelle cubique "
            "diffère des simulations directes."
        )

    if (
        profile[
            "transport_compensation"
        ]["interpolation"]
        != "cubic_periodic"
    ):
        raise RuntimeError(
            "La métadonnée multi-échelle cubique "
            "est incorrecte."
        )

    print(
        "Profil multi-échelle cubique : VALIDÉ"
    )


def validate_invalid_interpolations() -> None:
    print()
    print(
        "=== REJET DES INTERPOLATIONS INVALIDES ==="
    )

    for invalid in (
        "nearest",
        "cubic",
        "",
        None,
        17,
    ):
        try:
            itd_v25.validate_transport_interpolation(
                invalid
            )
        except ValueError as error:
            print(
                f"Mode {invalid!r}: RÉUSSI —",
                error,
            )
        else:
            raise RuntimeError(
                "Une interpolation invalide "
                "n'a pas été rejetée."
            )

    coordinates = np.asarray(
        (
            0.0,
            1.0,
            2.0,
        ),
        dtype=np.float64,
    )

    field = np.zeros(
        (
            3,
            3,
        ),
        dtype=np.float64,
    )

    try:
        itd_v25.periodic_cubic_backtrace(
            field,
            coordinates,
            coordinates,
            field,
            field,
            0.1,
        )
    except ValueError as error:
        print(
            "Grille trop petite : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Une grille cubique trop petite "
            "a été acceptée."
        )

    print(
        "Contrôle des interpolations V25 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DU TRANSPORT CUBIQUE "
        "PÉRIODIQUE — ITD V25 ==="
    )

    validate_v24_compatibility()
    validate_bilinear_branch_compatibility()
    validate_exact_node_transport()
    validate_interpolation_orders()
    validate_rate_orders()
    validate_multiscale_cubic()
    validate_invalid_interpolations()

    print()
    print(
        "Compatibilité V24 → V25                 : VALIDÉE"
    )
    print(
        "Branche bilinéaire historique           : CONSERVÉE"
    )
    print(
        "Déplacements nodaux exacts              : VALIDÉS"
    )
    print(
        "Interpolation cubique spatiale ordre 4  : VALIDÉE"
    )
    print(
        "Incrément cubique transporté ordre 4    : VALIDÉ"
    )
    print(
        "Taux cubique galiléen ordre 3           : VALIDÉ"
    )
    print(
        "Jerk : défaut du champ ordre 3          : VALIDÉ"
    )
    print(
        "Jerk : défaut du taux ordre 2           : VALIDÉ"
    )
    print(
        "Profil multi-échelle cubique            : VALIDÉ"
    )


if __name__ == "__main__":
    main()
