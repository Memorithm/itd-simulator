#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

import itd_v19
import itd_v20
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
MANUFACTURED_ORDER_MINIMUM = 1.90
MANUFACTURED_LIMIT_TOLERANCE = 2.0e-6

RESOLUTIONS = (
    33,
    65,
    129,
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
    "itd_v20_results"
)

REPORT_PATH = (
    OUTPUT_DIRECTORY
    / "decoupled_resolution_study.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIRECTORY
    / "decoupled_resolution_summary.json"
)


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def extract_diagnostics(
    result: dict[str, object],
) -> dict[str, float]:
    return (
        itd_v20.extract_single_scale_diagnostics(
            result
        )
    )


def validate_v19_compatibility() -> None:
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
        "=== COMPATIBILITÉ V19 → V20 ==="
    )

    reference = extract_diagnostics(
        itd_v19.simulate(
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
    )

    candidate = extract_diagnostics(
        itd_v20.simulate(
            "compatibilite_v20",
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
            "La V20 modifie les résultats "
            "historiques de la V19."
        )

    print(
        "Compatibilité V19 → V20 : VALIDÉE"
    )


def validate_combination_classification() -> None:
    common = {
        "metric": "test",
        "structural_length": None,
        "coarse": 1.0,
        "medium": 0.75,
        "fine": 0.6875,
        "refinement_ratio": 2.0,
        "coarse_medium_difference": 0.25,
        "medium_fine_difference": 0.0625,
        "observed_order": 2.0,
        "convergence_ratio": 0.25,
        "extrapolated_limit": (
            2.0 / 3.0
        ),
        "estimated_fine_error": (
            1.0 / 48.0
        ),
        "estimated_relative_fine_error": (
            1.0 / 32.0
        ),
    }

    certified = (
        itd_v20.combine_decoupled_convergence_rows(
            (
                {
                    **common,
                    "status": "asymptotic",
                },
            ),
            (
                {
                    **common,
                    "status": "asymptotic",
                },
            ),
        )
    )

    partial = (
        itd_v20.combine_decoupled_convergence_rows(
            (
                {
                    **common,
                    "status": "resolved",
                    "estimated_fine_error": 0.0,
                },
            ),
            (
                {
                    **common,
                    "status": "non_monotone",
                    "estimated_fine_error": None,
                    "estimated_relative_fine_error": None,
                    "extrapolated_limit": None,
                },
            ),
        )
    )

    uncertain = (
        itd_v20.combine_decoupled_convergence_rows(
            (
                {
                    **common,
                    "status": "degenerate",
                    "estimated_fine_error": None,
                    "estimated_relative_fine_error": None,
                    "extrapolated_limit": None,
                },
            ),
            (
                {
                    **common,
                    "status": "non_monotone",
                    "estimated_fine_error": None,
                    "estimated_relative_fine_error": None,
                    "extrapolated_limit": None,
                },
            ),
        )
    )

    print()
    print(
        "=== CLASSIFICATION DU BUDGET D'ERREUR ==="
    )

    print(
        "Deux axes estimables :",
        certified[0][
            "certification_status"
        ],
    )

    print(
        "Un seul axe estimable:",
        partial[0][
            "certification_status"
        ],
    )

    print(
        "Aucun axe estimable  :",
        uncertain[0][
            "certification_status"
        ],
    )

    if (
        certified[0][
            "certification_status"
        ]
        != "certified"
    ):
        raise RuntimeError(
            "Un budget complet n'a pas été "
            "classé comme certifié."
        )

    if (
        partial[0][
            "certification_status"
        ]
        != "partial"
    ):
        raise RuntimeError(
            "Un budget incomplet n'a pas été "
            "classé comme partiel."
        )

    if (
        uncertain[0][
            "certification_status"
        ]
        != "uncertain"
    ):
        raise RuntimeError(
            "Un budget non estimable n'a pas été "
            "classé comme incertain."
        )

    expected_combined = (
        2.0
        * float(
            common[
                "estimated_fine_error"
            ]
        )
    )

    actual_combined = float(
        certified[0][
            "combined_estimated_fine_error"
        ]
    )

    if abs(
        actual_combined
        - expected_combined
    ) > 1.0e-15:
        raise RuntimeError(
            "Le budget conservateur n'est pas "
            "la somme des deux erreurs."
        )

    print(
        "Classification du budget : VALIDÉE"
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


def manufactured_velocity(
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


def build_manufactured_profile(
    grid_size: int,
    time_steps: int,
) -> dict[str, object]:
    duration = 2.0

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

    times = np.linspace(
        0.0,
        duration,
        time_steps,
        endpoint=True,
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=-1.0,
        domain_max=1.0,
        duration=duration,
        time_steps=time_steps,
        characteristic_length=0.5,
    )

    return itd_v20.simulate_multiscale(
        (
            f"manufacture_"
            f"{grid_size}_{time_steps}"
        ),
        manufactured_velocity,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=(
            STRUCTURAL_LENGTHS
        ),
        curvature_function=zero_curvature,
        boundary_mode="finite",
    )


def find_combined_row(
    rows: tuple[
        dict[str, object],
        ...
    ],
    metric: str,
    structural_length: float | None,
) -> dict[str, object]:
    matches = tuple(
        row
        for row in rows
        if (
            row["metric"] == metric
            and row[
                "structural_length"
            ] == structural_length
        )
    )

    if len(matches) != 1:
        raise RuntimeError(
            "Diagnostic introuvable ou ambigu : "
            f"{metric}, {structural_length}."
        )

    return matches[0]


def validate_manufactured_decoupling() -> None:
    common_fine = (
        build_manufactured_profile(
            RESOLUTIONS[-1],
            RESOLUTIONS[-1],
        )
    )

    spatial_profiles = (
        build_manufactured_profile(
            RESOLUTIONS[0],
            RESOLUTIONS[-1],
        ),
        build_manufactured_profile(
            RESOLUTIONS[1],
            RESOLUTIONS[-1],
        ),
        common_fine,
    )

    temporal_profiles = (
        build_manufactured_profile(
            RESOLUTIONS[-1],
            RESOLUTIONS[0],
        ),
        build_manufactured_profile(
            RESOLUTIONS[-1],
            RESOLUTIONS[1],
        ),
        common_fine,
    )

    spatial_rows = (
        itd_v20.analyze_multiscale_profile_triplet(
            *spatial_profiles
        )
    )

    temporal_rows = (
        itd_v20.analyze_multiscale_profile_triplet(
            *temporal_profiles
        )
    )

    combined_rows = (
        itd_v20.combine_decoupled_convergence_rows(
            spatial_rows,
            temporal_rows,
        )
    )

    intensity = find_combined_row(
        combined_rows,
        "intensity_index",
        None,
    )

    exact_average = 1.72

    temporal_limit = float(
        intensity[
            "temporal_extrapolated_limit"
        ]
    )

    limit_error = abs(
        temporal_limit
        - exact_average
    )

    print()
    print(
        "=== ORACLE SPATIO-TEMPOREL DÉCOUPLÉ ==="
    )

    print(
        "Statut spatial de l'intensité :",
        intensity["spatial_status"],
    )

    print(
        "Statut temporel de l'intensité:",
        intensity["temporal_status"],
    )

    print(
        "Ordre temporel observé        :",
        f"{float(intensity['temporal_observed_order']):.9f}",
    )

    print(
        "Limite temporelle extrapolée  :",
        f"{temporal_limit:.15f}",
    )

    print(
        "Valeur analytique             :",
        f"{exact_average:.15f}",
    )

    print(
        "Erreur sur la limite          :",
        f"{limit_error:.6e}",
    )

    print(
        "Statut combiné                :",
        intensity[
            "certification_status"
        ],
    )

    if intensity["spatial_status"] != "resolved":
        raise RuntimeError(
            "L'oracle spatial affine devrait être "
            "résolu à la tolérance numérique."
        )

    if intensity["temporal_status"] != "asymptotic":
        raise RuntimeError(
            "L'oracle temporel ne se trouve pas "
            "dans le régime asymptotique."
        )

    if (
        float(
            intensity[
                "temporal_observed_order"
            ]
        )
        < MANUFACTURED_ORDER_MINIMUM
    ):
        raise RuntimeError(
            "La quadrature temporelle n'atteint "
            "pas l'ordre deux attendu."
        )

    if limit_error > MANUFACTURED_LIMIT_TOLERANCE:
        raise RuntimeError(
            "L'extrapolation temporelle est trop "
            "éloignée de la valeur analytique."
        )

    if (
        intensity[
            "certification_status"
        ]
        != "certified"
    ):
        raise RuntimeError(
            "L'oracle complet n'a pas obtenu "
            "un budget certifié."
        )

    summary = (
        itd_v20.summarize_decoupled_convergence_rows(
            combined_rows
        )
    )

    print(
        "Résumé de l'oracle :",
        summary,
    )

    print(
        "Oracle découplé : VALIDÉ"
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

    times = np.linspace(
        0.0,
        duration,
        time_steps,
        endpoint=True,
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=grid_size,
        domain_min=domain_min,
        domain_max=domain_max,
        duration=duration,
        time_steps=time_steps,
        characteristic_length=0.5,
    )

    return itd_v20.simulate_multiscale(
        (
            f"multi_vortex_"
            f"{grid_size}_{time_steps}"
        ),
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


def write_report(
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
        "fine_value",
        "fine_match_error",
        "certification_status",
        "spatial_status",
        "spatial_observed_order",
        "spatial_extrapolated_limit",
        "spatial_estimated_fine_error",
        "spatial_estimated_relative_fine_error",
        "temporal_status",
        "temporal_observed_order",
        "temporal_extrapolated_limit",
        "temporal_estimated_fine_error",
        "temporal_estimated_relative_fine_error",
        "combined_estimated_fine_error",
        "combined_estimated_relative_fine_error",
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


def validate_real_decoupled_study() -> None:
    common_fine = build_real_profile(
        RESOLUTIONS[-1],
        RESOLUTIONS[-1],
    )

    spatial_profiles = (
        build_real_profile(
            RESOLUTIONS[0],
            RESOLUTIONS[-1],
        ),
        build_real_profile(
            RESOLUTIONS[1],
            RESOLUTIONS[-1],
        ),
        common_fine,
    )

    temporal_profiles = (
        build_real_profile(
            RESOLUTIONS[-1],
            RESOLUTIONS[0],
        ),
        build_real_profile(
            RESOLUTIONS[-1],
            RESOLUTIONS[1],
        ),
        common_fine,
    )

    spatial_rows = (
        itd_v20.analyze_multiscale_profile_triplet(
            *spatial_profiles
        )
    )

    temporal_rows = (
        itd_v20.analyze_multiscale_profile_triplet(
            *temporal_profiles
        )
    )

    combined_rows = (
        itd_v20.combine_decoupled_convergence_rows(
            spatial_rows,
            temporal_rows,
        )
    )

    summary = (
        itd_v20.summarize_decoupled_convergence_rows(
            combined_rows
        )
    )

    write_report(
        combined_rows,
        summary,
    )

    print()
    print(
        "=== ÉTUDE MULTI-VORTEX DÉCOUPLÉE ==="
    )

    print(
        "Résolutions :",
        RESOLUTIONS,
    )

    print(
        "Nombre de diagnostics :",
        summary["row_count"],
    )

    print(
        "Statuts de certification:",
        summary["status_counts"],
    )

    print(
        "Ordre spatial minimal :",
        summary[
            "minimum_spatial_order"
        ],
    )

    print(
        "Ordre spatial maximal :",
        summary[
            "maximum_spatial_order"
        ],
    )

    print(
        "Ordre temporel minimal:",
        summary[
            "minimum_temporal_order"
        ],
    )

    print(
        "Ordre temporel maximal:",
        summary[
            "maximum_temporal_order"
        ],
    )

    print(
        "Erreur relative combinée maximale:",
        summary[
            "maximum_combined_estimated_relative_fine_error"
        ],
    )

    print(
        "Métrique la plus incertaine:",
        summary["worst_metric"],
    )

    print(
        "Longueur correspondante:",
        summary[
            "worst_structural_length"
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

    if summary["row_count"] != (
        2
        + len(STRUCTURAL_LENGTHS)
        * (
            len(
                itd_v20.STRUCTURAL_COMPONENT_NAMES
            )
            + 3
        )
    ):
        raise RuntimeError(
            "Le nombre de diagnostics du rapport "
            "découplé est incorrect."
        )

    if not REPORT_PATH.is_file():
        raise RuntimeError(
            "Le rapport CSV découplé "
            "n'a pas été créé."
        )

    if not SUMMARY_PATH.is_file():
        raise RuntimeError(
            "Le résumé JSON découplé "
            "n'a pas été créé."
        )

    print(
        "Étude réelle découplée : VALIDÉE"
    )


def validate_invalid_combinations() -> None:
    print()
    print(
        "=== REJET DES ÉTUDES INCOHÉRENTES ==="
    )

    base = {
        "metric": "test",
        "structural_length": None,
        "status": "resolved",
        "fine": 1.0,
        "estimated_fine_error": 0.0,
        "estimated_relative_fine_error": 0.0,
        "observed_order": float("inf"),
        "extrapolated_limit": 1.0,
    }

    try:
        itd_v20.combine_decoupled_convergence_rows(
            (base,),
            (
                {
                    **base,
                    "fine": 1.1,
                },
            ),
        )
    except ValueError as error:
        print(
            "Calculs fins distincts : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Deux études sans calcul fin commun "
            "ont été combinées."
        )

    try:
        itd_v20.combine_decoupled_convergence_rows(
            (base,),
            (
                {
                    **base,
                    "metric": "autre",
                },
            ),
        )
    except ValueError as error:
        print(
            "Métriques distinctes   : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Deux études contenant des métriques "
            "différentes ont été combinées."
        )

    try:
        itd_v20.summarize_decoupled_convergence_rows(
            ()
        )
    except ValueError as error:
        print(
            "Résumé vide            : RÉUSSI —",
            error,
        )
    else:
        raise RuntimeError(
            "Un résumé vide a été accepté."
        )

    print(
        "Contrôle de cohérence V20 : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DU BUDGET D'ERREUR "
        "SPATIO-TEMPOREL — ITD V20 ==="
    )

    validate_v19_compatibility()
    validate_combination_classification()
    validate_manufactured_decoupling()
    validate_real_decoupled_study()
    validate_invalid_combinations()

    print()
    print(
        "Compatibilité V19 → V20              : VALIDÉE"
    )
    print(
        "Raffinement spatial indépendant      : VALIDÉ"
    )
    print(
        "Raffinement temporel indépendant     : VALIDÉ"
    )
    print(
        "Calcul fin commun                    : VALIDÉ"
    )
    print(
        "Budget E_total ≤ E_x + E_t           : VALIDÉ"
    )
    print(
        "Oracle analytique découplé           : VALIDÉ"
    )
    print(
        "Rapport réel CSV/JSON                : VALIDÉ"
    )


if __name__ == "__main__":
    main()
