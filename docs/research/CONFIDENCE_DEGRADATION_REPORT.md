# Confidence-degradation report — a monotone, transparent discount under shift

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **local-solver**.

## Mechanism

`itd_research/ood_shift/policy.py`. Instead of a binary predict/abstain switch, confidence
is a **monotone, transparent** function of shift severity:

```
confidence_discount(severity) = clip(1 - (severity - s_low) / (s_high - s_low), 0, 1)
```

— full confidence at/below `s_low`, linearly decreasing to zero at `s_high`, never
increasing with severity. Bands are calibrated on **development data only**: `s_low` is
the 90th percentile of in-domain severity; `s_high` is the median severity of a *known*
far-OOD (Taylor-Green) control (“abstain when as anomalous as a far-OOD flow”). Inputs are
transparent (severity, shift type, quality, mask fraction); no holdout labels are used.

## The utility model

A policy assigns each frame a state and a confidence `c` (accept → 1, reduce → discount,
abstain → 0). Utility credits and charges are **confidence-weighted** so degrading
confidence is not a free lunch:

- `correct_accepted   = Σ c · [prediction correct]`
- `false_confidence   = Σ c · [prediction wrong]`   (charged at `high_cost = 4`)
- `unnecessary_abstention = #{abstained yet predictable}`  (charged at `moderate_cost = 1`)
- `utility = correct_accepted − 4·false_confidence − 1·unnecessary_abstention`  (per frame)

A **confident** wrong prediction is the worst outcome; a **hedged** (reduced-confidence)
wrong prediction is charged far less; a correct prediction earns credit proportional to
the confidence committed. This is the calibration incentive: high confidence only where
reliability is high.

## Calibrated bands (full campaign)

`s_low = 1.85`, `s_high = 171.75`, `global_threshold = 2.48`.

## Honest finding — the discount is well-behaved, the calibration is the weak link

The discount is monotone and transparent by construction (unit-tested). But the
**pre-committed** `s_high` sits at the far-OOD median (171.75), two orders of magnitude
above the near-OOD severities (~2–20). Consequently:

- near-OOD frames receive a discount of only `1 − (≈10−1.85)/170 ≈ 0.95` — i.e. **almost
  full confidence**, so the reduce band barely reduces confidence where it should;
- far-OOD frames (severity ~100) still get confidence ~0.42 — **predicted, not
  abstained** — which leaves residual false confidence.

This is reported, not fixed: lowering `s_high` after seeing the result would be post-hoc
optimization, prohibited by the preregistration. The consequence for the policy ranking
is analyzed honestly in `RISK_COVERAGE_ABSTENTION_REPORT.md` (H44 not supported under this
calibration; the utility-optimal operating point is at lower coverage than the
pre-committed threshold selects). The mechanism is sound; the transparent far-OOD-anchored
calibration is **not** the utility-optimal one, and we did not tune it to become so.
