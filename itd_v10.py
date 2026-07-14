#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from compare_scenarios import (
    Config,
    calm_field,
    coherent_vortex,
    curvature_field,
    multi_vortex_field,
    numerical_vorticity,
)


ZERO_THRESHOLD = 1.0e-12

# Longueur physique de référence utilisée pour rendre
# la rugosité adimensionnelle. Elle est indépendante
# du pas numérique de la grille.
STRUCTURAL_LENGTH = 0.5

STRUCTURAL_COMPONENT_NAMES = (
    "heterogeneity",
    "localization",
    "roughness",
    "sign_mixing",
    "temporal_deformation",
)

DEFAULT_STRUCTURAL_WEIGHTS = (
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
)


def normalize_structural_weights(
    weights: object,
) -> np.ndarray:
    """
    Valide et normalise cinq poids positifs ou nuls.

    L'ordre est :
        hétérogénéité,
        localisation,
        rugosité,
        mélange des signes,
        déformation temporelle.
    """
    array = np.asarray(
        weights,
        dtype=np.float64,
    )

    if array.shape != (5,):
        raise ValueError(
            "Les poids structurels doivent contenir "
            "exactement cinq valeurs."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "Les poids structurels doivent être finis."
        )

    if np.any(array < 0.0):
        raise ValueError(
            "Les poids structurels doivent être "
            "positifs ou nuls."
        )

    total = float(np.sum(array))

    if total <= 0.0:
        raise ValueError(
            "Au moins un poids structurel doit être "
            "strictement positif."
        )

    return array / total


def bounded(value: float) -> float:
    """
    Projection d'une grandeur positive dans [0, 1[.

        b(x) = x / (1 + x)
    """
    value = max(0.0, float(value))
    return value / (1.0 + value)


def spatial_mean(
    field: np.ndarray,
    spacing: float,
) -> float:
    """
    Moyenne spatiale obtenue par quadrature trapézoïdale 2D.

    La normalisation utilise l'aire géométrique exacte du
    domaine couvert par les points de la grille.
    """
    if field.ndim != 2:
        raise ValueError(
            "La quadrature spatiale attend un tableau 2D."
        )

    height = (field.shape[0] - 1) * spacing
    width = (field.shape[1] - 1) * spacing
    area = height * width

    if area <= 0.0:
        raise ValueError(
            "L'aire du domaine doit être strictement positive."
        )

    integral_x = np.trapezoid(
        field,
        dx=spacing,
        axis=1,
    )

    integral = float(
        np.trapezoid(
            integral_x,
            dx=spacing,
            axis=0,
        )
    )

    return integral / area


def structural_metrics(
    omega: np.ndarray,
    spacing: float,
    previous_omega: np.ndarray | None,
    delta_time: float | None,
    structural_length: float = STRUCTURAL_LENGTH,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
) -> dict[str, float]:
    structural_length = float(structural_length)

    if (
        not np.isfinite(structural_length)
        or structural_length < 0.0
    ):
        raise ValueError(
            "La longueur structurelle doit être "
            "finie et positive ou nulle."
        )

    weights_array = normalize_structural_weights(
        structural_weights
    )

    abs_omega = np.abs(omega)
    mean_square = spatial_mean(omega**2, spacing)
    rms = float(np.sqrt(mean_square))

    if rms < ZERO_THRESHOLD:
        return {
            "heterogeneity": 0.0,
            "localization": 0.0,
            "roughness": 0.0,
            "sign_mixing": 0.0,
            "temporal_deformation": 0.0,
            "structure_score": 0.0,
        }

    mean_absolute = spatial_mean(abs_omega, spacing)

    absolute_deviation = (
        abs_omega - mean_absolute
    )

    weighted_variance = spatial_mean(
        absolute_deviation**2,
        spacing,
    )

    heterogeneity = float(
        np.sqrt(
            max(weighted_variance, 0.0)
        )
        / max(mean_absolute, ZERO_THRESHOLD)
    )

    localization = float(
        spatial_mean(omega**4, spacing)
        / max(mean_square**2, ZERO_THRESHOLD)
        - 1.0
    )

    gradient_y, gradient_x = np.gradient(
        omega,
        spacing,
        spacing,
        edge_order=2,
    )

    gradient_norm = np.sqrt(
        gradient_x**2 + gradient_y**2
    )

    roughness = float(
        structural_length
        * spatial_mean(gradient_norm, spacing)
        / max(rms, ZERO_THRESHOLD)
    )

    sign_mixing = float(
        1.0
        - abs(spatial_mean(omega, spacing))
        / max(mean_absolute, ZERO_THRESHOLD)
    )

    sign_mixing = float(
        np.clip(sign_mixing, 0.0, 1.0)
    )

    temporal_deformation = 0.0

    if (
        previous_omega is not None
        and delta_time is not None
        and delta_time > 0.0
    ):
        previous_rms = float(
            np.sqrt(
                spatial_mean(
                    previous_omega**2,
                    spacing,
                )
            )
        )

        reference_rms = 0.5 * (
            rms + previous_rms
        )

        if reference_rms >= ZERO_THRESHOLD:
            temporal_deformation = float(
                np.sqrt(
                    spatial_mean(
                        (omega - previous_omega) ** 2,
                        spacing,
                    )
                )
                / (
                    delta_time
                    * reference_rms
                )
            )

    bounded_components = (
        bounded(heterogeneity),
        bounded(localization),
        bounded(roughness),
        sign_mixing,
        bounded(temporal_deformation),
    )

    structure_score = float(
        np.dot(
            weights_array,
            np.asarray(
                bounded_components,
                dtype=np.float64,
            ),
        )
    )

    return {
        "heterogeneity": heterogeneity,
        "localization": localization,
        "roughness": roughness,
        "sign_mixing": sign_mixing,
        "temporal_deformation": temporal_deformation,
        "structure_score": structure_score,
    }


