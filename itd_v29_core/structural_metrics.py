"""
Extraction de la signature structurelle et de ses poids.

Module généré automatiquement pour ITD V29.15.
L'API historique reste réexportée par itd_v29.py.
"""

from __future__ import annotations

import numpy as np

from itd_v29_core.constants import (
    DEFAULT_STRUCTURAL_WEIGHTS,
    STRUCTURAL_LENGTH,
    ZERO_THRESHOLD,
)

from itd_v29_core.spatial_geometry import normalize_spatial_geometry

from itd_v29_core.spatial_operators import (
    bounded,
    scalar_gradient_with_boundary,
    spatial_mean,
    validate_boundary_mode,
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


def structural_metrics(
    omega: np.ndarray,
    spacing: object,
    previous_omega: np.ndarray | None,
    delta_time: float | None,
    structural_length: float = STRUCTURAL_LENGTH,
    structural_weights: object = DEFAULT_STRUCTURAL_WEIGHTS,
    boundary_mode: str = "finite",
) -> dict[str, float]:
    geometry = normalize_spatial_geometry(
        spacing
    )

    structural_length = float(
        structural_length
    )

    boundary_mode = validate_boundary_mode(
        boundary_mode
    )

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

    omega = np.asarray(
        omega,
        dtype=np.float64,
    )

    if omega.ndim != 2:
        raise ValueError(
            "Le champ de vorticité doit être 2D."
        )

    if not np.all(np.isfinite(omega)):
        raise ValueError(
            "Le champ de vorticité contient une "
            "valeur non finie."
        )

    def mean_field(
        field: np.ndarray,
    ) -> float:
        return spatial_mean(
            field,
            geometry,
            boundary_mode,
        )

    abs_omega = np.abs(omega)
    mean_square = mean_field(omega**2)

    rms = float(
        np.sqrt(
            max(mean_square, 0.0)
        )
    )

    if rms < ZERO_THRESHOLD:
        return {
            "heterogeneity": 0.0,
            "localization": 0.0,
            "roughness": 0.0,
            "sign_mixing": 0.0,
            "temporal_deformation": 0.0,
            "structure_score": 0.0,
        }

    mean_absolute = mean_field(abs_omega)

    absolute_deviation = (
        abs_omega - mean_absolute
    )

    weighted_variance = mean_field(
        absolute_deviation**2
    )

    heterogeneity = float(
        np.sqrt(
            max(weighted_variance, 0.0)
        )
        / max(mean_absolute, ZERO_THRESHOLD)
    )

    localization = float(
        mean_field(omega**4)
        / max(mean_square**2, ZERO_THRESHOLD)
        - 1.0
    )

    gradient_y, gradient_x = (
        scalar_gradient_with_boundary(
            omega,
            geometry,
            boundary_mode,
        )
    )

    gradient_norm = np.sqrt(
        gradient_x**2
        + gradient_y**2
    )

    roughness = float(
        structural_length
        * mean_field(gradient_norm)
        / max(rms, ZERO_THRESHOLD)
    )

    sign_mixing = float(
        1.0
        - abs(mean_field(omega))
        / max(mean_absolute, ZERO_THRESHOLD)
    )

    sign_mixing = float(
        np.clip(
            sign_mixing,
            0.0,
            1.0,
        )
    )

    temporal_deformation = 0.0

    if (
        previous_omega is not None
        and delta_time is not None
        and delta_time > 0.0
    ):
        previous_omega = np.asarray(
            previous_omega,
            dtype=np.float64,
        )

        if previous_omega.shape != omega.shape:
            raise ValueError(
                "Les champs de vorticité successifs "
                "doivent avoir la même forme."
            )

        previous_rms = float(
            np.sqrt(
                max(
                    mean_field(
                        previous_omega**2
                    ),
                    0.0,
                )
            )
        )

        reference_rms = 0.5 * (
            rms + previous_rms
        )

        if reference_rms >= ZERO_THRESHOLD:
            temporal_deformation = float(
                np.sqrt(
                    max(
                        mean_field(
                            (
                                omega
                                - previous_omega
                            ) ** 2
                        ),
                        0.0,
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
