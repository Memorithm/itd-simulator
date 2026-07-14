#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v23
import itd_v24
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
LOCAL_TOLERANCE = 8.0e-12
COMPOSITION_TOLERANCE = 3.0e-13
EXACT_SEMILAGRANGIAN_TOLERANCE = 3.0e-11

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
            x - 0.20 * time
        )
        + 0.35
        * np.cos(
            2.0 * y
            + 0.10 * time
        )
        + 0.12
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


def make_quadratic_frame(
    initial_velocity: object,
    acceleration: object,
):
    initial = np.asarray(
        initial_velocity,
        dtype=np.float64,
    )

    acceleration_array = np.asarray(
        acceleration,
        dtype=np.float64,
    )

    if (
        initial.shape != (2,)
        or acceleration_array.shape != (2,)
    ):
        raise ValueError(
            "Les paramètres du référentiel doivent "
            "être des vecteurs de dimension deux."
        )

    def displacement(
        time: float,
    ) -> np.ndarray:
        return (
            initial * time
            + 0.5
            * acceleration_array
            * time**2
        )

    def velocity(
        time: float,
    ) -> np.ndarray:
        return (
            initial
            + acceleration_array * time
        )

    return displacement, velocity


def validate_v23_compatibility() -> None:
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
        "=== COMPATIBILITÉ V23 → V24 ==="
    )

    reference = (
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

    candidate = (
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
            "La V24 modifie les résultats "
            "historiques de la V23."
        )

    print(
        "Compatibilité V23 → V24 : VALIDÉE"
    )


def validate_galilean_reduction() -> None:
    _, x, y, _ = build_periodic_grid(
        64
    )

    frame_velocity = np.asarray(
        (
            0.37,
            -0.22,
        ),
        dtype=np.float64,
    )

    reference_time = -0.15

    def displacement(
        time: float,
    ) -> np.ndarray:
        return (
            frame_velocity
            * (
                time - reference_time
            )
        )

    def velocity(
        time: float,
    ) -> np.ndarray:
        del time

        return frame_velocity

    original = make_cellular_velocity(
        0.80,
        -0.55,
        growth_rate=0.09,
    )

    general_velocity = (
        itd_v24.translating_frame_transform_velocity_function(
            original,
            displacement,
            velocity,
        )
    )

    galilean_velocity = (
        itd_v23.galilean_transform_velocity_function(
            original,
            frame_velocity,
            reference_time=reference_time,
        )
    )

    general_scalar = (
        itd_v24.translating_frame_transform_scalar_function(
            periodic_scalar,
            displacement,
        )
    )

    galilean_scalar = (
        itd_v23.galilean_transform_scalar_function(
            periodic_scalar,
            frame_velocity,
            reference_time=reference_time,
        )
    )

    maximum_error = 0.0

    for time in (
        -0.15,
        0.0,
        0.43,
        1.10,
    ):
        general_vx, general_vy = (
            general_velocity(
                x,
                y,
                time,
            )
        )

        galilean_vx, galilean_vy = (
            galilean_velocity(
                x,
                y,
                time,
            )
        )

        maximum_error = max(
            maximum_error,
            float(
                np.max(
                    np.abs(
                        general_vx
                        - galilean_vx
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        general_vy
                        - galilean_vy
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        general_scalar(
                            x,
                            y,
                            time,
                        )
                        - galilean_scalar(
                            x,
                            y,
                            time,
                        )
                    )
                )
            ),
        )

    print()
    print(
        "=== RÉDUCTION AU CAS GALILÉEN ==="
    )

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > LOCAL_TOLERANCE:
        raise RuntimeError(
            "La translation uniforme V24 ne se "
            "réduit pas à la transformation V23."
        )

    print(
        "Translation uniforme = Galilée : VALIDÉE"
    )


def validate_local_accelerating_laws() -> None:
    grid_size = 96

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    displacement, frame_velocity = (
        make_quadratic_frame(
            (
                0.31,
                -0.17,
            ),
            (
                0.24,
                -0.13,
            ),
        )
    )

    time = 0.84

    original = make_cellular_velocity(
        0.90,
        -0.60,
        growth_rate=0.10,
    )

    transformed_velocity = (
        itd_v24.translating_frame_transform_velocity_function(
            original,
            displacement,
            frame_velocity,
        )
    )

    transformed_scalar = (
        itd_v24.translating_frame_transform_scalar_function(
            periodic_scalar,
            displacement,
        )
    )

    source_x, source_y = (
        itd_v24.translating_frame_source_coordinates(
            x,
            y,
            time,
            displacement,
        )
    )

    source_vx, source_vy = original(
        source_x,
        source_y,
        time,
    )

    current_frame_velocity = (
        frame_velocity(time)
    )

    transformed_vx, transformed_vy = (
        transformed_velocity(
            x,
            y,
            time,
        )
    )

    velocity_error = max(
        float(
            np.max(
                np.abs(
                    transformed_vx
                    - (
                        source_vx
                        - current_frame_velocity[0]
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
                        - current_frame_velocity[1]
                    )
                )
            )
        ),
    )

    source_omega = (
        itd_v24.numerical_vorticity_with_boundary(
            source_vx,
            source_vy,
            spacing,
            boundary_mode="periodic",
        )
    )

    transformed_omega = (
        itd_v24.numerical_vorticity_with_boundary(
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
        "=== LOIS LOCALES DU RÉFÉRENTIEL ACCÉLÉRÉ ==="
    )

    print(
        "Erreur de vitesse  :",
        f"{velocity_error:.6e}",
    )

    print(
        "Erreur de vorticité:",
        f"{vorticity_error:.6e}",
    )

    print(
        "Erreur scalaire    :",
        f"{scalar_error:.6e}",
    )

    if max(
        velocity_error,
        vorticity_error,
        scalar_error,
    ) > LOCAL_TOLERANCE:
        raise RuntimeError(
            "Les lois locales du référentiel "
            "accéléré sont incorrectes."
        )

    print(
        "Lois locales accélérées : VALIDÉES"
    )


def validate_accelerating_frame_composition() -> None:
    _, x, y, _ = build_periodic_grid(
        48
    )

    first_displacement, first_velocity = (
        make_quadratic_frame(
            (
                0.25,
                -0.10,
            ),
            (
                0.12,
                0.08,
            ),
        )
    )

    second_displacement, second_velocity = (
        make_quadratic_frame(
            (
                -0.07,
                0.19,
            ),
            (
                0.05,
                -0.11,
            ),
        )
    )

    def combined_displacement(
        time: float,
    ) -> np.ndarray:
        return (
            first_displacement(time)
            + second_displacement(time)
        )

    def combined_velocity(
        time: float,
    ) -> np.ndarray:
        return (
            first_velocity(time)
            + second_velocity(time)
        )

    original = make_cellular_velocity(
        0.75,
        -0.48,
        growth_rate=0.06,
    )

    direct = (
        itd_v24.translating_frame_transform_velocity_function(
            original,
            combined_displacement,
            combined_velocity,
        )
    )

    sequential = (
        itd_v24.translating_frame_transform_velocity_function(
            itd_v24.translating_frame_transform_velocity_function(
                original,
                first_displacement,
                first_velocity,
            ),
            second_displacement,
            second_velocity,
        )
    )

    direct_scalar = (
        itd_v24.translating_frame_transform_scalar_function(
            periodic_scalar,
            combined_displacement,
        )
    )

    sequential_scalar = (
        itd_v24.translating_frame_transform_scalar_function(
            itd_v24.translating_frame_transform_scalar_function(
                periodic_scalar,
                first_displacement,
            ),
            second_displacement,
        )
    )

    maximum_error = 0.0

    for time in (
        0.0,
        0.37,
        0.90,
    ):
        direct_vx, direct_vy = direct(
            x,
            y,
            time,
        )

        sequential_vx, sequential_vy = (
            sequential(
                x,
                y,
                time,
            )
        )

        maximum_error = max(
            maximum_error,
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
            float(
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
            ),
        )

    print()
    print(
        "=== COMPOSITION DES TRANSLATIONS TEMPORELLES ==="
    )

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > COMPOSITION_TOLERANCE:
        raise RuntimeError(
            "La composition des référentiels "
            "accélérés est incorrecte."
        )

    print(
        "T_b suivi de T_d = T_(b+d) : VALIDÉ"
    )


def validate_material_accelerating_objectivity() -> None:
    grid_sizes = (
        32,
        64,
        128,
        256,
    )

    transport_x = 0.82
    transport_y = -0.57
    growth_rate = 0.16

    displacement, frame_velocity = (
        make_quadratic_frame(
            (
                0.41,
                -0.29,
            ),
            (
                0.27,
                -0.18,
            ),
        )
    )

    defects: list[float] = []
    steps: list[float] = []
    eulerian_differences: list[float] = []

    print()
    print(
        "=== OBJECTIVITÉ MATÉRIELLE SOUS "
        "ACCÉLÉRATION ==="
    )

    print(
        "grille | pas spatial    | défaut | ordre | "
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

        delta_time = (
            0.35
            * spacing
            / max(
                abs(transport_x),
                abs(transport_y),
                1.0,
            )
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
            make_cellular_velocity(
                transport_x,
                transport_y,
                growth_rate=growth_rate,
            )
        )

        original_advection = (
            make_constant_velocity(
                transport_x,
                transport_y,
            )
        )

        transformed_velocity = (
            itd_v24.translating_frame_transform_velocity_function(
                original_velocity,
                displacement,
                frame_velocity,
            )
        )

        transformed_advection = (
            itd_v24.translating_frame_transform_velocity_function(
                original_advection,
                displacement,
                frame_velocity,
            )
        )

        original = (
            itd_v24.simulate_material_deformation(
                f"accelere_original_{grid_size}",
                original_velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=zero_curvature,
                boundary_mode="periodic",
                advection_velocity_function=(
                    original_advection
                ),
            )
        )

        transformed = (
            itd_v24.simulate_material_deformation(
                f"accelere_transforme_{grid_size}",
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

        defect = abs(
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

        eulerian_difference = abs(
            float(
                transformed[
                    "material_eulerian_rate_index"
                ]
            )
            - float(
                original[
                    "material_eulerian_rate_index"
                ]
            )
        )

        defects.append(defect)
        steps.append(spacing)
        eulerian_differences.append(
            eulerian_difference
        )

        if previous_defect is None:
            order_text = "—"
        else:
            order = float(
                np.log(
                    previous_defect / defect
                )
                / np.log(
                    previous_step / spacing
                )
            )

            order_text = f"{order:.6f}"

        print(
            f"{grid_size:6d} | "
            f"{spacing:14.10f} | "
            f"{defect:9.3e} | "
            f"{order_text:>8} | "
            f"{eulerian_difference:.6e}"
        )

        previous_defect = defect
        previous_step = spacing

    if not all(
        current < previous
        for previous, current in zip(
            defects,
            defects[1:],
        )
    ):
        raise RuntimeError(
            "Le défaut matériel sous accélération "
            "ne décroît pas."
        )

    final_orders = []

    for index in (
        len(defects) - 2,
        len(defects) - 1,
    ):
        final_orders.append(
            float(
                np.log(
                    defects[index - 1]
                    / defects[index]
                )
                / np.log(
                    steps[index - 1]
                    / steps[index]
                )
            )
        )

    if min(final_orders) < 1.8:
        raise RuntimeError(
            "L'objectivité sous accélération "
            "n'atteint pas l'ordre deux."
        )

    if eulerian_differences[-1] < 0.05:
        raise RuntimeError(
            "La mesure eulérienne ne distingue pas "
            "les référentiels accélérés."
        )

    print(
        "Objectivité matérielle accélérée "
        "d'ordre deux : VALIDÉE"
    )


def validate_exact_accelerating_semilagrangian() -> None:
    grid_size = 64

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    delta_time = 0.125

    physical_cell_shift = np.asarray(
        (
            3.0,
            -2.0,
        ),
        dtype=np.float64,
    )

    frame_quadratic_cells = np.asarray(
        (
            1.0,
            -1.0,
        ),
        dtype=np.float64,
    )

    transport = (
        physical_cell_shift
        * spacing
        / delta_time
    )

    def displacement(
        time: float,
    ) -> np.ndarray:
        normalized_time = (
            time / delta_time
        )

        return (
            frame_quadratic_cells
            * spacing
            * normalized_time**2
        )

    def frame_velocity(
        time: float,
    ) -> np.ndarray:
        return (
            2.0
            * frame_quadratic_cells
            * spacing
            * time
            / delta_time**2
        )

    times = (
        delta_time
        * np.arange(
            6,
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

    original_velocity = (
        make_cellular_velocity(
            transport[0],
            transport[1],
            growth_rate=0.14,
        )
    )

    original_transport = (
        make_constant_velocity(
            transport[0],
            transport[1],
        )
    )

    transformed_velocity = (
        itd_v24.translating_frame_transform_velocity_function(
            original_velocity,
            displacement,
            frame_velocity,
        )
    )

    transformed_transport = (
        itd_v24.translating_frame_transform_velocity_function(
            original_transport,
            displacement,
            frame_velocity,
        )
    )

    original = itd_v24.simulate(
        "semi_accelere_original",
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
    )

    transformed = itd_v24.simulate(
        "semi_accelere_transforme",
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
    )

    interval_error = float(
        np.max(
            np.abs(
                np.asarray(
                    transformed[
                        "temporal_deformation_compensated_interval"
                    ],
                    dtype=np.float64,
                )
                - np.asarray(
                    original[
                        "temporal_deformation_compensated_interval"
                    ],
                    dtype=np.float64,
                )
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
        "=== OBJECTIVITÉ SEMI-LAGRANGIENNE "
        "ACCÉLÉRÉE ==="
    )

    print(
        "Erreur des intervalles :",
        f"{interval_error:.6e}",
    )

    print(
        "Erreur de l'indice     :",
        f"{index_error:.6e}",
    )

    if max(
        interval_error,
        index_error,
    ) > EXACT_SEMILAGRANGIAN_TOLERANCE:
        raise RuntimeError(
            "La compensation semi-lagrangienne "
            "n'est pas objective sous l'accélération "
            "alignée sur la grille."
        )

    print(
        "Objectivité semi-lagrangienne accélérée : "
        "VALIDÉE"
    )


def validate_invalid_frames() -> None:
    print()
    print(
        "=== REJET DES RÉFÉRENTIELS ACCÉLÉRÉS "
        "INVALIDES ==="
    )

    invalid_functions = (
        None,
        "trajectoire",
        17,
    )

    for invalid in invalid_functions:
        try:
            itd_v24.evaluate_translating_frame_vector(
                invalid,
                0.0,
                "déplacement",
            )
        except ValueError as error:
            print(
                f"Fonction {invalid!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une fonction de référentiel invalide "
                "a été acceptée."
            )

    invalid_outputs = (
        lambda time: (),
        lambda time: (1.0,),
        lambda time: (
            1.0,
            2.0,
            3.0,
        ),
        lambda time: (
            np.nan,
            0.0,
        ),
        lambda time: (
            np.inf,
            0.0,
        ),
        lambda time: "mobile",
    )

    for invalid in invalid_outputs:
        try:
            itd_v24.evaluate_translating_frame_vector(
                invalid,
                0.0,
                "vitesse",
            )
        except ValueError as error:
            print(
                "Sortie invalide : RÉUSSI —",
                error,
            )
        else:
            raise RuntimeError(
                "Une sortie vectorielle invalide "
                "a été acceptée."
            )

    try:
        itd_v24.evaluate_translating_frame_vector(
            lambda time: (
                0.0,
                0.0,
            ),
            np.nan,
            "déplacement",
        )
    except ValueError as error:
        print(
            "Temps invalide  : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Un temps non fini a été accepté."
        )

    print(
        "Contrôle des référentiels V24 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DES RÉFÉRENTIELS EN "
        "TRANSLATION ACCÉLÉRÉE — ITD V24 ==="
    )

    validate_v23_compatibility()
    validate_galilean_reduction()
    validate_local_accelerating_laws()
    validate_accelerating_frame_composition()
    validate_material_accelerating_objectivity()
    validate_exact_accelerating_semilagrangian()
    validate_invalid_frames()

    print()
    print(
        "Compatibilité V23 → V24                    : VALIDÉE"
    )
    print(
        "Réduction au référentiel galiléen          : VALIDÉE"
    )
    print(
        "Vorticité sous translation accélérée       : VALIDÉE"
    )
    print(
        "Composition des trajectoires               : VALIDÉE"
    )
    print(
        "Dérivée matérielle asymptotiquement objective: VALIDÉE"
    )
    print(
        "Compensation semi-lagrangienne objective   : VALIDÉE"
    )
    print(
        "Variation eulérienne dépend du référentiel : EXPLICITE"
    )


if __name__ == "__main__":
    main()
