# Event-profile stability report (Mission 5, H34)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **cross-code**. Reproduce with `python -m itd_research.profiles run
--output <dir>`.

## Question (H34)

Do event-specific channel profiles remain stable across at least two independent
sources of the **same** event?

## Method

For the Taylor-Green breakdown produced by the pseudo-spectral and finite-difference
codes, compute per-channel held-out AUC (single-channel importance) on each source, then
rank-correlate the two importance profiles and measure top-3 channel overlap. The
profile registry (`itd_research.profiles.registry`) declares each profile's channels and
valid domain; `select_profile` refuses to apply outside the declared domain.

## Results

| quantity | value |
|---|--:|
| channel-importance rank correlation (spectral vs FD) | **0.47** |
| top-3 channel overlap | **0.67** (2 of 3) |

## H34 classification: **partially supported**

The Taylor-Green channel profile is **moderately** stable across the two codes: two of
the three most-predictive channels agree, and the overall importance ranking correlates
at 0.47. It is not fully stable — the reshuffle in the lower-importance channels and the
imperfect rank correlation mirror the cross-code event-timing discrepancy (H29) and the
fact that the enstrophy-defined breakdown is predictable by many channels, so their
ordering is only weakly determined. The declared profiles therefore carry an explicit
domain and known-failure-modes list, and are never applied silently outside them.

## Limitations

One event class (breakdown), two in-repo codes, small ensembles; single-channel
importance ignores interactions. A second event class and genuinely external sources
(blocked here) would strengthen the test.
