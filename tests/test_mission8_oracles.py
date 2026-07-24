"""Manufactured structural/topological oracles for Mission 8 (section 13, H61-H64).

Deterministic, offline, SOFTWARE/INTERPRETATION oracles -- never external scientific
evidence. They validate the region-detection, topology-tracking and structural-feature
machinery against a KNOWN ground truth before any external claim is made. Also regression
-tests the axis-order bug this file's own construction caught during development.
"""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.diagnostics_3d import q_criterion, velocity_gradient_3d
from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d
from itd_research.mission8 import fixtures as fx
from itd_research.mission8.vortex_regions import (
    background_noise_threshold,
    centroid_distance,
    core_count_series,
    detect_regions,
    detect_topology_events,
    dice,
    iou,
    label_components_3d,
)


def _q_field(u, v, w, x, y, z, mode="periodic"):
    return q_criterion(velocity_gradient_3d(u, v, w, x, y, z, mode))


def test_oracle_a_two_separated_vortices_gives_two_stable_regions() -> None:
    u, v, w, x, y, z = fx.two_separated_vortices()
    q = _q_field(u, v, w, x, y, z)
    thr = background_noise_threshold(q)
    _, regions = detect_regions(q, threshold=thr, comparison="greater", min_cells=4, periodic=True)
    assert len(regions) == 2
    # roughly equal-sized, symmetric cores (a shared, known ground truth, not a fluke).
    sizes = sorted(r.volume_cells for r in regions)
    assert sizes[1] / sizes[0] < 1.2


def test_oracle_b_controlled_merger_has_a_single_known_event() -> None:
    frames = fx.merging_pair_sequence(n_frames=8)
    q_fields = [_q_field(*fr) for fr in frames]
    counts = core_count_series(q_fields, threshold=0.0, comparison="greater", min_cells=4)
    # Recompute with the background-noise-aware threshold per frame (matches detector use).
    counts = [
        len(detect_regions(qf, threshold=background_noise_threshold(qf), comparison="greater", min_cells=4,
                          periodic=True)[1])
        for qf in q_fields
    ]
    assert counts == [2, 2, 2, 2, 1, 1, 1, 1]
    events = detect_topology_events(counts, persistence=2)
    assert len(events) == 1
    assert events[0].event_type == "core_merger"
    assert events[0].frame_index == 4


def test_oracle_c_splitting_structure_is_the_exact_reverse_of_the_merger() -> None:
    frames = fx.splitting_pair_sequence(n_frames=8)
    q_fields = [_q_field(*fr) for fr in frames]
    counts = [
        len(detect_regions(qf, threshold=background_noise_threshold(qf), comparison="greater", min_cells=4,
                          periodic=True)[1])
        for qf in q_fields
    ]
    assert counts == [1, 1, 1, 1, 2, 2, 2, 2]
    events = detect_topology_events(counts, persistence=2)
    assert len(events) == 1
    assert events[0].event_type == "core_split"
    assert events[0].frame_index == 4


def test_oracle_d_rigid_translation_preserves_region_count_and_shape() -> None:
    u, v, w, x, y, z = fx.two_separated_vortices()
    q_before = _q_field(u, v, w, x, y, z)
    thr = background_noise_threshold(q_before)
    _, regions_before = detect_regions(q_before, threshold=thr, comparison="greater", min_cells=4, periodic=True)

    tu, tv, tw = fx.translate_field(u, v, w, shift=(3, 5, -4))
    q_after = _q_field(tu, tv, tw, x, y, z)
    _, regions_after = detect_regions(q_after, threshold=background_noise_threshold(q_after),
                                       comparison="greater", min_cells=4, periodic=True)
    assert len(regions_after) == len(regions_before)
    assert sorted(r.volume_cells for r in regions_after) == sorted(r.volume_cells for r in regions_before)


def test_oracle_e_rotation_preserves_rotation_invariant_channels() -> None:
    u, v, w, x, y, z = fx.two_separated_vortices(n=32, separation=6.0, core=0.4)
    before = evaluate_itd3d(u, v, w, x, y, z, "periodic").as_dict()
    ru, rv, rw = fx.rotate_field_xy(u, v, w, k_quarter_turns=1)
    after = evaluate_itd3d(ru, rv, rw, x, y, z, "periodic").as_dict()
    # Scalar rotation-invariant channels (built from tensor/vector norms and traces, not
    # from any fixed spatial axis) must not change under a rigid 90-degree rotation.
    for name in ("intensity", "heterogeneity", "localization", "roughness"):
        assert after[name] == pytest.approx(before[name], rel=1e-9, abs=1e-12)


