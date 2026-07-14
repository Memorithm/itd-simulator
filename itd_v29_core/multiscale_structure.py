"""Profil structurel multi-échelle du simulateur ITD V29."""

from __future__ import annotations

import numpy as np

from itd_v29_core.constants import (
    STRUCTURAL_COMPONENT_NAMES,
)

def validate_structural_length_grid(
    structural_lengths: object,
) -> np.ndarray:
    """
    Valide une grille strictement croissante de
    longueurs structurelles positives ou nulles.
    """
    if isinstance(
        structural_lengths,
        (str, bytes),
    ):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "former une séquence numérique."
        )

    try:
        array = np.asarray(
            structural_lengths,
            dtype=np.float64,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ValueError(
            "Les longueurs structurelles doivent "
            "former une séquence numérique réelle."
        ) from error

    if array.ndim != 1:
        raise ValueError(
            "Les longueurs structurelles doivent "
            "former un tableau unidimensionnel."
        )

    if array.size < 2:
        raise ValueError(
            "Un profil multi-échelle exige au moins "
            "deux longueurs structurelles."
        )

    if not np.all(np.isfinite(array)):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "être finies."
        )

    if np.any(array < 0.0):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "être positives ou nulles."
        )

    if np.any(np.diff(array) <= 0.0):
        raise ValueError(
            "Les longueurs structurelles doivent "
            "être strictement croissantes."
        )

    copied = np.array(
        array,
        dtype=np.float64,
        copy=True,
    )

    copied.setflags(
        write=False
    )

    return copied


