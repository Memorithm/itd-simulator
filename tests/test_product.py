"""Tests for the product result contract and end-to-end pipeline (H26)."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.product.pipeline import benchmark_end_to_end, build_reference_pipeline
from itd_research.product.result import ITDAnalysisResult


def _result(**overrides: object) -> ITDAnalysisResult:
    base = dict(
        signature={"intensity": 1.0}, established_diagnostics={"enstrophy": 1.0},
        prediction=0.9, confidence=0.8, prediction_horizon="<=4",
        ood_score=1.0, abstained=False, abstention_reason="", calibration_profile="in-domain",
        input_quality="ok", mask_fraction=0.0, solver_or_dataset_provenance="test",
    )
    base.update(overrides)
    return ITDAnalysisResult(**base)  # type: ignore[arg-type]


def test_alarm_requires_full_context() -> None:
    _result().validate()  # ok
    with pytest.raises(ValueError):
        _result(solver_or_dataset_provenance="unknown").validate()  # bare alarm
    with pytest.raises(ValueError):
        _result(confidence=2.0).validate()
    # abstained results are never alarms and need no context
    _result(abstained=True, prediction=0.0, solver_or_dataset_provenance="unknown").validate()


def test_pipeline_analyze_produces_valid_result() -> None:
    pipeline = build_reference_pipeline(quick=True)
    rng = np.random.default_rng(0)
    u, v = rng.normal(size=(64, 64)), rng.normal(size=(64, 64))
    result = pipeline.analyze(u, v, 2.0 * np.pi / 64, provenance="unit-test")
    result.validate()  # never a bare alarm
    assert 0.0 <= result.confidence <= 1.0
    assert result.calibration_profile in {"in-domain", "borderline", "out-of-domain"}
    assert "total_ms" in result.latency
    # a random field is out of the merger distribution -> should abstain or low confidence
    assert result.abstained or result.confidence < 0.9


def test_pipeline_volume_path_and_benchmark() -> None:
    pipeline = build_reference_pipeline(quick=True)
    rng = np.random.default_rng(1)
    u, v, w = (rng.normal(size=(16, 16, 16)) for _ in range(3))
    vol = pipeline.analyze_volume(u, v, w, 2.0 * np.pi / 16)
    assert "volume_ingest_ms" in vol.latency
    result = benchmark_end_to_end(pipeline, "E2E-3D-S", repeats=3)
    assert result.p95_ms > 0.0 and result.size == 32
