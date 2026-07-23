# Near-OOD abstention report (Mission 5, H31)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **local-solver**. Reproduce with `python -m itd_research.ood_near run
--output <dir>` (a `--quick`/`validate` form runs in CI).

## Question (H31)

Mission 4's OOD cases were extremely different from training (trivial separation).
Does the abstention layer reduce risk under **subtle** shifts while preserving useful
coverage — without abstaining on nearly everything?

## Method

Fit the OOD reference and predictor on a narrow in-distribution merger band
(circulation 1.2, viscosity 0.0025). Challenge with subtle shifts — untrained
circulation (1.8), untrained viscosity (0.005), untrained resolution — plus a far-OOD
control (Taylor-Green). Report detection, whether near-OOD stays predictable, and the
abstention trade-off including **unnecessary abstention** (still-predictable near-OOD
that gets abstained).

## Results

| group | mean OOD score |
|---|--:|
| in-domain | 1.6 |
| near-viscosity | 6.3 |
| near-resolution | 101 |
| near-circulation | 131 |
| far Taylor-Green | 532 |

| metric | value |
|---|--:|
| detection AUC (in vs near) | 0.986 |
| detection AUC (in vs far) | 1.000 |
| near-OOD still-predictable AUC | 0.59 |
| in-domain coverage retained | 0.91 |
| selective risk (with abstention) | 0.001 |
| full risk (no abstention) | 0.42 |
| **unnecessary abstention rate** | **0.85** |

## H31 classification: **partially supported**

Abstention **does** cut selective risk (0.42 → 0.001) while keeping 91% in-domain
coverage — the safety benefit is real. **But** the distance detector is **too
aggressive** on subtle shifts: it over-abstains on **85%** of still-predictable near-OOD
frames. The reason is visible in the scores — an untrained *viscosity* barely moves the
features (6.3, genuinely near), but an untrained *circulation* or *resolution* moves
them almost as far as the far-OOD control (101–131 vs 532). A single Mahalanobis radius
therefore cannot separate "usable subtle shift" from "unreliable" for those axes.

So abstention improves safety but at a real coverage cost on subtle shifts — it does
**not** yet deliver the goal of "useful risk reduction without abstaining on nearly
everything." A shift-aware or per-axis calibrated detector is the needed improvement.

## Limitations

One in-distribution family (merger), three subtle-shift axes, a single distance metric,
small ensembles. The over-abstention is a genuine, reported limitation, not tuned away.
