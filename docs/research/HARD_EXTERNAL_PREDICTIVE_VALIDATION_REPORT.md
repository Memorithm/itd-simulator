# Hard external predictive validation report (Mission 4, H17–H26)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistered protocol `configs/mission4/preregistered_protocol.toml`
(SHA-256 `b49049e02d28561326c170c32ae34055b9e712bfca8721eb09404fbd35e1523f`); the runtime
verifies this hash, so the locked configuration is honoured (`matches_preregistration =
true`). Reproduce with `python -m itd_research.hard_prediction run --family {merger,
taylorgreen} --output <dir>` (a tiny `--quick` form runs in CI). No result was tuned
after inspecting the final holdout.

## Central question and headline

*Does ITD retain predictive or complementary value on hard, unseen, degraded events —
enough to distinguish it from established diagnostics?* **On the achievable evidence:
ITD predicts the events well, but it does not add credible value over an established
multi-feature baseline, and it does not transfer across solvers.** The genuinely
positive Mission 4 findings are robustness (H21/H22), out-of-distribution abstention
(H23), event-specific channel structure (H25), and end-to-end latency (H26).

## Design (leakage-safe, grouped by simulation)

Held-out flows are perturbed, parameter-jittered, seed-keyed simulations, split by
**simulation seed** into development (10–15) and final holdout (90–95); no frame of a
run appears in two splits. Events are **ITD-independent**: the 2D-merger core-count
2→1 transition, and the 3D-Taylor–Green enstrophy-production peak (a weak,
under-resolved breakdown). Features are the ITD full signature and a locked
established-diagnostic set on a common 2D plane. Models are interpretable (regularised
logistic; LDA/tree secondary). AUC CIs are grouped bootstraps resampling whole runs.

## H17 — hard-event prediction: **supported within tested scope**

On the locked holdout (6 runs/family), ITD alone predicts the event with
**AUC ≈ 1.0** (merger 1.000, Taylor–Green 1.000), zero missed events, and useful lead.
So ITD *does* predict these held-out transitions. (The tasks are still highly
separable; see limitations.)

## H18 — added value over established diagnostics: **not supported** (the key result)

The decisive product test — does `established + ITD` beat `established` on held-out
data? — fails the preregistered Gate H (margin 0.02, CI must exclude 0):

| family | AUC established | AUC established+ITD | ΔAUC | 95% grouped-bootstrap CI | verdict |
|---|--:|--:|--:|--:|---|
| merger | 0.991 | 1.000 | **+0.007** | [+0.000, +0.016] | not supported |
| Taylor–Green | 1.000 | 1.000 | **+0.000** | [+0.000, +0.000] | not supported |

Adding ITD improves held-out AUC by at most +0.007 — **below the 0.02 margin and with
a CI touching 0**. ITD carries essentially the same predictive information as the
established diagnostics on these events; it does not add credible value on top of them.
This is consistent with the Mission 3 ceiling ties and is preserved, not softened.

## H21 / H22 — robustness to degradation and partial observation: **supported within scope**

Training and testing at the *same* degradation level (so this measures signal
survival, not distribution shift), the held-out `established+ITD` AUC stays high:

| degradation | merger AUC | Taylor–Green AUC |
|---|--:|--:|
| clean | 1.000 | 1.000 |
| noise 5 % | 0.947 | 0.983 |
| noise 10 % | 0.927 | 0.958 |
| downsample ×2 | 1.000 | 1.000 |
| mask 20 % | 0.996 | 0.992 |
| central crop (H22) | 1.000 | 1.000 |
| downstream half (H22) | 1.000 | 1.000 |

The signal survives realistic noise, masking, downsampling, and partial-domain
observation (AUC ≥ 0.93 throughout). Robustness is a property of the *combined*
predictor; it does not revive ITD-specific added value.

## H19 / H20 / H23 / H24 / H25 / H26 — see the companion reports

`CROSS_SOLVER_TRANSFER_REPORT` (H19: **not supported** — merger→TG AUC 0.05, TG→merger
0.50), `CROSS_SOURCE_GENERALIZATION_REPORT` (H20: **blocked**), `OOD_ABSTENTION_REPORT`
(H23: **supported** — detection AUC 1.0, abstention cuts selective risk 0.53→0.007),
`HARD_PIV_PREDICTION_REPORT` (H24: **blocked**), `EVENT_SPECIFIC_CHANNEL_REPORT`
(H25: **supported** — merger favours localization/flatness, magnitude channels favour
the enstrophy-defined breakdown), `END_TO_END_REALTIME_REPORT` (H26: **supported** —
all workloads meet p95).

## Consolidated verdicts

| id | hypothesis | verdict |
|---|---|---|
| H17 | predicts hard held-out events | supported within tested scope |
| H18 | **adds value over established diagnostics** | **not supported** |
| H19 | cross-solver transfer | **not supported** |
| H20 | cross-source/institution transfer | **blocked** (one external source) |
| H21 | noise/filter/mask/downsample robustness | supported within tested scope |
| H22 | partial-observation robustness | supported within tested scope |
| H23 | OOD detection + abstention | supported within tested scope |
| H24 | annotated time-resolved PIV prediction | **blocked** (no such data) |
| H25 | event-specific channels | supported within tested scope |
| H26 | end-to-end real-time | supported within tested scope |

## Limitations (declared)

Two local solver families at modest resolution; the events remain highly separable, so
the tasks saturate (AUC ceiling) and cannot separate two already-excellent predictors —
which is itself the honest reason H18 fails rather than succeeds. External CFD/DNS and
annotated vortical PIV are unavailable in this environment (H20/H24 blocked; see the
dataset inventory). Nothing here certifies ITD; it shows ITD is a competitive but not
additive predictor on these held-out events, robust to degradation, and safely
abstaining out of domain.
