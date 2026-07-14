#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v21
import itd_v22
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
ALGEBRA_TOLERANCE = 2.0e-14
AFFINE_TOLERANCE = 3.0e-12
CONSISTENCY_TOLERANCE = 3.0e-13

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


def translating_cellular_velocity(
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


def constant_velocity(
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


def validate_v21_compatibility() -> None:
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
        endpoint=True,
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
        "=== COMPATIBILITÉ V21 → V22 ==="
    )

    reference = (
        itd_v21.extract_single_scale_diagnostics(
            itd_v21.simulate(
                "compatibilite_v21",
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
            "La V22 modifie les résultats "
            "historiques de la V21."
        )

    print(
        "Compatibilité V21 → V22 : VALIDÉE"
    )


def validate_field_identity() -> None:
    coordinates = np.linspace(
        -1.0,
        1.0,
        33,
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

    previous = (
        np.sin(x)
        * np.cos(y)
    )

    current = (
        1.05
        * np.sin(x - 0.03)
        * np.cos(y + 0.02)
    )

    midpoint_vx = (
        0.20
        + 0.05 * x
    )

    midpoint_vy = (
        -0.10
        + 0.04 * y
    )

    result = itd_v22.material_vorticity_interval(
        previous,
        current,
        midpoint_vx,
        midpoint_vy,
        spacing,
        0.125,
        boundary_mode="finite",
    )

    temporal = np.asarray(
        result["temporal_tendency"],
        dtype=np.float64,
    )

    advective = np.asarray(
        result["advective_tendency"],
        dtype=np.float64,
    )

    material = np.asarray(
        result["material_tendency"],
        dtype=np.float64,
    )

    error = float(
        np.max(
            np.abs(
                material
                - (
                    temporal
                    + advective
                )
            )
        )
    )

    print()
    print(
        "=== IDENTITÉ DE LA DÉRIVÉE MATÉRIELLE ==="
    )

    print(
        "Erreur de Dω/Dt = ∂tω + u·∇ω :",
        f"{error:.6e}",
    )

    if error > ALGEBRA_TOLERANCE:
        raise RuntimeError(
            "L'identité de champ de la dérivée "
            "matérielle n'est pas respectée."
        )

    print(
        "Identité différentielle : VALIDÉE"
    )


def validate_affine_nonuniform_oracle() -> None:
    parameter_x = np.linspace(
        0.0,
        1.0,
        57,
        dtype=np.float64,
    )

    parameter_y = np.linspace(
        0.0,
        1.0,
        43,
        dtype=np.float64,
    )

    x_coordinates = (
        -1.5
        + 3.0 * parameter_x**1.4
    )

    y_coordinates = (
        -1.0
        + 2.0 * parameter_y**1.7
    )

    x, y = np.meshgrid(
        x_coordinates,
        y_coordinates,
        indexing="xy",
    )

    geometry = itd_v22.RectilinearGeometry(
        x_coordinates,
        y_coordinates,
    )

    delta_time = 0.30
    transport_x = 0.40
    transport_y = -0.20

    previous = (
        1.25
        + 0.70 * x
        - 0.35 * y
    )

    current = (
        1.25
        + 0.70
        * (
            x
            - transport_x
            * delta_time
        )
        - 0.35
        * (
            y
            - transport_y
            * delta_time
        )
    )

    result = itd_v22.material_vorticity_interval(
        previous,
        current,
        np.full_like(
            x,
            transport_x,
        ),
        np.full_like(
            y,
            transport_y,
        ),
        geometry,
        delta_time,
        boundary_mode="finite",
    )

    material = np.asarray(
        result["material_tendency"],
        dtype=np.float64,
    )

    maximum_error = float(
        np.max(
            np.abs(material)
        )
    )

    material_rate = float(
        result["material_rate"]
    )

    print()
    print(
        "=== ORACLE AFFINE NON UNIFORME ==="
    )

    print(
        "Résidu matériel maximal :",
        f"{maximum_error:.6e}",
    )

    print(
        "Taux matériel normalisé :",
        f"{material_rate:.6e}",
    )

    if maximum_error > AFFINE_TOLERANCE:
        raise RuntimeError(
            "Le transport affine exact produit "
            "une déformation matérielle."
        )

    if material_rate > AFFINE_TOLERANCE:
        raise RuntimeError(
            "Le taux matériel affine est excessif."
        )

    print(
        "Oracle affine non uniforme : VALIDÉ"
    )


def validate_zero_advection_equivalence() -> None:
    grid_size = 48

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    times = np.linspace(
        0.0,
        1.0,
        9,
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=1.0,
        time_steps=times.size,
        characteristic_length=0.5,
    )

    result = (
        itd_v22.simulate_material_deformation(
            "advection_nulle",
            translating_cellular_velocity(
                0.0,
                0.0,
                growth_rate=0.18,
            ),
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
            boundary_mode="periodic",
            advection_velocity_function=(
                constant_velocity(
                    0.0,
                    0.0,
                )
            ),
        )
    )

    eulerian = np.asarray(
        result[
            "material_eulerian_rate_interval"
        ],
        dtype=np.float64,
    )

    material = np.asarray(
        result[
            "material_deformation_interval"
        ],
        dtype=np.float64,
    )

    exact = np.array_equal(
        eulerian,
        material,
    )

    print()
    print(
        "=== ADVECTION NULLE ==="
    )

    print(
        "Égalité bit à bit Euler/matériel :",
        exact,
    )

    if not exact:
        raise RuntimeError(
            "Une advection nulle modifie le "
            "diagnostic eulérien."
        )

    print(
        "Advection nulle : VALIDÉE"
    )


def validate_rigid_translation_convergence() -> None:
    grid_sizes = (
        32,
        64,
        128,
        256,
    )

    transport_x = 0.70
    transport_y = -0.40

    errors: list[float] = []
    steps: list[float] = []

    print()
    print(
        "=== CONVERGENCE MATÉRIELLE D'UNE "
        "TRANSLATION RIGIDE ==="
    )

    print(
        "grille | pas spatial    | "
        "résidu matériel | ordre"
    )

    previous_error: float | None = None
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

        result = (
            itd_v22.simulate_material_deformation(
                f"translation_{grid_size}",
                translating_cellular_velocity(
                    transport_x,
                    transport_y,
                ),
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=zero_curvature,
                boundary_mode="periodic",
                advection_velocity_function=(
                    constant_velocity(
                        transport_x,
                        transport_y,
                    )
                ),
            )
        )

        error = float(
            result[
                "material_deformation_index"
            ]
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
            f"{error:16.6e} | "
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
            "Le résidu matériel ne décroît pas."
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
            "La dérivée matérielle n'atteint pas "
            "l'ordre deux attendu."
        )

    print(
        "Translation matérielle d'ordre deux : "
        "VALIDÉE"
    )


def validate_growth_oracle_convergence() -> None:
    grid_sizes = (
        32,
        64,
        128,
        256,
    )

    transport_x = 0.55
    transport_y = -0.35
    growth_rate = 0.22

    errors: list[float] = []
    steps: list[float] = []

    print()
    print(
        "=== CROISSANCE INTRINSÈQUE MATÉRIELLE ==="
    )

    print(
        "grille | valeur obtenue | valeur attendue | "
        "erreur | ordre"
    )

    previous_error: float | None = None
    previous_step: float | None = None

    for grid_size in grid_sizes:
        _, x, y, spacing = (
            build_periodic_grid(
                grid_size
            )
        )

        delta_time = (
            0.30
            * spacing
            / max(
                abs(transport_x),
                abs(transport_y),
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

        result = (
            itd_v22.simulate_material_deformation(
                f"croissance_{grid_size}",
                translating_cellular_velocity(
                    transport_x,
                    transport_y,
                    growth_rate=growth_rate,
                ),
                x,
                y,
                times,
                spacing,
                cfg,
                curvature_function=zero_curvature,
                boundary_mode="periodic",
                advection_velocity_function=(
                    constant_velocity(
                        transport_x,
                        transport_y,
                    )
                ),
            )
        )

        obtained = float(
            result[
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

        error = abs(
            obtained - expected
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
            f"{obtained:14.10f} | "
            f"{expected:15.10f} | "
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
            "L'erreur de croissance matérielle "
            "ne décroît pas."
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
            "L'oracle de croissance matérielle "
            "n'atteint pas l'ordre deux."
        )

    print(
        "Croissance matérielle d'ordre deux : "
        "VALIDÉE"
    )


def validate_eulerian_consistency() -> None:
    grid_size = 64

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    times = np.linspace(
        0.0,
        1.0,
        17,
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=1.0,
        time_steps=times.size,
        characteristic_length=0.5,
    )

    result = (
        itd_v22.simulate_material_deformation(
            "coherence_eulerienne",
            translating_cellular_velocity(
                0.35,
                -0.20,
                growth_rate=0.10,
            ),
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
            boundary_mode="periodic",
            advection_velocity_function=(
                constant_velocity(
                    0.35,
                    -0.20,
                )
            ),
        )
    )

    consistency_error = float(
        result[
            "material_eulerian_consistency_error"
        ]
    )

    print()
    print(
        "=== COHÉRENCE AVEC LA MESURE EULÉRIENNE ==="
    )

    print(
        "Erreur maximale :",
        f"{consistency_error:.6e}",
    )

    if (
        consistency_error
        > CONSISTENCY_TOLERANCE
    ):
        raise RuntimeError(
            "La mesure eulérienne différentielle "
            "ne correspond pas à la V21."
        )

    print(
        "Cohérence eulérienne : VALIDÉE"
    )


def validate_invalid_inputs() -> None:
    print()
    print(
        "=== REJET DES ENTRÉES MATÉRIELLES INVALIDES ==="
    )

    for invalid_dt in (
        0.0,
        -1.0,
        np.nan,
        np.inf,
        "temps",
        None,
    ):
        try:
            itd_v22.validate_positive_time_interval(
                invalid_dt
            )
        except ValueError as error:
            print(
                f"Intervalle {invalid_dt!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un intervalle temporel invalide "
                "n'a pas été rejeté."
            )

    field = np.zeros(
        (5, 5),
        dtype=np.float64,
    )

    try:
        itd_v22.material_vorticity_interval(
            field,
            np.zeros(
                (6, 5),
                dtype=np.float64,
            ),
            field,
            field,
            1.0,
            0.1,
        )
    except ValueError as error:
        print(
            "Formes incohérentes : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Des champs de formes incohérentes "
            "ont été acceptés."
        )

    try:
        itd_v22.simulate_material_deformation(
            "advection_invalide",
            multi_vortex_field,
            field,
            field,
            (
                0.0,
                1.0,
            ),
            1.0,
            Config(
                grid_size=5,
                time_steps=2,
            ),
            advection_velocity_function="vent",
        )
    except ValueError as error:
        print(
            "Advection invalide    : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Un champ d'advection invalide "
            "a été accepté."
        )

    print(
        "Contrôle des entrées V22 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE LA DÉRIVÉE "
        "MATÉRIELLE — ITD V22 ==="
    )

    validate_v21_compatibility()
    validate_field_identity()
    validate_affine_nonuniform_oracle()
    validate_zero_advection_equivalence()
    validate_rigid_translation_convergence()
    validate_growth_oracle_convergence()
    validate_eulerian_consistency()
    validate_invalid_inputs()

    print()
    print(
        "Compatibilité V21 → V22             : VALIDÉE"
    )
    print(
        "Identité Dω/Dt = ∂tω + u·∇ω         : VALIDÉE"
    )
    print(
        "Oracle affine non uniforme          : VALIDÉ"
    )
    print(
        "Advection nulle = mesure eulérienne : VALIDÉE"
    )
    print(
        "Translation matérielle ordre deux   : VALIDÉE"
    )
    print(
        "Croissance intrinsèque ordre deux   : VALIDÉE"
    )
    print(
        "Mesure eulérienne historique        : CONSERVÉE"
    )


if __name__ == "__main__":
    main()
