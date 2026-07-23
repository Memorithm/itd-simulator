# Full-volume ITD-3D performance report (Mission 5, H35)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **performance**. Reproduce with `python -m itd_research.full_volume
bench --output <dir>`. Timings are hardware-dependent feasibility measurements, not
guarantees.

## Question (H35)

Mission 4's product pipeline reduced volumes to a midplane. Does **full-volume** ITD-3D
(no planar reduction) meet declared performance envelopes for selected grids?

## Method

Compute over the **complete** 3D grid: the 8-channel ITD-3D superset and the
established velocity-gradient diagnostics (Q-positive fraction, λ₂-negative fraction,
swirling strength) — 11 quantities, no reduction. Measure p50/p95/p99 latency, peak
traced memory, and throughput on dense random fields after warm-up.

## Results (single-node CPU; environment recorded in the JSON artifact)

| workload | grid | p50 | p95 | p99 | peak mem | budget | verdict |
|---|---|--:|--:|--:|--:|--:|---|
| VOL-3D-XS | 32³ | 156 ms | 173 ms | 174 ms | 13 MB | 250 ms | **meets** |
| VOL-3D-S | 48³ | 421 ms | 427 ms | 427 ms | 43 MB | 1200 ms | **meets** |
| VOL-3D-M | 64³ | 980 ms | 992 ms | 993 ms | 101 MB | 4000 ms | **meets** |

All 11 channels are evaluated over the full volume.

## H35 classification: **supported within tested scope**

Full-volume ITD-3D meets its declared envelope on this CPU for 32³/48³/64³ — with
substantial headroom (each p95 is well under budget). The cost is dominated by the
per-voxel eigen-decompositions (λ₂, swirling strength) and the two velocity-gradient
tensors; memory is modest (≤ 0.1 GB at 64³).

## Scope and honesty

* This is genuinely **full-volume** — no midplane reduction (distinct from the Mission 4
  end-to-end pipeline, which analysed a plane).
* VOL-3D-L (128³) is declared **batch/offline** and is not claimed real-time; at 8×
  the cells of 64³ it would be several seconds per frame on this CPU.
* Optimization (batched symmetric eigensolvers, preallocation, chunking, an optional
  native/GPU backend) could lower these; any faster backend must first match the NumPy
  reference numerically. The Mission 5 Rust crate is the first step of that path but
  does not yet implement the 3D channels.

## Limitations

Single machine, single-thread NumPy, dense random inputs, modest sample for the
percentiles. Budgets are indicative targets; different hardware moves the verdicts.
