# H29 competent-baseline report — does ITD beat a *fair* established baseline across codes?

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration `configs/mission6/preregistered_protocol.toml`
(SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`), committed
before final evaluation. Evidence class: **cross-code** (two in-repo numerical methods,
Taylor-Green; NOT cross-institution). No result was tuned after inspecting the holdout;
the 0.02 margin was not lowered; **the below-chance baseline is not used as evidence**.

## The question

Mission 5 reported ITD transferring across codes at AUC ~0.85 while the established
diagnostics **anti-transferred** at ~0.03 — a below-chance baseline. Mission 6 asks the
honest follow-up: the M5 established features are **scale/amplitude dependent** across
numerical methods, while ITD channels are **dimensionless ratios**. If we make the
established baseline *competent* by removing absolute scale (a fair normalization),
does ITD still win — or was the apparent advantage **normalization, not structure**?

## Method (preregistered)

`itd_research/cross_code/transfer.py`. Per-run normalizations (`normalization.py`):
`per_run_zscore`, `per_run_rank`, `per_run_minmax` (raw is the M5 reference, never a
competent candidate). The competent normalization is **selected on development folds
only** to *maximize the established baseline's* cross-code AUC (deliberately adversarial
to ITD). Train and test use disjoint seeds; frames of one run never split. The selected
method is then evaluated **once** on the holdout seeds (90–95), both directions.

## Selection (development, seeds 10–15)

Mean established cross-code AUC over both directions, dev folds only:

| normalization | dev established AUC |
|---|---|
| per_run_zscore | 0.194 |
| **per_run_rank** | **0.667 ← selected** |
| per_run_minmax | 0.583 |

`per_run_rank` gave the established baseline its best fair shot on development.

## Holdout (seeds 90–95, evaluated once)

| direction | established_raw | **established_competent** | itd_structural | itd_full | combined |
|---|---|---|---|---|---|
| spectral→fd | 0.033 | 0.188 (≤ chance) | 0.312 | 0.029 | 0.042 |
| fd→spectral | 0.831 | 0.500 (≤ chance) | 0.800 | 0.826 | 0.771 |

## Honest reading — H38 **not supported**

1. **The competent baseline is not above chance on the holdout** (0.188 and 0.500). The
   `per_run_rank` normalization that looked best on development (0.667) did **not**
   generalize to the holdout seeds. Per the preregistered `below_chance_policy`, a
   baseline that is not above chance **cannot** anchor a claim of ITD value.
2. In the one direction where transfer works at all (fd→spectral), **established-raw =
   0.831 ties/edges ITD-full = 0.826**. ITD does **not** beat a competent baseline there;
   if anything the raw established diagnostic is marginally higher.
3. The dev→holdout collapse of the competent baseline (0.667 → 0.188/0.500) shows the
   normalized advantage is **unstable across the seed split**, not a robust structural
   signal.

**Verdict: H38 not supported.** The Mission 5 cross-code advantage does not survive a
competent, non-degenerate baseline chosen fairly on development. This is the outcome the
preregistration flagged as the honest, likely result — reported without alteration.

See `H29_BIDIRECTIONAL_TRANSFER_REPORT.md` (direction asymmetry, H40) and
`CROSS_CODE_CHANNEL_STABILITY_REPORT.md` (the full normalization × direction grid).
