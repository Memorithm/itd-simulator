#!/usr/bin/env python3

from __future__ import annotations

import numpy as np

import itd_v16
import itd_v17
from compare_scenarios import (
    Config,
    curvature_field,
    multi_vortex_field,
)


COMPATIBILITY_TOLERANCE = 2.0e-13
UNIFORM_SCALING_TOLERANCE = 8.0e-12
RECTILINEAR_SCALING_TOLERANCE = 3.0e-11
POINTWISE_TOLERANCE = 8.0e-12
COMPOSITION_TOLERANCE = 2.0e-13

SCALE_FACTORS = (
    0.40,
    0.75,
    2.50,
    6.00,
)

COMPONENTS = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
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


def build_uniform_case() -> tuple[
    Config,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
    cfg = Config(
        grid_size=81,
        domain_min=-2.0,
        domain_max=2.0,
        duration=2.5,
        time_steps=8,
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

    times = np.asarray(
        (
            0.0,
            0.0625,
            0.20,
            0.45,
            0.90,
            1.40,
            1.95,
            2.50,
        ),
        dtype=np.float64,
    )

    return (
        cfg,
        coordinates,
        x,
        y,
        times,
        spacing,
    )


def validate_v16_compatibility() -> None:
    (
        cfg,
        _,
        x,
        y,
        times,
        spacing,
    ) = build_uniform_case()

    print(
        "=== COMPATIBILITÉ V16 → V17 ==="
    )

    reference = extract_results(
        itd_v16.simulate(
            "compatibilite_v16",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=curvature_field,
        )
    )

    candidate = extract_results(
        itd_v17.simulate(
            "compatibilite_v17",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=curvature_field,
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
            "La V17 modifie les résultats "
            "historiques de la V16."
        )

    print(
        "Compatibilité V16 → V17 : VALIDÉE"
    )


def validate_uniform_scaling_covariance() -> None:
    (
        cfg,
        coordinates,
        x,
        y,
        times,
        spacing,
    ) = build_uniform_case()

    structural_length = 0.5

    reference = extract_results(
        itd_v17.simulate(
            "echelle_reference",
            multi_vortex_field,
            x,
            y,
            times,
            spacing,
            cfg,
            curvature_function=curvature_field,
            structural_length=structural_length,
        )
    )

    print()
    print(
        "=== COVARIANCE SUR GRILLE UNIFORME ==="
    )

    print(
        "facteur | erreur maximale | "
        "métrique la plus sensible"
    )

    global_maximum = 0.0

    for factor in SCALE_FACTORS:
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
                itd_v17.scale_length(
                    cfg.characteristic_length,
                    factor,
                    "caractéristique",
                )
            ),
        )

        scaled_velocity = (
            itd_v17.scale_velocity_function(
                multi_vortex_field,
                factor,
            )
        )

        scaled_curvature = (
            itd_v17.scale_curvature_function(
                curvature_field,
                factor,
            )
        )

        candidate = extract_results(
            itd_v17.simulate(
                f"echelle_{factor:g}",
                scaled_velocity,
                scaled_x,
                scaled_y,
                times,
                factor * spacing,
                scaled_cfg,
                curvature_function=scaled_curvature,
                structural_length=(
                    itd_v17.scale_length(
                        structural_length,
                        factor,
                        "structurelle",
                    )
                ),
            )
        )

        errors = {
            key: scaled_error(
                candidate[key],
                reference[key],
            )
            for key in reference
        }

        maximum_error = max(
            errors.values()
        )

        worst_metric = max(
            errors,
            key=errors.get,
        )

        global_maximum = max(
            global_maximum,
            maximum_error,
        )

        print(
            f"{factor:7.2f} | "
            f"{maximum_error:15.6e} | "
            f"{worst_metric}"
        )

    if (
        global_maximum
        > UNIFORM_SCALING_TOLERANCE
    ):
        raise RuntimeError(
            "La signature n'est pas covariante "
            "sous dilatation spatiale uniforme."
        )

    print(
        "Covariance uniforme complète : VALIDÉE"
    )


def validate_pointwise_scaling_laws() -> None:
    (
        cfg,
        coordinates,
        x,
        y,
        _,
        spacing,
    ) = build_uniform_case()

    factor = 3.70
    time = 1.25

    scaled_coordinates = (
        factor * coordinates
    )

    scaled_x, scaled_y = np.meshgrid(
        scaled_coordinates,
        scaled_coordinates,
        indexing="xy",
    )

    base_vx, base_vy = multi_vortex_field(
        x,
        y,
        time,
    )

    scaled_velocity = (
        itd_v17.scale_velocity_function(
            multi_vortex_field,
            factor,
        )
    )

    scaled_vx, scaled_vy = scaled_velocity(
        scaled_x,
        scaled_y,
        time,
    )

    base_omega = (
        itd_v17.numerical_vorticity_with_boundary(
            base_vx,
            base_vy,
            spacing,
            boundary_mode="finite",
        )
    )

    scaled_omega = (
        itd_v17.numerical_vorticity_with_boundary(
            scaled_vx,
            scaled_vy,
            factor * spacing,
            boundary_mode="finite",
        )
    )

    vorticity_error = float(
        np.max(
            np.abs(
                scaled_omega
                - base_omega
            )
        )
    )

    base_curvature = curvature_field(
        x,
        y,
        time,
    )

    scaled_curvature_function = (
        itd_v17.scale_curvature_function(
            curvature_field,
            factor,
        )
    )

    scaled_curvature = (
        scaled_curvature_function(
            scaled_x,
            scaled_y,
            time,
        )
    )

    base_exponent = (
        cfg.characteristic_length**2
        * base_curvature
    )

    scaled_length = (
        factor
        * cfg.characteristic_length
    )

    scaled_exponent = (
        scaled_length**2
        * scaled_curvature
    )

    exponent_error = float(
        np.max(
            np.abs(
                scaled_exponent
                - base_exponent
            )
        )
    )

    print()
    print(
        "=== ORACLES DIMENSIONNELS POINT À POINT ==="
    )

    print(
        "Erreur de la vorticité :",
        f"{vorticity_error:.6e}",
    )

    print(
        "Erreur de l'exposant ℓ²R:",
        f"{exponent_error:.6e}",
    )

    if vorticity_error > POINTWISE_TOLERANCE:
        raise RuntimeError(
            "La vorticité n'est pas invariante "
            "sous le changement d'échelle."
        )

    if exponent_error > POINTWISE_TOLERANCE:
        raise RuntimeError(
            "Le produit sans dimension ℓ²R "
            "n'est pas invariant."
        )

    print(
        "Lois dimensionnelles point à point : "
        "VALIDÉES"
    )


def rectilinear_velocity(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> tuple[np.ndarray, np.ndarray]:
    vx = (
        np.sin(0.8 * y)
        + 0.18 * x * y
        + 0.04 * time * x
    )

    vy = (
        np.cos(0.6 * x)
        - 0.12 * x * y
        + 0.03 * time * y
    )

    return vx, vy


def rectilinear_curvature(
    x: np.ndarray,
    y: np.ndarray,
    time: float,
) -> np.ndarray:
    return (
        0.22
        * np.exp(
            -(
                x**2
                + 0.7 * y**2
            )
        )
        + 0.04 * x
        - 0.03 * y
        + 0.02
        * np.sin(0.5 * time)
        * x
        * y
    )


def build_rectilinear_case() -> tuple[
    Config,
    itd_v17.RectilinearGeometry,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    nx = 65
    ny = 49

    parameter_x = np.linspace(
        0.0,
        1.0,
        nx,
        dtype=np.float64,
    )

    parameter_y = np.linspace(
        0.0,
        1.0,
        ny,
        dtype=np.float64,
    )

    x_coordinates = (
        -1.7
        + 3.4 * parameter_x**1.35
    )

    y_coordinates = (
        -1.1
        + 2.2 * parameter_y**1.65
    )

    geometry = itd_v17.RectilinearGeometry(
        x_coordinates,
        y_coordinates,
    )

    x, y = np.meshgrid(
        x_coordinates,
        y_coordinates,
        indexing="xy",
    )

    times = np.asarray(
        (
            0.0,
            0.10,
            0.32,
            0.70,
            1.15,
            1.80,
        ),
        dtype=np.float64,
    )

    cfg = Config(
        grid_size=max(nx, ny),
        duration=float(times[-1]),
        time_steps=times.size,
        characteristic_length=0.40,
    )

    return (
        cfg,
        geometry,
        x,
        y,
        times,
    )


def validate_rectilinear_scaling_covariance() -> None:
    (
        cfg,
        geometry,
        x,
        y,
        times,
    ) = build_rectilinear_case()

    structural_length = 0.35

    reference = extract_results(
        itd_v17.simulate(
            "rectiligne_reference",
            rectilinear_velocity,
            x,
            y,
            times,
            geometry,
            cfg,
            curvature_function=rectilinear_curvature,
            structural_length=structural_length,
        )
    )

    print()
    print(
        "=== COVARIANCE RECTILIGNE NON UNIFORME ==="
    )

    global_maximum = 0.0

    for factor in (
        0.50,
        2.25,
        5.00,
    ):
        scaled_geometry = (
            itd_v17.scale_spatial_geometry(
                geometry,
                factor,
            )
        )

        scaled_x, scaled_y = np.meshgrid(
            scaled_geometry.x_coordinates,
            scaled_geometry.y_coordinates,
            indexing="xy",
        )

        scaled_cfg = Config(
            grid_size=cfg.grid_size,
            duration=cfg.duration,
            time_steps=cfg.time_steps,
            characteristic_length=(
                factor
                * cfg.characteristic_length
            ),
        )

        candidate = extract_results(
            itd_v17.simulate(
                f"rectiligne_{factor:g}",
                itd_v17.scale_velocity_function(
                    rectilinear_velocity,
                    factor,
                ),
                scaled_x,
                scaled_y,
                times,
                scaled_geometry,
                scaled_cfg,
                curvature_function=(
                    itd_v17.scale_curvature_function(
                        rectilinear_curvature,
                        factor,
                    )
                ),
                structural_length=(
                    factor
                    * structural_length
                ),
            )
        )

        errors = {
            key: scaled_error(
                candidate[key],
                reference[key],
            )
            for key in reference
        }

        maximum_error = max(
            errors.values()
        )

        worst_metric = max(
            errors,
            key=errors.get,
        )

        global_maximum = max(
            global_maximum,
            maximum_error,
        )

        print(
            f"facteur={factor:5.2f}  "
            f"erreur={maximum_error:.6e}  "
            f"métrique={worst_metric}"
        )

    if (
        global_maximum
        > RECTILINEAR_SCALING_TOLERANCE
    ):
        raise RuntimeError(
            "La covariance d'échelle échoue "
            "sur une grille non uniforme."
        )

    print(
        "Covariance rectiligne : VALIDÉE"
    )


def validate_length_scaling_is_necessary() -> None:
    (
        cfg,
        coordinates,
        x,
        y,
        times,
        spacing,
    ) = build_uniform_case()

    structural_length = 0.5
    factor = 2.50

    reference = itd_v17.simulate(
        "necessite_reference",
        multi_vortex_field,
        x,
        y,
        times,
        spacing,
        cfg,
        curvature_function=curvature_field,
        structural_length=structural_length,
    )

    scaled_coordinates = (
        factor * coordinates
    )

    scaled_x, scaled_y = np.meshgrid(
        scaled_coordinates,
        scaled_coordinates,
        indexing="xy",
    )

    wrong_cfg = Config(
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
            cfg.characteristic_length
        ),
    )

    wrong = itd_v17.simulate(
        "longueurs_non_redimensionnees",
        itd_v17.scale_velocity_function(
            multi_vortex_field,
            factor,
        ),
        scaled_x,
        scaled_y,
        times,
        factor * spacing,
        wrong_cfg,
        curvature_function=(
            itd_v17.scale_curvature_function(
                curvature_field,
                factor,
            )
        ),
        structural_length=structural_length,
    )

    intensity_difference = abs(
        float(wrong["intensity_index"])
        - float(reference["intensity_index"])
    )

    reference_roughness = float(
        dict(
            reference["component_indices"]
        )["roughness"]
    )

    wrong_roughness = float(
        dict(
            wrong["component_indices"]
        )["roughness"]
    )

    roughness_difference = abs(
        wrong_roughness
        - reference_roughness
    )

    print()
    print(
        "=== NÉCESSITÉ DU REDIMENSIONNEMENT "
        "DES LONGUEURS ==="
    )

    print(
        "Écart d'intensité sans ℓc' = aℓc :",
        f"{intensity_difference:.6e}",
    )

    print(
        "Écart de rugosité sans ℓs' = aℓs :",
        f"{roughness_difference:.6e}",
    )

    if intensity_difference < 1.0e-4:
        raise RuntimeError(
            "Le test ne détecte pas l'absence "
            "de redimensionnement de la longueur "
            "caractéristique."
        )

    if roughness_difference < 1.0e-4:
        raise RuntimeError(
            "Le test ne détecte pas l'absence "
            "de redimensionnement de la longueur "
            "structurelle."
        )

    print(
        "Rôle des longueurs explicites : VALIDÉ"
    )


def validate_scaling_composition() -> None:
    (
        _,
        geometry,
        _,
        _,
        _,
    ) = build_rectilinear_case()

    first_factor = 1.70
    second_factor = 0.60
    combined_factor = (
        first_factor
        * second_factor
    )

    origin = (
        0.35,
        -0.20,
    )

    coordinates = np.linspace(
        -2.0,
        2.0,
        41,
        dtype=np.float64,
    )

    x, y = np.meshgrid(
        coordinates,
        coordinates,
        indexing="xy",
    )

    time = 0.8

    direct_velocity = (
        itd_v17.scale_velocity_function(
            rectilinear_velocity,
            combined_factor,
            origin=origin,
        )
    )

    sequential_velocity = (
        itd_v17.scale_velocity_function(
            itd_v17.scale_velocity_function(
                rectilinear_velocity,
                first_factor,
                origin=origin,
            ),
            second_factor,
            origin=origin,
        )
    )

    direct_vx, direct_vy = direct_velocity(
        x,
        y,
        time,
    )

    sequential_vx, sequential_vy = (
        sequential_velocity(
            x,
            y,
            time,
        )
    )

    velocity_error = float(
        np.max(
            np.sqrt(
                (
                    direct_vx
                    - sequential_vx
                ) ** 2
                + (
                    direct_vy
                    - sequential_vy
                ) ** 2
            )
        )
    )

    direct_curvature = (
        itd_v17.scale_curvature_function(
            rectilinear_curvature,
            combined_factor,
            origin=origin,
        )
    )

    sequential_curvature = (
        itd_v17.scale_curvature_function(
            itd_v17.scale_curvature_function(
                rectilinear_curvature,
                first_factor,
                origin=origin,
            ),
            second_factor,
            origin=origin,
        )
    )

    curvature_error = float(
        np.max(
            np.abs(
                direct_curvature(
                    x,
                    y,
                    time,
                )
                - sequential_curvature(
                    x,
                    y,
                    time,
                )
            )
        )
    )

    direct_geometry = (
        itd_v17.scale_spatial_geometry(
            geometry,
            combined_factor,
            origin=origin,
        )
    )

    sequential_geometry = (
        itd_v17.scale_spatial_geometry(
            itd_v17.scale_spatial_geometry(
                geometry,
                first_factor,
                origin=origin,
            ),
            second_factor,
            origin=origin,
        )
    )

    geometry_error = max(
        float(
            np.max(
                np.abs(
                    direct_geometry.x_coordinates
                    - sequential_geometry.x_coordinates
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    direct_geometry.y_coordinates
                    - sequential_geometry.y_coordinates
                )
            )
        ),
    )

    print()
    print(
        "=== COMPOSITION DES DILATATIONS ==="
    )

    print(
        "Erreur du champ vectoriel :",
        f"{velocity_error:.6e}",
    )

    print(
        "Erreur de la courbure      :",
        f"{curvature_error:.6e}",
    )

    print(
        "Erreur de la géométrie     :",
        f"{geometry_error:.6e}",
    )

    if velocity_error > COMPOSITION_TOLERANCE:
        raise RuntimeError(
            "La composition des transformations "
            "de vitesse est incorrecte."
        )

    if curvature_error > COMPOSITION_TOLERANCE:
        raise RuntimeError(
            "La composition des transformations "
            "de courbure est incorrecte."
        )

    if geometry_error > COMPOSITION_TOLERANCE:
        raise RuntimeError(
            "La composition des géométries "
            "redimensionnées est incorrecte."
        )

    print(
        "S_a suivi de S_b = S_(ab) : VALIDÉ"
    )


def validate_invalid_scalings() -> None:
    print()
    print(
        "=== REJET DES ÉCHELLES INVALIDES ==="
    )

    for invalid in (
        0.0,
        -1.0,
        np.nan,
        np.inf,
        -np.inf,
        "double",
        None,
    ):
        try:
            itd_v17.validate_spatial_scale_factor(
                invalid
            )
        except ValueError as error:
            print(
                f"Facteur {invalid!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Un facteur d'échelle invalide "
                "n'a pas été rejeté."
            )

    for invalid_length in (
        -0.1,
        np.nan,
        np.inf,
        "longueur",
        None,
    ):
        try:
            itd_v17.scale_length(
                invalid_length,
                2.0,
            )
        except ValueError as error:
            print(
                f"Longueur {invalid_length!r}: "
                f"RÉUSSI — {error}"
            )
        else:
            raise RuntimeError(
                "Une longueur invalide "
                "n'a pas été rejetée."
            )

    print(
        "Contrôle des échelles invalides : VALIDÉ"
    )


def main() -> None:
    print(
        "=== VALIDATION DE LA COVARIANCE "
        "D'ÉCHELLE SPATIALE — ITD V17 ==="
    )

    validate_v16_compatibility()
    validate_uniform_scaling_covariance()
    validate_pointwise_scaling_laws()
    validate_rectilinear_scaling_covariance()
    validate_length_scaling_is_necessary()
    validate_scaling_composition()
    validate_invalid_scalings()

    print()
    print(
        "Compatibilité V16 → V17             : VALIDÉE"
    )
    print(
        "Vorticité sous changement d'échelle : VALIDÉE"
    )
    print(
        "Produit sans dimension ℓ²R          : VALIDÉ"
    )
    print(
        "Signature sur grille uniforme       : VALIDÉE"
    )
    print(
        "Signature sur grille non uniforme   : VALIDÉE"
    )
    print(
        "Longueur caractéristique ℓc' = aℓc  : VALIDÉE"
    )
    print(
        "Longueur structurelle ℓs' = aℓs     : VALIDÉE"
    )
    print(
        "Composition des dilatations         : VALIDÉE"
    )


if __name__ == "__main__":
    main()
