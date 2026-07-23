"""Tests for region-conditioned PIV agreement (H14)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from itd_research.external_validation.piv_agreement import (
    classify_h14,
    region_conditioned_agreement,
    swirling_strength_2d,
)

_EXCERPT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "external" / "biofilm_piv_excerpt.npz"


def _rigid_rotation(nodes: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    coords = np.linspace(-1.0, 1.0, nodes)
    yy, xx = np.meshgrid(coords, coords, indexing="ij")
    return -yy, xx, coords


def test_swirling_strength_positive_in_solid_rotation() -> None:
    from itd_research.diagnostics_3d import velocity_gradient_2d

    u, v, coords = _rigid_rotation()
    gradient = velocity_gradient_2d(u, v, coords, coords, "finite")
    swirl = swirling_strength_2d(gradient)
    assert np.all(swirl[2:-2, 2:-2] > 0.0)  # solid rotation swirls everywhere


def test_region_conditioned_agreement_on_rotation_is_high() -> None:
    u, v, coords = _rigid_rotation()
    agreement = region_conditioned_agreement(u, v, coords, coords)
    # Solid-body rotation is entirely rotation-dominated.
    assert agreement.rotation_fraction > 0.8
    assert 0.0 <= agreement.jaccard_top_intensity_rotation <= 1.0


def test_biofilm_excerpt_shear_contamination_is_measurable() -> None:
    data = np.load(_EXCERPT)
    a = region_conditioned_agreement(data["u"], data["v"], data["x"], data["y"])
    # In-region agreement exceeds whole-field agreement (shear inflates intensity).
    assert a.rotation_region_spearman > a.whole_field_spearman
    verdict, _ = classify_h14(a)
    assert verdict in {"supported within tested scope", "partially supported", "not supported"}
