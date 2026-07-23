"""The ITD product result contract (research, Mission 4 section 20).

A single object carrying the signature, established diagnostics, the prediction and
its confidence/horizon, the OOD score and abstention decision, calibration and
input-quality status, latency, and provenance. The invariant ``validate`` enforces
that the product never emits a bare alarm: a positive prediction must be accompanied
by confidence, a calibration domain, a data-quality status, and provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ITDAnalysisResult:
    """A complete, self-describing analysis result for one frame."""

    signature: dict[str, float]
    established_diagnostics: dict[str, float]
    prediction: float                 # probability of the event within the horizon
    confidence: float                 # 1 - normalized OOD distance, clipped to [0, 1]
    prediction_horizon: str           # human-readable horizon
    ood_score: float
    abstained: bool
    abstention_reason: str
    calibration_profile: str          # "in-domain" | "borderline" | "out-of-domain"
    input_quality: str                # "ok" | "degraded" | "poor"
    mask_fraction: float
    uncertainty_summary: dict[str, float] = field(default_factory=dict)
    latency: dict[str, float] = field(default_factory=dict)
    model_version: str = "itd_research.hard_prediction/logistic"
    solver_or_dataset_provenance: str = "unknown"
    repository_commit: str = "unknown"
    # Mission 5 additions (section 18): full provenance for a product result.
    analysis_id: str = "unset"
    timestamp: str = "unset"
    flow_profile: str = "unset"
    protocol_hash: str = "unset"
    model_hash: str = "unset"

    def is_alarm(self) -> bool:
        return (not self.abstained) and self.prediction >= 0.5

    def validate(self) -> None:
        """Reject a bare alarm: an emitted alarm must carry full context."""
        if not self.is_alarm():
            return
        missing: list[str] = []
        if not (0.0 <= self.confidence <= 1.0):
            missing.append("confidence")
        if self.calibration_profile not in {"in-domain", "borderline", "out-of-domain"}:
            missing.append("calibration_profile")
        if self.input_quality not in {"ok", "degraded", "poor"}:
            missing.append("input_quality")
        if self.solver_or_dataset_provenance in {"", "unknown"}:
            missing.append("provenance")
        if missing:
            raise ValueError(f"bare alarm rejected; missing context: {sorted(missing)}")

    def as_dict(self) -> dict[str, object]:
        return {
            "signature": self.signature,
            "established_diagnostics": self.established_diagnostics,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "prediction_horizon": self.prediction_horizon,
            "ood_score": self.ood_score,
            "abstained": self.abstained,
            "abstention_reason": self.abstention_reason,
            "calibration_profile": self.calibration_profile,
            "input_quality": self.input_quality,
            "mask_fraction": self.mask_fraction,
            "uncertainty_summary": self.uncertainty_summary,
            "latency": self.latency,
            "model_version": self.model_version,
            "solver_or_dataset_provenance": self.solver_or_dataset_provenance,
            "repository_commit": self.repository_commit,
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "flow_profile": self.flow_profile,
            "protocol_hash": self.protocol_hash,
            "model_hash": self.model_hash,
        }
