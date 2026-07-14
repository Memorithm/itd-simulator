#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

import itd_v18
import itd_v19
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13

INTENSITY_ORDER_MINIMUM = 1.90
INTENSITY_EXTRAPOLATION_TOLERANCE = 5.0e-6

ROUGHNESS_ORDER_MINIMUM = 1.90
ROUGHNESS_EXTRAPOLATION_TOLERANCE = 5.0e-6

MANUFACTURED_GRID_SIZES = (
    32,
    64,
    128,
)

REAL_GRID_SIZES = (
    33,
    65,
    129,
)

REAL_TIME_STEPS = (
    17,
    33,
    65,
)

STRUCTURAL_LENGTHS = np.asarray(
    (
        0.0,
        0.25,
        0.50,
        1.00,
        2.00,
    ),
    dtype=np.float64,
)

OUTPUT_DIRECTORY = Path(
    "itd_v19_results"
)

REPORT_PATH = (
    OUTPUT_DIRECTORY
    / "resolution_study.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIRECTORY
    / "resolution_study_summary.json"
)


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def validate_v18_compatibility() -> None:
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
        "=== COMPATIBILITÉ V18 → V19 ==="
    )

    reference = itd_v18.simulate(
        "compatibilite_v18",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=curvature_field,
        structural_length=0.5,
    )

    candidate = itd_v19.simulate(
        "compatibilite_v19",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=curvature_field,
        structural_length=0.5,
    )

    reference_diagnostics = (
        itd_v18.extract_single_scale_diagnostics(
            reference
        )
        if hasattr(
            itd_v18,
            "extract_single_scale_diagnostics",
        )
        else {
            "intensity_index": float(
                reference["intensity_index"]
            ),
            "structure_index": float(
                reference["structure_index"]
            ),
            "coupled_index": float(
                reference["coupled_index"]
            ),
            "temporal_deformation_index": float(
                reference[
                    "temporal_deformation_index"
                ]
            ),
            **{
                f"component:{name}": float(value)
                for name, value in dict(
                    reference[
                        "component_indices"
                    ]
                ).items()
            },
        }
    )

    candidate_diagnostics = (
        itd_v19.extract_single_scale_diagnostics(
            candidate
        )
    )

    errors = (
        scaled_error(
            candidate_diagnostics[key],
            reference_diagnostics[key],
        )
        for key in reference_diagnostics
    )

    maximum_error = max(errors)

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V19 modifie les résultats "
            "historiques de la V18."
        )

    print(
        "Compatibilité V18 → V19 : VALIDÉE"
    )


