# Full-volume optimization report — shared-gradient reuse (H48)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **performance** + **software-equivalence**. Timings are hardware-dependent
feasibility measurements, not guarantees.

## The optimization

The Mission 5 `evaluate_full_volume` computes the velocity-gradient tensor **twice** —
once inside the ITD-3D channel kernel and once for the established Q / λ₂ / swirl
diagnostics. `itd_research/full_volume/optimized.py` computes it **once** and shares it:
`evaluate_itd3d` gained an optional `gradient=` fast path, and the optimized full-volume
path passes the single gradient to both consumers. It also supports **selective profiles**
(`merger`, `stretching`, `full`) that return only the requested channels.

## Numerical equivalence — **bitwise equal**

The optimization removes duplicate work; it does not change any operator or reduction, so
the result is identical by construction. `verify_equivalence` confirms it:

| check | result |
|---|---|
| optimized 'full' vs reference (per channel) | `max_abs_diff = 0.0`, `max_rel_diff = 0.0` |
| classification | **bitwise_equal** |
| precomputed-gradient vs recomputed (`evaluate_itd3d`) | exact equality (unit-tested) |

The preregistered equivalence bar (≤ 1e-9 relative) is met at the strongest level.

## Latency (single node, deterministic single-thread)

| workload | nodes | reference p95 | optimized p95 | speedup | equivalence |
|---|---|---|---|---|---|
| VOL-3D-XS | 32³ | ~192 ms | ~191 ms | ~1.02× | bitwise_equal |
| VOL-3D-S | 48³ | 687 ms | 592 ms | **1.16×** | bitwise_equal |

The saving grows with problem size (the shared gradient is a larger absolute cost at 48³),
reaching ~14% p95 reduction at VOL-3D-S while preserving numerical results exactly.

## Honest scope

- The realized gain is the **shared velocity gradient** (and any skipped established
  diagnostics under a selective profile). The fused ITD kernel still evaluates its channel
  set internally, so selective profiles are a **projection**, not per-channel compute
  pruning — stated plainly rather than over-claimed.
- Larger gains would require restructuring the fused kernel, which risks the numerical
  equivalence the mission requires (“without altering authoritative numerical results”).
  We prioritized **exact (bitwise) equivalence** over aggressive speedup.

**Verdict: H48 supported within tested scope** — a bitwise-equivalent optimization that
reduces full-volume p95 latency (up to ~1.16× at 48³), with no change to any authoritative
value.