def simulate(
    name: str,
    velocity_function: Callable,
    x: np.ndarray,
    y: np.ndarray,
    times: np.ndarray,
    spacing: float,
    cfg: Config,
    curvature_function: Callable = curvature_field,
    structural_length: float = STRUCTURAL_LENGTH,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
) -> dict[str, object]:
    structural_length = float(structural_length)

    if (
        not np.isfinite(structural_length)
        or structural_length < 0.0
    ):
        raise ValueError(
            "La longueur structurelle doit être "
            "finie et positive ou nulle."
        )
    weights_array = normalize_structural_weights(
        structural_weights
    )

    intensity_rate = np.zeros_like(times)
    structure_rate = np.zeros_like(times)
    coupled_rate = np.zeros_like(times)

    heterogeneity = np.zeros_like(times)
    localization = np.zeros_like(times)
    roughness = np.zeros_like(times)
    sign_mixing = np.zeros_like(times)
    temporal_deformation = np.zeros_like(times)

    previous_omega: np.ndarray | None = None
    previous_time: float | None = None

    for index, time_value in enumerate(times):
        time = float(time_value)

        vx, vy = velocity_function(
            x,
            y,
            time,
        )

        omega = numerical_vorticity(
            vx,
            vy,
            spacing,
        )

        curvature = np.asarray(
            curvature_function(
                x,
                y,
                time,
            ),
            dtype=np.float64,
        )

        if curvature.shape != x.shape:
            raise ValueError(
                "Le champ de courbure doit avoir la même "
                "forme que la grille spatiale."
            )

        if not np.all(np.isfinite(curvature)):
            raise ValueError(
                "Le champ de courbure contient une valeur "
                "non finie."
            )

        curvature_weight = np.exp(
            cfg.characteristic_length**2
            * curvature
        )

        intensity_rate[index] = spatial_mean(
            omega**2 * curvature_weight,
            spacing,
        )

        delta_time = (
            time - previous_time
            if previous_time is not None
            else None
        )

        metrics = structural_metrics(
            omega,
            spacing,
            previous_omega,
            delta_time,
            structural_length=structural_length,
            structural_weights=weights_array,
        )

        structure_rate[index] = metrics[
            "structure_score"
        ]

        heterogeneity[index] = metrics[
            "heterogeneity"
        ]

        localization[index] = metrics[
            "localization"
        ]

        roughness[index] = metrics[
            "roughness"
        ]

        sign_mixing[index] = metrics[
            "sign_mixing"
        ]

        temporal_deformation[index] = metrics[
            "temporal_deformation"
        ]

        # Diagnostic couplé expérimental.
        # Il ne remplace pas les deux axes indépendants.
        coupled_rate[index] = (
            intensity_rate[index]
            * (1.0 + structure_rate[index])
        )

        previous_omega = omega.copy()
        previous_time = time

    # La déformation calculée à l'indice i correspond à
    # l'intervalle temporel [t_(i-1), t_i].
    #
    # Elle est donc intégrée directement sur les intervalles,
    # sans lui attribuer artificiellement une valeur nodale.
    if len(times) < 2:
        raise ValueError(
            "La simulation exige au moins deux instants."
        )

    interval_dt = np.diff(times)

    if (
        not np.all(np.isfinite(interval_dt))
        or np.any(interval_dt <= 0.0)
    ):
        raise ValueError(
            "Les instants doivent être finis et "
            "strictement croissants."
        )

    observed_duration = float(
        times[-1] - times[0]
    )

    interval_midpoints = 0.5 * (
        times[:-1] + times[1:]
    )

    interval_deformation = (
        temporal_deformation[1:].copy()
    )

    bounded_heterogeneity = (
        np.maximum(heterogeneity, 0.0)
        / (
            1.0
            + np.maximum(heterogeneity, 0.0)
        )
    )

    bounded_localization = (
        np.maximum(localization, 0.0)
        / (
            1.0
            + np.maximum(localization, 0.0)
        )
    )

    bounded_roughness = (
        np.maximum(roughness, 0.0)
        / (
            1.0
            + np.maximum(roughness, 0.0)
        )
    )

    bounded_sign_mixing = np.clip(
        sign_mixing,
        0.0,
        1.0,
    )

    bounded_interval_deformation = (
        np.maximum(interval_deformation, 0.0)
        / (
            1.0
            + np.maximum(interval_deformation, 0.0)
        )
    )

    # Les quatre composantes nodales sont évaluées au milieu
    # de chaque intervalle par moyenne trapézoïdale.
    component_intervals = np.vstack(
        (
            0.5 * (
                bounded_heterogeneity[:-1]
                + bounded_heterogeneity[1:]
            ),
            0.5 * (
                bounded_localization[:-1]
                + bounded_localization[1:]
            ),
            0.5 * (
                bounded_roughness[:-1]
                + bounded_roughness[1:]
            ),
            0.5 * (
                bounded_sign_mixing[:-1]
                + bounded_sign_mixing[1:]
            ),
            bounded_interval_deformation,
        )
    )

    interval_structure = np.tensordot(
        weights_array,
        component_intervals,
        axes=(0, 0),
    )

    component_index_values = (
        np.sum(
            component_intervals * interval_dt,
            axis=1,
        )
        / observed_duration
    )

    component_indices = {
        component_name: float(component_value)
        for component_name, component_value in zip(
            STRUCTURAL_COMPONENT_NAMES,
            component_index_values,
            strict=True,
        )
    }

    intensity_interval = 0.5 * (
        intensity_rate[:-1]
        + intensity_rate[1:]
    )

    coupled_interval = (
        intensity_interval
        * (1.0 + interval_structure)
    )

    intensity_index = float(
        np.trapezoid(
            intensity_rate,
            times,
        )
        / observed_duration
    )

    temporal_deformation_index = float(
        np.sum(
            interval_deformation
            * interval_dt
        )
        / observed_duration
    )

    structure_index = float(
        np.sum(
            interval_structure
            * interval_dt
        )
        / observed_duration
    )

    coupled_index = float(
        np.sum(
            coupled_interval
            * interval_dt
        )
        / observed_duration
    )

    # Séries nodales uniquement destinées aux graphiques
    # et aux fichiers CSV. Les indices ci-dessus utilisent
    # directement les valeurs d'intervalle.
    temporal_deformation = np.interp(
        times,
        interval_midpoints,
        interval_deformation,
        left=float(interval_deformation[0]),
        right=float(interval_deformation[-1]),
    )

    structure_rate = np.interp(
        times,
        interval_midpoints,
        interval_structure,
        left=float(interval_structure[0]),
        right=float(interval_structure[-1]),
    )

    coupled_rate = np.interp(
        times,
        interval_midpoints,
        coupled_interval,
        left=float(coupled_interval[0]),
        right=float(coupled_interval[-1]),
    )

    return {
        "name": name,
        "intensity_rate": intensity_rate,
        "structure_rate": structure_rate,
        "coupled_rate": coupled_rate,
        "heterogeneity": heterogeneity,
        "localization": localization,
        "roughness": roughness,
        "sign_mixing": sign_mixing,
        "temporal_deformation": temporal_deformation,
        "temporal_deformation_interval": interval_deformation,
        "temporal_interval_dt": interval_dt,
        "temporal_interval_midpoints": interval_midpoints,
        "temporal_deformation_index": temporal_deformation_index,
        "structure_interval": interval_structure,
        "coupled_interval": coupled_interval,
        "structural_component_names": STRUCTURAL_COMPONENT_NAMES,
        "structural_weights": tuple(
            float(value)
            for value in weights_array
        ),
        "component_indices": component_indices,
        "intensity_index": intensity_index,
        "structure_index": structure_index,
        "coupled_index": coupled_index,
    }