def test_oracle_f_amplitude_scaling_behaves_as_declared() -> None:
    u, v, w, x, y, z = fx.two_separated_vortices()
    before = evaluate_itd3d(u, v, w, x, y, z, "periodic").as_dict()
    su, sv, sw = fx.scale_amplitude(u, v, w, factor=2.0)
    after = evaluate_itd3d(su, sv, sw, x, y, z, "periodic").as_dict()
    # intensity is quadratic in the field (mean magnitude^2 * weight) -> scales as factor^2.
    assert after["intensity"] == pytest.approx(before["intensity"] * 4.0, rel=1e-9)
    # localization and heterogeneity are dimensionless ratios -> invariant to amplitude.
    assert after["localization"] == pytest.approx(before["localization"], rel=1e-9, abs=1e-12)
    assert after["heterogeneity"] == pytest.approx(before["heterogeneity"], rel=1e-9, abs=1e-12)


def test_oracle_g_resolution_sweep_grid_sizes() -> None:
    sizes = fx.resolution_sweep_grids(16, factors=(1, 2, 4))
    assert sizes == [16, 32, 64]


def test_oracle_h_masking_degrades_region_detection_without_crashing() -> None:
    u, v, w, x, y, z = fx.two_separated_vortices()
    mu, mv, mw = fx.apply_mask(u, v, w, fraction=0.3, seed=7)
    q = _q_field(mu, mv, mw, x, y, z)
    assert np.all(np.isfinite(q))
    _, regions = detect_regions(q, threshold=background_noise_threshold(q), comparison="greater", min_cells=1,
                                 periodic=True)
    assert len(regions) >= 1  # some structure should survive moderate masking


def test_oracle_i_noise_amplifies_under_derivatives_and_needs_a_size_floor() -> None:
    # Q-criterion differentiates the field, so even 2% velocity noise creates hundreds of
    # tiny spurious Q>0 blobs (high-frequency noise has a large gradient) -- a genuine,
    # important finding: an amplitude-only threshold is not enough under noise, a
    # region-SIZE floor is also needed. At min_cells=4 (fine for the clean signal) the
    # noisy counts explode into the hundreds; a realistic min_cells recovers the true event.
    frames = fx.merging_pair_sequence(n_frames=8)
    noisy_fields = []
    for i, fr in enumerate(frames):
        u, v, w, x, y, z = fr
        nu, nv, nw = fx.apply_noise(u, v, w, level=0.02, seed=100 + i)
        noisy_fields.append(_q_field(nu, nv, nw, x, y, z))

    tiny_floor_counts = [
        len(detect_regions(qf, threshold=background_noise_threshold(qf), comparison="greater",
                            min_cells=4, periodic=True)[1])
        for qf in noisy_fields
    ]
    assert max(tiny_floor_counts) > 50  # noise floods the field with spurious micro-regions

    robust_counts = [
        len(detect_regions(qf, threshold=background_noise_threshold(qf), comparison="greater",
                            min_cells=30, periodic=True)[1])
        for qf in noisy_fields
    ]
    assert robust_counts == [2, 2, 2, 2, 1, 1, 1, 1]
    events = detect_topology_events(robust_counts, persistence=2)
    assert len(events) == 1
    assert events[0].event_type == "core_merger" and events[0].frame_index == 4


def test_oracle_j_pure_shear_has_no_vortex_regions() -> None:
    u, v, w, x, y, z = fx.pure_shear_control()
    q = _q_field(u, v, w, x, y, z)
    assert float(np.max(q)) <= 0.0
    _, regions = detect_regions(q, threshold=0.0, comparison="greater", min_cells=1)
    assert len(regions) == 0


def test_axis_order_regression_z_outer_y_middle_x_inner() -> None:
    # Regression test for the axis-permutation bug caught while building these fixtures:
    # velocity_gradient_3d requires shape (nz, ny, nx); a (nx, ny, nz)-ordered field
    # silently produces a field with (numerically) zero Q everywhere.
    u, v, w, x, y, z = fx.two_separated_vortices()
    assert u.shape == (x.size, y.size, y.size) or u.shape[0] == z.size
    q = _q_field(u, v, w, x, y, z)
    assert float(np.max(q)) > 0.0


def test_region_metrics_iou_dice_centroid_are_sane() -> None:
    mask_a = np.zeros((8, 8, 8), dtype=bool)
    mask_a[2:5, 2:5, 2:5] = True
    mask_b = np.zeros((8, 8, 8), dtype=bool)
    mask_b[3:6, 3:6, 3:6] = True
    assert 0.0 < iou(mask_a, mask_b) < 1.0
    assert 0.0 < dice(mask_a, mask_b) < 1.0
    assert iou(mask_a, mask_a) == 1.0
    assert dice(mask_a, mask_a) == 1.0
    assert centroid_distance((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)) == 5.0


def test_label_components_3d_is_deterministic() -> None:
    rng = np.random.default_rng(0)
    mask = rng.random((10, 10, 10)) > 0.7
    labels_a, sizes_a = label_components_3d(mask)
    labels_b, sizes_b = label_components_3d(mask)
    assert np.array_equal(labels_a, labels_b)
    assert sizes_a == sizes_b
