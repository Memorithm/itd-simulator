#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v14_1
import itd_v15
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
ORACLE_TOLERANCE = 8.0e-12
TRANSLATION_TOLERANCE = 8.0e-13
DILATION_TOLERANCE = 1.0e-12

TEMPORAL_RATE = 0.20

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)

SPATIAL_COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
)

SCALAR_RESULTS = (
    "intensity_index",
    "structure_index",
    "coupled_index",
    "temporal_deformation_index",
)


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def extract_results(
    result: dict[str, object],
) -> dict[str, float]:
    extracted = {
        name: float(result[name])
        for name in SCALAR_RESULTS
    }

    components = {
        str(name): float(value)
        for name, value in dict(
            result["component_indices"]
        ).items()
    }

    for component in COMPONENTS:
        extracted[
            f"component:{component}"
        ] = components[component]

    return extracted


def build_spatial_grid(
    grid_size: int = 41,
) -> tuple[
    np.ndarray,
    np.ndarray,
    float,
]:
    coordinates = np.linspace(
        -1.0,
        1.0,
        grid_size,
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

    return x, y, spacing


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


def exponential_rotation_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    amplitude = float(
        np.exp(
            TEMPORAL_RATE * time
        )
    )

    return (
        -0.5 * amplitude * y,
        0.5 * amplitude * x,
    )


def linear_amplitude_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    amplitude = (
        1.0
        + 0.30 * time
    )

    return (
        -0.5 * amplitude * y,
        0.5 * amplitude * x,
    )


def validate_v14_1_compatibility() -> None:
    cfg = Config(
        grid_size=65,
        time_steps=81,
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
        "=== COMPATIBILITÉ V14.1 → V15 ==="
    )

    maximum_error = 0.0

    for name, velocity_function in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        reference = extract_results(
            itd_v14_1.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        candidate = extract_results(
            itd_v15.simulate(
                name,
                velocity_function,
                x,
                y,
                times,
                spacing,
                cfg,
            )
        )

        error = max(
            scaled_error(
                candidate[key],
                reference[key],
            )
            for key in reference
        )

        maximum_error = max(
            maximum_error,
            error,
        )

        print(
            f"{name:24s}: "
            f"erreur maximale={error:.6e}"
        )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V15 n'est pas compatible "
            "avec la V14.1."
        )

    print(
        "Compatibilité V14.1 → V15 : VALIDÉE"
    )


def validate_temporal_metadata() -> None:
    regular = itd_v15.TemporalGeometry(
        np.linspace(
            1.0,
            3.0,
            9,
            dtype=np.float64,
        )
    )

    irregular_times = np.asarray(
        (
            0.0,
            0.0625,
            0.1875,
            0.5,
            1.0,
            1.75,
            2.5,
        ),
        dtype=np.float64,
    )

    irregular = itd_v15.TemporalGeometry(
        irregular_times
    )

    print()
    print(
        "=== MÉTADONNÉES TEMPORELLES ==="
    )

    print(
        "Grille régulière   :",
        regular.as_dict(),
    )

    print(
        "Grille irrégulière :",
        irregular.as_dict(),
    )

    if not regular.uniform:
        raise RuntimeError(
            "Une grille uniforme n'a pas "
            "été reconnue."
        )

    if irregular.uniform:
        raise RuntimeError(
            "Une grille irrégulière a été "
            "classée comme uniforme."
        )

    if irregular.sample_count != 7:
        raise RuntimeError(
            "Le nombre d'échantillons temporels "
            "est incorrect."
        )

    if irregular.interval_count != 6:
        raise RuntimeError(
            "Le nombre d'intervalles temporels "
            "est incorrect."
        )

    if irregular.duration != 2.5:
        raise RuntimeError(
            "La durée temporelle est incorrecte."
        )

    if irregular.minimum_dt != 0.0625:
        raise RuntimeError(
            "Le pas temporel minimal est incorrect."
        )

    if irregular.maximum_dt != 0.75:
        raise RuntimeError(
            "Le pas temporel maximal est incorrect."
        )

    print(
        "Métadonnées temporelles : VALIDÉES"
    )


def validate_exponential_deformation_oracle() -> None:
    x, y, spacing = build_spatial_grid()

    times = np.asarray(
        (
            0.0,
            0.0625,
            0.1875,
            0.5,
            1.0,
            1.75,
            2.5,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=x.shape[1],
        time_steps=times.size,
    )

    result = itd_v15.simulate(
        "oracle_exponentiel",
        exponential_rotation_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        boundary_mode="finite",
    )

    interval_dt = np.diff(times)

    expected_interval = (
        2.0
        * np.tanh(
            0.5
            * TEMPORAL_RATE
            * interval_dt
        )
        / interval_dt
    )

    actual_interval = np.asarray(
        result["temporal_deformation_interval"],
        dtype=np.float64,
    )

    interval_error = float(
        np.max(
            np.abs(
                actual_interval
                - expected_interval
            )
        )
    )

    expected_index = float(
        np.sum(
            expected_interval
            * interval_dt
        )
        / (
            times[-1]
            - times[0]
        )
    )

    actual_index = float(
        result["temporal_deformation_index"]
    )

    index_error = abs(
        actual_index
        - expected_index
    )

    print()
    print(
        "=== ORACLE EXPONENTIEL DE DÉFORMATION ==="
    )

    print(
        "Erreur maximale des intervalles :",
        f"{interval_error:.6e}",
    )

    print(
        "Indice attendu                  :",
        f"{expected_index:.15f}",
    )

    print(
        "Indice obtenu                   :",
        f"{actual_index:.15f}",
    )

    print(
        "Erreur de l'indice              :",
        f"{index_error:.6e}",
    )

    if interval_error > ORACLE_TOLERANCE:
        raise RuntimeError(
            "L'oracle analytique des intervalles "
            "temporels n'est pas respecté."
        )

    if index_error > ORACLE_TOLERANCE:
        raise RuntimeError(
            "L'oracle analytique de l'indice "
            "temporel n'est pas respecté."
        )

    print(
        "Oracle temporel exponentiel : VALIDÉ"
    )


def validate_time_translation_invariance() -> None:
    x, y, spacing = build_spatial_grid()

    base_times = np.asarray(
        (
            0.0,
            0.125,
            0.375,
            0.75,
            1.25,
            2.0,
        ),
        dtype=np.float64,
    )

    shift = 8.0

    shifted_times = (
        base_times + shift
    )

    cfg = Config(
        grid_size=x.shape[1],
        time_steps=base_times.size,
    )

    def shifted_velocity(
        x_value: np.ndarray,
        y_value: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        return exponential_rotation_velocity(
            x_value,
            y_value,
            time - shift,
        )

    base = extract_results(
        itd_v15.simulate(
            "translation_reference",
            exponential_rotation_velocity,
            x,
            y,
            base_times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
        )
    )

    shifted = extract_results(
        itd_v15.simulate(
            "translation_decalee",
            shifted_velocity,
            x,
            y,
            shifted_times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
        )
    )

    errors = {
        key: scaled_error(
            shifted[key],
            base[key],
        )
        for key in base
    }

    maximum_error = max(
        errors.values()
    )

    worst_metric = max(
        errors,
        key=errors.get,
    )

    print()
    print(
        "=== INVARIANCE PAR TRANSLATION DU TEMPS ==="
    )

    print(
        "Décalage temporel :",
        shift,
    )

    print(
        "Erreur maximale   :",
        f"{maximum_error:.6e}",
    )

    print(
        "Métrique sensible :",
        worst_metric,
    )

    if maximum_error > TRANSLATION_TOLERANCE:
        raise RuntimeError(
            "La description dynamique dépend "
            "de l'origine absolue du temps."
        )

    print(
        "Translation de l'origine temporelle : "
        "VALIDÉE"
    )


def validate_time_dilation_covariance() -> None:
    x, y, spacing = build_spatial_grid()

    base_times = np.asarray(
        (
            0.0,
            0.125,
            0.375,
            0.75,
            1.25,
            2.0,
        ),
        dtype=np.float64,
    )

    dilation = 4.0

    dilated_times = (
        dilation * base_times
    )

    cfg = Config(
        grid_size=x.shape[1],
        time_steps=base_times.size,
    )

    spatial_only_weights = (
        1.0,
        1.0,
        1.0,
        1.0,
        0.0,
    )

    def dilated_velocity(
        x_value: np.ndarray,
        y_value: np.ndarray,
        time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        return exponential_rotation_velocity(
            x_value,
            y_value,
            time / dilation,
        )

    reference = itd_v15.simulate(
        "dilatation_reference",
        exponential_rotation_velocity,
        x,
        y,
        base_times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        structural_weights=spatial_only_weights,
    )

    dilated = itd_v15.simulate(
        "dilatation_temporelle",
        dilated_velocity,
        x,
        y,
        dilated_times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
        structural_weights=spatial_only_weights,
    )

    invariant_names = (
        "intensity_index",
        "structure_index",
        "coupled_index",
    )

    invariant_errors = {
        name: scaled_error(
            float(dilated[name]),
            float(reference[name]),
        )
        for name in invariant_names
    }

    reference_components = dict(
        reference["component_indices"]
    )

    dilated_components = dict(
        dilated["component_indices"]
    )

    for component in SPATIAL_COMPONENTS:
        invariant_errors[
            f"component:{component}"
        ] = scaled_error(
            float(
                dilated_components[component]
            ),
            float(
                reference_components[component]
            ),
        )

    maximum_invariant_error = max(
        invariant_errors.values()
    )

    raw_reference = np.asarray(
        reference[
            "temporal_deformation_interval"
        ],
        dtype=np.float64,
    )

    raw_dilated = np.asarray(
        dilated[
            "temporal_deformation_interval"
        ],
        dtype=np.float64,
    )

    interval_scaling_error = float(
        np.max(
            np.abs(
                dilation
                * raw_dilated
                - raw_reference
            )
        )
    )

    reference_index = float(
        reference[
            "temporal_deformation_index"
        ]
    )

    dilated_index = float(
        dilated[
            "temporal_deformation_index"
        ]
    )

    index_scaling_error = abs(
        dilation
        * dilated_index
        - reference_index
    )

    print()
    print(
        "=== COVARIANCE SOUS DILATATION DU TEMPS ==="
    )

    print(
        "Facteur de dilatation            :",
        dilation,
    )

    print(
        "Erreur des quantités invariantes :",
        f"{maximum_invariant_error:.6e}",
    )

    print(
        "Erreur des vitesses d'intervalle :",
        f"{interval_scaling_error:.6e}",
    )

    print(
        "Erreur de l'indice de déformation:",
        f"{index_scaling_error:.6e}",
    )

    if (
        maximum_invariant_error
        > DILATION_TOLERANCE
    ):
        raise RuntimeError(
            "Une quantité purement spatiale dépend "
            "de l'échelle temporelle."
        )

    if (
        interval_scaling_error
        > DILATION_TOLERANCE
    ):
        raise RuntimeError(
            "La vitesse de déformation ne suit pas "
            "la loi inverse sous dilatation."
        )

    if (
        index_scaling_error
        > DILATION_TOLERANCE
    ):
        raise RuntimeError(
            "L'indice temporel ne suit pas "
            "la loi inverse sous dilatation."
        )

    print(
        "Loi C_D(a t) = C_D(t) / a : VALIDÉE"
    )


def validate_irregular_temporal_quadrature() -> None:
    x, y, spacing = build_spatial_grid(
        grid_size=17
    )

    duration = 2.0
    amplitude_slope = 0.30

    exact_average = (
        1.0
        + amplitude_slope * duration
        + (
            amplitude_slope**2
            * duration**2
            / 3.0
        )
    )

    sample_counts = (
        9,
        17,
        33,
        65,
    )

    errors: list[float] = []
    maximum_steps: list[float] = []

    print()
    print(
        "=== CONVERGENCE TEMPORELLE SUR "
        "GRILLES IRRÉGULIÈRES ==="
    )

    print(
        "instants | max(dt)        | "
        "erreur intensité | ordre"
    )

    previous_error: float | None = None
    previous_step: float | None = None

    for sample_count in sample_counts:
        parameter = np.linspace(
            0.0,
            1.0,
            sample_count,
            dtype=np.float64,
        )

        times = (
            duration
            * parameter**1.4
        )

        maximum_step = float(
            np.max(
                np.diff(times)
            )
        )

        cfg = Config(
            grid_size=x.shape[1],
            time_steps=sample_count,
        )

        result = itd_v15.simulate(
            f"quadrature_{sample_count}",
            linear_amplitude_velocity,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=zero_curvature,
        )

        error = abs(
            float(
                result["intensity_index"]
            )
            - exact_average
        )

        errors.append(error)
        maximum_steps.append(
            maximum_step
        )

        if previous_error is None:
            order_text = "—"
        else:
            order = float(
                np.log(
                    previous_error / error
                )
                / np.log(
                    previous_step
                    / maximum_step
                )
            )

            order_text = f"{order:.6f}"

        print(
            f"{sample_count:8d} | "
            f"{maximum_step:14.10f} | "
            f"{error:16.6e} | "
            f"{order_text}"
        )

        previous_error = error
        previous_step = maximum_step

    if not all(
        current < previous
        for previous, current in zip(
            errors,
            errors[1:],
        )
    ):
        raise RuntimeError(
            "L'erreur de quadrature temporelle "
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
                    maximum_steps[index - 1]
                    / maximum_steps[index]
                )
            )
        )

    if min(final_orders) < 1.8:
        raise RuntimeError(
            "La quadrature temporelle irrégulière "
            "n'atteint pas l'ordre deux attendu."
        )

    if errors[-1] > 3.0e-5:
        raise RuntimeError(
            "L'erreur temporelle finale "
            "est trop élevée."
        )

    print(
        "Quadrature temporelle irrégulière "
        "d'ordre deux : VALIDÉE"
    )


def validate_simulation_metadata() -> None:
    x, y, spacing = build_spatial_grid(
        grid_size=17
    )

    times = np.asarray(
        (
            1.0,
            1.125,
            1.5,
            2.0,
            2.75,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=x.shape[1],
        time_steps=times.size,
    )

    result = itd_v15.simulate(
        "metadata_temporelles",
        exponential_rotation_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=zero_curvature,
    )

    metadata = dict(
        result["temporal_geometry"]
    )

    print()
    print(
        "=== MÉTADONNÉES DE SIMULATION ==="
    )

    for key, value in metadata.items():
        print(
            f"{key:16s}: {value}"
        )

    expected = itd_v15.TemporalGeometry(
        times
    ).as_dict()

    if metadata != expected:
        raise RuntimeError(
            "Les métadonnées temporelles du résultat "
            "ne correspondent pas à la grille."
        )

    print(
        "Métadonnées exportées : VALIDÉES"
    )


def validate_invalid_time_grids() -> None:
    invalid_grids = (
        (),
        (0.0,),
        (0.0, 0.0),
        (0.0, 1.0, 1.0),
        (0.0, 2.0, 1.0),
        (0.0, np.nan, 1.0),
        (0.0, np.inf, 1.0),
        [[0.0, 1.0]],
        "0, 1",
        None,
    )

    print()
    print(
        "=== REJET DES GRILLES TEMPORELLES INVALIDES ==="
    )

    for invalid in invalid_grids:
        try:
            itd_v15.normalize_time_grid(
                invalid
            )
        except ValueError as error:
            print(
                f"Rejet {invalid!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une grille temporelle invalide "
                "n'a pas été rejetée."
            )

    print(
        "Contrôle des grilles temporelles : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE LA GÉOMÉTRIE "
        "TEMPORELLE — ITD V15 ==="
    )

    validate_v14_1_compatibility()
    validate_temporal_metadata()
    validate_exponential_deformation_oracle()
    validate_time_translation_invariance()
    validate_time_dilation_covariance()
    validate_irregular_temporal_quadrature()
    validate_simulation_metadata()
    validate_invalid_time_grids()

    print()
    print(
        "Compatibilité V14.1 → V15          : VALIDÉE"
    )
    print(
        "Temps irréguliers                   : VALIDÉS"
    )
    print(
        "Oracle analytique de déformation    : VALIDÉ"
    )
    print(
        "Translation de l'origine temporelle : VALIDÉE"
    )
    print(
        "Dilatation temporelle               : VALIDÉE"
    )
    print(
        "Quadrature temporelle d'ordre deux  : VALIDÉE"
    )
    print(
        "Métadonnées temporelles explicites  : VALIDÉES"
    )


if __name__ == "__main__":
    main()
