#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v10
from compare_scenarios import (
    Config,
    calm_field,
    coherent_vortex,
    multi_vortex_field,
)


GRID_SIZE = 81
TIME_STEPS = 101
TOLERANCE = 2.0e-12

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)


def relative_error(
    value: float,
    expected: float,
) -> float:
    if abs(expected) < 1.0e-15:
        return abs(value - expected)

    return abs(value - expected) / abs(expected)


def build_environment() -> tuple[
    Config,
    np.ndarray,
    np.ndarray,
    float,
    np.ndarray,
]:
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


def run(
    name: str,
    velocity_function,
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
    times: np.ndarray,
    structural_weights: object = (
        1.0,
        1.0,
        1.0,
        1.0,
        1.0,
    ),
) -> dict[str, object]:
    return itd_v10.simulate(
        name,
        velocity_function,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_weights=structural_weights,
    )


def validate_primary_classification(
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
    times: np.ndarray,
) -> None:
    calm = run(
        "calme_irrotationnel",
        calm_field,
        cfg,
        x,
        y,
        spacing,
        times,
    )

    coherent = run(
        "vortex_coherent",
        coherent_vortex,
        cfg,
        x,
        y,
        spacing,
        times,
    )

    complex_result = run(
        "multi_vortex_complexe",
        multi_vortex_field,
        cfg,
        x,
        y,
        spacing,
        times,
    )

    calm_intensity = float(calm["intensity_index"])
    calm_structure = float(calm["structure_index"])

    coherent_intensity = float(
        coherent["intensity_index"]
    )
    coherent_structure = float(
        coherent["structure_index"]
    )

    complex_intensity = float(
        complex_result["intensity_index"]
    )
    complex_structure = float(
        complex_result["structure_index"]
    )

    print("=== CLASSIFICATION PRINCIPALE ===")
    print(
        "Calme       :",
        f"I={calm_intensity:.12f}",
        f"C={calm_structure:.12f}",
    )
    print(
        "Cohérent    :",
        f"I={coherent_intensity:.12f}",
        f"C={coherent_structure:.12f}",
    )
    print(
        "Multi-vortex:",
        f"I={complex_intensity:.12f}",
        f"C={complex_structure:.12f}",
    )

    if abs(calm_intensity) > TOLERANCE:
        raise RuntimeError(
            "Le champ calme possède une intensité non nulle."
        )

    if abs(calm_structure) > TOLERANCE:
        raise RuntimeError(
            "Le champ calme possède une structure non nulle."
        )

    if coherent_intensity <= complex_intensity:
        raise RuntimeError(
            "La classification de l'intensité a échoué."
        )

    if complex_structure <= coherent_structure:
        raise RuntimeError(
            "La classification structurelle a échoué."
        )

    print("Classification principale : RÉUSSIE")


