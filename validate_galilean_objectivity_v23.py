#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v22
import itd_v23
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
POINTWISE_TOLERANCE = 8.0e-12
COMPOSITION_TOLERANCE = 2.0e-13
OBJECTIVITY_TOLERANCE = 2.0e-11
METHOD_ORACLE_TOLERANCE = 3.0e-11

DOMAIN_LENGTH = 2.0 * np.pi
AMPLITUDE = 0.75


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


def periodic_scalar(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    return (
        np.sin(
            x - 0.30 * time
        )
        + 0.40
        * np.cos(
            2.0 * y
            + 0.20 * time
        )
        + 0.15
        * np.sin(
            x + y
        )
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


def make_cellular_velocity(
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


def validate_v22_compatibility() -> None:
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
        "=== COMPATIBILITÉ V22 → V23 ==="
    )

    reference = (
        itd_v22.extract_single_scale_diagnostics(
            itd_v22.simulate(
                "compatibilite_v22",
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
        itd_v23.extract_single_scale_diagnostics(
            itd_v23.simulate(
                "compatibilite_v23",
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
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V23 modifie les résultats "
            "historiques de la V22."
        )

    print(
        "Compatibilité V22 → V23 : VALIDÉE"
    )


def validate_pointwise_galilean_laws() -> None:
    grid_size = 96

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    transport = (
        0.80,
        -0.55,
    )

    frame_velocity = (
        0.27,
        -0.19,
    )

    reference_time = 0.15
    time = 0.83

    velocity = make_cellular_velocity(
        transport[0],
        transport[1],
        growth_rate=0.11,
    )

    transformed_velocity = (
        itd_v23.galilean_transform_velocity_function(
            velocity,
            frame_velocity,
            reference_time=reference_time,
        )
    )

    source_x, source_y = (
        itd_v23.galilean_source_coordinates(
            x,
            y,
            time,
            frame_velocity,
            reference_time=reference_time,
        )
    )

    source_vx, source_vy = velocity(
        source_x,
        source_y,
        time,
    )

    transformed_vx, transformed_vy = (
        transformed_velocity(
            x,
            y,
            time,
        )
    )

    vector_error = max(
        float(
            np.max(
                np.abs(
                    transformed_vx
                    - (
                        source_vx
                        - frame_velocity[0]
                    )
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    transformed_vy
                    - (
                        source_vy
                        - frame_velocity[1]
                    )
                )
            )
        ),
    )

    source_omega = (
        itd_v23.numerical_vorticity_with_boundary(
            source_vx,
            source_vy,
            spacing,
            boundary_mode="periodic",
        )
    )

    transformed_omega = (
        itd_v23.numerical_vorticity_with_boundary(
            transformed_vx,
            transformed_vy,
            spacing,
            boundary_mode="periodic",
        )
    )

    vorticity_error = float(
        np.max(
            np.abs(
                transformed_omega
                - source_omega
            )
        )
    )

    transformed_scalar = (
        itd_v23.galilean_transform_scalar_function(
            periodic_scalar,
            frame_velocity,
            reference_time=reference_time,
        )
    )

    scalar_error = float(
        np.max(
            np.abs(
                transformed_scalar(
                    x,
                    y,
                    time,
                )
                - periodic_scalar(
                    source_x,
                    source_y,
                    time,
                )
            )
        )
    )

    print()
    print(
        "=== LOIS GALILÉENNES POINT À POINT ==="
    )

    print(
        "Erreur du champ vectoriel :",
        f"{vector_error:.6e}",
    )

    print(
        "Erreur de la vorticité    :",
        f"{vorticity_error:.6e}",
    )

    print(
        "Erreur du champ scalaire  :",
        f"{scalar_error:.6e}",
    )

    if vector_error > POINTWISE_TOLERANCE:
        raise RuntimeError(
            "La transformation du champ de vitesse "
            "est incorrecte."
        )

    if vorticity_error > POINTWISE_TOLERANCE:
        raise RuntimeError(
            "La vorticité n'est pas un scalaire "
            "galiléen numérique."
        )

    if scalar_error > POINTWISE_TOLERANCE:
        raise RuntimeError(
            "La transformation scalaire galiléenne "
            "est incorrecte."
        )

    print(
        "Lois galiléennes locales : VALIDÉES"
    )


def validate_galilean_composition() -> None:
    _, x, y, _ = build_periodic_grid(
        48
    )

    time = 0.77
    reference_time = -0.20

    first_frame = np.asarray(
        (
            0.35,
            -0.15,
        ),
        dtype=np.float64,
    )

    second_frame = np.asarray(
        (
            -0.10,
            0.28,
        ),
        dtype=np.float64,
    )

    combined_frame = (
        first_frame + second_frame
    )

    velocity = make_cellular_velocity(
        0.90,
        -0.60,
        growth_rate=0.07,
    )

    direct_velocity = (
        itd_v23.galilean_transform_velocity_function(
            velocity,
            combined_frame,
            reference_time=reference_time,
        )
    )

    sequential_velocity = (
        itd_v23.galilean_transform_velocity_function(
            itd_v23.galilean_transform_velocity_function(
                velocity,
                first_frame,
                reference_time=reference_time,
            ),
            second_frame,
            reference_time=reference_time,
        )
    )

    direct_vx, direct_vy = direct_velocity(
        x,
        y,
        time,
    )

    sequential_vx, sequential_vy = (
        sequential_velocity(
            x,
            y,
            time,
        )
    )

    velocity_error = max(
        float(
            np.max(
                np.abs(
                    direct_vx
                    - sequential_vx
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    direct_vy
                    - sequential_vy
                )
            )
        ),
    )

    direct_scalar = (
        itd_v23.galilean_transform_scalar_function(
            periodic_scalar,
            combined_frame,
            reference_time=reference_time,
        )
    )

    sequential_scalar = (
        itd_v23.galilean_transform_scalar_function(
            itd_v23.galilean_transform_scalar_function(
                periodic_scalar,
                first_frame,
                reference_time=reference_time,
            ),
            second_frame,
            reference_time=reference_time,
        )
    )

    scalar_error = float(
        np.max(
            np.abs(
                direct_scalar(
                    x,
                    y,
                    time,
                )
                - sequential_scalar(
                    x,
                    y,
                    time,
                )
            )
        )
    )

    inverse_velocity = (
        itd_v23.galilean_transform_velocity_function(
            itd_v23.galilean_transform_velocity_function(
                velocity,
                first_frame,
                reference_time=reference_time,
            ),
            -first_frame,
            reference_time=reference_time,
        )
    )

    original_vx, original_vy = velocity(
        x,
        y,
        time,
    )

    inverse_vx, inverse_vy = inverse_velocity(
        x,
        y,
        time,
    )

    inverse_error = max(
        float(
            np.max(
                np.abs(
                    inverse_vx
                    - original_vx
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    inverse_vy
                    - original_vy
                )
            )
        ),
    )

    print()
    print(
        "=== COMPOSITION DES RÉFÉRENTIELS ==="
    )

    print(
        "Erreur de composition vectorielle :",
        f"{velocity_error:.6e}",
    )

    print(
        "Erreur de composition scalaire    :",
        f"{scalar_error:.6e}",
    )

    print(
        "Erreur du référentiel inverse      :",
        f"{inverse_error:.6e}",
    )

    if max(
        velocity_error,
        scalar_error,
        inverse_error,
    ) > COMPOSITION_TOLERANCE:
        raise RuntimeError(
            "La composition galiléenne ne respecte "
            "pas G_c G_d = G_(c+d)."
        )

    print(
        "G_c suivi de G_d = G_(c+d) : VALIDÉ"
    )


def build_objectivity_case():
    grid_size = 64

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    transport = np.asarray(
        (
            1.0,
            -2.0,
        ),
        dtype=np.float64,
    )

    frame_velocity = np.asarray(
        (
            0.5,
            -1.0,
        ),
        dtype=np.float64,
    )

    growth_rate = 0.16

    delta_time = (
        2.0 * spacing
    )

    times = (
        delta_time
        * np.arange(
            7,
            dtype=np.float64,
        )
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=float(times[-1]),
        time_steps=times.size,
        characteristic_length=0.5,
    )

    velocity = make_cellular_velocity(
        transport[0],
        transport[1],
        growth_rate=growth_rate,
    )

    advection = make_constant_velocity(
        transport[0],
        transport[1],
    )

    transformed_velocity = (
        itd_v23.galilean_transform_velocity_function(
            velocity,
            frame_velocity,
        )
    )

    transformed_advection = (
        itd_v23.galilean_transform_velocity_function(
            advection,
            frame_velocity,
        )
    )

    return (
        cfg,
        x,
        y,
        times,
        spacing,
        velocity,
        advection,
        transformed_velocity,
        transformed_advection,
    )


def validate_material_objectivity() -> None:
    """
    Vérifie l'objectivité asymptotique de la
    discrétisation matérielle V22.

    La dérivée matérielle continue est galiléenne,
    mais la combinaison discrète :

        différence temporelle centrée
        + gradient spatial centré

    ne commute pas exactement avec une transformation
    galiléenne à résolution finie.

    Le défaut de commutation doit toutefois converger
    vers zéro à l'ordre deux.
    """
    grid_sizes = (
        32,
        64,
        128,
        256,
    )

    transport = np.asarray(
        (
            1.0,
            -2.0,
        ),
        dtype=np.float64,
    )

    frame_velocity = np.asarray(
        (
            0.5,
            -1.0,
        ),
        dtype=np.float64,
    )

    growth_rate = 0.16

    defects: list[float] = []
    spatial_steps: list[float] = []
    eulerian_frame_differences: list[
        float
    ] = []

    print()
    print(
        "=== OBJECTIVITÉ ASYMPTOTIQUE DE LA "
        "DÉRIVÉE MATÉRIELLE ==="
    )

    print(
        "grille | pas spatial    | "
        "défaut galiléen | ordre | "
        "écart eulérien"
    )

    previous_defect: float | None = None
    previous_step: float | None = None

    for grid_size in grid_sizes:
        _, x, y, spacing = (
            build_periodic_grid(
                grid_size
            )
        )

        # Même nombre de cellules traversées à
        # chaque résolution :
        #
        # transport original :
        #   (+2, -4) cellules par intervalle ;
        #
        # transport dans le nouveau référentiel :
        #   (+1, -2) cellules par intervalle.
        delta_time = (
            2.0 * spacing
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

        velocity = make_cellular_velocity(
            transport[0],
            transport[1],
            growth_rate=growth_rate,
        )

        advection = make_constant_velocity(
            transport[0],
            transport[1],
        )

        transformed_velocity = (
            itd_v23.galilean_transform_velocity_function(
                velocity,
                frame_velocity,
            )
        )

        transformed_advection = (
            itd_v23.galilean_transform_velocity_function(
                advection,
                frame_velocity,
            )
        )

        original = (
            itd_v23.simulate_material_deformation(
                f"materiel_original_{grid_size}",
                velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=zero_curvature,
                boundary_mode="periodic",
                advection_velocity_function=(
                    advection
                ),
            )
        )

        transformed = (
            itd_v23.simulate_material_deformation(
                f"materiel_galileen_{grid_size}",
                transformed_velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=zero_curvature,
                boundary_mode="periodic",
                advection_velocity_function=(
                    transformed_advection
                ),
            )
        )

        original_material = np.asarray(
            original[
                "material_deformation_interval"
            ],
            dtype=np.float64,
        )

        transformed_material = np.asarray(
            transformed[
                "material_deformation_interval"
            ],
            dtype=np.float64,
        )

        interval_defect = float(
            np.max(
                np.abs(
                    transformed_material
                    - original_material
                )
            )
        )

        index_defect = abs(
            float(
                transformed[
                    "material_deformation_index"
                ]
            )
            - float(
                original[
                    "material_deformation_index"
                ]
            )
        )

        defect = max(
            interval_defect,
            index_defect,
        )

        original_eulerian_index = float(
            original[
                "material_eulerian_rate_index"
            ]
        )

        transformed_eulerian_index = float(
            transformed[
                "material_eulerian_rate_index"
            ]
        )

        eulerian_difference = abs(
            transformed_eulerian_index
            - original_eulerian_index
        )

        defects.append(defect)
        spatial_steps.append(spacing)
        eulerian_frame_differences.append(
            eulerian_difference
        )

        if previous_defect is None:
            order_text = "—"
        else:
            if (
                defect <= 0.0
                or previous_defect <= 0.0
            ):
                raise RuntimeError(
                    "Le défaut galiléen doit être "
                    "strictement positif avant "
                    "d'atteindre l'arrondi machine."
                )

            order = float(
                np.log(
                    previous_defect / defect
                )
                / np.log(
                    previous_step / spacing
                )
            )

            order_text = (
                f"{order:.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{spacing:14.10f} | "
            f"{defect:15.6e} | "
            f"{order_text:>8} | "
            f"{eulerian_difference:.6e}"
        )

        previous_defect = defect
        previous_step = spacing

    monotone = all(
        current < previous
        for previous, current in zip(
            defects,
            defects[1:],
        )
    )

    if not monotone:
        raise RuntimeError(
            "Le défaut d'objectivité matérielle "
            "ne décroît pas avec le raffinement."
        )

    observed_orders = []

    for index in range(
        1,
        len(defects),
    ):
        observed_orders.append(
            float(
                np.log(
                    defects[index - 1]
                    / defects[index]
                )
                / np.log(
                    spatial_steps[index - 1]
                    / spatial_steps[index]
                )
            )
        )

    final_orders = (
        observed_orders[-2:]
    )

    minimum_final_order = min(
        final_orders
    )

    print(
        "Ordres finaux du défaut galiléen :",
        [
            float(value)
            for value in final_orders
        ],
    )

    print(
        "Défaut final                       :",
        f"{defects[-1]:.6e}",
    )

    print(
        "Écart eulérien final               :",
        f"{eulerian_frame_differences[-1]:.6e}",
    )

    if minimum_final_order < 1.8:
        raise RuntimeError(
            "Le défaut d'objectivité matérielle "
            "ne converge pas à l'ordre deux."
        )

    # La mesure eulérienne doit rester dépendante
    # du référentiel même lorsque la grille est fine.
    if (
        eulerian_frame_differences[-1]
        < 0.05
    ):
        raise RuntimeError(
            "L'oracle ne distingue pas la dépendance "
            "au cadre de la mesure eulérienne."
        )

    print(
        "Objectivité matérielle asymptotique "
        "d'ordre deux : VALIDÉE"
    )

def validate_semilagrangian_objectivity() -> None:
    (
        cfg,
        x,
        y,
        times,
        spacing,
        velocity,
        advection,
        transformed_velocity,
        transformed_advection,
    ) = build_objectivity_case()

    original = itd_v23.simulate(
        "semi_lagrangien_original",
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
        transport_velocity_function=advection,
    )

    transformed = itd_v23.simulate(
        "semi_lagrangien_galileen",
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
            transformed_advection
        ),
    )

    original_compensated = np.asarray(
        original[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    transformed_compensated = np.asarray(
        transformed[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    interval_error = float(
        np.max(
            np.abs(
                transformed_compensated
                - original_compensated
            )
        )
    )

    index_error = abs(
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
    )

    print()
    print(
        "=== OBJECTIVITÉ SEMI-LAGRANGIENNE ==="
    )

    print(
        "Erreur des intervalles compensés :",
        f"{interval_error:.6e}",
    )

    print(
        "Erreur de l'indice compensé       :",
        f"{index_error:.6e}",
    )

    if interval_error > OBJECTIVITY_TOLERANCE:
        raise RuntimeError(
            "La compensation semi-lagrangienne "
            "dépend du référentiel."
        )

    if index_error > OBJECTIVITY_TOLERANCE:
        raise RuntimeError(
            "L'indice semi-lagrangien dépend du "
            "référentiel."
        )

    print(
        "Compensation semi-lagrangienne "
        "objective : VALIDÉE"
    )


def validate_v21_v22_consistency() -> None:
    grid_sizes = (
        32,
        64,
        128,
        256,
    )

    transport_x = 1.0
    transport_y = -2.0
    growth_rate = 0.22

    errors: list[float] = []
    steps: list[float] = []

    print()
    print(
        "=== ACCORD ASYMPTOTIQUE V21 / V22 ==="
    )

    print(
        "grille | pas spatial    | V21 compensé | "
        "V22 matériel | écart | ordre"
    )

    previous_error: float | None = None
    previous_step: float | None = None

    for grid_size in grid_sizes:
        _, x, y, spacing = (
            build_periodic_grid(
                grid_size
            )
        )

        delta_time = spacing

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

        velocity = make_cellular_velocity(
            transport_x,
            transport_y,
            growth_rate=growth_rate,
        )

        advection = make_constant_velocity(
            transport_x,
            transport_y,
        )

        semilagrangian = itd_v23.simulate(
            f"v21_{grid_size}",
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
            transport_velocity_function=advection,
        )

        material = (
            itd_v23.simulate_material_deformation(
                f"v22_{grid_size}",
                velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=zero_curvature,
                boundary_mode="periodic",
                advection_velocity_function=advection,
            )
        )

        semilagrangian_value = float(
            semilagrangian[
                "temporal_deformation_compensated_index"
            ]
        )

        material_value = float(
            material[
                "material_deformation_index"
            ]
        )

        expected = float(
            2.0
            * np.tanh(
                0.5
                * growth_rate
                * delta_time
            )
            / delta_time
        )

        oracle_error = abs(
            semilagrangian_value
            - expected
        )

        if oracle_error > METHOD_ORACLE_TOLERANCE:
            raise RuntimeError(
                "La mesure V21 alignée sur les nœuds "
                "ne reproduit pas l'oracle."
            )

        error = abs(
            material_value
            - semilagrangian_value
        )

        errors.append(error)
        steps.append(spacing)

        if previous_error is None:
            order_text = "—"
        else:
            order = float(
                np.log(
                    previous_error / error
                )
                / np.log(
                    previous_step / spacing
                )
            )

            order_text = f"{order:.6f}"

        print(
            f"{grid_size:6d} | "
            f"{spacing:14.10f} | "
            f"{semilagrangian_value:12.9f} | "
            f"{material_value:12.9f} | "
            f"{error:9.3e} | "
            f"{order_text}"
        )

        previous_error = error
        previous_step = spacing

    if not all(
        current < previous
        for previous, current in zip(
            errors,
            errors[1:],
        )
    ):
        raise RuntimeError(
            "L'écart V21/V22 ne décroît pas "
            "avec le raffinement."
        )

    final_orders = []

    for index in (
        len(errors) - 2,
        len(errors) - 1,
    ):
        final_orders.append(
            float(
                np.log(
                    errors[index - 1]
                    / errors[index]
                )
                / np.log(
                    steps[index - 1]
                    / steps[index]
                )
            )
        )

    if min(final_orders) < 1.8:
        raise RuntimeError(
            "V21 et V22 ne convergent pas l'une "
            "vers l'autre à l'ordre deux."
        )

    print(
        "Accord V21/V22 d'ordre deux : VALIDÉ"
    )


def validate_invalid_galilean_inputs() -> None:
    print()
    print(
        "=== REJET DES RÉFÉRENTIELS INVALIDES ==="
    )

    for invalid_velocity in (
        (),
        (1.0,),
        (1.0, 2.0, 3.0),
        (1.0, np.nan),
        (1.0, np.inf),
        "mobile",
        None,
    ):
        try:
            itd_v23.validate_galilean_frame_velocity(
                invalid_velocity
            )
        except ValueError as error:
            print(
                f"Vitesse {invalid_velocity!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une vitesse de référentiel invalide "
                "n'a pas été rejetée."
            )

    for invalid_time in (
        np.nan,
        np.inf,
        "origine",
        None,
    ):
        try:
            itd_v23.validate_galilean_reference_time(
                invalid_time
            )
        except ValueError as error:
            print(
                f"Temps {invalid_time!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un instant de référence invalide "
                "n'a pas été rejeté."
            )

    try:
        itd_v23.galilean_transform_velocity_function(
            "vitesse",
            (
                0.0,
                0.0,
            ),
        )
    except ValueError as error:
        print(
            "Champ invalide : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Un champ de vitesse non appelable "
            "a été accepté."
        )

    print(
        "Contrôle des référentiels V23 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE L'OBJECTIVITÉ "
        "GALILÉENNE — ITD V23 ==="
    )

    validate_v22_compatibility()
    validate_pointwise_galilean_laws()
    validate_galilean_composition()
    validate_material_objectivity()
    validate_semilagrangian_objectivity()
    validate_v21_v22_consistency()
    validate_invalid_galilean_inputs()

    print()
    print(
        "Compatibilité V22 → V23                : VALIDÉE"
    )
    print(
        "Vorticité scalaire galiléenne          : VALIDÉE"
    )
    print(
        "Composition G_c G_d = G_(c+d)          : VALIDÉE"
    )
    print(
        "Dérivée matérielle asymptotiquement objective: VALIDÉE"
    )
    print(
        "Compensation semi-lagrangienne objective: VALIDÉE"
    )
    print(
        "Accord asymptotique V21/V22 ordre deux : VALIDÉ"
    )
    print(
        "Variation eulérienne dépend du cadre   : EXPLICITE"
    )


if __name__ == "__main__":
    main()
