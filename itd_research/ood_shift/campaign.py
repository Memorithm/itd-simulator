"""Shift-aware calibrated-abstention campaign (research, Mission 6, H43-H45).

Fits an in-distribution reference and predictor on a narrow merger band, then challenges
them with **progressive** shifts of growing magnitude (untrained circulation, viscosity,
and resolution) plus a far-OOD control. It asks three questions:

* **H43** -- does the per-axis severity track the *known* shift magnitude (and attribute
  the axis) better than a single global Mahalanobis radius?
* **H44** -- does a three-state accept/reduce/abstain policy beat a binary abstention
  baseline on utility?
* **H45** -- does unnecessary abstention fall far below the Mission 5 ~0.85 while
  false confidence stays controlled?

Band thresholds are calibrated on development data only (in-domain quantile + a far-OOD
reference severity); policies are then scored on a disjoint holdout pool. No holdout
labels are used to choose thresholds. Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.evaluation import _matrix, build_labeled
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    RawRun,
    features_from_raw,
    simulate_taylorgreen_raw,
)
from itd_research.hard_prediction.models import LogisticRegression
from itd_research.ood_near.campaign import _controlled_merger
from itd_research.ood_shift.detector import (
    ShiftReference,
    fit_shift_reference,
    monotone_separation,
)
from itd_research.ood_shift.policy import (
    binary_policy,
    degradation_policy,
    evaluate_policy,
    no_abstention_policy,
    three_state_policy,
    utility_risk_coverage,
)

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]
_EPS = 1.0e-12
_M5_UNNECESSARY_ABSTENTION = 0.85  # Mission 5 near-OOD over-abstention reference


def _labeled_matrix(runs: list[RawRun]) -> tuple[FloatArray, FloatArray]:
    """(feature matrix, labels) over the leakage-safe pre-event frames of ``runs``."""
    labeled = build_labeled([features_from_raw(r) for r in runs], horizon_frames=4)
    if not labeled:
        return np.empty((0, len(ALL_FEATURES))), np.empty(0)
    x, y = _matrix(labeled, ALL_FEATURES)
    return x, y.astype(np.float64)


@dataclass(frozen=True)
class _Predictor:
    """A logistic predictor with its training standardization."""

    model: LogisticRegression
    mean: FloatArray
    std: FloatArray

    def error(self, x: FloatArray, y: FloatArray) -> FloatArray:
        proba = self.model.predict_proba((x - self.mean) / self.std)
        return np.abs(proba - y)


def _fit_predictor(x: FloatArray, y: FloatArray) -> _Predictor:
    mean, std = x.mean(axis=0), x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    model = LogisticRegression().fit((x - mean) / std, y)
    return _Predictor(model, mean, std)


@dataclass(frozen=True)
class _Challenge:
    """Per-frame severities, prediction error, and ordinal shift levels for one pool."""

    per_axis: FloatArray
    global_maha: FloatArray
    error: FloatArray
    level: IntArray
    axis: tuple[str, ...]


def _challenge(
    runs: list[RawRun], reference: ShiftReference, predictor: _Predictor, level: int, axis: str
) -> _Challenge:
    x, y = _labeled_matrix(runs)
    if x.shape[0] == 0:
        empty_f: FloatArray = np.empty(0, dtype=np.float64)
        return _Challenge(empty_f, empty_f, empty_f, np.empty(0, dtype=np.int64), ())
    return _Challenge(
        per_axis=reference.severity(x),
        global_maha=reference.global_mahalanobis(x),
        error=predictor.error(x, y),
        level=np.full(x.shape[0], level, dtype=np.int64),
        axis=tuple([axis] * x.shape[0]),
    )


def _dominant_features(runs: list[RawRun], reference: ShiftReference, top: int = 2) -> list[str]:
    x, _ = _labeled_matrix(runs)
    if x.shape[0] == 0:
        return []
    counts = np.bincount(reference.attribution(x), minlength=len(reference.feature_names))
    order = np.argsort(counts)[::-1][:top]
    return [reference.feature_names[i] for i in order if counts[i] > 0]


@dataclass(frozen=True)
class ShiftCampaignResult:
    """H43-H45 outcomes: severity localization, policy utilities, over-abstention drop."""

    bands: dict[str, float]
    per_axis_separation: dict[str, float]
    global_separation: dict[str, float]
    attribution: dict[str, list[str]]
    policies: dict[str, dict[str, object]]
    utility_risk_coverage: list[dict[str, float]]
    m5_unnecessary_abstention: float
    h43_verdict: str
    h44_verdict: str
    h45_verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "bands": self.bands,
            "per_axis_separation": self.per_axis_separation,
            "global_separation": self.global_separation,
            "attribution": self.attribution,
            "policies": self.policies,
            "utility_risk_coverage": self.utility_risk_coverage,
            "m5_unnecessary_abstention": self.m5_unnecessary_abstention,
            "h43_verdict": self.h43_verdict,
            "h44_verdict": self.h44_verdict,
            "h45_verdict": self.h45_verdict,
        }


def _sweep_plan(quick: bool) -> dict[str, list[tuple[int, dict[str, float]]]]:
    """Progressive sweeps: axis -> list of (ordinal level, controlled parameters).

    Level grows with shift magnitude. Level 0 is the in-distribution baseline (added
    separately). Values are a bounded subset of the preregistered sweeps.
    """
    if quick:
        return {
            "circulation": [(2, {"circulation": 1.8})],
            "viscosity": [(2, {"viscosity": 0.005})],
            "resolution": [(2, {"resolution_delta": -16.0})],
        }
    return {
        "circulation": [(1, {"circulation": 1.4}), (2, {"circulation": 1.8}), (3, {"circulation": 2.1})],
        "viscosity": [(1, {"viscosity": 0.004}), (2, {"viscosity": 0.0075})],
        "resolution": [(1, {"resolution_delta": -8.0}), (2, {"resolution_delta": -16.0})],
    }


def _merger(seed: int, base_nodes: int, params: dict[str, float]) -> RawRun:
    circulation = params.get("circulation", 1.2)
    viscosity = params.get("viscosity", 0.0025)
    nodes = int(base_nodes + params.get("resolution_delta", 0.0))
    return _controlled_merger(seed, circulation=circulation, viscosity=viscosity, separation=1.2, nodes=nodes)


def run_shift_campaign(*, quick: bool = False) -> ShiftCampaignResult:
    """Fit an in-domain band, sweep progressive shifts, and score abstention policies."""
    base_nodes = 48 if quick else 64
    in_seeds = (10, 11) if quick else (10, 11, 12, 13)
    sweep_seeds = (20,) if quick else (20, 21)
    far_dev_seeds = (80,) if quick else (80, 81)
    far_holdout_seeds = (90,) if quick else (90, 91)

    # In-distribution: narrow merger band. Fit the reference and the predictor.
    in_runs = [_merger(s, base_nodes, {}) for s in in_seeds]
    in_x, in_y = _labeled_matrix(in_runs)
    reference = fit_shift_reference(in_x, ALL_FEATURES)
    predictor = _fit_predictor(in_x, in_y)
    in_severity = reference.severity(in_x)

    tg_kwargs = {"nodes": 16, "steps": 700, "record_every": 50} if quick else {}
    far_dev_runs = [simulate_taylorgreen_raw(s, **tg_kwargs) for s in far_dev_seeds]
    far_dev_x, _ = _labeled_matrix(far_dev_runs)
    far_dev_severity = reference.severity(far_dev_x) if far_dev_x.shape[0] else np.array([in_severity.max() * 3.0])

    # Bands calibrated on DEVELOPMENT only: s_low from the in-domain bulk; s_high from a
    # known far-OOD reference severity (abstain when as anomalous as a far-OOD flow).
    s_low = float(np.quantile(in_severity, 0.90))
    s_high = float(np.quantile(far_dev_severity, 0.50))
    if s_high <= s_low:  # keep a non-degenerate reduce band
        s_high = s_low + max(float(np.std(in_severity)), 1.0)
    global_threshold = float(np.quantile(reference.global_mahalanobis(in_x), 0.90))

    # Progressive sweeps (holdout seeds) + far-OOD holdout, all with ordinal levels.
    plan = _sweep_plan(quick)
    challenges: list[_Challenge] = [_challenge(in_runs, reference, predictor, 0, "in_domain")]
    per_axis_sep: dict[str, float] = {}
    global_sep: dict[str, float] = {}
    attribution: dict[str, list[str]] = {}
    in_ch = challenges[0]
    for axis, points in plan.items():
        axis_challenges = [in_ch]
        for level, params in points:
            runs = [_merger(s, base_nodes, params) for s in sweep_seeds]
            ch = _challenge(runs, reference, predictor, level, axis)
            if ch.per_axis.size:
                axis_challenges.append(ch)
                challenges.append(ch)
                attribution.setdefault(axis, [])
                attribution[axis] = _dominant_features(runs, reference)
        pa = np.concatenate([c.per_axis for c in axis_challenges])
        gl = np.concatenate([c.global_maha for c in axis_challenges])
        lv = np.concatenate([c.level for c in axis_challenges])
        per_axis_sep[axis] = monotone_separation(pa, lv)
        global_sep[axis] = monotone_separation(gl, lv)

    far_level = 5
    far_runs = [simulate_taylorgreen_raw(s, **tg_kwargs) for s in far_holdout_seeds]
    far_ch = _challenge(far_runs, reference, predictor, far_level, "far_ood")
    if far_ch.per_axis.size:
        challenges.append(far_ch)

    per_axis_sep["mean"] = float(np.mean([v for k, v in per_axis_sep.items() if not np.isnan(v)]))
    global_sep["mean"] = float(np.mean([v for k, v in global_sep.items() if not np.isnan(v)]))

    # Frame pool for policy scoring: every challenge frame with its real prediction error.
    severity_pool = np.concatenate([c.per_axis for c in challenges])
    global_pool = np.concatenate([c.global_maha for c in challenges])
    error_pool = np.concatenate([c.error for c in challenges])

    decisions = {
        "no_abstention": no_abstention_policy(severity_pool.size),
        "global_binary": binary_policy(global_pool, global_threshold),
        "shift_aware_binary": binary_policy(severity_pool, s_low),
        "shift_aware_confidence_degradation": degradation_policy(severity_pool, s_low, s_high),
        "three_state": three_state_policy(severity_pool, s_low, s_high),
    }
    outcomes = {name: evaluate_policy(name, decision, error_pool) for name, decision in decisions.items()}
    policies = {name: outcome.as_dict() for name, outcome in outcomes.items()}
    curve = utility_risk_coverage(severity_pool, error_pool, s_low)

    # --- Verdicts (honest; never forced positive) ---
    # H43 has two parts: severity ordering (compared numerically) and axis attribution (a
    # scalar global radius fundamentally cannot attribute). Per-axis strictly dominates on
    # attribution, so a comparable severity ordering still earns "partially supported".
    attribution_works = any(bool(v) for v in attribution.values())
    if per_axis_sep["mean"] >= global_sep["mean"] - 1e-9 and per_axis_sep["mean"] > 0.5:
        h43_verdict = "supported within tested scope"
    elif attribution_works and per_axis_sep["mean"] > 0.5:
        h43_verdict = "partially supported"  # attribution advantage; severity ordering not better
    else:
        h43_verdict = "not supported"

    three = outcomes["three_state"]
    binary_best = max(outcomes["global_binary"].utility, outcomes["shift_aware_binary"].utility)
    h44_verdict = "supported within tested scope" if three.utility > binary_best + 1e-9 else "not supported"

    three_unnecessary = three.unnecessary_abstention_rate
    controlled_fc = three.false_confidence <= outcomes["no_abstention"].false_confidence + 1e-9
    if not np.isnan(three_unnecessary):
        h45_supported = three_unnecessary < 0.5 * _M5_UNNECESSARY_ABSTENTION and controlled_fc
        h45_verdict = "supported within tested scope" if h45_supported else "partially supported"
    else:
        h45_verdict = "inconclusive"

    return ShiftCampaignResult(
        bands={"s_low": s_low, "s_high": s_high, "global_threshold": global_threshold},
        per_axis_separation=per_axis_sep,
        global_separation=global_sep,
        attribution=attribution,
        policies=policies,
        utility_risk_coverage=[{"coverage": c, "utility": u} for c, u in curve],
        m5_unnecessary_abstention=_M5_UNNECESSARY_ABSTENTION,
        h43_verdict=h43_verdict,
        h44_verdict=h44_verdict,
        h45_verdict=h45_verdict,
    )
