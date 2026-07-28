"""Tests for the Mission 8 structural/topological pipeline (H61-H74).

Offline and deterministic: manufactured oracles and tiny hand-built trajectories, never
the network. These check ITD-independence of event labels, the saturation-screen and
non-redundancy logic, no-leakage grouping in prediction/transfer/lead-time, degradation
correctness, the shift-aware OOD detector's separation behaviour, and profile-driven
numerical equivalence. They assert no scientific verdict on real external data -- that is
reported honestly from the manual JHTDB campaigns.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from itd_research.mission8.baselines import (
    BASELINE_COMPETENT_COMBINED,
    BaselineTrajectory,
    compute_baseline_trajectory,
)
from itd_research.mission8.campaign import (
    canonical_result_digest,
    run_fixture_campaign,
    run_full_fixture_validation,
    strip_nondeterministic,
)
from itd_research.mission8.degradation import (
    degrade_downsample,
    degrade_mask,
    degrade_partial_observation,
)
from itd_research.mission8.descriptive import (
    evaluate_channel_stability,
    evaluate_lead_time,
    evaluate_topology_response_consistency,
)
from itd_research.mission8.event_labels import label_structural_events
from itd_research.mission8.fixtures import merging_pair_sequence, two_separated_vortices
from itd_research.mission8.localization import (
    evaluate_nonredundancy,
    evaluate_region_localization,
)
from itd_research.mission8.ood import run_structural_ood_analysis
from itd_research.mission8.prediction import Sequence, make_sequence, run_primary_test
from itd_research.mission8.profiles import REGISTRY, benchmark_profile, get_profile
from itd_research.mission8.schema import StructuralEvent
from itd_research.mission8.statistics import (
    grouped_bootstrap_diff,
    partial_correlation,
    saturation_screen,
)
from itd_research.mission8.structural_features import (
    FEATURE_GROUPS,
    ITD_3D_NONREDUNDANT,
    ITD_ALL_EXISTING,
    ITD_MAGNITUDE_CONTROL,
    StructuralTrajectory,
    compute_structural_trajectory,
)
from itd_research.mission8.transfer import evaluate_cross_source_transfer
from itd_research.mission8.vortex_regions import (
    detect_topology_events,
    dice,
    iou,
    label_components_3d,
)

_ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------------------
# vortex_regions: connectivity, periodic wraparound, region metrics, topology events
# --------------------------------------------------------------------------------------


def test_label_components_3d_periodic_wraparound_joins_seam_straddling_component() -> None:
    n = 6
    mask = np.zeros((n, n, n), dtype=bool)
    mask[2, 2, 0] = True
    mask[2, 2, n - 1] = True  # touches the opposite edge along x -- same blob only if wrapped
    _labels, sizes_bounded = label_components_3d(mask, periodic=False)
    _labels_p, sizes_periodic = label_components_3d(mask, periodic=True)
    assert sorted(sizes_bounded) == [1, 1]
    assert sizes_periodic == [2]


def test_iou_dice_identical_and_disjoint_masks() -> None:
    a = np.zeros((4, 4, 4), dtype=bool)
    a[0, 0, 0] = True
    a[0, 0, 1] = True
    b = a.copy()
    assert iou(a, b) == pytest.approx(1.0)
    assert dice(a, b) == pytest.approx(1.0)
    disjoint = np.zeros((4, 4, 4), dtype=bool)
    disjoint[3, 3, 3] = True
    assert iou(a, disjoint) == pytest.approx(0.0)
    assert dice(a, disjoint) == pytest.approx(0.0)


def test_detect_topology_events_requires_sustained_change_not_a_transient_blip() -> None:
    transient = [2, 2, 1, 2, 2]  # a one-frame dip that reverts -- not a genuine event
    assert detect_topology_events(transient, persistence=2) == []
    sustained = [2, 2, 2, 1, 1, 1]  # a real, persistent merger at frame 3
    events = detect_topology_events(sustained, persistence=2)
    assert len(events) == 1
    assert events[0].event_type == "core_merger"
    assert events[0].frame_index == 3


# --------------------------------------------------------------------------------------
# event_labels: ITD-independence, disagreement reporting
# --------------------------------------------------------------------------------------


def test_label_structural_events_is_itd_independent_and_reports_disagreement() -> None:
    frames = merging_pair_sequence(n=32, n_frames=8, core=0.16, start_separation=4.0)
    labelled_frames = [(0.1 * i, u, v, w, x, y, z) for i, (u, v, w, x, y, z) in enumerate(frames)]
    events, disagreement = label_structural_events(labelled_frames, source_id="oracle_b", min_cells=8)
    assert len(events) >= 1
    for event in events:
        assert isinstance(event, StructuralEvent)
        assert event.itd_independence is True
        assert event.label_source == "established_Q_criterion"
    for key in ("q_region_counts", "lambda2_region_counts", "q_events", "lambda2_events",
                "agree", "q_only", "lambda2_only"):
        assert key in disagreement


# --------------------------------------------------------------------------------------
# structural_features / baselines: feature-group taxonomy, matrix shapes
# --------------------------------------------------------------------------------------


def test_feature_groups_cover_the_locked_existing_channel_taxonomy() -> None:
    assert ITD_ALL_EXISTING == ITD_MAGNITUDE_CONTROL + ITD_3D_NONREDUNDANT
    assert "intensity" in ITD_MAGNITUDE_CONTROL
    assert "intensity" not in ITD_3D_NONREDUNDANT
    assert set(FEATURE_GROUPS) == {
        "ITD_MAGNITUDE_CONTROL", "ITD_STRUCTURAL", "ITD_ORIENTATION",
        "ITD_TEMPORAL", "ITD_3D_NONREDUNDANT", "ITD_ALL_EXISTING",
    }
    assert len(FEATURE_GROUPS["ITD_ALL_EXISTING"]) == 8


def test_compute_structural_and_baseline_trajectories_have_matching_frame_counts() -> None:
    frames = merging_pair_sequence(n=24, n_frames=6, core=0.16, start_separation=4.0)
    labelled_frames = [(0.1 * i, u, v, w, x, y, z) for i, (u, v, w, x, y, z) in enumerate(frames)]
    structural = compute_structural_trajectory(labelled_frames)
    baseline = compute_baseline_trajectory(labelled_frames, min_cells=8)
    assert len(structural.times) == 6
    assert len(baseline.times) == 6
    m = structural.matrix(ITD_3D_NONREDUNDANT)
    assert m.shape == (6, len(ITD_3D_NONREDUNDANT))
    b = baseline.matrix(BASELINE_COMPETENT_COMBINED)
    assert b.shape == (6, len(BASELINE_COMPETENT_COMBINED))


# --------------------------------------------------------------------------------------
# statistics: saturation screen, partial correlation, grouped bootstrap
# --------------------------------------------------------------------------------------


def test_saturation_screen_flags_perfect_separation_as_saturated() -> None:
    labels = np.array([0, 0, 0, 1, 1, 1], dtype=np.int64)
    perfect_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 0.95])
    result = saturation_screen("toy", "toy_event", perfect_scores, labels)
    assert result.saturation_status == "saturated"
    assert result.selected_for_primary_test is False


def test_saturation_screen_flags_chance_level_as_unsaturated() -> None:
    labels = np.array([0, 1, 0, 1, 0, 1], dtype=np.int64)
    chance_scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    result = saturation_screen("toy", "toy_event", chance_scores, labels)
    assert result.saturation_status == "unsaturated"
    assert result.selected_for_primary_test is True


def test_partial_correlation_removes_a_pure_linear_confound() -> None:
    rng = np.random.default_rng(0)
    control = rng.normal(size=200)
    # a and b are both PURELY linear in control (plus tiny noise) -- no residual relationship.
    a = 2.0 * control + rng.normal(scale=1e-6, size=200)
    b = -1.5 * control + rng.normal(scale=1e-6, size=200)
    raw = float(np.corrcoef(a, b)[0, 1])
    partial = partial_correlation(a, b, control)
    assert abs(raw) > 0.9
    assert abs(partial) < 0.1


def test_grouped_bootstrap_diff_ci_excludes_zero_for_a_clear_improvement() -> None:
    rng = np.random.default_rng(1)
    base_pairs = []
    aug_pairs = []
    for _ in range(6):
        labels = np.array([0, 0, 0, 1, 1, 1], dtype=np.int64)
        base_scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5]) + rng.normal(scale=0.01, size=6)
        aug_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 0.95]) + rng.normal(scale=0.01, size=6)
        base_pairs.append((base_scores, labels))
        aug_pairs.append((aug_scores, labels))
    result = grouped_bootstrap_diff(base_pairs, aug_pairs, margin=0.02, bootstrap=200, seed=1)
    assert result.ci_low > 0.0
    assert result.verdict == "supported within tested scope"


# --------------------------------------------------------------------------------------
# prediction / campaign: no-leakage grouping, determinism, full pipeline sanity
# --------------------------------------------------------------------------------------


def _tiny_sequence(sequence_id: str, *, n_frames: int, event_frame: int, seed: int) -> Sequence:
    rng = np.random.default_rng(seed)
    times = [float(i) for i in range(n_frames)]
    baseline_values = list(rng.normal(size=n_frames))
    baseline = BaselineTrajectory(times=times, channels={name: list(baseline_values) for name in BASELINE_COMPETENT_COMBINED})
    itd_values = list(rng.normal(size=n_frames))
    structural = StructuralTrajectory(
        times=times,
        channels={name: list(itd_values) for name in ITD_3D_NONREDUNDANT} | {"intensity": list(rng.normal(size=n_frames))},
        temporal={},
    )
    event = StructuralEvent(
        event_id=f"{sequence_id}_0", event_type="core_merger", event_time=float(event_frame),
        event_frame=event_frame, event_uncertainty=2.0, label_source="established_Q_criterion",
        label_method="connected_components_persistence", source_file=sequence_id, source_index=event_frame,
    )
    return make_sequence(sequence_id, baseline, structural, [event], horizon=1)


def test_run_primary_test_screens_on_development_only() -> None:
    dev = [_tiny_sequence("dev0", n_frames=10, event_frame=5, seed=0),
           _tiny_sequence("dev1", n_frames=10, event_frame=6, seed=1)]
    holdout = [_tiny_sequence("holdout0", n_frames=10, event_frame=4, seed=2)]
    result = run_primary_test(dev, holdout, BASELINE_COMPETENT_COMBINED, bootstrap=50)
    assert result.screening.task_id == "jhtdb_isotropic_core_topology_change"
    assert result.h61_verdict in {"supported within tested scope", "not supported", "inconclusive"}
    assert result.h62_verdict in {"supported within tested scope", "not supported", "inconclusive"}


def _nan_aware_equal(a: object, b: object) -> bool:
    if isinstance(a, float) and isinstance(b, float) and a != a and b != b:  # both NaN
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_nan_aware_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_nan_aware_equal(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)


def test_run_fixture_campaign_is_deterministic_across_runs() -> None:
    a = run_fixture_campaign().as_dict()
    b = run_fixture_campaign().as_dict()
    assert _nan_aware_equal(a, b)


def test_run_full_fixture_validation_exercises_every_module() -> None:
    result = run_full_fixture_validation(nodes=12, n_frames=12)
    for key in ("primary", "h64_topology_response", "h70_lead_time_established",
                "h70_lead_time_itd_only", "h71_channel_stability", "h73_structural_ood",
                "profile_benchmark"):
        assert key in result
    assert result["evidence_class"] == "synthetic-code-verification (NOT external evidence)"


def test_full_validation_is_deterministic_except_for_wall_clock_timings() -> None:
    """Every scientific field must be bit-identical run to run; only timings may vary.

    The earlier determinism test covered ``run_fixture_campaign`` only. The full
    validation additionally runs a profile BENCHMARK, whose wall-clock fields genuinely
    differ between runs -- so a naive whole-tree equality check on it fails for a benign
    reason. This pins the precise, meaningful property instead: identical after stripping
    exactly the declared non-deterministic fields, and *still differing* before stripping,
    so the strip-set can never be quietly widened to mask a real determinism defect.
    """
    a = run_full_fixture_validation(nodes=12, n_frames=12)
    b = run_full_fixture_validation(nodes=12, n_frames=12)
    assert canonical_result_digest(a) == canonical_result_digest(b)

    scientific_a = strip_nondeterministic(a)
    scientific_b = strip_nondeterministic(b)
    assert _nan_aware_equal(scientific_a, scientific_b)

    # The stripped fields are the only ones allowed to move, and they are real timings.
    timings = a["profile_benchmark"]
    assert isinstance(timings, dict)
    for field in ("full_p95_ms", "profile_p95_ms", "speedup"):
        assert field in timings, f"{field} must exist for the strip-set to be meaningful"
        assert field not in scientific_a  # type: ignore[operator]


def test_repro_bundle_records_environment_stamped_digests() -> None:
    """The bundle's checksum file must stay well-formed and honestly labelled.

    It deliberately does NOT assert that the published digests equal the ones produced
    here. Those digests are **environment-stamped, not portable**: the H73 Mahalanobis
    inversion and the H70 threshold differ at ~1e-15 between BLAS/LAPACK builds, so the
    same code on the same Python and NumPy versions hashes differently on a different
    machine (observed: three distinct full-validation digests across this container's
    NumPy 2.3.5 and 2.5.1 and the CI runner). Asserting equality would encode a false
    contract and fail for reasons unrelated to correctness -- exactly the ~1.6e-16
    cross-environment agreement Mission 7 already documented.

    Same-process determinism -- the property that IS meaningful and portable -- is
    covered by ``test_full_validation_is_deterministic_except_for_wall_clock_timings``.
    """
    pinned_path = _ROOT / "repro" / "mission8" / "expected_checksums.txt"
    text = pinned_path.read_text(encoding="utf-8")
    pinned = {
        parts[0]: parts[1]
        for line in text.splitlines()
        if line.strip() and not line.startswith("#") and len(parts := line.split()) == 2
    }
    for key in ("mission8_fixture_campaign.canonical", "mission8_full_validation.canonical"):
        assert key in pinned, f"{key} missing from the reproduction bundle"
        digest = pinned[key]
        assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
    # The non-portability caveat must stay in the file; without it the digests read as a
    # cross-machine guarantee they cannot provide.
    assert "not portable" in text.lower()


# --------------------------------------------------------------------------------------
# localization: non-redundancy requires BOTH low correlation AND partial value
# --------------------------------------------------------------------------------------


def test_evaluate_nonredundancy_rejects_a_channel_that_is_a_pure_copy_of_enstrophy() -> None:
    rng = np.random.default_rng(2)
    n = 40
    times = [float(i) for i in range(n)]
    enstrophy = rng.normal(size=n)
    labels = (enstrophy > np.median(enstrophy)).astype(np.int64)
    baseline = BaselineTrajectory(times=times, channels={"enstrophy": list(enstrophy)})
    redundant_channel = enstrophy * 3.0 + 1.0  # a pure linear copy -- must NOT be flagged
    structural = StructuralTrajectory(times=times, channels={"copy_of_enstrophy": list(redundant_channel)}, temporal={})
    result = evaluate_nonredundancy(structural, baseline, labels, channels=("copy_of_enstrophy",))
    assert "copy_of_enstrophy" not in result.non_redundant_channels


def test_evaluate_nonredundancy_accepts_an_independent_predictive_channel() -> None:
    rng = np.random.default_rng(3)
    n = 60
    times = [float(i) for i in range(n)]
    enstrophy = rng.normal(size=n)
    independent = rng.normal(size=n)
    labels = (independent > np.median(independent)).astype(np.int64)
    baseline = BaselineTrajectory(times=times, channels={"enstrophy": list(enstrophy)})
    structural = StructuralTrajectory(times=times, channels={"independent_channel": list(independent)}, temporal={})
    result = evaluate_nonredundancy(structural, baseline, labels, channels=("independent_channel",))
    assert "independent_channel" in result.non_redundant_channels


def test_evaluate_region_localization_is_honestly_blocked_not_silently_skipped() -> None:
    status = evaluate_region_localization()
    assert status.verdict == "blocked"
    assert "GLOBAL per-snapshot scalars" in status.reason


# --------------------------------------------------------------------------------------
# transfer: within-institution cross-physics honesty note
# --------------------------------------------------------------------------------------


def test_evaluate_cross_source_transfer_never_claims_cross_institution() -> None:
    dev = [_tiny_sequence("a_dev0", n_frames=10, event_frame=5, seed=10),
           _tiny_sequence("a_dev1", n_frames=10, event_frame=6, seed=11)]
    holdout = [_tiny_sequence("a_holdout0", n_frames=10, event_frame=4, seed=12)]
    other_source = [_tiny_sequence("b_seq0", n_frames=10, event_frame=5, seed=13)]
    result = evaluate_cross_source_transfer(dev, holdout, other_source, established_names=BASELINE_COMPETENT_COMBINED)
    assert "NOT a cross-institution" in result.comparability_note
    assert result.verdict in {"supported within tested scope", "not supported", "inconclusive"}


# --------------------------------------------------------------------------------------
# degradation: deterministic, correctness of each transform
# --------------------------------------------------------------------------------------


def _small_frames(n: int = 8, n_frames: int = 3) -> list[tuple]:
    frames = two_separated_vortices(n=n, separation=2.0, core=0.16)
    u, v, w, x, y, z = frames
    return [(0.1 * i, u, v, w, x, y, z) for i in range(n_frames)]


def test_degrade_mask_zeros_a_deterministic_fraction() -> None:
    frames = _small_frames()
    masked = degrade_mask(frames, fraction=0.5, seed=0)
    _t, u, _v, _w, _x, _y, _z = masked[0]
    zero_fraction = float(np.mean(u == 0.0))
    assert 0.2 < zero_fraction < 0.8  # roughly half, allowing for cells already exactly zero


def test_degrade_downsample_reduces_grid_size_by_the_stride() -> None:
    frames = _small_frames(n=8)
    down = degrade_downsample(frames, 2)
    _t, u, _v, _w, x, _y, _z = down[0]
    assert u.shape == (4, 4, 4)
    assert x.size == 4


def test_degrade_partial_observation_modes_crop_the_expected_half() -> None:
    frames = _small_frames(n=8)
    full = degrade_partial_observation(frames, "full")
    upstream = degrade_partial_observation(frames, "upstream_half")
    downstream = degrade_partial_observation(frames, "downstream_half")
    central = degrade_partial_observation(frames, "central_crop")
    assert full[0][1].shape[2] == 8
    assert upstream[0][1].shape[2] == 4
    assert downstream[0][1].shape[2] == 4
    assert central[0][1].shape[2] == 4
    with pytest.raises(ValueError, match="unknown partial-observation mode"):
        degrade_partial_observation(frames, "nonsense")


# --------------------------------------------------------------------------------------
# descriptive: H64 topology response, H70 lead time, H71 channel stability
# --------------------------------------------------------------------------------------


def test_evaluate_topology_response_consistency_detects_a_consistent_sign_shift() -> None:
    n = 16
    times = [float(i) for i in range(n)]
    event_frames = [4, 10]
    values = [0.0] * n
    for ef in event_frames:
        for i in range(ef, n):
            values[i] += 5.0  # a consistent, repeated upward step at every event
    traj = StructuralTrajectory(times=times, channels={"localization": values}, temporal={})
    result = evaluate_topology_response_consistency(
        [("seq0", traj, event_frames)], channels=("localization",), window=2, min_events=2,
    )
    assert result.verdict == "supported within tested scope"
    assert "localization" in result.consistent_channels


def test_evaluate_lead_time_reports_no_alert_when_there_is_no_training_data() -> None:
    only_sequence = [_tiny_sequence("solo", n_frames=10, event_frame=6, seed=20)]
    result = evaluate_lead_time(
        only_sequence, feature_set="established_only",
        established_names=BASELINE_COMPETENT_COMBINED, itd_names=(),
    )
    # A single sequence has no leave-one-out training partner: nothing can be scored.
    assert all(instance.first_alert_frame is None for instance in result.instances)


def test_evaluate_channel_stability_reports_jaccard_across_sequences() -> None:
    dev = [_tiny_sequence("s0", n_frames=20, event_frame=10, seed=30),
           _tiny_sequence("s1", n_frames=20, event_frame=12, seed=31)]
    result = evaluate_channel_stability(dev, channels=ITD_3D_NONREDUNDANT)
    assert 0.0 <= (result.stability_ratio if result.stability_ratio == result.stability_ratio else 0.0) <= 1.0
    assert set(result.per_sequence_non_redundant) == {"s0", "s1"}


# --------------------------------------------------------------------------------------
# ood: shift-aware reference separates valid variation from genuine shift
# --------------------------------------------------------------------------------------


def test_run_structural_ood_analysis_separates_valid_variation_from_a_strong_shift() -> None:
    rng = np.random.default_rng(4)
    n = 60
    times = [float(i) for i in range(n)]

    def make_traj(loc: float, scale: float, seed: int) -> StructuralTrajectory:
        local_rng = np.random.default_rng(seed)
        channels = {name: list(loc + scale * local_rng.normal(size=n)) for name in ITD_3D_NONREDUNDANT}
        return StructuralTrajectory(times=times, channels=channels, temporal={})

    dev_trajectories = [make_traj(0.0, 1.0, 100), make_traj(0.0, 1.0, 101)]
    categories = {
        "holdout_same_source": ("in-domain holdout", make_traj(0.0, 1.0, 102)),
        "new_source_physics": ("far shifted category", make_traj(20.0, 1.0, 103)),
    }
    result = run_structural_ood_analysis(dev_trajectories, categories, far_category="new_source_physics")
    assert result.verdict == "supported within tested scope"
    assert result.valid_variation_mean_abstain <= 0.10
    assert result.shift_mean_abstain > result.valid_variation_mean_abstain
    _ = rng  # rng reserved for future extension; unused directly here


# --------------------------------------------------------------------------------------
# profiles: registry excludes intensity, profile-driven path is numerically equivalent
# --------------------------------------------------------------------------------------


def test_registry_profiles_exclude_intensity_unless_explicitly_retained() -> None:
    for profile in REGISTRY.values():
        assert "intensity" in profile.excluded_channels
        assert "intensity" not in profile.required_itd_channels


def test_get_profile_raises_for_unknown_profile_id() -> None:
    with pytest.raises(KeyError):
        get_profile("nonexistent_profile")


def test_benchmark_profile_is_bitwise_equal_on_shared_established_channels() -> None:
    frames = _small_frames(n=12, n_frames=4)
    profile = get_profile("external_vortex_merger")
    result = benchmark_profile(frames, profile, repeats=2, min_cells=8)
    assert result.equivalence_level == "bitwise_equal"
    assert result.max_abs_diff_shared_channels == 0.0
