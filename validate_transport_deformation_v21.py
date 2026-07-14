#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v20_1
import itd_v21
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
EXACT_TRANSPORT_TOLERANCE = 2.0e-11
AMPLITUDE_ORACLE_TOLERANCE = 2.0e-11
MULTISCALE_TOLERANCE = 5.0e-13

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


def extract_diagnostics(
    module: object,
    result: dict[str, object],
) -> dict[str, float]:
    return module.extract_single_scale_diagnostics(
        result
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


def make_constant_transport(
    transport_x: float,
    transport_y: float,
):
    def transport(
        x: np.ndarray,
        y: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        del time

        return (
            np.full_like(
                x,
                transport_x,
                dtype=np.float64,
            ),
            np.full_like(
                y,
                transport_y,
                dtype=np.float64,
            ),
        )

    return transport


def validate_v20_1_compatibility() -> None:
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
        "=== COMPATIBILITÉ V20.1 → V21 ==="
    )

    reference = extract_diagnostics(
        itd_v20_1,
        itd_v20_1.simulate(
            "compatibilite_v20_1",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=curvature_field,
            structural_length=0.5,
        ),
    )

    candidate_result = itd_v21.simulate(
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

    candidate = extract_diagnostics(
        itd_v21,
        candidate_result,
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
            "Le mode eulérien V21 modifie les "
            "résultats historiques de la V20.1."
        )

    if (
        candidate_result[
            "temporal_deformation_mode"
        ]
        != "eulerian"
    ):
        raise RuntimeError(
            "Le mode temporel par défaut "
            "n'est pas eulérien."
        )

    if (
        candidate_result[
            "temporal_deformation_compensated"
        ]
        is not None
    ):
        raise RuntimeError(
            "Le mode eulérien expose à tort une "
            "série compensée."
        )

    print(
        "Compatibilité V20.1 → V21 : VALIDÉE"
    )


def validate_exact_rigid_translation() -> None:
    grid_size = 64
    coordinates, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    del coordinates

    delta_time = 0.125

    transport_x = (
        spacing / delta_time
    )

    transport_y = (
        -2.0 * spacing
        / delta_time
    )

    times = (
        delta_time
        * np.arange(
            9,
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

    result = itd_v21.simulate(
        "translation_rigide_exacte",
        make_translating_velocity(
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
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            make_constant_transport(
                transport_x,
                transport_y,
            )
        ),
    )

    eulerian_index = float(
        result[
            "temporal_deformation_eulerian_index"
        ]
    )

    compensated_index = float(
        result[
            "temporal_deformation_compensated_index"
        ]
    )

    compensated_intervals = np.asarray(
        result[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    maximum_interval = float(
        np.max(
            np.abs(
                compensated_intervals
            )
        )
    )

    print()
    print(
        "=== TRANSLATION RIGIDE EXACTE ==="
    )

    print(
        "Déformation eulérienne  :",
        f"{eulerian_index:.12e}",
    )

    print(
        "Déformation compensée   :",
        f"{compensated_index:.12e}",
    )

    print(
        "Maximum par intervalle  :",
        f"{maximum_interval:.12e}",
    )

    if eulerian_index <= 0.05:
        raise RuntimeError(
            "La variation eulérienne ne détecte "
            "pas le déplacement du motif."
        )

    if (
        compensated_index
        > EXACT_TRANSPORT_TOLERANCE
    ):
        raise RuntimeError(
            "Une translation rigide exacte est "
            "interprétée comme une déformation."
        )

    if (
        maximum_interval
        > EXACT_TRANSPORT_TOLERANCE
    ):
        raise RuntimeError(
            "Un intervalle de translation rigide "
            "possède un résidu excessif."
        )

    if not np.isclose(
        float(
            result[
                "temporal_deformation_index"
            ]
        ),
        compensated_index,
        rtol=0.0,
        atol=0.0,
    ):
        raise RuntimeError(
            "Le mode sélectionné n'utilise pas "
            "l'indice compensé."
        )

    print(
        "Transport rigide séparé de la "
        "déformation : VALIDÉ"
    )


def validate_intrinsic_growth_oracle() -> None:
    grid_size = 64

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    delta_time = 0.10

    transport_x = (
        spacing / delta_time
    )

    transport_y = (
        -spacing / delta_time
    )

    growth_rate = 0.22

    times = (
        delta_time
        * np.arange(
            11,
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

    result = itd_v21.simulate(
        "croissance_intrinseque",
        make_translating_velocity(
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
        temporal_deformation_mode=(
            "transport_compensated"
        ),
        transport_velocity_function=(
            make_constant_transport(
                transport_x,
                transport_y,
            )
        ),
    )

    actual = np.asarray(
        result[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    interval_dt = np.diff(
        times
    )

    expected = (
        2.0
        * np.tanh(
            0.5
            * growth_rate
            * interval_dt
        )
        / interval_dt
    )

    maximum_error = float(
        np.max(
            np.abs(
                actual - expected
            )
        )
    )

    expected_index = float(
        np.sum(
            expected * interval_dt
        )
        / (
            times[-1] - times[0]
        )
    )

    actual_index = float(
        result[
            "temporal_deformation_compensated_index"
        ]
    )

    index_error = abs(
        actual_index
        - expected_index
    )

    eulerian_index = float(
        result[
            "temporal_deformation_eulerian_index"
        ]
    )

    print()
    print(
        "=== CROISSANCE INTRINSÈQUE TRANSPORTÉE ==="
    )

    print(
        "Erreur maximale des intervalles :",
        f"{maximum_error:.6e}",
    )

    print(
        "Indice compensé attendu        :",
        f"{expected_index:.15f}",
    )

    print(
        "Indice compensé obtenu         :",
        f"{actual_index:.15f}",
    )

    print(
        "Indice eulérien                :",
        f"{eulerian_index:.15f}",
    )

    if (
        maximum_error
        > AMPLITUDE_ORACLE_TOLERANCE
    ):
        raise RuntimeError(
            "Le résidu compensé ne reproduit pas "
            "la croissance analytique."
        )

    if (
        index_error
        > AMPLITUDE_ORACLE_TOLERANCE
    ):
        raise RuntimeError(
            "L'indice compensé ne reproduit pas "
            "l'oracle analytique."
        )

    if eulerian_index <= actual_index:
        raise RuntimeError(
            "La mesure eulérienne ne contient pas "
            "la contribution supplémentaire du "
            "transport."
        )

    print(
        "Déformation intrinsèque après transport : "
        "VALIDÉE"
    )


def validate_zero_transport_equivalence() -> None:
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

    growth_rate = 0.18

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=1.0,
        time_steps=times.size,
        characteristic_length=0.5,
    )

    result = itd_v21.simulate(
        "transport_nul",
        make_translating_velocity(
            0.0,
            0.0,
            growth_rate=growth_rate,
        ),
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
            make_constant_transport(
                0.0,
                0.0,
            )
        ),
    )

    eulerian = np.asarray(
        result[
            "temporal_deformation_eulerian_interval"
        ],
        dtype=np.float64,
    )

    compensated = np.asarray(
        result[
            "temporal_deformation_compensated_interval"
        ],
        dtype=np.float64,
    )

    exact = np.array_equal(
        eulerian,
        compensated,
    )

    maximum_error = float(
        np.max(
            np.abs(
                eulerian - compensated
            )
        )
    )

    print()
    print(
        "=== TRANSPORT NUL ==="
    )

    print(
        "Égalité bit à bit :",
        exact,
    )

    print(
        "Erreur maximale   :",
        f"{maximum_error:.6e}",
    )

    if not exact:
        raise RuntimeError(
            "La compensation par un transport nul "
            "modifie le diagnostic eulérien."
        )

    print(
        "Transport nul = mesure eulérienne : VALIDÉ"
    )


def validate_subcell_convergence() -> None:
    grid_sizes = (
        32,
        64,
        128,
        256,
    )

    delta_time = 0.20
    cell_shift_x = 0.37
    cell_shift_y = -0.41

    errors: list[float] = []
    steps: list[float] = []

    print()
    print(
        "=== CONVERGENCE DU TRANSPORT SOUS-MAILLE ==="
    )

    print(
        "grille | pas spatial    | résidu compensé | ordre"
    )

    previous_error: float | None = None
    previous_step: float | None = None

    for grid_size in grid_sizes:
        _, x, y, spacing = (
            build_periodic_grid(
                grid_size
            )
        )

        transport_x = (
            cell_shift_x
            * spacing
            / delta_time
        )

        transport_y = (
            cell_shift_y
            * spacing
            / delta_time
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

        result = itd_v21.simulate(
            f"sous_maille_{grid_size}",
            make_translating_velocity(
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
            temporal_deformation_mode=(
                "transport_compensated"
            ),
            transport_velocity_function=(
                make_constant_transport(
                    transport_x,
                    transport_y,
                )
            ),
        )

        error = float(
            result[
                "temporal_deformation_compensated_index"
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

            order_text = (
                f"{order:.6f}"
            )

        print(
            f"{grid_size:6d} | "
            f"{spacing:14.10f} | "
            f"{error:17.6e} | "
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
            "Le résidu sous-maille ne décroît pas "
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
            "L'interpolation de transport n'atteint "
            "pas l'ordre deux attendu."
        )

    print(
        "Transport sous-maille d'ordre deux : "
        "VALIDÉ"
    )


def validate_multiscale_compensated_profile() -> None:
    grid_size = 48

    _, x, y, spacing = (
        build_periodic_grid(
            grid_size
        )
    )

    delta_time = 0.125

    transport_x = (
        spacing / delta_time
    )

    transport_y = 0.0

    times = (
        delta_time
        * np.arange(
            7,
            dtype=np.float64,
        )
    )

    lengths = np.asarray(
        (
            0.0,
            0.5,
            1.0,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=float(times[-1]),
        time_steps=times.size,
        characteristic_length=0.5,
    )

    velocity = make_translating_velocity(
        transport_x,
        transport_y,
        growth_rate=0.12,
    )

    transport = make_constant_transport(
        transport_x,
        transport_y,
    )

    profile = itd_v21.simulate_multiscale(
        "profil_compense",
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
    )

    signatures = np.asarray(
        profile[
            "structural_signatures"
        ],
        dtype=np.float64,
    )

    structure_indices = np.asarray(
        profile[
            "structure_indices"
        ],
        dtype=np.float64,
    )

    coupled_indices = np.asarray(
        profile[
            "coupled_indices"
        ],
        dtype=np.float64,
    )

    global_error = 0.0

    for index, length in enumerate(
        lengths
    ):
        direct = itd_v21.simulate(
            f"direct_compense_{length:g}",
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
        )

        components = dict(
            direct[
                "component_indices"
            ]
        )

        expected_signature = np.asarray(
            tuple(
                float(
                    components[name]
                )
                for name in (
                    itd_v21.STRUCTURAL_COMPONENT_NAMES
                )
            ),
            dtype=np.float64,
        )

        error = max(
            float(
                np.max(
                    np.abs(
                        signatures[index]
                        - expected_signature
                    )
                )
            ),
            abs(
                structure_indices[index]
                - float(
                    direct[
                        "structure_index"
                    ]
                )
            ),
            abs(
                coupled_indices[index]
                - float(
                    direct[
                        "coupled_index"
                    ]
                )
            ),
        )

        global_error = max(
            global_error,
            error,
        )

    print()
    print(
        "=== PROFIL MULTI-ÉCHELLE COMPENSÉ ==="
    )

    print(
        "Erreur maximale profil/direct :",
        f"{global_error:.6e}",
    )

    if global_error > MULTISCALE_TOLERANCE:
        raise RuntimeError(
            "Le profil multi-échelle compensé "
            "diffère des simulations directes."
        )

    print(
        "Profil multi-échelle compensé : VALIDÉ"
    )


def validate_invalid_modes() -> None:
    print()
    print(
        "=== REJET DES CONFIGURATIONS INVALIDES ==="
    )

    for invalid_mode in (
        "lagrangian",
        "",
        None,
        17,
    ):
        try:
            itd_v21.validate_temporal_deformation_mode(
                invalid_mode
            )
        except ValueError as error:
            print(
                f"Mode {invalid_mode!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un mode temporel invalide "
                "n'a pas été rejeté."
            )

    coordinates = np.linspace(
        -1.0,
        1.0,
        17,
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

    times = np.asarray(
        (
            0.0,
            0.5,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=17,
        domain_min=-1.0,
        domain_max=1.0,
        duration=0.5,
        time_steps=2,
        characteristic_length=0.5,
    )

    try:
        itd_v21.simulate(
            "transport_fini_interdit",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
            boundary_mode="finite",
            temporal_deformation_mode=(
                "transport_compensated"
            ),
            transport_velocity_function=(
                make_constant_transport(
                    0.0,
                    0.0,
                )
            ),
        )
    except ValueError as error:
        print(
            "Frontière finie : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "La compensation de transport a accepté "
            "une frontière finie sans convention."
        )

    _, periodic_x, periodic_y, periodic_spacing = (
        build_periodic_grid(
            16
        )
    )

    periodic_cfg = Config(
        grid_size=16,
        domain_min=0.0,
        domain_max=DOMAIN_LENGTH,
        duration=0.5,
        time_steps=2,
        characteristic_length=0.5,
    )

    try:
        itd_v21.simulate(
            "transport_absent",
            make_translating_velocity(
                0.2,
                0.0,
            ),
            periodic_x,
            periodic_y,
            times,
            periodic_spacing,
            periodic_cfg,
            curvature_function=zero_curvature,
            boundary_mode="periodic",
            temporal_deformation_mode=(
                "transport_compensated"
            ),
            transport_velocity_function=None,
        )
    except ValueError as error:
        print(
            "Champ absent    : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Le mode compensé a accepté l'absence "
            "de champ de transport."
        )

    print(
        "Contrôle des configurations V21 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION TRANSPORT CONTRE "
        "DÉFORMATION — ITD V21 ==="
    )

    validate_v20_1_compatibility()
    validate_exact_rigid_translation()
    validate_intrinsic_growth_oracle()
    validate_zero_transport_equivalence()
    validate_subcell_convergence()
    validate_multiscale_compensated_profile()
    validate_invalid_modes()

    print()
    print(
        "Compatibilité V20.1 → V21           : VALIDÉE"
    )
    print(
        "Variation eulérienne conservée      : VALIDÉE"
    )
    print(
        "Translation rigide compensée        : VALIDÉE"
    )
    print(
        "Déformation intrinsèque récupérée   : VALIDÉE"
    )
    print(
        "Transport nul identique à Euler     : VALIDÉ"
    )
    print(
        "Interpolation périodique ordre deux : VALIDÉE"
    )
    print(
        "Profil multi-échelle compensé       : VALIDÉ"
    )


if __name__ == "__main__":
    main()
