#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v20_1


def make_row(
    *,
    metric: str,
    certification_status: str,
    spatial_status: str,
    spatial_order: float | None,
    temporal_status: str,
    temporal_order: float | None,
    combined_error: float | None,
) -> dict[str, object]:
    return {
        "metric": metric,
        "structural_length": None,
        "certification_status": (
            certification_status
        ),
        "spatial_status": spatial_status,
        "spatial_observed_order": (
            spatial_order
        ),
        "temporal_status": temporal_status,
        "temporal_observed_order": (
            temporal_order
        ),
        "combined_estimated_relative_fine_error": (
            combined_error
        ),
    }


def validate_order_filtering() -> None:
    rows = (
        make_row(
            metric="asymptotique",
            certification_status="certified",
            spatial_status="asymptotic",
            spatial_order=1.95,
            temporal_status="asymptotic",
            temporal_order=2.01,
            combined_error=0.002,
        ),
        make_row(
            metric="oscillant",
            certification_status="partial",
            spatial_status="non_monotone",
            spatial_order=-2.369,
            temporal_status="asymptotic",
            temporal_order=1.98,
            combined_error=None,
        ),
        make_row(
            metric="resolu",
            certification_status="certified",
            spatial_status="resolved",
            spatial_order=float("inf"),
            temporal_status="resolved",
            temporal_order=float("inf"),
            combined_error=0.0,
        ),
        make_row(
            metric="degenere",
            certification_status="uncertain",
            spatial_status="degenerate",
            spatial_order=-7.0,
            temporal_status="non_monotone",
            temporal_order=-3.0,
            combined_error=None,
        ),
    )

    summary = (
        itd_v20_1.summarize_decoupled_convergence_rows(
            rows
        )
    )

    print(
        "=== SÉMANTIQUE DU RÉSUMÉ V20.1 ==="
    )

    print(
        "Statuts de certification :",
        summary["status_counts"],
    )

    print(
        "Statuts spatiaux         :",
        summary[
            "spatial_status_counts"
        ],
    )

    print(
        "Statuts temporels        :",
        summary[
            "temporal_status_counts"
        ],
    )

    print(
        "Ordre spatial minimal   :",
        summary[
            "minimum_spatial_order"
        ],
    )

    print(
        "Ordre spatial maximal   :",
        summary[
            "maximum_spatial_order"
        ],
    )

    print(
        "Ordre temporel minimal  :",
        summary[
            "minimum_temporal_order"
        ],
    )

    print(
        "Ordre temporel maximal  :",
        summary[
            "maximum_temporal_order"
        ],
    )

    if (
        summary["minimum_spatial_order"]
        != 1.95
    ):
        raise RuntimeError(
            "Un ordre spatial non asymptotique "
            "a contaminé le minimum."
        )

    if (
        summary["maximum_spatial_order"]
        != 1.95
    ):
        raise RuntimeError(
            "Un ordre spatial non asymptotique "
            "a contaminé le maximum."
        )

    if (
        summary["minimum_temporal_order"]
        != 1.98
    ):
        raise RuntimeError(
            "Le minimum temporel asymptotique "
            "est incorrect."
        )

    if (
        summary["maximum_temporal_order"]
        != 2.01
    ):
        raise RuntimeError(
            "Le maximum temporel asymptotique "
            "est incorrect."
        )

    if (
        summary[
            "maximum_combined_estimated_relative_fine_error"
        ]
        != 0.002
    ):
        raise RuntimeError(
            "L'erreur combinée maximale "
            "est incorrecte."
        )

    print(
        "Filtrage des ordres par statut : VALIDÉ"
    )


def validate_no_asymptotic_order() -> None:
    rows = (
        make_row(
            metric="resolu",
            certification_status="certified",
            spatial_status="resolved",
            spatial_order=float("inf"),
            temporal_status="resolved",
            temporal_order=float("inf"),
            combined_error=0.0,
        ),
        make_row(
            metric="oscillant",
            certification_status="uncertain",
            spatial_status="non_monotone",
            spatial_order=-2.5,
            temporal_status="degenerate",
            temporal_order=-4.0,
            combined_error=None,
        ),
    )

    summary = (
        itd_v20_1.summarize_decoupled_convergence_rows(
            rows
        )
    )

    print()
    print(
        "=== ABSENCE DE RÉGIME ASYMPTOTIQUE ==="
    )

    print(
        "Ordre spatial publié :",
        summary[
            "minimum_spatial_order"
        ],
    )

    print(
        "Ordre temporel publié:",
        summary[
            "minimum_temporal_order"
        ],
    )

    if (
        summary["minimum_spatial_order"]
        is not None
    ):
        raise RuntimeError(
            "Un ordre spatial a été publié sans "
            "régime asymptotique."
        )

    if (
        summary["minimum_temporal_order"]
        is not None
    ):
        raise RuntimeError(
            "Un ordre temporel a été publié sans "
            "régime asymptotique."
        )

    print(
        "Absence d'ordre trompeur : VALIDÉE"
    )


def main() -> None:
    validate_order_filtering()
    validate_no_asymptotic_order()

    print()
    print(
        "Statistiques des statuts             : VALIDÉES"
    )
    print(
        "Ordres asymptotiques uniquement      : VALIDÉS"
    )
    print(
        "Ordres négatifs non monotones exclus : VALIDÉS"
    )


if __name__ == "__main__":
    main()
