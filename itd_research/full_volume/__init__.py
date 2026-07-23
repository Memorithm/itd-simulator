"""Full-volume ITD-3D performance benchmark (research, Mission 5, H35).

Measures the cost of evaluating ITD-3D over the COMPLETE volume -- no planar/midplane
reduction (which Mission 4's product pipeline used). All 3D channels and the
established velocity-gradient diagnostics (Q, lambda_2, swirling strength) are computed
on the full grid. Timings are hardware-dependent feasibility measurements, not
guarantees. Experimental research; does not modify ``ITD V29.18``.
"""

from __future__ import annotations

from itd_research.full_volume.benchmark import (
    WORKLOADS,
    VolumeResult,
    benchmark_volume,
    evaluate_full_volume,
)

__all__ = ["WORKLOADS", "VolumeResult", "benchmark_volume", "evaluate_full_volume"]
