#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v9
import itd_v10
from compare_scenarios import (
    Config,
    coherent_vortex,
    multi_vortex_field,
)


GRID_SIZE = 161
TIME_STEPS = 201
TOLERANCE = 2.0e-13

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)


def relative_error(
    value: float,
    reference: float,
) -> float:
    if abs(reference) < 1.0e-15:
        return abs(value - reference)

    return abs(value - reference) / abs(reference)


def bounded_array(
    values: np.ndarray,
) -> np.ndarray:
    positive = np.maximum(values, 0.0)
    return positive / (1.0 + positive)


def build_environment():
    cfg = Config(
        grid_size=GRID_SIZE,
        time_steps=TIME_STEPS,
    )

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        dtype=np.float64,
    )

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    spacing = float(
        coordinates[1] - coordinates[0]
    )

    times = np.linspace(
        0.0,
        cfg.duration,
        cfg.time_steps,
        dtype=np.float64,
    )

    return cfg, x, y, spacing, times


def reconstruct_component_indices(
    result: dict[str, object],
) -> dict[str, float]:
    interval_dt = np.asarray(
        result["temporal_interval_dt"],
        dtype=np.float64,
    )

    duration = float(np.sum(interval_dt))

    reconstructed: dict[str, float] = {}

    for component in (
        "heterogeneity",
        "localization",
        "roughness",
    ):
        nodal = bounded_array(
            np.asarray(
                result[component],
                dtype=np.float64,
            )
        )

        interval_values = 0.5 * (
            nodal[:-1] + nodal[1:]
        )

        reconstructed[component] = float(
            np.sum(interval_values * interval_dt)
            / duration
        )

    sign_mixing = np.clip(
        np.asarray(
            result["sign_mixing"],
            dtype=np.float64,
        ),
        0.0,
        1.0,
    )

    reconstructed["sign_mixing"] = float(
        np.sum(
            0.5
            * (
                sign_mixing[:-1]
                + sign_mixing[1:]
            )
            * interval_dt
        )
        / duration
    )

    interval_deformation = bounded_array(
        np.asarray(
            result["temporal_deformation_interval"],
            dtype=np.float64,
        )
    )

    reconstructed["temporal_deformation"] = float(
        np.sum(
            interval_deformation * interval_dt
        )
        / duration
    )

    return reconstructed


def validate_compatibility(
    cfg,
    x,
    y,
    spacing,
    times,
) -> None:
    print("=== COMPATIBILITÉ V9 → V10 ===")

    for name, field in (
        ("vortex_coherent", coherent_vortex),
        ("multi_vortex_complexe", multi_vortex_field),
    ):
        old = itd_v9.simulate(
            name,
            field,
            x,
            y,
            times,
            spacing,
            cfg,
        )

        new = itd_v10.simulate(
            name,
            field,
            x,
            y,
            times,
            spacing,
            cfg,
        )

        print()
        print("Scénario :", name)

        for metric in (
            "intensity_index",
            "structure_index",
            "coupled_index",
            "temporal_deformation_index",
        ):
            old_value = float(old[metric])
            new_value = float(new[metric])

            error = relative_error(
                new_value,
                old_value,
            )

            print(
                f"{metric:28s}: "
                f"V9={old_value:.15f}  "
                f"V10={new_value:.15f}  "
                f"erreur={error:.3e}"
            )

            if error > TOLERANCE:
                raise RuntimeError(
                    "La compatibilité V9 → V10 "
                    f"échoue pour {metric}."
                )

    print()
    print("Compatibilité par défaut : RÉUSSIE")


def validate_signature(
    cfg,
    x,
    y,
    spacing,
    times,
) -> None:
    print()
    print("=== SIGNATURE STRUCTURELLE VECTORIELLE ===")

    result = itd_v10.simulate(
        "multi_vortex_complexe",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
    )

    stored = {
        name: float(value)
        for name, value in dict(
            result["component_indices"]
        ).items()
    }

    reconstructed = reconstruct_component_indices(
        result
    )

    for component in COMPONENTS:
        error = relative_error(
            stored[component],
            reconstructed[component],
        )

        print(
            f"{component:22s}: "
            f"stocké={stored[component]:.15f}  "
            f"reconstruit={reconstructed[component]:.15f}  "
            f"erreur={error:.3e}"
        )

        if error > TOLERANCE:
            raise RuntimeError(
                "La composante structurelle "
                f"{component} est incorrecte."
            )

    weights = np.asarray(
        result["structural_weights"],
        dtype=np.float64,
    )

    signature = np.asarray(
        [
            stored[component]
            for component in COMPONENTS
        ],
        dtype=np.float64,
    )

    expected_structure = float(
        np.dot(weights, signature)
    )

    obtained_structure = float(
        result["structure_index"]
    )

    scalar_error = relative_error(
        obtained_structure,
        expected_structure,
    )

    print()
    print(
        "Poids normalisés       :",
        tuple(float(value) for value in weights),
    )
    print(
        "Structure par produit  :",
        f"{expected_structure:.15f}",
    )
    print(
        "Structure enregistrée  :",
        f"{obtained_structure:.15f}",
    )
    print(
        "Erreur                 :",
        f"{scalar_error:.3e}",
    )

    if scalar_error > TOLERANCE:
        raise RuntimeError(
            "Le résumé scalaire n'est pas le produit "
            "des poids par la signature."
        )


