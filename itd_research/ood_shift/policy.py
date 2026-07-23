"""Calibrated confidence degradation and three-state abstention (research, H44/H45).

Mission 5 used a single hard threshold: predict below it, abstain above it. On subtle
shifts that were *still predictable* this over-abstained on ~85% of usable frames. This
module replaces the binary switch with:

* a transparent, **monotone confidence discount** in the shift severity, and
* a **three-state** policy -- ``accept`` (full confidence), ``accept_with_reduced_
  confidence`` (predict, but flag it), ``abstain`` (no prediction) -- with band
  thresholds ``s_low`` / ``s_high``.

Policies are scored by a **utility** that credits confident-correct predictions, charges
confidence-weighted false confidence at ``high_cost`` (a confident wrong prediction is
worst; a hedged wrong one is only lightly charged), and charges *unnecessary abstention*
-- abstaining on a frame that was actually predictable -- at ``moderate_cost``. Under
this utility the three-state policy should beat a binary abstention baseline that must
either predict or abstain on the whole middle band. Experimental research; does not
modify ``ITD V29.18``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]

ACCEPT = "accept"
REDUCE = "accept_with_reduced_confidence"
ABSTAIN = "abstain"
_PREDICTABLE_ERROR = 0.5
HIGH_COST = 4.0
MODERATE_COST = 1.0


def confidence_discount(severity: FloatArray, s_low: float, s_high: float) -> FloatArray:
    """Monotone confidence multiplier: 1 below ``s_low``, linear down to 0 at ``s_high``.

    Transparent and strictly non-increasing in severity, so higher shift always means no
    more confidence. Values are clipped to ``[0, 1]``; a degenerate band (``s_high <=
    s_low``) collapses to a hard step at ``s_low``.
    """
    sev = np.asarray(severity, dtype=np.float64)
    if s_high <= s_low:
        return np.where(sev <= s_low, 1.0, 0.0).astype(np.float64)
    frac = (sev - s_low) / (s_high - s_low)
    return np.clip(1.0 - frac, 0.0, 1.0).astype(np.float64)


@dataclass(frozen=True)
class PolicyDecision:
    """Per-frame states and confidences for one policy."""

    states: list[str]
    confidence: FloatArray

    @property
    def abstained(self) -> BoolArray:
        return np.asarray([s == ABSTAIN for s in self.states], dtype=bool)


def three_state_policy(severity: FloatArray, s_low: float, s_high: float) -> PolicyDecision:
    """accept below ``s_low``, abstain at/above ``s_high``, reduce-confidence between."""
    sev = np.asarray(severity, dtype=np.float64)
    disc = confidence_discount(sev, s_low, s_high)
    states: list[str] = []
    confidence: FloatArray = np.empty(sev.size, dtype=np.float64)
    for i, value in enumerate(sev):
        if value <= s_low:
            states.append(ACCEPT)
            confidence[i] = 1.0
        elif value >= s_high:
            states.append(ABSTAIN)
            confidence[i] = 0.0
        else:
            states.append(REDUCE)
            confidence[i] = float(disc[i])
    return PolicyDecision(states, confidence)


def binary_policy(score: FloatArray, threshold: float) -> PolicyDecision:
    """Predict (full confidence) at/below ``threshold``, abstain above it (Mission 5)."""
    values = np.asarray(score, dtype=np.float64)
    states = [ACCEPT if v <= threshold else ABSTAIN for v in values]
    confidence: FloatArray = np.asarray([1.0 if v <= threshold else 0.0 for v in values], dtype=np.float64)
    return PolicyDecision(states, confidence)


def no_abstention_policy(n: int) -> PolicyDecision:
    """Always predict at full confidence."""
    return PolicyDecision([ACCEPT] * n, np.ones(n, dtype=np.float64))


def degradation_policy(severity: FloatArray, s_low: float, s_high: float) -> PolicyDecision:
    """Never abstain; predict every frame at a severity-discounted confidence."""
    disc = confidence_discount(severity, s_low, s_high)
    return PolicyDecision([ACCEPT if c >= 1.0 else REDUCE for c in disc], disc)


@dataclass(frozen=True)
class PolicyOutcome:
    """Utility decomposition and coverage for one policy on one frame pool."""

    name: str
    utility: float                    # per-frame mean utility
    correct_accepted: float           # confidence-weighted, per-frame mean
    false_confidence: float           # confidence-weighted, per-frame mean
    unnecessary_abstention_rate: float  # abstained-yet-predictable / predictable
    coverage: float                   # fraction predicted (accept or reduce)
    reduced_fraction: float
    abstain_fraction: float

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "utility": self.utility,
            "correct_accepted": self.correct_accepted,
            "false_confidence": self.false_confidence,
            "unnecessary_abstention_rate": self.unnecessary_abstention_rate,
            "coverage": self.coverage,
            "reduced_fraction": self.reduced_fraction,
            "abstain_fraction": self.abstain_fraction,
        }


def evaluate_policy(
    name: str, decision: PolicyDecision, error: FloatArray,
    *, high_cost: float = HIGH_COST, moderate_cost: float = MODERATE_COST,
) -> PolicyOutcome:
    """Score a policy by confidence-weighted utility.

    ``error`` is the per-frame prediction error (|p - y|); a frame is *predictable* when
    that error is below 0.5. Credit and false-confidence are confidence-weighted, so a
    hedged (reduced-confidence) wrong prediction is charged far less than a confident one,
    and abstaining on a predictable frame is charged ``moderate_cost``.
    """
    err = np.asarray(error, dtype=np.float64)
    n = err.size
    if n == 0:
        return PolicyOutcome(name, float("nan"), 0.0, 0.0, float("nan"), 0.0, 0.0, 0.0)
    correct = err < _PREDICTABLE_ERROR
    abstained = decision.abstained
    predicted = ~abstained
    conf = decision.confidence

    correct_accepted = float(np.sum(conf[predicted & correct]))
    false_confidence = float(np.sum(conf[predicted & ~correct]))
    unnecessary = int(np.sum(abstained & correct))
    predictable_total = int(np.sum(correct))

    utility_total = correct_accepted - high_cost * false_confidence - moderate_cost * unnecessary
    reduced = float(np.mean([s == REDUCE for s in decision.states]))
    return PolicyOutcome(
        name=name,
        utility=utility_total / n,
        correct_accepted=correct_accepted / n,
        false_confidence=false_confidence / n,
        unnecessary_abstention_rate=(unnecessary / predictable_total) if predictable_total else float("nan"),
        coverage=float(np.mean(predicted)),
        reduced_fraction=reduced,
        abstain_fraction=float(np.mean(abstained)),
    )


def utility_risk_coverage(
    severity: FloatArray, error: FloatArray, s_low: float,
    *, points: int = 12, high_cost: float = HIGH_COST, moderate_cost: float = MODERATE_COST,
) -> list[tuple[float, float]]:
    """Three-state utility as the abstain threshold ``s_high`` sweeps (coverage, utility)."""
    sev = np.asarray(severity, dtype=np.float64)
    hi = float(np.max(sev)) if sev.size else s_low + 1.0
    curve: list[tuple[float, float]] = []
    for s_high in np.linspace(s_low, hi, points):
        decision = three_state_policy(sev, s_low, float(s_high))
        outcome = evaluate_policy("sweep", decision, error, high_cost=high_cost, moderate_cost=moderate_cost)
        curve.append((outcome.coverage, outcome.utility))
    return curve
