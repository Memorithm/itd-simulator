# Same-physics cross-code report (Mission 5, H29)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **cross-code** (two independent in-repo numerical methods; **NOT**
cross-institution). Reproduce with `python -m itd_research.cross_code run --output <dir>`
(a `--quick`/`validate` form runs in CI).

## Question (H29)

Does a predictor calibrated on one solver transfer to another solver simulating
substantially the same physics (Taylor-Green), and does adding ITD add credible value
on the cross-code holdout?

## The two codes (genuinely different numerics)

* **spectral3d** — pseudo-spectral, rotational nonlinear form, RK4, 2/3 dealiasing.
* **fd_solver** (new) — 2nd-order central finite differences for advection/diffusion,
  explicit fractional-step time advance, exact spectral Leray projection.

They differ in truncation error, dispersion, and time integration. This separates
*solver* from *physics/event/dimensionality* — correcting the Mission 4 confound.

## Integral agreement (same physics)

| quantity | spectral3d | fd_solver | agreement |
|---|--:|--:|---|
| initial energy | 0.125 | 0.125 | identical |
| energy trajectory correlation (normalized time) | — | — | **0.9997** |
| enstrophy trajectory correlation | — | — | 0.879 |
| enstrophy peak (event) time | 1.58 | 2.08 | **rel. error 0.31** |

The codes agree closely on the robust **integral** physics (energy) but the **fine
event timing** (enstrophy-production peak) differs by ~31% — a genuine, numerics-
sensitive discrepancy at this under-resolved 24³, reported not hidden.

## Cross-code prediction (train spectral, test finite-difference)

Held-out AUC on the finite-difference Taylor-Green (6 dev spectral runs → 6 FD holdout):

| feature set | cross-code held-out AUC |
|---|--:|
| established diagnostics | **0.03** |
| ITD only | **0.85** |
| established + ITD | 0.50 |
| added value (established+ITD − established) | +0.47, CI [+0.375, +0.500] |

## H29 classification: **partially supported** — with an explicit caveat

Read honestly, this is the **most ITD-positive** result across all missions **and** a
cautionary one:

* **ITD transfers across codes far better than the established diagnostics.** ITD-only
  reaches AUC 0.85 on the finite-difference holdout, while the established diagnostics
  **anti-transfer** (0.03 — the spectral-calibrated boundary points the wrong way on the
  FD data, because the event timing and enstrophy scaling shift between codes).
* **But the preregistered added-value verdict is confounded.** The added-value test
  (established+ITD vs established) mechanically "passes" (+0.47) only because the
  baseline is **below chance**; adding ITD rescues a failing baseline to 0.50. That is
  *not* ITD adding value on top of a competent baseline — and indeed established+ITD
  (0.50) is **worse** than ITD-only (0.85), because the anti-transferring established
  features drag the combination down.

So the defensible statement is: *on this cross-code holdout, ITD-only transfers
substantially better than established-only; the combined established+ITD does not, and
the added-value margin is met only through a degenerate below-chance baseline.* This is
promising for ITD's transferability but is **not** a clean win, and rests on a small
sample (6+6) of two in-repo codes.

## Limitations

Two in-repo pseudo-spectral/finite-difference codes (not external, not cross-
institution), one physics (Taylor-Green), 24³ (under-resolved), 6+6 runs, one event
definition. The below-chance baseline makes the added-value metric degenerate here; a
competent-baseline external replication (the Re=3900 cylinder wake) is the correct next
test and is blocked in this environment. No certified revision is implied.
