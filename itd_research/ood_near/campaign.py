"""Near-OOD abstention campaign on the merger family (research, Mission 5, H31).

An OOD reference and a predictor are fitted on an in-distribution merger family (a
narrow circulation/viscosity band). They are then challenged with **subtle** shifts:
untrained circulation, untrained viscosity, and untrained resolution -- flows that are
often still predictable -- and with a **far**-OOD control (Taylor-Green midplane). The
campaign asks whether abstention lowers risk on the genuinely-unreliable shifts without
over-abstaining on the still-usable ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.external_validation.spectral_ns import (
    gaussian_vortex_pair,
    simulate_vorticity,
    spectral_grid,
    velocity_from_vorticity,
)
from itd_research.hard_prediction.evaluation import _matrix, build_labeled
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    RawRun,
    features_from_raw,
    simulate_taylorgreen_raw,
)
from itd_research.hard_prediction.models import LogisticRegression
from itd_research.ood.abstention import risk_coverage_curve, selective_evaluation
from itd_research.ood.reference import fit_reference
from itd_research.prediction.evaluation import roc_auc
from itd_research.prediction.events import core_count_series, detect_merger_frame

FloatArray: TypeAlias = NDArray[np.float64]


def _perturb(nodes: int, seed: int, amplitude: float) -> FloatArray:
    rng = np.random.default_rng(seed)
    field_hat: NDArray[np.complex128] = np.zeros((nodes, nodes), dtype=np.complex128)
    for _ in range(6):
        kx, ky = int(rng.integers(1, 4)), int(rng.integers(1, 4))
        field_hat[ky, kx] += amplitude * np.exp(1j * rng.uniform(0.0, 2.0 * np.pi))
    field = np.fft.ifft2(field_hat).real
    return np.ascontiguousarray(field - field.mean())


def _controlled_merger(
    seed: int, circulation: float, viscosity: float, separation: float, nodes: int
) -> RawRun:
    """A merger run with explicitly controlled parameters (for in/near-OOD bands)."""
    length = 2.0 * np.pi
    grid = spectral_grid(nodes, length)
    spacing = length / nodes
    omega0 = gaussian_vortex_pair(
        grid, circulation=circulation, core=0.5, separation=separation, same_sign=True
    )
    omega0 = omega0 + 0.15 * _perturb(nodes, seed, float(np.max(np.abs(omega0))))
    omega0 = np.ascontiguousarray(omega0 - omega0.mean())
    steps = int(round(2800 * (80 / nodes)))  # keep physical duration ~constant across resolutions
    result = simulate_vorticity(omega0, grid, viscosity, 0.002, steps, max(steps // 20, 1))
    counts = core_count_series(result.vorticity, fraction=0.6, min_cells=max(int(20 * (nodes / 80) ** 2), 6))
    event = detect_merger_frame(counts)
    velocities = tuple(velocity_from_vorticity(o, grid) for o in result.vorticity)
    return RawRun(seed, "merger_controlled", spacing, result.times, event, velocities)


def _feature_matrix(run) -> FloatArray:  # type: ignore[no-untyped-def]
    return np.column_stack([run.features[name] for name in ALL_FEATURES])


@dataclass(frozen=True)
class NearOODResult:
    """Per-group OOD scores, prediction quality, and abstention outcome."""

    group_mean_scores: dict[str, float]
    detection_auc_near: float
    detection_auc_far: float
    predictable_near_auc: float
    selective: dict[str, float]
    unnecessary_abstention_rate: float
    risk_coverage: list[tuple[float, float]]
    h31_verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "group_mean_scores": self.group_mean_scores,
            "detection_auc_near": self.detection_auc_near,
            "detection_auc_far": self.detection_auc_far,
            "predictable_near_auc": self.predictable_near_auc,
            "selective": self.selective,
            "unnecessary_abstention_rate": self.unnecessary_abstention_rate,
            "risk_coverage": [{"coverage": c, "selective_risk": r} for c, r in self.risk_coverage],
            "h31_verdict": self.h31_verdict,
        }


def run_near_ood_campaign(*, quick: bool = False) -> NearOODResult:
    """Fit on an in-distribution merger band; challenge with subtle shifts."""
    nodes = 64 if quick else 80
    in_seeds = (10, 11, 12) if quick else (10, 11, 12, 13)
    near_seeds = (20, 21) if quick else (20, 21, 22)
    tg_seeds = (90,) if quick else (90, 91)

    # In-distribution: narrow circulation/viscosity band.
    in_runs = [_controlled_merger(s, circulation=1.2, viscosity=0.0025, separation=1.2, nodes=nodes) for s in in_seeds]
    in_labeled = build_labeled([features_from_raw(r) for r in in_runs], horizon_frames=4)
    in_matrix = np.vstack([_feature_matrix(features_from_raw(r)) for r in in_runs])
    reference = fit_reference(in_matrix)
    train_x, train_y = _matrix(in_labeled, ALL_FEATURES)
    mean, std = train_x.mean(axis=0), train_x.std(axis=0)
    std = np.where(std < 1e-12, 1.0, std)
    model = LogisticRegression().fit((train_x - mean) / std, train_y.astype(np.float64))

    # Near-OOD: untrained circulation, viscosity, and resolution (subtle shifts).
    near_groups: dict[str, list[RawRun]] = {
        "near_circulation": [_controlled_merger(s, 1.8, 0.0025, 1.2, nodes) for s in near_seeds],
        "near_viscosity": [_controlled_merger(s, 1.2, 0.005, 1.2, nodes) for s in near_seeds],
        "near_resolution": [_controlled_merger(s, 1.2, 0.0025, 1.2, max(nodes - 16, 48)) for s in near_seeds],
    }
    far_runs = [simulate_taylorgreen_raw(s, **({"nodes": 16, "steps": 700, "record_every": 50} if quick else {}))
                for s in tg_seeds]

    def score_group(runs: list[RawRun]) -> FloatArray:
        return reference.score(np.vstack([_feature_matrix(features_from_raw(r)) for r in runs]))

    group_scores = {"in_domain": reference.score(in_matrix)}
    for name, runs in near_groups.items():
        group_scores[name] = score_group(runs)
    group_scores["far_taylorgreen"] = score_group(far_runs)
    group_means = {k: float(np.mean(v)) for k, v in group_scores.items()}

    near_all = np.concatenate([group_scores[g] for g in near_groups])
    far_all = group_scores["far_taylorgreen"]
    in_scores = group_scores["in_domain"]
    detection_near = roc_auc(
        np.concatenate([in_scores, near_all]),
        np.concatenate([np.zeros(in_scores.size), np.ones(near_all.size)]).astype(np.int64),
    )
    detection_far = roc_auc(
        np.concatenate([in_scores, far_all]),
        np.concatenate([np.zeros(in_scores.size), np.ones(far_all.size)]).astype(np.int64),
    )

    # Are the near-OOD events still predictable by the in-domain model?
    near_labeled = build_labeled(
        [features_from_raw(r) for runs in near_groups.values() for r in runs], horizon_frames=4
    )
    if near_labeled:
        nx, ny = _matrix(near_labeled, ALL_FEATURES)
        near_pred = model.predict_proba((nx - mean) / std)
        predictable_near_auc = roc_auc(near_pred, ny)
        near_error = np.abs(near_pred - ny)
        near_scores_for_frames = reference.score(nx)
    else:
        predictable_near_auc = float("nan")
        near_error = np.array([])
        near_scores_for_frames = np.array([])

    # Abstention: threshold at the 90th percentile of in-domain scores (keep most in-domain).
    threshold = float(np.quantile(in_scores, 0.9))
    # Pool: in-domain frames (real error) + near-OOD frames (real error) + far-OOD (error 1).
    in_pred = model.predict_proba((train_x - mean) / std)
    in_error = np.abs(in_pred - train_y)
    far_scores = far_all
    # Frame-aligned pool: in-domain (train) + near-OOD + far-OOD.
    pool_scores = np.concatenate([reference.score(train_x), near_scores_for_frames, far_scores])
    pool_error = np.concatenate([in_error, near_error, np.ones(far_scores.size)])
    pool_is_ood = np.concatenate([
        np.zeros(train_x.shape[0], bool),
        np.ones(near_scores_for_frames.size, bool),
        np.ones(far_scores.size, bool),
    ])
    selective = selective_evaluation(pool_scores, pool_error, pool_is_ood, threshold)
    curve = risk_coverage_curve(pool_scores, pool_error)

    # Unnecessary abstention: near-OOD frames that are correctly predictable (error<0.5)
    # but abstained (score > threshold).
    if near_scores_for_frames.size:
        predictable = near_error < 0.5
        abstained = near_scores_for_frames > threshold
        denom = int(np.sum(predictable))
        unnecessary = float(np.sum(predictable & abstained) / denom) if denom else 0.0
    else:
        unnecessary = float("nan")

    # H31: abstention must lower selective risk vs full risk, keep in-domain coverage,
    # and not over-abstain on still-predictable near-OOD.
    supported = (
        selective.selective_risk < selective.full_risk - 1e-9
        and selective.in_domain_coverage >= 0.5
        and (np.isnan(unnecessary) or unnecessary < 0.5)
    )
    verdict = "supported within tested scope" if supported else "partially supported"
    if np.isnan(detection_near) or detection_near < 0.55:
        verdict = "not supported"

    return NearOODResult(
        group_mean_scores=group_means,
        detection_auc_near=detection_near,
        detection_auc_far=detection_far,
        predictable_near_auc=predictable_near_auc,
        selective=selective.as_dict(),
        unnecessary_abstention_rate=unnecessary,
        risk_coverage=curve,
        h31_verdict=verdict,
    )
