"""Product-level ITD analysis result and end-to-end pipeline (research, H26).

Wraps the research diagnostics/prediction/OOD stack in a single result contract that
never emits a bare alarm: every prediction carries confidence, calibration-domain
status, data-quality status, and provenance. The end-to-end pipeline measures the
*complete* per-frame latency (ingest -> validate -> mask -> diagnostics -> ITD ->
predict -> OOD -> serialize). Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.product.pipeline import (
    AnalysisPipeline,
    benchmark_end_to_end,
    build_reference_pipeline,
)
from itd_research.product.result import ITDAnalysisResult

__all__ = [
    "AnalysisPipeline",
    "ITDAnalysisResult",
    "benchmark_end_to_end",
    "build_reference_pipeline",
]
