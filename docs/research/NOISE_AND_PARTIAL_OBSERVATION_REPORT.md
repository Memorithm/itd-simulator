# Noise and partial-observation robustness report (Mission 4, H21/H22)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce with `python -m itd_research.hard_prediction run --output <dir>` (degradation
sweep). Evidence class: **local-solver** held-out flows.

## Questions

* **H21** — does the predictor retain useful information after realistic noise,
  filtering, masking, and downsampling?
* **H22** — does it remain useful when only part of the domain is observed?

## Method

Each degradation is a deterministic, seeded transform of the velocity field applied at
feature-extraction time; the ITD-independent event label is unchanged. To isolate
*signal survival* (not distribution shift, which is H23), the predictor is trained and
tested at the **same** degradation level. AUC is the held-out `established+ITD` score.

## Results (held-out AUC)

| degradation | merger | Taylor–Green |
|---|--:|--:|
| clean | 1.000 | 1.000 |
| Gaussian noise 5 % RMS | 0.947 | 0.983 |
| Gaussian noise 10 % RMS | 0.927 | 0.958 |
| downsample ×2 (anti-aliased) | 1.000 | 1.000 |
| random mask 20 % (repaired) | 0.996 | 0.992 |
| central crop (H22) | 1.000 | 1.000 |
| downstream half (H22) | 1.000 | 1.000 |

## Classification: **H21 supported within scope; H22 supported within scope**

The signal survives every tested degradation: AUC stays ≥ 0.93 under 10 % noise and
≥ 0.99 under masking, downsampling, and partial-domain cropping. Noise is the most
damaging axis (monotone AUC decline with level), as expected; spatial degradations
(downsample, crop) barely move the AUC because the merger/breakdown signal is
large-scale. Masking at 20 % is tolerated because invalid vectors are neighbour-filled
(repaired mode) and reported separately from measured vectors.

## Important scope note

This is the robustness of the **combined** `established+ITD` predictor. It does **not**
show ITD-specific robustness advantage — the added-value test (H18) already found ITD
adds no credible value, so the robustness is a property the established diagnostics
share. Distinct from this, a predictor trained on *clean* data and tested on *degraded*
data collapses (distribution shift); that is the OOD problem addressed by abstention in
`OOD_ABSTENTION_REPORT`, not a robustness failure of the features per se.

## Limitations

Local-solver flows, two families, modest resolution; noise is additive Gaussian (a
measurement-like proxy, not facility-specific PIV noise); masking uses neighbour
repair. Degradation on external measured fields would be the stronger test and is
gated behind dataset integration.