def validate_richardson_classification() -> None:
    resolved = itd_v19.richardson_triplet(
        1.25,
        1.25,
        1.25,
    )

    asymptotic = itd_v19.richardson_triplet(
        1.0,
        0.75,
        0.6875,
    )

    non_monotone = (
        itd_v19.richardson_triplet(
            1.0,
            0.8,
            0.9,
        )
    )

    degenerate = itd_v19.richardson_triplet(
        1.0,
        1.0,
        0.9,
    )

    print()
    print(
        "=== CLASSIFICATION DES TRIPLETS ==="
    )

    print(
        "Triplet résolu       :",
        resolved["status"],
    )

    print(
        "Triplet asymptotique :",
        asymptotic["status"],
    )

    print(
        "Triplet non monotone :",
        non_monotone["status"],
    )

    print(
        "Triplet dégénéré     :",
        degenerate["status"],
    )

    if resolved["status"] != "resolved":
        raise RuntimeError(
            "Un triplet identique n'a pas été "
            "classé comme résolu."
        )

    if (
        resolved["estimated_fine_error"]
        != 0.0
    ):
        raise RuntimeError(
            "Un triplet résolu possède une "
            "erreur non nulle."
        )

    if asymptotic["status"] != "asymptotic":
        raise RuntimeError(
            "Un triplet asymptotique n'a pas été "
            "correctement classé."
        )

    if abs(
        float(
            asymptotic["observed_order"]
        )
        - 2.0
    ) > 1.0e-14:
        raise RuntimeError(
            "L'ordre analytique du triplet test "
            "n'est pas égal à deux."
        )

    if (
        non_monotone["status"]
        != "non_monotone"
    ):
        raise RuntimeError(
            "Une suite oscillante n'a pas été "
            "détectée."
        )

    if degenerate["status"] != "degenerate":
        raise RuntimeError(
            "Un triplet partiellement constant "
            "n'a pas été classé comme dégénéré."
        )

    print(
        "Classification de convergence : VALIDÉE"
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


def periodic_wave_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    del y
    del time

    return (
        np.zeros_like(
            x,
            dtype=np.float64,
        ),
        np.sin(x),
    )


def build_manufactured_profiles() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    profiles: list[
        dict[str, object]
    ] = []

    for grid_size in (
        MANUFACTURED_GRID_SIZES
    ):
        coordinates = np.linspace(
            0.0,
            2.0 * np.pi,
            grid_size,
            endpoint=False,
            dtype=np.float64,
        )

        spacing = (
            2.0 * np.pi
            / grid_size
        )

        x, y = np.meshgrid(
            coordinates,
            coordinates,
            indexing="xy",
        )

        times = np.asarray(
            (
                0.0,
                1.0,
            ),
            dtype=np.float64,
        )

        cfg = Config(
            grid_size=grid_size,
            domain_min=0.0,
            domain_max=2.0 * np.pi,
            duration=1.0,
            time_steps=2,
            characteristic_length=0.5,
        )

        profiles.append(
            itd_v19.simulate_multiscale(
                f"onde_periodique_{grid_size}",
                periodic_wave_velocity,
                x,
                y,
                times,
                spacing,
                cfg,
                structural_lengths=(
                    STRUCTURAL_LENGTHS
                ),
                curvature_function=zero_curvature,
                boundary_mode="periodic",
            )
        )

    return (
        profiles[0],
        profiles[1],
        profiles[2],
    )


def validate_manufactured_solution() -> None:
    coarse, medium, fine = (
        build_manufactured_profiles()
    )

    intensity_estimate = (
        itd_v19.richardson_triplet(
            float(
                coarse["intensity_index"]
            ),
            float(
                medium["intensity_index"]
            ),
            float(
                fine["intensity_index"]
            ),
        )
    )

    raw_roughness_arrays = tuple(
        np.asarray(
            profile[
                "raw_roughness_indices"
            ],
            dtype=np.float64,
        )
        for profile in (
            coarse,
            medium,
            fine,
        )
    )

    length_index = int(
        np.where(
            STRUCTURAL_LENGTHS == 1.0
        )[0][0]
    )

    roughness_estimate = (
        itd_v19.richardson_triplet(
            raw_roughness_arrays[0][
                length_index
            ],
            raw_roughness_arrays[1][
                length_index
            ],
            raw_roughness_arrays[2][
                length_index
            ],
        )
    )

    exact_intensity = 0.5

    exact_raw_roughness = (
        2.0
        * np.sqrt(2.0)
        / np.pi
    )

    intensity_extrapolation_error = abs(
        float(
            intensity_estimate[
                "extrapolated_limit"
            ]
        )
        - exact_intensity
    )

    roughness_extrapolation_error = abs(
        float(
            roughness_estimate[
                "extrapolated_limit"
            ]
        )
        - exact_raw_roughness
    )

    print()
    print(
        "=== ORACLE PÉRIODIQUE DE RICHARDSON ==="
    )

    print(
        "Intensités :",
        [
            float(
                profile["intensity_index"]
            )
            for profile in (
                coarse,
                medium,
                fine,
            )
        ],
    )

    print(
        "Ordre intensité observé :",
        f"{float(intensity_estimate['observed_order']):.9f}",
    )

    print(
        "Limite intensité estimée:",
        f"{float(intensity_estimate['extrapolated_limit']):.15f}",
    )

    print(
        "Erreur contre 1/2       :",
        f"{intensity_extrapolation_error:.6e}",
    )

    print(
        "Ordre rugosité observé  :",
        f"{float(roughness_estimate['observed_order']):.9f}",
    )

    print(
        "Limite rugosité estimée :",
        f"{float(roughness_estimate['extrapolated_limit']):.15f}",
    )

    print(
        "Erreur contre 2√2/π     :",
        f"{roughness_extrapolation_error:.6e}",
    )

    if (
        intensity_estimate["status"]
        != "asymptotic"
    ):
        raise RuntimeError(
            "L'intensité manufacturée n'est pas "
            "dans le régime asymptotique attendu."
        )

    if (
        float(
            intensity_estimate[
                "observed_order"
            ]
        )
        < INTENSITY_ORDER_MINIMUM
    ):
        raise RuntimeError(
            "L'ordre observé de l'intensité est "
            "inférieur à deux."
        )

    if (
        intensity_extrapolation_error
        > INTENSITY_EXTRAPOLATION_TOLERANCE
    ):
        raise RuntimeError(
            "L'extrapolation de l'intensité "
            "est trop éloignée de la valeur exacte."
        )

    if (
        roughness_estimate["status"]
        != "asymptotic"
    ):
        raise RuntimeError(
            "La rugosité manufacturée n'est pas "
            "dans le régime asymptotique attendu."
        )

    if (
        float(
            roughness_estimate[
                "observed_order"
            ]
        )
        < ROUGHNESS_ORDER_MINIMUM
    ):
        raise RuntimeError(
            "L'ordre observé de la rugosité est "
            "inférieur à deux."
        )

    if (
        roughness_extrapolation_error
        > ROUGHNESS_EXTRAPOLATION_TOLERANCE
    ):
        raise RuntimeError(
            "L'extrapolation de la rugosité "
            "est trop éloignée de 2√2/π."
        )

    rows = (
        itd_v19.analyze_multiscale_profile_triplet(
            coarse,
            medium,
            fine,
        )
    )

    summary = (
        itd_v19.summarize_convergence_rows(
            rows
        )
    )

    print(
        "Résumé de l'oracle :",
        summary,
    )

    if summary["row_count"] != (
        2
        + len(STRUCTURAL_LENGTHS)
        * (
            len(
                itd_v19.STRUCTURAL_COMPONENT_NAMES
            )
            + 3
        )
    ):
        raise RuntimeError(
            "Le nombre de diagnostics "
            "multi-échelles est incorrect."
        )

    print(
        "Oracle de Richardson : VALIDÉ"
    )


def build_real_profile(
    grid_size: int,
    time_steps: int,
) -> dict[str, object]:
    domain_min = -2.0
    domain_max = 2.0
    duration = 2.5

    coordinates = np.linspace(
        domain_min,
        domain_max,
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

    parameter = np.linspace(
        0.0,
        1.0,
        time_steps,
        dtype=np.float64,
    )

    times = (
        duration
        * parameter**1.25
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=domain_min,
        domain_max=domain_max,
        duration=duration,
        time_steps=time_steps,
        characteristic_length=0.5,
    )

    return itd_v19.simulate_multiscale(
        f"etude_resolution_{grid_size}",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=(
            STRUCTURAL_LENGTHS
        ),
        curvature_function=curvature_field,
        boundary_mode="finite",
    )


def write_resolution_report(
    rows: tuple[
        dict[str, object],
        ...
    ],
    summary: dict[str, object],
) -> None:
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    field_names = (
        "metric",
        "structural_length",
        "status",
        "coarse",
        "medium",
        "fine",
        "refinement_ratio",
        "coarse_medium_difference",
        "medium_fine_difference",
        "observed_order",
        "convergence_ratio",
        "extrapolated_limit",
        "estimated_fine_error",
        "estimated_relative_fine_error",
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=field_names,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row.get(field)
                    for field in field_names
                }
            )

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def validate_real_resolution_report() -> None:
    profiles = tuple(
        build_real_profile(
            grid_size,
            time_steps,
        )
        for grid_size, time_steps in zip(
            REAL_GRID_SIZES,
            REAL_TIME_STEPS,
            strict=True,
        )
    )

    rows = (
        itd_v19.analyze_multiscale_profile_triplet(
            profiles[0],
            profiles[1],
            profiles[2],
        )
    )

    summary = (
        itd_v19.summarize_convergence_rows(
            rows
        )
    )

    write_resolution_report(
        rows,
        summary,
    )

    print()
    print(
        "=== ÉTUDE DU SCÉNARIO MULTI-VORTEX ==="
    )

    print(
        "Grilles spatiales :",
        REAL_GRID_SIZES,
    )

    print(
        "Grilles temporelles:",
        REAL_TIME_STEPS,
    )

    print(
        "Nombre de diagnostics:",
        summary["row_count"],
    )

    print(
        "Statuts :",
        summary["status_counts"],
    )

    print(
        "Ordre minimal fini :",
        summary[
            "minimum_finite_order"
        ],
    )

    print(
        "Ordre maximal fini :",
        summary[
            "maximum_finite_order"
        ],
    )

    print(
        "Erreur relative maximale estimée :",
        summary[
            "maximum_estimated_relative_fine_error"
        ],
    )

    print(
        "Rapport CSV :",
        REPORT_PATH.resolve(),
    )

    print(
        "Résumé JSON:",
        SUMMARY_PATH.resolve(),
    )

    if not REPORT_PATH.is_file():
        raise RuntimeError(
            "Le rapport CSV n'a pas été créé."
        )

    if not SUMMARY_PATH.is_file():
        raise RuntimeError(
            "Le résumé JSON n'a pas été créé."
        )

    if summary["row_count"] <= 0:
        raise RuntimeError(
            "L'étude de résolution ne contient "
            "aucun diagnostic."
        )

    print(
        "Rapport de résolution réel : VALIDÉ"
    )


def validate_invalid_inputs() -> None:
    print()
    print(
        "=== REJET DES PARAMÈTRES INVALIDES ==="
    )

    for invalid_ratio in (
        1.0,
        0.5,
        0.0,
        -2.0,
        np.nan,
        np.inf,
        "deux",
        None,
    ):
        try:
            itd_v19.validate_refinement_ratio(
                invalid_ratio
            )
        except ValueError as error:
            print(
                f"Rapport {invalid_ratio!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un rapport de raffinement invalide "
                "n'a pas été rejeté."
            )

    for invalid_tolerance in (
        -1.0,
        np.nan,
        np.inf,
        "tolérance",
        None,
    ):
        try:
            itd_v19.validate_convergence_tolerance(
                invalid_tolerance
            )
        except ValueError as error:
            print(
                f"Tolérance {invalid_tolerance!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une tolérance invalide "
                "n'a pas été rejetée."
            )

    for triplet in (
        (
            np.nan,
            1.0,
            1.0,
        ),
        (
            1.0,
            np.inf,
            1.0,
        ),
        (
            1.0,
            1.0,
            "fin",
        ),
    ):
        try:
            itd_v19.richardson_triplet(
                *triplet
            )
        except ValueError as error:
            print(
                f"Triplet {triplet!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un triplet invalide "
                "n'a pas été rejeté."
            )

    print(
        "Contrôle des paramètres V19 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE LA CERTIFICATION "
        "NUMÉRIQUE — ITD V19 ==="
    )

    validate_v18_compatibility()
    validate_richardson_classification()
    validate_manufactured_solution()
    validate_real_resolution_report()
    validate_invalid_inputs()

    print()
    print(
        "Compatibilité V18 → V19             : VALIDÉE"
    )
    print(
        "Classification des régimes          : VALIDÉE"
    )
    print(
        "Ordre deux sur solution manufacturée: VALIDÉ"
    )
    print(
        "Extrapolation vers la limite exacte : VALIDÉE"
    )
    print(
        "Profil multi-échelle certifiable    : VALIDÉ"
    )
    print(
        "Rapport de résolution CSV/JSON      : VALIDÉ"
    )


if __name__ == "__main__":
    main()
