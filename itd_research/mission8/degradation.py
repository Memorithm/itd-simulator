"""Noise, masking, resolution and partial-observation degradation sweeps (Mission 8, H66-H68).

Rebuilds each sequence's baseline + structural trajectories and ITD-independent events
from DEGRADED raw frames at each level, then reruns the same established-vs-augmented
holdout comparison as the primary test. Reports established-only, ITD-only, and combined
holdout AUC plus the ITD-specific added value at every level, so H66/H67/H68 are judged on
the ITD-specific effect -- NOT merely on whether the combined model stays accurate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.mission8.baselines import (
    BASELINE_COMPETENT_COMBINED,
    compute_baseline_trajectory,
)
from itd_research.mission8.event_labels import label_structural_events
from itd_research.mission8.fixtures import apply_mask, apply_noise
from itd_research.mission8.prediction import Sequence, make_sequence, run_primary_test
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    compute_structural_trajectory,
)

FloatArray: TypeAlias = NDArray[np.float64]

FrameTuple = tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]

# Under injected noise, tiny derivative-amplified micro-regions can otherwise flood the
# count (see the manufactured Oracle I finding); a robust size floor is required.
_NOISE_MIN_CELLS = 30


def degrade_noise(frames: list[FrameTuple], level: float, seed: int) -> list[FrameTuple]:
    out = []
    for i, (t, u, v, w, x, y, z) in enumerate(frames):
        if level <= 0.0:
            out.append((t, u, v, w, x, y, z))
            continue
        nu, nv, nw = apply_noise(u, v, w, level=level, seed=seed * 1000 + i)
        out.append((t, nu, nv, nw, x, y, z))
    return out


def degrade_mask(frames: list[FrameTuple], fraction: float, seed: int) -> list[FrameTuple]:
    out = []
    for i, (t, u, v, w, x, y, z) in enumerate(frames):
        if fraction <= 0.0:
            out.append((t, u, v, w, x, y, z))
            continue
        mu, mv, mw = apply_mask(u, v, w, fraction=fraction, seed=seed * 1000 + i)
        out.append((t, mu, mv, mw, x, y, z))
    return out


def degrade_downsample(frames: list[FrameTuple], factor: int) -> list[FrameTuple]:
    if factor <= 1:
        return frames
    out = []
    for t, u, v, w, x, y, z in frames:
        sl = np.s_[::factor, ::factor, ::factor]
        out.append((t, u[sl], v[sl], w[sl], x[::factor], y[::factor], z[::factor]))
    return out


def degrade_partial_observation(frames: list[FrameTuple], mode: str) -> list[FrameTuple]:
    """Crop each frame's volume along x (axis 2); coordinates are cropped to match."""
    out = []
    for t, u, v, w, x, y, z in frames:
        nx = x.size
        if mode == "full":
            xs = slice(0, nx)
        elif mode == "central_crop":
            q = nx // 4
            xs = slice(q, nx - q)
        elif mode == "upstream_half":
            xs = slice(0, nx // 2)
        elif mode == "downstream_half":
            xs = slice(nx // 2, nx)
        else:
            raise ValueError(f"unknown partial-observation mode {mode!r}")
        out.append((t, u[:, :, xs], v[:, :, xs], w[:, :, xs], x[xs], y, z))
    return out


@dataclass(frozen=True)
class DegradationLevelResult:
    kind: str
    level: float | int | str
    holdout_auc_established: float
    holdout_auc_itd_only: float
    holdout_auc_augmented: float
    added_value_diff: float
    added_value_ci_low: float
    added_value_ci_high: float

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind, "level": self.level,
            "holdout_auc_established": self.holdout_auc_established,
            "holdout_auc_itd_only": self.holdout_auc_itd_only,
            "holdout_auc_augmented": self.holdout_auc_augmented,
            "added_value_diff": self.added_value_diff,
            "added_value_ci_low": self.added_value_ci_low,
            "added_value_ci_high": self.added_value_ci_high,
        }


def _sequences_from_frames(
    labelled_frames: list[tuple[str, list[FrameTuple]]], *, min_cells: int, horizon: int,
) -> list[Sequence]:
    sequences: list[Sequence] = []
    for sequence_id, frames in labelled_frames:
        baseline = compute_baseline_trajectory(frames, min_cells=min_cells)
        structural = compute_structural_trajectory(frames)
        events, _ = label_structural_events(frames, source_id=sequence_id, min_cells=min_cells)
        sequences.append(make_sequence(sequence_id, baseline, structural, events, horizon=horizon))
    return sequences


def evaluate_degradation_level(
    dev_frames: list[tuple[str, list[FrameTuple]]], holdout_frames: list[tuple[str, list[FrameTuple]]],
    *, kind: str, level: float | int | str, min_cells: int,
    established_names: tuple[str, ...] = BASELINE_COMPETENT_COMBINED,
    itd_names: tuple[str, ...] = ITD_3D_NONREDUNDANT, horizon: int = 2, bootstrap: int = 500,
) -> DegradationLevelResult:
    dev_sequences = _sequences_from_frames(dev_frames, min_cells=min_cells, horizon=horizon)
    holdout_sequences = _sequences_from_frames(holdout_frames, min_cells=min_cells, horizon=horizon)
    result = run_primary_test(
        dev_sequences, holdout_sequences, established_names, itd_names=itd_names, bootstrap=bootstrap,
    )
    return DegradationLevelResult(
        kind=kind, level=level,
        holdout_auc_established=result.holdout_auc_established,
        holdout_auc_itd_only=result.holdout_auc_itd_only,
        holdout_auc_augmented=result.holdout_auc_augmented,
        added_value_diff=result.added_value.diff_mean,
        added_value_ci_low=result.added_value.ci_low,
        added_value_ci_high=result.added_value.ci_high,
    )


def run_degradation_sweep(
    dev_frames: list[tuple[str, list[FrameTuple]]], holdout_frames: list[tuple[str, list[FrameTuple]]],
    *, kind: str, levels: list[float | int | str], seed: int = 42, bootstrap: int = 500,
) -> list[DegradationLevelResult]:
    """Sweep one degradation kind (``noise``, ``mask``, ``downsample``, ``partial_observation``)."""
    results = []
    for level in levels:
        if kind == "noise":
            min_cells = _NOISE_MIN_CELLS if level and float(level) > 0 else 8
            dev_t = [(sid, degrade_noise(fr, float(level), seed)) for sid, fr in dev_frames]
            holdout_t = [(sid, degrade_noise(fr, float(level), seed + 1)) for sid, fr in holdout_frames]
        elif kind == "mask":
            min_cells = 8
            dev_t = [(sid, degrade_mask(fr, float(level), seed)) for sid, fr in dev_frames]
            holdout_t = [(sid, degrade_mask(fr, float(level), seed + 1)) for sid, fr in holdout_frames]
        elif kind == "downsample":
            min_cells = max(2, 8 // max(int(level), 1))
            dev_t = [(sid, degrade_downsample(fr, int(level))) for sid, fr in dev_frames]
            holdout_t = [(sid, degrade_downsample(fr, int(level))) for sid, fr in holdout_frames]
        elif kind == "partial_observation":
            min_cells = 8
            dev_t = [(sid, degrade_partial_observation(fr, str(level))) for sid, fr in dev_frames]
            holdout_t = [(sid, degrade_partial_observation(fr, str(level))) for sid, fr in holdout_frames]
        else:
            raise ValueError(f"unknown degradation kind {kind!r}")
        results.append(evaluate_degradation_level(
            dev_t, holdout_t, kind=kind, level=level, min_cells=min_cells, bootstrap=bootstrap,
        ))
    return results
