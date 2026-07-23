# Risk-coverage abstention report — three-state vs binary (H44/H45)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **local-solver**. Costs: false-confidence `high_cost = 4`,
unnecessary-abstention `moderate_cost = 1` (preregistered).

## The questions

- **H44**: does a three-state `accept / accept_with_reduced_confidence / abstain` policy
  **beat binary abstention** on utility?
- **H45**: does unnecessary abstention fall **far below** the Mission 5 ~0.85 while
  selective risk stays controlled?

## Policy comparison (full campaign, per-frame utility; higher is better)

| policy | utility | coverage | false_confidence | unnecessary_abstention |
|---|---|---|---|---|
| no_abstention | −0.512 | 1.00 | 0.302 | 0.000 |
| global_binary | −0.221 | 0.24 | 0.000 | 0.658 |
| shift_aware_binary | **−0.151** | 0.31 | 0.012 | 0.575 |
| shift_aware_confidence_degradation | −0.263 | 1.00 | 0.222 | 0.000 |
| three_state | −0.263 | 0.95 | 0.222 | 0.000 |

## H45 — **supported**: unnecessary abstention eliminated

The three-state policy drives **unnecessary abstention to 0.00**, versus **0.58–0.66** for
the binary policies and the Mission 5 ~0.85. The specific over-abstention problem Mission 5
identified — rejecting still-predictable shifted frames — is solved: the reduce band keeps
those frames as (hedged) predictions instead of abstaining. False confidence (0.222) stays
below the do-nothing `no_abstention` baseline (0.302). **H45 supported within tested
scope**, with the explicit caveat below.

## H44 — **not supported**: three-state does not beat binary on total utility

Under the preregistered utility and the pre-committed far-OOD-anchored `s_high`, the
three-state policy (−0.263) **does not beat** the best binary policy (`shift_aware_binary`,
−0.151). Eliminating abstention means predicting on far-OOD frames with residual
confidence, and at `high_cost = 4` that false confidence dominates the saved abstention
cost. **H44 not supported.**

Two honest caveats that keep this from being oversold *or* dismissed:

1. **The ranking is not robust.** At the CI/quick resolution the same code gives
   three_state utility **+0.182** beating binary **+0.024** (H44 "supported"); at full
   resolution it flips to the table above. A result that flips with resolution is **not a
   robust advantage** — reported as such.
2. **The utility-optimal operating point is at lower coverage.** The three-state
   risk-coverage sweep peaks near **coverage 0.63 (utility +0.004)** and is negative at the
   pre-committed coverage 0.95. A lower `s_high` would have done better — but choosing it
   *after* seeing this curve is post-hoc optimization, which the preregistration forbids.
   The curve is shown so the reader sees the gap honestly.

## Net honest conclusion

The shift-aware machinery **achieves its narrow goal** (H45: eliminate unnecessary
abstention on still-predictable shifts) but **does not achieve the broader goal**
(H44: better total utility than binary abstention) under the preregistered costs and the
transparent, pre-committed calibration. It trades one error type (over-abstention) for
another (residual false confidence); which trade is preferable is cost-dependent and, at
these costs, does not favor three-state. No calibration was tuned to force a positive H44.
