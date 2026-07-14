#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v17
import itd_v18
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
DIRECT_COMPARISON_TOLERANCE = 5.0e-13
SCALING_TOLERANCE = 2.0e-12
LAW_TOLERANCE = 5.0e-13

STRUCTURAL_LENGTHS = np.asarray(
    (
        0.0,
        0.10,
        0.25,
        0.50,
        1.00,
        2.00,
        4.00,
    ),
    dtype=np.float64,
)

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)


def scaled_error(
    value: float,
    reference: float,
) -> float:
    return abs(value - reference) / max(
        1.0,
        abs(reference),
    )


def build_case() -> tuple[
    Config,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
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

    parameter = np.linspace(
        0.0,
        1.0,
        cfg.time_steps,
        dtype=np.float64,
    )

    times = (
        cfg.duration
        * parameter**1.35
    )

    return cfg, x, y, times, spacing


def validate_v17_compatibility() -> None:
    cfg, x, y, times, spacing = build_case()

    print(
        "=== COMPATIBILITÉ V17 → V18 ==="
    )

    reference = itd_v17.simulate(
        "compatibilite_v17",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=curvature_field,
        structural_length=0.5,
    )

    candidate = itd_v18.simulate(
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

    scalar_keys = (
        "intensity_index",
        "structure_index",
        "coupled_index",
        "temporal_deformation_index",
    )

    errors = [
        scaled_error(
            float(candidate[key]),
            float(reference[key]),
        )
        for key in scalar_keys
    ]

    reference_components = dict(
        reference["component_indices"]
    )

    candidate_components = dict(
        candidate["component_indices"]
    )

    errors.extend(
        scaled_error(
            float(
                candidate_components[component]
            ),
            float(
                reference_components[component]
            ),
        )
        for component in COMPONENTS
    )

    maximum_error = max(errors)

    print(
        "Erreur maximale :",
        f"{maximum_error:.6e}",
    )

    if maximum_error > COMPATIBILITY_TOLERANCE:
        raise RuntimeError(
            "La V18 modifie les résultats "
            "historiques de la V17."
        )

    print(
        "Compatibilité V17 → V18 : VALIDÉE"
    )


def validate_profile_against_direct_simulations() -> None:
    cfg, x, y, times, spacing = build_case()

    profile = itd_v18.simulate_multiscale(
        "profil_direct",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=STRUCTURAL_LENGTHS,
        curvature_function=curvature_field,
    )

    signatures = np.asarray(
        profile["structural_signatures"],
        dtype=np.float64,
    )

    structure_indices = np.asarray(
        profile["structure_indices"],
        dtype=np.float64,
    )

    coupled_indices = np.asarray(
        profile["coupled_indices"],
        dtype=np.float64,
    )

    print()
    print(
        "=== PROFIL DÉRIVÉ CONTRE SIMULATIONS DIRECTES ==="
    )

    print(
        "longueur | erreur signature | "
        "erreur structure | erreur couplée"
    )

    global_maximum = 0.0

    for index, structural_length in enumerate(
        STRUCTURAL_LENGTHS
    ):
        direct = itd_v18.simulate(
            f"direct_{structural_length:g}",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=curvature_field,
            structural_length=float(
                structural_length
            ),
        )

        direct_components = dict(
            direct["component_indices"]
        )

        expected_signature = np.asarray(
            tuple(
                float(
                    direct_components[name]
                )
                for name in COMPONENTS
            ),
            dtype=np.float64,
        )

        signature_error = float(
            np.max(
                np.abs(
                    signatures[index]
                    - expected_signature
                )
            )
        )

        structure_error = abs(
            structure_indices[index]
            - float(
                direct["structure_index"]
            )
        )

        coupled_error = abs(
            coupled_indices[index]
            - float(
                direct["coupled_index"]
            )
        )

        maximum_error = max(
            signature_error,
            structure_error,
            coupled_error,
        )

        global_maximum = max(
            global_maximum,
            maximum_error,
        )

        print(
            f"{structural_length:8.2f} | "
            f"{signature_error:16.6e} | "
            f"{structure_error:16.6e} | "
            f"{coupled_error:14.6e}"
        )

    if (
        global_maximum
        > DIRECT_COMPARISON_TOLERANCE
    ):
        raise RuntimeError(
            "Le profil multi-échelle dérivé "
            "diffère des simulations directes."
        )

    print(
        "Équivalence profil/direct : VALIDÉE"
    )


def validate_multiscale_laws() -> None:
    cfg, x, y, times, spacing = build_case()

    profile = itd_v18.simulate_multiscale(
        "lois_multiechelles",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=STRUCTURAL_LENGTHS,
        curvature_function=curvature_field,
    )

    signatures = np.asarray(
        profile["structural_signatures"],
        dtype=np.float64,
    )

    raw_roughness = np.asarray(
        profile["raw_roughness_indices"],
        dtype=np.float64,
    )

    unit_position = int(
        np.where(
            STRUCTURAL_LENGTHS == 1.0
        )[0][0]
    )

    unit_raw_roughness = float(
        raw_roughness[unit_position]
    )

    expected_raw = (
        STRUCTURAL_LENGTHS
        * unit_raw_roughness
    )

    raw_linearity_error = float(
        np.max(
            np.abs(
                raw_roughness
                - expected_raw
            )
        )
    )

    roughness_position = COMPONENTS.index(
        "roughness"
    )

    bounded_roughness = signatures[
        :,
        roughness_position,
    ]

    non_roughness_positions = tuple(
        index
        for index, name in enumerate(
            COMPONENTS
        )
        if name != "roughness"
    )

    invariant_error = float(
        np.max(
            np.abs(
                signatures[
                    :,
                    non_roughness_positions,
                ]
                - signatures[
                    0,
                    non_roughness_positions,
                ]
            )
        )
    )

    monotonic = bool(
        np.all(
            np.diff(
                bounded_roughness
            ) > 0.0
        )
    )

    zero_roughness = float(
        bounded_roughness[0]
    )

    bounded_valid = bool(
        np.all(
            (
                bounded_roughness >= 0.0
            )
            & (
                bounded_roughness < 1.0
            )
        )
    )

    print()
    print(
        "=== LOIS DU PROFIL MULTI-ÉCHELLE ==="
    )

    print(
        "Erreur de linéarité brute Q(ℓ)=ℓQ(1):",
        f"{raw_linearity_error:.6e}",
    )

    print(
        "Erreur des composantes indépendantes :",
        f"{invariant_error:.6e}",
    )

    print(
        "Rugosité nulle pour ℓ=0             :",
        f"{zero_roughness:.15f}",
    )

    print(
        "Rugosité bornée strictement croissante:",
        monotonic,
    )

    if raw_linearity_error > LAW_TOLERANCE:
        raise RuntimeError(
            "La rugosité brute n'est pas "
            "linéaire en longueur structurelle."
        )

    if invariant_error > LAW_TOLERANCE:
        raise RuntimeError(
            "Une composante indépendante de "
            "l'échelle varie avec la longueur."
        )

    if abs(zero_roughness) > LAW_TOLERANCE:
        raise RuntimeError(
            "La rugosité ne s'annule pas "
            "pour une longueur nulle."
        )

    if not monotonic:
        raise RuntimeError(
            "La rugosité bornée n'est pas "
            "strictement croissante."
        )

    if not bounded_valid:
        raise RuntimeError(
            "La composante de rugosité sort "
            "de l'intervalle [0,1[."
        )

    print(
        "Lois multi-échelles : VALIDÉES"
    )


def validate_spatial_scaling_of_profile() -> None:
    cfg, x, y, times, spacing = build_case()

    factor = 3.25

    coordinates = np.linspace(
        cfg.domain_min,
        cfg.domain_max,
        cfg.grid_size,
        endpoint=True,
        dtype=np.float64,
    )

    reference = itd_v18.simulate_multiscale(
        "profil_echelle_reference",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=STRUCTURAL_LENGTHS,
        curvature_function=curvature_field,
    )

    scaled_coordinates = (
        factor * coordinates
    )

    scaled_x, scaled_y = np.meshgrid(
        scaled_coordinates,
        scaled_coordinates,
        indexing="xy",
    )

    scaled_cfg = Config(
        grid_size=cfg.grid_size,
        domain_min=(
            factor * cfg.domain_min
        ),
        domain_max=(
            factor * cfg.domain_max
        ),
        duration=cfg.duration,
        time_steps=cfg.time_steps,
        characteristic_length=(
            factor
            * cfg.characteristic_length
        ),
    )

    scaled = itd_v18.simulate_multiscale(
        "profil_echelle_dilate",
        itd_v18.scale_velocity_function(
            multi_vortex_field,
            factor,
        ),
        scaled_x,
        scaled_y,
        times,
        factor * spacing,
        scaled_cfg,
        structural_lengths=(
            factor
            * STRUCTURAL_LENGTHS
        ),
        curvature_function=(
            itd_v18.scale_curvature_function(
                curvature_field,
                factor,
            )
        ),
    )

    reference_signatures = np.asarray(
        reference["structural_signatures"],
        dtype=np.float64,
    )

    scaled_signatures = np.asarray(
        scaled["structural_signatures"],
        dtype=np.float64,
    )

    signature_error = float(
        np.max(
            np.abs(
                scaled_signatures
                - reference_signatures
            )
        )
    )

    structure_error = float(
        np.max(
            np.abs(
                np.asarray(
                    scaled["structure_indices"],
                    dtype=np.float64,
                )
                - np.asarray(
                    reference["structure_indices"],
                    dtype=np.float64,
                )
            )
        )
    )

    coupled_error = float(
        np.max(
            np.abs(
                np.asarray(
                    scaled["coupled_indices"],
                    dtype=np.float64,
                )
                - np.asarray(
                    reference["coupled_indices"],
                    dtype=np.float64,
                )
            )
        )
    )

    print()
    print(
        "=== COVARIANCE DU PROFIL MULTI-ÉCHELLE ==="
    )

    print(
        "Facteur spatial       :",
        factor,
    )

    print(
        "Erreur des signatures :",
        f"{signature_error:.6e}",
    )

    print(
        "Erreur des structures :",
        f"{structure_error:.6e}",
    )

    print(
        "Erreur des couplages  :",
        f"{coupled_error:.6e}",
    )

    if max(
        signature_error,
        structure_error,
        coupled_error,
    ) > SCALING_TOLERANCE:
        raise RuntimeError(
            "Le profil ne respecte pas "
            "Sigma_(aS)(a ell) = Sigma_S(ell)."
        )

    print(
        "Covariance multi-échelle : VALIDÉE"
    )


def validate_profile_metadata() -> None:
    cfg, x, y, times, spacing = build_case()

    profile = itd_v18.simulate_multiscale(
        "metadata_multiechelles",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        structural_lengths=STRUCTURAL_LENGTHS,
        curvature_function=curvature_field,
    )

    lengths = np.asarray(
        profile["structural_lengths"],
        dtype=np.float64,
    )

    signatures = np.asarray(
        profile["structural_signatures"],
        dtype=np.float64,
    )

    print()
    print(
        "=== MÉTADONNÉES MULTI-ÉCHELLES ==="
    )

    print(
        "Nombre de longueurs :",
        profile["length_count"],
    )

    print(
        "Forme des signatures:",
        signatures.shape,
    )

    print(
        "Longueurs           :",
        lengths.tolist(),
    )

    if profile["length_count"] != len(
        STRUCTURAL_LENGTHS
    ):
        raise RuntimeError(
            "Le nombre de longueurs exporté "
            "est incorrect."
        )

    if signatures.shape != (
        len(STRUCTURAL_LENGTHS),
        len(COMPONENTS),
    ):
        raise RuntimeError(
            "La matrice des signatures possède "
            "une forme incorrecte."
        )

    if not np.array_equal(
        lengths,
        STRUCTURAL_LENGTHS,
    ):
        raise RuntimeError(
            "La grille des longueurs exportée "
            "est incorrecte."
        )

    if tuple(
        profile[
            "structural_component_names"
        ]
    ) != COMPONENTS:
        raise RuntimeError(
            "Les noms des composantes sont "
            "incorrects."
        )

    print(
        "Métadonnées multi-échelles : VALIDÉES"
    )


def validate_invalid_length_grids() -> None:
    invalid_grids = (
        (),
        (0.5,),
        (0.5, 0.5),
        (1.0, 0.5),
        (-0.1, 0.5),
        (0.0, np.nan),
        (0.0, np.inf),
        [[0.0, 1.0]],
        "0, 1",
        None,
    )

    print()
    print(
        "=== REJET DES GRILLES D'ÉCHELLES INVALIDES ==="
    )

    for invalid in invalid_grids:
        try:
            itd_v18.validate_structural_length_grid(
                invalid
            )
        except ValueError as error:
            print(
                f"Rejet {invalid!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une grille multi-échelle invalide "
                "n'a pas été rejetée."
            )

    print(
        "Contrôle des grilles d'échelles : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE LA SIGNATURE "
        "MULTI-ÉCHELLE — ITD V18 ==="
    )

    validate_v17_compatibility()
    validate_profile_against_direct_simulations()
    validate_multiscale_laws()
    validate_spatial_scaling_of_profile()
    validate_profile_metadata()
    validate_invalid_length_grids()

    print()
    print(
        "Compatibilité V17 → V18             : VALIDÉE"
    )
    print(
        "Profil dérivé en une simulation     : VALIDÉ"
    )
    print(
        "Équivalence aux simulations directes: VALIDÉE"
    )
    print(
        "Rugosité brute linéaire en ℓs       : VALIDÉE"
    )
    print(
        "Composantes indépendantes de ℓs     : VALIDÉES"
    )
    print(
        "Covariance Sigma_(aS)(aℓ)=Sigma_S(ℓ): VALIDÉE"
    )
    print(
        "Signature vectorielle multi-échelle : VALIDÉE"
    )


if __name__ == "__main__":
    main()
