# End-to-end real-time report (Mission 4, H26)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce with `python -m itd_research.product bench --output <dir>`. Timings are
**hardware-dependent** feasibility measurements on the CPU NumPy reference, not
guarantees. Evidence class: **performance**.

## Question (H26)

Does the **complete** streaming pipeline — ingest → validate → mask → diagnostics →
ITD → predict → OOD → serialize — meet declared p95/p99 latency budgets?

## Method

A reference `AnalysisPipeline` (fitted predictor + OOD reference + normalization) runs
every stage per frame and times each. Unlike the Mission 3 real-time report (which
measured the ITD kernel alone), this measures the *whole* pipeline, including
prediction, OOD scoring, the abstention decision, and result serialization, on
worst-case dense random inputs after warm-up. The 3D workloads ingest a full volume and
reduce to the z-midplane for the planar prediction path.

## Results (single-node CPU; environment recorded in the JSON artifact)

| workload | size | p50 | p95 | p99 | max | budget | verdict |
|---|---|--:|--:|--:|--:|--:|---|
| E2E-2D-S | 128² | 5.7 ms | 6.9 ms | 7.6 ms | — | 20 ms | **meets** |
| E2E-2D-M | 256² | 26.1 ms | 28.0 ms | 28.4 ms | — | 80 ms | **meets** |
| E2E-3D-S | 32³ | 1.2 ms | 1.3 ms | 1.3 ms | — | 100 ms | **meets** |
| E2E-3D-M | 48³ | 2.2 ms | 2.5 ms | 2.6 ms | — | 400 ms | **meets** |

## H26 classification: **supported within tested scope**

Every declared workload meets its p95 (and p99) budget for the **complete** pipeline on
this CPU. The 2D planar workloads are dominated by the feature-extraction stage
(finite-difference derivatives + the ITD signature); prediction and OOD scoring are a
few microseconds. The 3D workloads are inexpensive because the product performs
**planar** analysis of the volume (z-midplane) — the honest streaming case for PIV and
DNS-midplane inputs.

## Scope and honesty

* "Real-time" means only "meets the declared p95 budget on the measured node." Larger
  2D fields (≥ 512²) and full-volume 3D ITD are **not** in the streaming product and
  are not claimed real-time.
* The pipeline is bounded and deterministic; the `ITDAnalysisResult` it emits carries
  latency, confidence, calibration domain, data-quality, and provenance, and its
  `validate()` rejects a bare alarm.
* No GPU or native backend is measured; a faster backend must match the CPU reference
  numerically before its timings are quoted.

## Limitations

Single machine, single-thread NumPy, dense random inputs (a worst case for FFT/derivative
cost), a modest sample for the percentiles. Budgets are indicative targets, not
contractual guarantees; different hardware moves the verdicts.
