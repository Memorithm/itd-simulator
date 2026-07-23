"""End-to-end analysis pipeline and latency benchmark (research, H26).

``AnalysisPipeline`` bundles a fitted predictor, an OOD reference, and the feature
normalization, and turns one field into an :class:`ITDAnalysisResult` while timing
every stage. ``benchmark_end_to_end`` measures the *complete* per-frame latency
(p50/p95/p99) over a bounded stream for declared 2D and 3D-volume workloads. Timings
are hardware-dependent feasibility measurements, not guarantees.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.hard_prediction.evaluation import _matrix, build_labeled
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    extract_features_2d,
    features_from_raw,
    simulate_merger_raw,
)
from itd_research.hard_prediction.models import LogisticRegression
from itd_research.ood.reference import OODReference, fit_reference
from itd_research.product.result import ITDAnalysisResult

FloatArray: TypeAlias = NDArray[np.float64]
BoolArray: TypeAlias = NDArray[np.bool_]
_EPS = 1.0e-12


@dataclass
class AnalysisPipeline:
    """A fitted end-to-end pipeline (model + OOD reference + normalization)."""

    model: LogisticRegression
    reference: OODReference
    mean: FloatArray
    std: FloatArray
    in_domain_threshold: float
    horizon: str = "<= 4 frames"
    commit: str = "unknown"

    def analyze(
        self, u: FloatArray, v: FloatArray, spacing: float,
        *, valid: BoolArray | None = None, provenance: str = "stream",
    ) -> ITDAnalysisResult:
        latency: dict[str, float] = {}
        t0 = time.perf_counter()

        # validate
        if u.shape != v.shape or u.ndim != 2:
            raise ValueError("analyze expects matching 2D u, v.")
        finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
        latency["validate_ms"] = (time.perf_counter() - t0) * 1e3

        # mask / quality
        t = time.perf_counter()
        mask_fraction = 0.0 if valid is None else float(np.mean(~valid))
        input_quality = "ok" if (finite and mask_fraction < 0.05) else ("degraded" if mask_fraction < 0.25 else "poor")
        latency["mask_ms"] = (time.perf_counter() - t) * 1e3

        # diagnostics + ITD (feature extraction)
        t = time.perf_counter()
        feats = extract_features_2d(u, v, spacing, valid=valid)
        latency["features_ms"] = (time.perf_counter() - t) * 1e3

        vector = np.array([[feats[name] for name in ALL_FEATURES]], dtype=np.float64)
        z = (vector - self.mean) / self.std

        # predict
        t = time.perf_counter()
        prediction = float(self.model.predict_proba(z)[0])
        latency["predict_ms"] = (time.perf_counter() - t) * 1e3

        # ood + confidence + abstention
        t = time.perf_counter()
        ood_score = float(self.reference.score(vector)[0])
        confidence = float(np.clip(1.0 - ood_score / (2.0 * self.in_domain_threshold + _EPS), 0.0, 1.0))
        if ood_score <= self.in_domain_threshold:
            calibration_profile, abstained, reason = "in-domain", False, "in calibration domain"
        elif ood_score <= 2.0 * self.in_domain_threshold:
            calibration_profile, abstained, reason = "borderline", False, "borderline; prediction with low confidence"
        else:
            calibration_profile, abstained, reason = "out-of-domain", True, "OOD score exceeds calibration domain"
        if input_quality == "poor":
            abstained, reason = True, "input quality poor"
        latency["ood_ms"] = (time.perf_counter() - t) * 1e3

        established = {name: feats[name] for name in feats if name not in
                       ("intensity", "heterogeneity", "localization", "roughness",
                        "sign_mixing", "temporal_deformation", "structure_score")}
        signature = {name: feats[name] for name in
                     ("intensity", "heterogeneity", "localization", "roughness",
                      "sign_mixing", "temporal_deformation", "structure_score")}

        # serialize
        t = time.perf_counter()
        latency["total_ms"] = (time.perf_counter() - t0) * 1e3
        result = ITDAnalysisResult(
            signature=signature, established_diagnostics=established,
            prediction=0.0 if abstained else prediction,
            confidence=confidence, prediction_horizon=self.horizon,
            ood_score=ood_score, abstained=abstained, abstention_reason=reason,
            calibration_profile=calibration_profile, input_quality=input_quality,
            mask_fraction=mask_fraction, uncertainty_summary={"confidence": confidence},
            latency=latency, solver_or_dataset_provenance=provenance, repository_commit=self.commit,
        )
        latency["serialize_ms"] = (time.perf_counter() - t) * 1e3
        result.validate()
        return result

    def analyze_volume(
        self, u: FloatArray, v: FloatArray, w: FloatArray, spacing: float, *, provenance: str = "volume"
    ) -> ITDAnalysisResult:
        """Ingest a 3D volume, reduce to the z-midplane, and analyze (planar product)."""
        t0 = time.perf_counter()
        enstrophy_3d = 0.5 * float(np.mean(u**2 + v**2 + w**2))  # cheap volume aggregate
        mid = u.shape[0] // 2
        result = self.analyze(np.ascontiguousarray(u[mid]), np.ascontiguousarray(v[mid]), spacing,
                              provenance=provenance)
        merged = dict(result.latency)
        merged["volume_ingest_ms"] = (time.perf_counter() - t0) * 1e3
        merged["total_ms"] = merged.get("volume_ingest_ms", 0.0)
        est = dict(result.established_diagnostics)
        est["volume_energy"] = enstrophy_3d
        return ITDAnalysisResult(
            signature=result.signature, established_diagnostics=est, prediction=result.prediction,
            confidence=result.confidence, prediction_horizon=result.prediction_horizon,
            ood_score=result.ood_score, abstained=result.abstained, abstention_reason=result.abstention_reason,
            calibration_profile=result.calibration_profile, input_quality=result.input_quality,
            mask_fraction=result.mask_fraction, uncertainty_summary=result.uncertainty_summary,
            latency=merged, solver_or_dataset_provenance=provenance, repository_commit=self.commit,
        )


def build_reference_pipeline(seeds: tuple[int, ...] = (10, 11, 12), *, quick: bool = True, commit: str = "unknown") -> AnalysisPipeline:
    """Fit a reference pipeline on a few in-distribution merger runs."""
    kwargs = {"nodes": 56, "steps": 2000, "record_every": 100} if quick else {}
    runs = [features_from_raw(simulate_merger_raw(s, **kwargs)) for s in seeds]
    labeled = build_labeled(runs, horizon_frames=4)
    x, y = _matrix(labeled, ALL_FEATURES)
    mean, std = x.mean(axis=0), x.std(axis=0)
    std = np.where(std < _EPS, 1.0, std)
    model = LogisticRegression().fit((x - mean) / std, y.astype(np.float64))
    reference = fit_reference(x)
    in_scores = reference.score(x)
    threshold = float(np.quantile(in_scores, 0.95))
    return AnalysisPipeline(model, reference, mean, std, threshold, commit=commit)


@dataclass(frozen=True)
class WorkloadResult:
    name: str
    kind: str
    size: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    throughput_hz: float
    budget_ms: float
    meets_budget: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name, "kind": self.kind, "size": self.size,
            "p50_ms": self.p50_ms, "p95_ms": self.p95_ms, "p99_ms": self.p99_ms,
            "max_ms": self.max_ms, "throughput_hz": self.throughput_hz,
            "budget_ms": self.budget_ms, "meets_budget": self.meets_budget,
        }


_WORKLOADS = {
    "E2E-2D-S": ("2d", 128, 20.0),
    "E2E-2D-M": ("2d", 256, 80.0),
    "E2E-3D-S": ("3d", 32, 100.0),
    "E2E-3D-M": ("3d", 48, 400.0),
}


def _random_2d(size: int, seed: int) -> tuple[FloatArray, FloatArray]:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(size, size)), rng.normal(size=(size, size))


def _random_3d(size: int, seed: int) -> tuple[FloatArray, FloatArray, FloatArray]:
    rng = np.random.default_rng(seed)
    return (rng.normal(size=(size, size, size)), rng.normal(size=(size, size, size)),
            rng.normal(size=(size, size, size)))


def benchmark_end_to_end(
    pipeline: AnalysisPipeline, name: str, *, repeats: int = 30
) -> WorkloadResult:
    """Measure complete per-frame latency for a declared workload (p50/p95/p99)."""
    kind, size, budget = _WORKLOADS[name]
    spacing = 2.0 * np.pi / size
    # warm-up
    if kind == "2d":
        u, v = _random_2d(size, 0)
        pipeline.analyze(u, v, spacing)
    else:
        u, v, w = _random_3d(size, 0)
        pipeline.analyze_volume(u, v, w, spacing)
    times: list[float] = []
    for i in range(1, repeats + 1):
        if kind == "2d":
            u, v = _random_2d(size, i)
            t = time.perf_counter()
            pipeline.analyze(u, v, spacing)
        else:
            u, v, w = _random_3d(size, i)
            t = time.perf_counter()
            pipeline.analyze_volume(u, v, w, spacing)
        times.append((time.perf_counter() - t) * 1e3)
    arr = np.asarray(times)
    p50, p95, p99 = (float(np.percentile(arr, q)) for q in (50, 95, 99))
    return WorkloadResult(
        name, kind, size, p50, p95, p99, float(arr.max()),
        float(1000.0 / max(p50, _EPS)), budget, bool(p95 <= budget),
    )