def validate_one_hot_weights(
    cfg,
    x,
    y,
    spacing,
    times,
) -> None:
    print()
    print("=== POIDS À COMPOSANTE UNIQUE ===")

    for index, component in enumerate(COMPONENTS):
        weights = [0.0] * len(COMPONENTS)
        weights[index] = 1.0

        result = itd_v10.simulate(
            f"one_hot_{component}",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            structural_weights=weights,
        )

        reconstructed = reconstruct_component_indices(
            result
        )

        obtained = float(
            result["structure_index"]
        )

        expected = reconstructed[component]

        error = relative_error(
            obtained,
            expected,
        )

        print(
            f"{component:22s}: "
            f"structure={obtained:.15f}  "
            f"attendu={expected:.15f}  "
            f"erreur={error:.3e}"
        )

        if error > TOLERANCE:
            raise RuntimeError(
                "Échec du poids unitaire pour "
                f"{component}."
            )


def validate_arbitrary_weights(
    cfg,
    x,
    y,
    spacing,
    times,
) -> None:
    print()
    print("=== POIDS ARBITRAIRES ===")

    raw_weights = np.asarray(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        dtype=np.float64,
    )

    normalized = raw_weights / np.sum(raw_weights)

    result = itd_v10.simulate(
        "weighted_multi_vortex",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_weights=raw_weights,
    )

    reconstructed = reconstruct_component_indices(
        result
    )

    signature = np.asarray(
        [
            reconstructed[component]
            for component in COMPONENTS
        ],
        dtype=np.float64,
    )

    expected = float(
        np.dot(normalized, signature)
    )

    obtained = float(
        result["structure_index"]
    )

    returned_weights = np.asarray(
        result["structural_weights"],
        dtype=np.float64,
    )

    weight_error = float(
        np.max(
            np.abs(
                returned_weights - normalized
            )
        )
    )

    structure_error = relative_error(
        obtained,
        expected,
    )

    print(
        "Poids bruts       :",
        tuple(float(value) for value in raw_weights),
    )
    print(
        "Poids normalisés  :",
        tuple(float(value) for value in returned_weights),
    )
    print(
        "Structure attendue:",
        f"{expected:.15f}",
    )
    print(
        "Structure obtenue :",
        f"{obtained:.15f}",
    )
    print(
        "Erreur poids      :",
        f"{weight_error:.3e}",
    )
    print(
        "Erreur structure  :",
        f"{structure_error:.3e}",
    )

    if weight_error > TOLERANCE:
        raise RuntimeError(
            "La normalisation des poids est incorrecte."
        )

    if structure_error > TOLERANCE:
        raise RuntimeError(
            "La combinaison pondérée est incorrecte."
        )


def validate_rejections(
    cfg,
    x,
    y,
    spacing,
    times,
) -> None:
    print()
    print("=== REJET DES POIDS INVALIDES ===")

    invalid_weights = (
        (),
        (1.0, 1.0),
        (1.0, 1.0, -1.0, 1.0, 1.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (1.0, 1.0, float("nan"), 1.0, 1.0),
        (1.0, 1.0, float("inf"), 1.0, 1.0),
    )

    for weights in invalid_weights:
        try:
            itd_v10.simulate(
                "invalid_weights",
                coherent_vortex,
                x,
                y,
                times[:2],
                spacing,
                cfg,
                structural_weights=weights,
            )
        except ValueError as error:
            print(
                f"Rejet {weights!r}: RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                f"Les poids invalides {weights!r} "
                "n'ont pas été rejetés."
            )


def main() -> None:
    cfg, x, y, spacing, times = build_environment()

    print(
        "=== VALIDATION DES POIDS STRUCTURELS — ITD V10 ==="
    )

    validate_compatibility(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    validate_signature(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    validate_one_hot_weights(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    validate_arbitrary_weights(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    validate_rejections(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    print()
    print("Compatibilité V9 → V10    : VALIDÉE")
    print("Signature vectorielle      : VALIDÉE")
    print("Combinaison pondérée       : VALIDÉE")
    print("Poids arbitraires explicites: VALIDÉS")


if __name__ == "__main__":
    main()
