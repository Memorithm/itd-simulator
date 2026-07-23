"""Region-conditioned ITD-vs-rotation agreement on a PIV field (research, H14).

Tests the falsifiable version of "PIV validates ITD in every vortex region": within
the genuinely rotation-dominated region (Okubo-Weiss ``W < 0``), does ITD's local
rotational intensity ``omega^2`` rank-agree with an independent rotation-strength
diagnostic (2D swirling strength ``lambda_ci``)? The agreement is reported both
whole-field and *conditioned on the rotation region*, so shear-dominated background
cannot inflate it. Labels (the rotation region) are ITD-independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d import okubo_weiss_2d, velocity_gradient_2d

FloatArray: TypeAlias = NDArray[np.float64]


def _spearman(a: FloatArray, b: FloatArray) -> float:
    if a.size < 4:
        return float("nan")
    ra = np.argsort(np.argsort(a, kind="mergesort")).astype(np.float64)
    rb = np.argsort(np.argsort(b, kind="mergesort")).astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    denom = float(np.sqrt(np.sum(ra**2) * np.sum(rb**2)))
    return float(np.sum(ra * rb) / denom) if denom > 0 else float("nan")


def swirling_strength_2d(gradient: FloatArray) -> FloatArray:
    """2D swirling strength ``lambda_ci`` (imaginary eigenvalue part) per node."""
    trace = gradient[..., 0, 0] + gradient[..., 1, 1]
    det = gradient[..., 0, 0] * gradient[..., 1, 1] - gradient[..., 0, 1] * gradient[..., 1, 0]
    discriminant = trace**2 - 4.0 * det
    return np.asarray(np.sqrt(np.maximum(-discriminant, 0.0)) / 2.0, dtype=np.float64)


@dataclass(frozen=True)
class PivAgreement:
    """Region-conditioned agreement between ITD intensity and rotation strength."""

    n_nodes: int
    rotation_fraction: float
    whole_field_spearman: float
    rotation_region_spearman: float
    jaccard_top_intensity_rotation: float

    def as_dict(self) -> dict[str, object]:
        return {
            "n_nodes": self.n_nodes,
            "rotation_fraction": self.rotation_fraction,
            "whole_field_spearman": self.whole_field_spearman,
            "rotation_region_spearman": self.rotation_region_spearman,
            "jaccard_top_intensity_rotation": self.jaccard_top_intensity_rotation,
        }


def region_conditioned_agreement(
    u: FloatArray, v: FloatArray, x: FloatArray, y: FloatArray, top_fraction: float = 0.2
) -> PivAgreement:
    """Whole-field and rotation-region rank agreement of ITD intensity vs swirl."""
    gradient = velocity_gradient_2d(u, v, x, y, "finite")
    vorticity = gradient[..., 1, 0] - gradient[..., 0, 1]
    intensity = vorticity**2
    swirl = swirling_strength_2d(gradient)
    okubo = okubo_weiss_2d(gradient)
    rotation = okubo < 0.0

    flat_intensity = intensity.ravel()
    flat_swirl = swirl.ravel()
    flat_rotation = rotation.ravel()

    whole = _spearman(flat_intensity, flat_swirl)
    region = _spearman(flat_intensity[flat_rotation], flat_swirl[flat_rotation])

    k = max(int(round(top_fraction * flat_intensity.size)), 1)
    top_idx = np.argsort(flat_intensity)[-k:]
    top_mask = np.zeros(flat_intensity.size, dtype=bool)
    top_mask[top_idx] = True
    intersection = int(np.sum(top_mask & flat_rotation))
    union = int(np.sum(top_mask | flat_rotation))
    jaccard = intersection / union if union else 0.0

    return PivAgreement(
        n_nodes=int(flat_intensity.size),
        rotation_fraction=float(np.mean(flat_rotation)),
        whole_field_spearman=whole,
        rotation_region_spearman=region,
        jaccard_top_intensity_rotation=jaccard,
    )


def classify_h14(agreement: PivAgreement) -> tuple[str, str]:
    """H14 verdict from the region-conditioned agreement on real PIV."""
    strong = 0.7
    moderate = 0.3
    if agreement.rotation_region_spearman >= strong and agreement.whole_field_spearman >= moderate:
        return (
            "supported within tested scope",
            "ITD intensity agrees with rotation strength both whole-field and in the "
            "rotation region on this PIV field.",
        )
    if agreement.rotation_region_spearman >= moderate:
        return (
            "partially supported",
            f"ITD intensity agrees with rotation strength moderately *inside* vortices "
            f"(Spearman {agreement.rotation_region_spearman:.2f}) but poorly whole-field "
            f"({agreement.whole_field_spearman:.2f}; top-intensity/rotation Jaccard "
            f"{agreement.jaccard_top_intensity_rotation:.2f}) -- shear inflates intensity, "
            "so the 'every vortex region' claim fails.",
        )
    return (
        "not supported",
        f"ITD intensity does not agree with rotation strength even inside vortices "
        f"(Spearman {agreement.rotation_region_spearman:.2f}) on this PIV field.",
    )