def derive_multiscale_profile(
    reference_result: dict[str, object],
    structural_lengths: object,
) -> dict[str, object]:
    """
    Dérive un profil multi-échelle à partir d'une
    simulation effectuée avec structural_length = 1.

    La rugosité brute vérifie exactement :

        Q_raw(ell) = ell * Q_raw(1).

    Les autres composantes ne dépendent pas de ell.
    """
    lengths = validate_structural_length_grid(
        structural_lengths
    )

    required_keys = (
        "intensity_rate",
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
        "temporal_deformation_interval",
        "temporal_interval_dt",
        "structural_weights",
        "intensity_index",
        "temporal_deformation_index",
    )

    missing = tuple(
        key
        for key in required_keys
        if key not in reference_result
    )

    if missing:
        raise ValueError(
            "Le résultat de référence ne contient "
            "pas toutes les données nécessaires : "
            + ", ".join(missing)
        )

    intensity_rate = np.asarray(
        reference_result["intensity_rate"],
        dtype=np.float64,
    )

    heterogeneity = np.asarray(
        reference_result["heterogeneity"],
        dtype=np.float64,
    )

    localization = np.asarray(
        reference_result["localization"],
        dtype=np.float64,
    )

    unit_roughness = np.asarray(
        reference_result["roughness"],
        dtype=np.float64,
    )

    sign_mixing = np.asarray(
        reference_result["sign_mixing"],
        dtype=np.float64,
    )

    interval_deformation = np.asarray(
        reference_result[
            "temporal_deformation_interval"
        ],
        dtype=np.float64,
    )

    interval_dt = np.asarray(
        reference_result[
            "temporal_interval_dt"
        ],
        dtype=np.float64,
    )

    weights = np.asarray(
        reference_result["structural_weights"],
        dtype=np.float64,
    )

    nodal_size = intensity_rate.size
    interval_size = nodal_size - 1

    nodal_arrays = (
        heterogeneity,
        localization,
        unit_roughness,
        sign_mixing,
    )

    if nodal_size < 2:
        raise ValueError(
            "Le résultat de référence doit contenir "
            "au moins deux instants."
        )

    if any(
        array.shape != (nodal_size,)
        for array in nodal_arrays
    ):
        raise ValueError(
            "Les séries nodales du résultat de "
            "référence ont des formes incohérentes."
        )

    if interval_deformation.shape != (
        interval_size,
    ):
        raise ValueError(
            "La série de déformation d'intervalle "
            "a une forme incohérente."
        )

    if interval_dt.shape != (
        interval_size,
    ):
        raise ValueError(
            "La grille des intervalles temporels "
            "a une forme incohérente."
        )

    if weights.shape != (
        len(STRUCTURAL_COMPONENT_NAMES),
    ):
        raise ValueError(
            "Le vecteur de pondération structurelle "
            "a une forme incohérente."
        )

    all_arrays = (
        intensity_rate,
        heterogeneity,
        localization,
        unit_roughness,
        sign_mixing,
        interval_deformation,
        interval_dt,
        weights,
    )

    if not all(
        np.all(np.isfinite(array))
        for array in all_arrays
    ):
        raise ValueError(
            "Le résultat de référence contient "
            "une valeur non finie."
        )

    if np.any(interval_dt <= 0.0):
        raise ValueError(
            "Les intervalles temporels doivent être "
            "strictement positifs."
        )

    duration = float(
        np.sum(
            interval_dt,
            dtype=np.float64,
        )
    )

    if (
        not np.isfinite(duration)
        or duration <= 0.0
    ):
        raise ValueError(
            "La durée du profil doit être finie "
            "et strictement positive."
        )

    bounded_heterogeneity = (
        np.maximum(
            heterogeneity,
            0.0,
        )
        / (
            1.0
            + np.maximum(
                heterogeneity,
                0.0,
            )
        )
    )

    bounded_localization = (
        np.maximum(
            localization,
            0.0,
        )
        / (
            1.0
            + np.maximum(
                localization,
                0.0,
            )
        )
    )

    bounded_sign_mixing = np.clip(
        sign_mixing,
        0.0,
        1.0,
    )

    bounded_interval_deformation = (
        np.maximum(
            interval_deformation,
            0.0,
        )
        / (
            1.0
            + np.maximum(
                interval_deformation,
                0.0,
            )
        )
    )

    heterogeneity_interval = 0.5 * (
        bounded_heterogeneity[:-1]
        + bounded_heterogeneity[1:]
    )

    localization_interval = 0.5 * (
        bounded_localization[:-1]
        + bounded_localization[1:]
    )

    sign_mixing_interval = 0.5 * (
        bounded_sign_mixing[:-1]
        + bounded_sign_mixing[1:]
    )

    intensity_interval = 0.5 * (
        intensity_rate[:-1]
        + intensity_rate[1:]
    )

    length_count = int(
        lengths.size
    )

    signatures = np.empty(
        (
            length_count,
            len(STRUCTURAL_COMPONENT_NAMES),
        ),
        dtype=np.float64,
    )

    raw_roughness_indices = np.empty(
        length_count,
        dtype=np.float64,
    )

    structure_indices = np.empty(
        length_count,
        dtype=np.float64,
    )

    coupled_indices = np.empty(
        length_count,
        dtype=np.float64,
    )

    component_indices: list[
        dict[str, float]
    ] = []

    structure_intervals: list[
        np.ndarray
    ] = []

    coupled_intervals: list[
        np.ndarray
    ] = []

    for index, structural_length in enumerate(
        lengths
    ):
        raw_roughness = (
            structural_length
            * unit_roughness
        )

        bounded_roughness = (
            np.maximum(
                raw_roughness,
                0.0,
            )
            / (
                1.0
                + np.maximum(
                    raw_roughness,
                    0.0,
                )
            )
        )

        roughness_interval = 0.5 * (
            bounded_roughness[:-1]
            + bounded_roughness[1:]
        )

        raw_roughness_interval = 0.5 * (
            raw_roughness[:-1]
            + raw_roughness[1:]
        )

        component_interval = np.vstack(
            (
                heterogeneity_interval,
                localization_interval,
                roughness_interval,
                sign_mixing_interval,
                bounded_interval_deformation,
            )
        )

        signature = (
            np.sum(
                component_interval
                * interval_dt,
                axis=1,
            )
            / duration
        )

        structure_interval = np.tensordot(
            weights,
            component_interval,
            axes=(0, 0),
        )

        coupled_interval = (
            intensity_interval
            * (
                1.0
                + structure_interval
            )
        )

        structure_index = float(
            np.sum(
                structure_interval
                * interval_dt,
                dtype=np.float64,
            )
            / duration
        )

        coupled_index = float(
            np.sum(
                coupled_interval
                * interval_dt,
                dtype=np.float64,
            )
            / duration
        )

        raw_roughness_index = float(
            np.sum(
                raw_roughness_interval
                * interval_dt,
                dtype=np.float64,
            )
            / duration
        )

        signatures[index] = signature

        structure_indices[index] = (
            structure_index
        )

        coupled_indices[index] = (
            coupled_index
        )

        raw_roughness_indices[index] = (
            raw_roughness_index
        )

        component_indices.append(
            {
                name: float(value)
                for name, value in zip(
                    STRUCTURAL_COMPONENT_NAMES,
                    signature,
                    strict=True,
                )
            }
        )

        structure_intervals.append(
            structure_interval.copy()
        )

        coupled_intervals.append(
            coupled_interval.copy()
        )

    return {
        "name": reference_result.get(
            "name",
            "multiscale",
        ),
        "structural_lengths": lengths,
        "length_count": length_count,
        "structural_component_names": (
            STRUCTURAL_COMPONENT_NAMES
        ),
        "structural_weights": tuple(
            float(value)
            for value in weights
        ),
        "structural_signatures": signatures,
        "component_indices": tuple(
            component_indices
        ),
        "raw_roughness_indices": (
            raw_roughness_indices
        ),
        "structure_indices": structure_indices,
        "coupled_indices": coupled_indices,
        "intensity_index": float(
            reference_result["intensity_index"]
        ),
        "temporal_deformation_index": float(
            reference_result[
                "temporal_deformation_index"
            ]
        ),
        "structure_intervals": tuple(
            structure_intervals
        ),
        "coupled_intervals": tuple(
            coupled_intervals
        ),
        "reference_structural_length": 1.0,
        "reference_result": reference_result,
    }