def main() -> None:
    cfg = Config()

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

    scenarios = (
        (
            "calme_irrotationnel",
            calm_field,
        ),
        (
            "vortex_coherent",
            coherent_vortex,
        ),
        (
            "multi_vortex_complexe",
            multi_vortex_field,
        ),
    )

    results = [
        simulate(
            name,
            velocity_function,
            x,
            y,
            times,
            spacing,
            cfg,
        )
        for name, velocity_function in scenarios
    ]

    output_dir = Path("itd_v10_results")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_path = output_dir / "summary.csv"

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as summary_file:
        summary_file.write(
            "scenario,"
            "intensity_index,"
            "structure_index,"
            "coupled_diagnostic\n"
        )

        for result in results:
            summary_file.write(
                f'{result["name"]},'
                f'{result["intensity_index"]},'
                f'{result["structure_index"]},'
                f'{result["coupled_index"]}\n'
            )

    for result in results:
        name = str(result["name"])

        table = np.column_stack(
            (
                times,
                np.asarray(result["intensity_rate"]),
                np.asarray(result["structure_rate"]),
                np.asarray(result["coupled_rate"]),
                np.asarray(result["heterogeneity"]),
                np.asarray(result["localization"]),
                np.asarray(result["roughness"]),
                np.asarray(result["sign_mixing"]),
                np.asarray(
                    result["temporal_deformation"]
                ),
            )
        )

        np.savetxt(
            output_dir / f"{name}.csv",
            table,
            delimiter=",",
            header=(
                "time,"
                "intensity_rate,"
                "structure_rate,"
                "coupled_rate,"
                "heterogeneity,"
                "localization,"
                "roughness,"
                "sign_mixing,"
                "temporal_deformation"
            ),
            comments="",
        )

    plt.figure(figsize=(10, 6))

    for result in results:
        plt.plot(
            times,
            np.asarray(result["structure_rate"]),
            label=str(result["name"]),
        )

    plt.xlabel("Temps")
    plt.ylabel("Indice structurel instantané")
    plt.title("Évolution de la complexité structurelle")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir / "structure_over_time.png",
        dpi=160,
    )
    plt.close()

    plt.figure(figsize=(9, 7))

    for result in results:
        intensity = float(
            result["intensity_index"]
        )

        structure = float(
            result["structure_index"]
        )

        plt.scatter(
            intensity,
            structure,
            s=100,
        )

        plt.annotate(
            str(result["name"]),
            (intensity, structure),
            xytext=(8, 6),
            textcoords="offset points",
        )

    plt.xlabel("Intensité dynamique ITD")
    plt.ylabel("Complexité structurelle")
    plt.title(
        "Espace dynamique à deux dimensions"
    )
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        output_dir / "intensity_structure_map.png",
        dpi=160,
    )
    plt.close()

    calm = results[0]
    coherent = results[1]
    complex_result = results[2]

    assert float(calm["intensity_index"]) < 1.0e-20
    assert float(calm["structure_index"]) < 1.0e-20

    assert (
        float(coherent["intensity_index"])
        > float(complex_result["intensity_index"])
    )

    assert (
        float(complex_result["structure_index"])
        > float(coherent["structure_index"])
    )

    print("=== SIMULATEUR ITD VERSION 10 ===")
    print(
        "Longueur structurelle :",
        f"{STRUCTURAL_LENGTH:.6f}",
    )

    for result in results:
        print()
        print(
            "Scénario             :",
            result["name"],
        )
        print(
            "Intensité ITD        :",
            f'{float(result["intensity_index"]):.12f}',
        )
        print(
            "Structure            :",
            f'{float(result["structure_index"]):.12f}',
        )
        print(
            "Diagnostic couplé    :",
            f'{float(result["coupled_index"]):.12f}',
        )

    print()
    print(
        "Validation deux axes : RÉUSSIE"
    )
    print(
        "Résumé               :",
        summary_path.resolve(),
    )


if __name__ == "__main__":
    main()
