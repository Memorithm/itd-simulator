# Cross-code channel-stability report — the full normalization × direction grid

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`.
Evidence class: **cross-code** (Taylor-Green, pseudo-spectral ⇄ finite-difference).

## Purpose

Transparency: show **every** normalization × direction holdout AUC, so no reader can
suspect a hidden normalization made ITD (or the established baseline) look better. This
descriptive grid is **explicitly not** used to choose the H38/H39 verdict — that verdict
is bound to the development-selected competent method (`per_run_rank`; see
`H29_COMPETENT_BASELINE_REPORT.md`). Selecting a method *after* seeing this grid would be
holdout fishing and is prohibited by the preregistration.

## Descriptive holdout grid (seeds 90–95, transparency only)

### spectral → fd

| normalization | established | itd_structural | itd_full |
|---|---|---|---|
| raw | 0.033 | 0.033 | 0.854 |
| per_run_zscore | 0.146 | 0.146 | 0.146 |
| per_run_rank | 0.188 | 0.312 | 0.029 |
| per_run_minmax | 0.458 | 0.146 | 0.146 |

### fd → spectral

| normalization | established | itd_structural | itd_full |
|---|---|---|---|
| raw | 0.831 | 0.500 | 0.500 |
| per_run_zscore | 0.253 | 0.265 | 0.319 |
| per_run_rank | 0.500 | 0.800 | 0.826 |
| per_run_minmax | 0.561 | 0.733 | 0.906 |

## Honest reading — the signal is **noise-dominated and unstable**

- The AUCs swing wildly with normalization and direction. `itd_full` spectral→fd is
  **0.854** under `raw` but **0.029** under `per_run_rank`; fd→spectral it is **0.500**
  under `raw` but **0.906** under `per_run_minmax`. No channel set has a stable,
  direction- and normalization-robust advantage.
- The **Mission 5 headline** (ITD ~0.85 spectral→fd, raw) is reproduced exactly here as
  the single `raw / spectral→fd / itd_full = 0.854` cell — and it is revealed as **one
  fragile corner** of a 24-cell grid that evaporates when the direction flips or the
  features are normalized.
- A tempting cherry-pick — `per_run_minmax / fd→spectral / itd_full = 0.906` vs its
  established 0.561 — is **not** claimable: it is the opposite direction's counterpart
  (`per_run_minmax / spectral→fd / itd_full = 0.146`, below chance) that kills it, and
  the preregistration binds the verdict to the dev-selected method regardless.

## Why so unstable

The Taylor-Green event is early (event frame ≈ 6 of ~26), leaving only a handful of
leakage-safe pre-event frames per run; with 6 dev + 6 holdout seeds the grouped estimates
carry wide uncertainty. The grid is best read as **evidence of instability**, not as a
menu of results to pick from.

**Conclusion.** No ITD channel subset demonstrates stable cross-code structural transfer.
This corroborates H38 (not supported) and H40 (not supported) and supersedes the Mission 5
single-corner impression with a fuller, honest picture.
