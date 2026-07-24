"""Descriptive structural analyses: topology-response consistency (H64), temporal lead
time (H70), and non-redundant-channel stability across sequences/sources (H71).

These are DESCRIPTIVE checks, run alongside but never substituting for the primary H61/H62
predictive test. All three keep the same grouping discipline as the rest of Mission 8:
independent unit = sequence, never a frame; H70's lead-time scores come from a
leave-one-sequence-out fit, so no sequence is ever scored by a model that trained on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.models import LogisticRegression
from itd_research.mission8.localization import evaluate_nonredundancy
from itd_research.mission8.prediction import Sequence, feature_matrix
from itd_research.mission8.structural_features import (
    ITD_3D_NONREDUNDANT,
    StructuralTrajectory,
)

FloatArray: TypeAlias = NDArray[np.float64]
_EPS = 1e-12


# --------------------------------------------------------------------------------------
# H64: consistent response to topology-change events
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ChannelResponseConsistency:
    channel: str
    n_events: int
    shifts: list[float]
    sign_consistency: float
    mean_abs_shift: float

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel, "n_events": self.n_events, "shifts": self.shifts,
            "sign_consistency": self.sign_consistency, "mean_abs_shift": self.mean_abs_shift,
        }


@dataclass(frozen=True)
class TopologyResponseResult:
    window: int
    per_channel: list[ChannelResponseConsistency]
    consistent_channels: list[str]
    verdict: str
    reasoning: str

    def as_dict(self) -> dict[str, object]:
        return {
            "window": self.window, "per_channel": [c.as_dict() for c in self.per_channel],
            "consistent_channels": self.consistent_channels, "verdict": self.verdict, "reasoning": self.reasoning,
        }


def evaluate_topology_response_consistency(
    sequences_with_events: list[tuple[str, StructuralTrajectory, list[int]]],
    *, channels: tuple[str, ...] = ITD_3D_NONREDUNDANT, window: int = 2,
    consistency_threshold: float = 0.8, min_events: int = 3,
) -> TopologyResponseResult:
    """H64: does an ITD channel move in a consistent direction around topology-change events?

    For each channel, computes the pre-vs-post-event mean shift at every ITD-independent
    event instance (across all supplied sequences), then the fraction sharing the majority
    sign. High sign-consistency across several independent event instances is the evidence
    required -- a single instance or a near-50/50 sign split is not.
    """
    per_channel = []
    consistent = []
    for name in channels:
        shifts: list[float] = []
        for _sequence_id, traj, event_frames in sequences_with_events:
            values = np.asarray(traj.channels[name], dtype=np.float64)
            n = values.size
            for frame in event_frames:
                pre_lo, pre_hi = max(0, frame - window), frame
                post_lo, post_hi = frame, min(n, frame + window + 1)
                if pre_hi <= pre_lo or post_hi <= post_lo:
                    continue
                shifts.append(float(np.mean(values[post_lo:post_hi]) - np.mean(values[pre_lo:pre_hi])))
        if len(shifts) < min_events:
            per_channel.append(ChannelResponseConsistency(name, len(shifts), shifts, float("nan"), float("nan")))
            continue
        signs = np.sign(shifts)
        nonzero = signs[signs != 0]
        consistency = max(float(np.mean(nonzero > 0)), float(np.mean(nonzero < 0))) if nonzero.size else float("nan")
        mean_abs = float(np.mean(np.abs(shifts)))
        per_channel.append(ChannelResponseConsistency(name, len(shifts), shifts, consistency, mean_abs))
        if not np.isnan(consistency) and consistency >= consistency_threshold:
            consistent.append(name)

    if not any(c.n_events >= min_events for c in per_channel):
        verdict, reasoning = "inconclusive", f"Fewer than {min_events} usable topology-event instances available."
    elif consistent:
        verdict = "supported within tested scope"
        reasoning = (
            f"{len(consistent)} channel(s) show >= {consistency_threshold:.0%} sign-consistent response "
            f"across the available event instances: {consistent}."
        )
    else:
        verdict = "not supported"
        reasoning = "No channel shows a consistent-sign response to topology-change events across instances."
    return TopologyResponseResult(
        window=window, per_channel=per_channel, consistent_channels=consistent, verdict=verdict, reasoning=reasoning,
    )


# --------------------------------------------------------------------------------------
# H70: temporal lead time (grouped, leave-one-sequence-out)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class LeadTimeInstance:
    sequence_id: str
    event_frame: int
    event_time: float
    first_alert_frame: int | None
    lead_time_frames: int | None
    lead_time_seconds: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "sequence_id": self.sequence_id, "event_frame": self.event_frame, "event_time": self.event_time,
            "first_alert_frame": self.first_alert_frame, "lead_time_frames": self.lead_time_frames,
            "lead_time_seconds": self.lead_time_seconds,
        }


@dataclass(frozen=True)
class LeadTimeResult:
    feature_set: str
    threshold: float
    instances: list[LeadTimeInstance]
    detected_fraction: float
    mean_lead_time_frames: float
    verdict: str
    reasoning: str

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_set": self.feature_set, "threshold": self.threshold,
            "instances": [i.as_dict() for i in self.instances],
            "detected_fraction": self.detected_fraction, "mean_lead_time_frames": self.mean_lead_time_frames,
            "verdict": self.verdict, "reasoning": self.reasoning,
        }


def _leave_one_sequence_out_scores(
    sequences: list[Sequence], established_names: tuple[str, ...], itd_names: tuple[str, ...],
) -> dict[str, FloatArray]:
    """Grouped leave-one-sequence-out per-frame scores: never fit and score the same sequence."""
    scores_by_id: dict[str, FloatArray] = {}
    for i, seq in enumerate(sequences):
        train = sequences[:i] + sequences[i + 1:]
        if not train:
            scores_by_id[seq.sequence_id] = np.full(len(seq.labels), np.nan)
            continue
        train_x = np.concatenate([feature_matrix(s, established_names, itd_names) for s in train], axis=0)
        train_y = np.concatenate([s.labels for s in train]).astype(np.float64)
        if len(np.unique(train_y)) < 2:
            scores_by_id[seq.sequence_id] = np.full(len(seq.labels), np.nan)
            continue
        mean, std = train_x.mean(axis=0), train_x.std(axis=0)
        std = np.where(std < _EPS, 1.0, std)
        model = LogisticRegression().fit((train_x - mean) / std, train_y)
        x = feature_matrix(seq, established_names, itd_names)
        scores_by_id[seq.sequence_id] = model.predict_proba((x - mean) / std)
    return scores_by_id


def evaluate_lead_time(
    sequences: list[Sequence], *, feature_set: str,
    established_names: tuple[str, ...], itd_names: tuple[str, ...],
    threshold_quantile: float = 0.75, max_lookback: int = 6,
) -> LeadTimeResult:
    """H70: leave-one-sequence-out score series; first-alert frame vs the true event frame.

    ``threshold`` is calibrated as a quantile of the pooled out-of-sample scores (never
    tuned per event). A positive lead time means the alert preceded the true event frame.
    """
    scores_by_id = _leave_one_sequence_out_scores(sequences, established_names, itd_names)
    pooled = np.concatenate(list(scores_by_id.values())) if scores_by_id else np.array([])
    pooled = pooled[~np.isnan(pooled)]
    threshold = float(np.quantile(pooled, threshold_quantile)) if pooled.size else float("nan")

    instances: list[LeadTimeInstance] = []
    for seq in sequences:
        scores = scores_by_id.get(seq.sequence_id, np.array([]))
        for event in seq.events:
            frame = event.event_frame
            first_alert = None
            for lookback in range(max_lookback, -1, -1):
                idx = frame - lookback
                if 0 <= idx < len(scores) and not np.isnan(scores[idx]) and scores[idx] >= threshold:
                    first_alert = idx
                    break
            if first_alert is None:
                instances.append(LeadTimeInstance(seq.sequence_id, frame, event.event_time, None, None, None))
                continue
            lead_frames = frame - first_alert
            dt = float(seq.structural.times[1] - seq.structural.times[0]) if len(seq.structural.times) > 1 else float("nan")
            instances.append(LeadTimeInstance(
                seq.sequence_id, frame, event.event_time, first_alert, lead_frames, lead_frames * dt,
            ))

    detected = [i for i in instances if i.first_alert_frame is not None]
    detected_fraction = len(detected) / len(instances) if instances else float("nan")
    mean_lead = float(np.mean([i.lead_time_frames for i in detected])) if detected else float("nan")

    if not instances:
        verdict, reasoning = "inconclusive", "No topology events available to evaluate lead time."
    elif detected_fraction >= 0.5 and not np.isnan(mean_lead) and mean_lead > 0:
        verdict = "supported within tested scope"
        reasoning = (
            f"{feature_set}: {len(detected)}/{len(instances)} events preceded by an alert, "
            f"mean lead time {mean_lead:.2f} frames."
        )
    else:
        verdict = "not supported"
        reasoning = (
            f"{feature_set}: only {len(detected)}/{len(instances)} events preceded by an alert "
            f"(mean lead {mean_lead}); no reliable early-warning lead time on this evidence."
        )
    return LeadTimeResult(
        feature_set=feature_set, threshold=threshold, instances=instances,
        detected_fraction=detected_fraction, mean_lead_time_frames=mean_lead, verdict=verdict, reasoning=reasoning,
    )


# --------------------------------------------------------------------------------------
# H71: non-redundant-channel stability across sequences/sources
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ChannelStabilityResult:
    per_sequence_non_redundant: dict[str, list[str]]
    intersection: list[str]
    union: list[str]
    stability_ratio: float
    verdict: str
    reasoning: str

    def as_dict(self) -> dict[str, object]:
        return {
            "per_sequence_non_redundant": self.per_sequence_non_redundant,
            "intersection": self.intersection, "union": self.union,
            "stability_ratio": self.stability_ratio, "verdict": self.verdict, "reasoning": self.reasoning,
        }


def evaluate_channel_stability(
    sequences: list[Sequence], *, channels: tuple[str, ...] = ITD_3D_NONREDUNDANT,
) -> ChannelStabilityResult:
    """H71: does the SAME channel get flagged non-redundant (H63) across independent sequences?

    Runs the H63 non-redundancy check per sequence and compares the flagged channel sets.
    Stability is a Jaccard ratio (intersection / union); an empty union means no sequence
    flagged anything, which is reported as its own (non-redundancy-absent) outcome.
    """
    per_seq: dict[str, list[str]] = {}
    for seq in sequences:
        result = evaluate_nonredundancy(seq.structural, seq.baseline, seq.labels, channels=channels)
        per_seq[seq.sequence_id] = result.non_redundant_channels

    sets = [set(v) for v in per_seq.values() if v]
    union = set.union(*sets) if sets else set()
    intersection = set.intersection(*sets) if sets else set()
    stability = (len(intersection) / len(union)) if union else float("nan")

    if not sets:
        verdict = "not supported"
        reasoning = "No sequence flagged any non-redundant channel (H63); there is nothing to test for stability."
    elif not np.isnan(stability) and stability >= 0.5:
        verdict = "supported within tested scope"
        reasoning = f"Non-redundant channel set is stable across sequences (Jaccard={stability:.2f}): {sorted(intersection)}."
    else:
        verdict = "not supported"
        reasoning = (
            f"Non-redundant channel set is unstable across sequences (Jaccard="
            f"{0.0 if np.isnan(stability) else stability:.2f}); flagged channels differ per sequence: {per_seq}."
        )
    return ChannelStabilityResult(
        per_sequence_non_redundant=per_seq, intersection=sorted(intersection), union=sorted(union),
        stability_ratio=stability, verdict=verdict, reasoning=reasoning,
    )