def validate_vector_signature(
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
    times: np.ndarray,
) -> None:
    result = run(
        "signature_multi_vortex",
        multi_vortex_field,
        cfg,
        x,
        y,
        spacing,
        times,
    )

    component_indices = {
        str(name): float(value)
        for name, value in dict(
            result["component_indices"]
        ).items()
    }

    weights = np.asarray(
        result["structural_weights"],
        dtype=np.float64,
    )

    expected_names = set(COMPONENTS)
    obtained_names = set(component_indices)

    if obtained_names != expected_names:
        raise RuntimeError(
            "Composantes structurelles incorrectes : "
            f"{sorted(obtained_names)}"
        )

    if weights.shape != (5,):
        raise RuntimeError(
            "Le vecteur de poids n'a pas cinq éléments."
        )

    if not np.isclose(
        float(np.sum(weights)),
        1.0,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise RuntimeError(
            "Les poids structurels ne sont pas normalisés."
        )

    signature = np.asarray(
        [
            component_indices[name]
            for name in COMPONENTS
        ],
        dtype=np.float64,
    )

    expected_structure = float(
        np.dot(weights, signature)
    )

    obtained_structure = float(
        result["structure_index"]
    )

    error = relative_error(
        obtained_structure,
        expected_structure,
    )

    print()
    print("=== SIGNATURE VECTORIELLE ===")

    for name in COMPONENTS:
        print(
            f"{name:22s}: "
            f"{component_indices[name]:.15f}"
        )

    print(
        "Poids normalisés      :",
        tuple(float(value) for value in weights),
    )
    print(
        "Structure reconstruite:",
        f"{expected_structure:.15f}",
    )
    print(
        "Structure enregistrée :",
        f"{obtained_structure:.15f}",
    )
    print(
        "Erreur relative       :",
        f"{error:.3e}",
    )

    if error > TOLERANCE:
        raise RuntimeError(
            "La structure scalaire ne correspond pas "
            "à la signature pondérée."
        )

    print("Signature vectorielle : RÉUSSIE")


def validate_one_hot_weights(
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
    times: np.ndarray,
) -> None:
    print()
    print("=== POIDS À COMPOSANTE UNIQUE ===")

    for index, component in enumerate(COMPONENTS):
        weights = [0.0] * len(COMPONENTS)
        weights[index] = 1.0

        result = run(
            f"one_hot_{component}",
            multi_vortex_field,
            cfg,
            x,
            y,
            spacing,
            times,
            structural_weights=weights,
        )

        component_indices = {
            str(name): float(value)
            for name, value in dict(
                result["component_indices"]
            ).items()
        }

        obtained = float(
            result["structure_index"]
        )

        expected = component_indices[component]

        error = relative_error(
            obtained,
            expected,
        )

        print(
            f"{component:22s}: "
            f"obtenu={obtained:.15f}  "
            f"attendu={expected:.15f}  "
            f"erreur={error:.3e}"
        )

        if error > TOLERANCE:
            raise RuntimeError(
                "Échec du poids unitaire pour "
                f"{component}."
            )

    print("Poids unitaires : RÉUSSIS")


def validate_arbitrary_weights(
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
    times: np.ndarray,
) -> None:
    raw_weights = np.asarray(
        (1.0, 2.0, 3.0, 4.0, 5.0),
        dtype=np.float64,
    )

    normalized = raw_weights / np.sum(raw_weights)

    result = run(
        "poids_arbitraires",
        multi_vortex_field,
        cfg,
        x,
        y,
        spacing,
        times,
        structural_weights=raw_weights,
    )

    returned_weights = np.asarray(
        result["structural_weights"],
        dtype=np.float64,
    )

    component_indices = {
        str(name): float(value)
        for name, value in dict(
            result["component_indices"]
        ).items()
    }

    signature = np.asarray(
        [
            component_indices[name]
            for name in COMPONENTS
        ],
        dtype=np.float64,
    )

    expected = float(
        np.dot(normalized, signature)
    )

    obtained = float(
        result["structure_index"]
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

    print()
    print("=== POIDS ARBITRAIRES ===")
    print(
        "Poids normalisés :",
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
        "Erreur des poids  :",
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

    print("Poids arbitraires : RÉUSSIS")


def validate_invalid_weights(
    cfg: Config,
    x: np.ndarray,
    y: np.ndarray,
    spacing: float,
    times: np.ndarray,
) -> None:
    invalid_weights = (
        (),
        (1.0, 1.0),
        (1.0, 1.0, -1.0, 1.0, 1.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (1.0, 1.0, float("nan"), 1.0, 1.0),
        (1.0, 1.0, float("inf"), 1.0, 1.0),
    )

    print()
    print("=== REJET DES POIDS INVALIDES ===")

    for weights in invalid_weights:
        try:
            run(
                "poids_invalides",
                coherent_vortex,
                cfg,
                x,
                y,
                spacing,
                times[:2],
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

    print("Contrôle des poids invalides : RÉUSSI")


def main() -> None:
    cfg, x, y, spacing, times = build_environment()

    print(
        "=== VALIDATION AUTONOME ITD V10 ==="
    )

    validate_primary_classification(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    validate_vector_signature(
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

    validate_invalid_weights(
        cfg,
        x,
        y,
        spacing,
        times,
    )

    print()
    print("Validation autonome V10 : RÉUSSIE")


if __name__ == "__main__":
    main()
