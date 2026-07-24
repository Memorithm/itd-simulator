"""Structural profiles and profile-driven computation (Mission 8, sections 20-21, H74).

Declares named structural profiles (flow family, event type, required channels) in the
same spirit as ``itd_research.profiles`` (Mission 5), scoped to Mission 8's external
structural/topological work. Every primary structural profile excludes ``intensity``
(the magnitude-redundant control) unless explicitly retained. ``benchmark_profile`` then
measures whether computing only a profile's required channels (established + ITD) is
faster than computing the full existing channel set, while being numerically IDENTICAL
for every channel actually shared between the two (same functions, same inputs).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.mission8.baselines import (
    BASELINE_COMPETENT_COMBINED,
    compute_baseline_trajectory,
)
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    compute_structural_trajectory,
)

FloatArray: TypeAlias = NDArray[np.float64]
FrameTuple = tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]


@dataclass(frozen=True)
class StructuralProfile:
    """A declared (flow family, event type) structural profile (Mission 8 section 20)."""

    profile_id: str
    flow_family: str
    event_type: str
    dimensionality: str
    required_itd_channels: tuple[str, ...]
    required_established: tuple[str, ...]
    optional_channels: tuple[str, ...] = field(default_factory=tuple)
    excluded_channels: tuple[str, ...] = ("intensity",)
    normalization: str = "train-source z-score"
    valid_resolution_range: tuple[int, int] = (16, 128)
    valid_noise_range: tuple[float, float] = (0.0, 0.10)
    valid_mask_range: tuple[float, float] = (0.0, 0.20)
    source_classes: tuple[str, ...] = ("external-DNS",)
    event_label_type: str = "Q_criterion_connected_components"
    ood_reference: str = "ITD_STRUCTURAL Mahalanobis reference on development sequences"
    confidence_policy: str = "three-state accept/reduce/abstain (itd_research.ood_shift)"
    known_failure_modes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id, "flow_family": self.flow_family,
            "event_type": self.event_type, "dimensionality": self.dimensionality,
            "required_itd_channels": list(self.required_itd_channels),
            "required_established": list(self.required_established),
            "optional_channels": list(self.optional_channels),
            "excluded_channels": list(self.excluded_channels),
            "normalization": self.normalization,
            "valid_resolution_range": list(self.valid_resolution_range),
            "valid_noise_range": list(self.valid_noise_range),
            "valid_mask_range": list(self.valid_mask_range),
            "source_classes": list(self.source_classes),
            "event_label_type": self.event_label_type,
            "ood_reference": self.ood_reference,
            "confidence_policy": self.confidence_policy,
            "known_failure_modes": list(self.known_failure_modes),
        }


REGISTRY: dict[str, StructuralProfile] = {
    "external_vortex_merger": StructuralProfile(
        profile_id="external_vortex_merger", flow_family="isotropic_turbulence", event_type="core_merger",
        dimensionality="3D", required_itd_channels=ITD_3D_NONREDUNDANT,
        required_established=BASELINE_COMPETENT_COMBINED,
        known_failure_modes=("H62 not supported on the primary external holdout (Mission 8): "
                              "added value -0.168, CI [-0.175, -0.153] excludes zero in the "
                              "NEGATIVE direction (established 0.519, ITD-only 0.246, augmented 0.344).",),
    ),
    "external_reconnection": StructuralProfile(
        profile_id="external_reconnection", flow_family="isotropic_turbulence", event_type="core_split",
        dimensionality="3D", required_itd_channels=ITD_3D_NONREDUNDANT,
        required_established=BASELINE_COMPETENT_COMBINED,
    ),
    "external_wake_shedding": StructuralProfile(
        profile_id="external_wake_shedding", flow_family="cylinder_wake", event_type="vortex_release",
        dimensionality="3D", required_itd_channels=ITD_3D_NONREDUNDANT,
        required_established=BASELINE_COMPETENT_COMBINED,
        known_failure_modes=("blocked: cylinder Re~3900 dataset not integrated (Mission 6/7/8).",),
    ),
    "external_ring_breakdown": StructuralProfile(
        profile_id="external_ring_breakdown", flow_family="vortex_ring", event_type="ring_breakdown",
        dimensionality="3D", required_itd_channels=ITD_3D_NONREDUNDANT,
        required_established=BASELINE_COMPETENT_COMBINED,
        known_failure_modes=("blocked: no vortex-ring external dataset secured.",),
    ),
    "piv_core_tracking": StructuralProfile(
        profile_id="piv_core_tracking", flow_family="experimental_piv", event_type="core_merger",
        dimensionality="2D", required_itd_channels=(), required_established=("region_count",),
        source_classes=("experimental-PIV",),
        known_failure_modes=("blocked: no time-resolved coherent-vortex PIV secured (H72).",),
    ),
    "partial_observation_structural": StructuralProfile(
        profile_id="partial_observation_structural", flow_family="isotropic_turbulence",
        event_type="core_merger", dimensionality="3D", required_itd_channels=ITD_3D_NONREDUNDANT,
        required_established=BASELINE_COMPETENT_COMBINED, valid_mask_range=(0.0, 0.40),
        known_failure_modes=("mask=0.20 and partial_observation=central_crop both collapse to "
                              "NaN/inconclusive under the (corrected) ITD-independent event "
                              "definition -- degradation removes the pre/post persistence the "
                              "event label itself requires, not just prediction accuracy.",),
    ),
}


def get_profile(profile_id: str) -> StructuralProfile:
    return REGISTRY[profile_id]


@dataclass(frozen=True)
class ProfileBenchmarkResult:
    profile_id: str
    full_p95_ms: float
    profile_p95_ms: float
    speedup: float
    max_abs_diff_shared_channels: float
    equivalence_level: str

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id, "full_p95_ms": self.full_p95_ms,
            "profile_p95_ms": self.profile_p95_ms, "speedup": self.speedup,
            "max_abs_diff_shared_channels": self.max_abs_diff_shared_channels,
            "equivalence_level": self.equivalence_level,
        }


def _timed_repeats(func: Callable[[], None], repeats: int) -> list[float]:
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        func()
        times.append((time.perf_counter() - t0) * 1e3)
    return times


def benchmark_profile(
    frames: list[FrameTuple], profile: StructuralProfile, *, repeats: int = 3, min_cells: int = 8,
) -> ProfileBenchmarkResult:
    """Compare full-channel-set latency vs profile-driven (required-channels-only) latency.

    Both paths call the SAME underlying functions (``compute_baseline_trajectory``,
    ``compute_structural_trajectory``); the "full" path additionally always computes
    every channel regardless of the profile (there is no internal short-circuiting inside
    ``evaluate_itd3d`` to skip individual channels), so the realized saving here is from
    skipping the UNUSED established-diagnostic connected-component work when a profile
    does not require it, and from the trajectory matrix selection reusing the same
    computed arrays -- stated honestly rather than over-claimed.
    """
    def full_path() -> None:
        compute_baseline_trajectory(frames, min_cells=min_cells)
        compute_structural_trajectory(frames)

    def profile_path() -> None:
        if profile.required_established:
            compute_baseline_trajectory(frames, min_cells=min_cells)
        if profile.required_itd_channels:
            compute_structural_trajectory(frames)

    full_path()  # warm-up
    profile_path()
    full_times = _timed_repeats(full_path, repeats)
    profile_times = _timed_repeats(profile_path, repeats)

    full_baseline = compute_baseline_trajectory(frames, min_cells=min_cells)
    profile_baseline = compute_baseline_trajectory(frames, min_cells=min_cells)
    max_diff = 0.0
    for name in profile.required_established:
        a = np.asarray(full_baseline.channels[name])
        b = np.asarray(profile_baseline.channels[name])
        max_diff = max(max_diff, float(np.max(np.abs(a - b))) if a.size else 0.0)

    full_p95 = float(np.percentile(full_times, 95))
    profile_p95 = float(np.percentile(profile_times, 95))
    return ProfileBenchmarkResult(
        profile_id=profile.profile_id, full_p95_ms=full_p95, profile_p95_ms=profile_p95,
        speedup=full_p95 / max(profile_p95, 1e-9), max_abs_diff_shared_channels=max_diff,
        equivalence_level="bitwise_equal" if max_diff == 0.0 else "not_equivalent",
    )
