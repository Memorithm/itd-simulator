# H29 bidirectional transfer report — is the cross-code signal symmetric? (H40)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **cross-code** (pseudo-spectral ⇄ finite-difference, Taylor-Green).

## The question (H40)

A genuinely transferable structural signal should work in **both** directions:
train-on-spectral→test-on-FD **and** train-on-FD→test-on-spectral. Mission 5 reported
only one direction. Mission 6 evaluates both.

## Result (holdout seeds 90–95, dev-selected competent normalization `per_run_rank`)

| direction | established_raw | established_competent | itd_structural | itd_full |
|---|---|---|---|---|
| spectral→fd | 0.033 | 0.188 | 0.312 | 0.029 |
| fd→spectral | 0.831 | 0.500 | 0.800 | 0.826 |

## Honest reading — H40 **not supported**

The two directions **disagree sharply**:

- **fd→spectral**: a model trained on the finite-difference code transfers to the
  spectral code — established-raw (0.831) and ITD (0.80–0.83) are both above chance and
  roughly tied.
- **spectral→fd**: a model trained on the spectral code transfers to *neither* baseline
  above chance — established, ITD-structural and ITD-full are all **below chance**
  (0.03–0.31). The learned decision is effectively sign-flipped on the FD code.

This asymmetry points to a **code-pair artefact** (one code appears to be a smoother /
more-regularized source whose model generalizes to the other, but not vice versa) rather
than a **direction-invariant structural property of ITD**. A universal, transferable ITD
signature would not depend on which code is the source.

**Verdict: H40 not supported.** The cross-code result is not useful in both directions;
combined with H38 (not supported), the Mission 5 "promising but confounded" transfer is
best explained as a small-sample, direction-specific effect, not evidence that ITD
carries transferable structural information across numerical methods.

## Related hypotheses (same campaign, honestly bounded)

- **H37** (ITD-only stays predictive across codes, larger ensemble): *partially / not
  supported* — ITD is above chance only in the fd→spectral direction and not above a
  competent baseline; it is below chance spectral→fd.
- **H41** (transfer across resolution changes) and **H42** (survives temporal-alignment
  policies): **not separately established** — with the cross-code signal itself failing
  H38/H40 on the base configuration, resolution- and alignment-robustness of a positive
  transfer are moot. Reported honestly as *inconclusive*, not claimed.
