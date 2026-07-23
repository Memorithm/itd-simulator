# Real-time performance report (H15)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce with `python -m itd_research.realtime bench --output <dir>`. Timings are
**hardware-dependent**; they measure feasibility on the CPU NumPy reference, not a
guarantee.

## Question (H15, falsifiable)

Which declared workload classes can the ITD reference evaluate within an explicit
latency budget, at measured p95/p99 (not mean)?

## Method

Per-frame ITD evaluation latency for each class: the 2D signature
(`evaluate_signature`) for 2D classes, the 3D candidate (`evaluate_itd3d`) for 3D
classes, on random divergence-unconstrained fields (worst-case dense input),
after warm-up. Latency percentiles, throughput, and peak traced memory recorded.

## Results (single-node CPU; environment recorded in the JSON artifact)

| class | size | p50 | p95 | p99 | budget | verdict |
|---|---|--:|--:|--:|--:|---|
| RT-2D-S | 128^2 | 2.9 ms | 3.2 ms | 3.3 ms | 5 ms | **meets** |
| RT-2D-M | 512^2 | 38.6 ms | 39.9 ms | 40.3 ms | 50 ms | **meets** |
| RT-3D-S | 32^3 | 26.6 ms | 28.5 ms | 28.7 ms | 50 ms | **meets** |
| RT-3D-M | 64^3 | 201.7 ms | 212.4 ms | 216.1 ms | 500 ms | **meets** |

## H15 classification: **supported within tested scope**

All four declared workload classes meet their p95 latency budgets on this CPU. The
larger classes (RT-2D-L 2048^2, RT-3D-L 128^3) are declared batch/offline and are
**not** claimed real-time; they are out of the interactive budget on this hardware.

## Streaming reference

`itd_research.realtime.streaming.FrameStream` provides bounded, deterministic
streaming: strictly-increasing timestamp ordering (out-of-order and duplicate
frames rejected), missing-frame detection from the expected timestep, dropped-frame
accounting, backpressure via a maximum queue depth, an incremental temporal channel
from consecutive frames, explicit checkpointable state, and reset.

## Limitations

Single machine, single-thread NumPy, dense random inputs (a worst case for FFT
cost); percentiles from a modest sample; no GPU/native backend measured (a faster
backend must be numerically checked against this reference before use). Budgets are
indicative targets, not contractual guarantees; different hardware will move the
verdicts. "Real-time" here means "meets the declared p95 budget on the measured
node," nothing stronger.
