# Cross-source structural transfer report (H65)

Status: **research report — H65 is now CONCLUSIVE** (it was *inconclusive* in Mission 8).
Not a certified revision; does not modify `ITD V29.18`.

Follow-up protocol: `configs/mission8h65/preregistered_protocol.toml`
(SHA-256 `83c20f854bf4cc5e049978f089baf671cafe616009a60e3d8008c76fdac549fa`), committed
`825447d` and **pushed before any source-B data was fetched**. Parent protocol
`configs/mission8/preregistered_protocol.toml` (SHA-256 `ddd64804…`).

## Design

Calibrate `BASELINE_COMPETENT_COMBINED` and `BASELINE_COMPETENT_COMBINED +
ITD_3D_NONREDUNDANT` on source A's development sequences (`iso_run1`, `iso_run2`, JHTDB
isotropic1024coarse), then evaluate **without refitting** on source B (JHTDB mhd1024) —
same event definition, same feature sets, same model, source-level grouping.

Both sources are JHTDB (same institution, same access modality): this is a
**within-institution cross-physics** transfer test (isotropic hydrodynamic → forced MHD
turbulence), never a cross-institution generalization claim.

## Why Mission 8 was inconclusive, and what changed

Mission 8 fetched two MHD windows (24 and 16 frames). Both contained **zero** qualifying
Q-criterion topology events, so the source-B label set was single-class and no ROC-AUC was
computable. That was a data-collection artefact, not a finding.

This follow-up preregistered **six** windows at fixed, pre-declared origins on a spread
lattice, with the binding rule that **all six are fetched and all six are used, whatever
they contain** — including any window with zero events. No window could be added, dropped
or re-rolled after a result was seen.

### Declared deviation: 26 frames per window, not the preregistered 48

The protocol specified 48 frames per window. **That was impossible, and specifying it was a
planning error on my part**: `mhd1024` has a hard time-range limit at `t = 2.5`. All six
windows failed at exactly the same frame (index 26, `t = 2.60`), and a targeted probe
confirmed the boundary — `t = 2.50` succeeds, `t ≥ 2.55` returns HTTP 500. The maximum
window length at `dt = 0.1` is therefore 26 frames.

The truncation is **uniform, externally imposed and content-independent**: the same
absolute time cut applies to every window, it was determined by the dataset rather than by
inspecting any result, and **no origin was substituted** (the protocol's anti-substitution
rule is intact). The evaluation proceeds on 6 × 26 = **156 frames**, versus Mission 8's 2
windows / 40 frames.

## Source-B acquisition (all six windows, as preregistered)

| window | origin | frames | events | positive frames |
|---|---|---|---|---|
| `mhd_w1` | (100, 200, 300) | 26 | 1 — `core_split`@25 | 3 |
| `mhd_w2` | (500, 200, 300) | 26 | 2 — `core_merger`@16, `core_split`@18 | 5 |
| `mhd_w3` | (100, 600, 300) | 26 | **0** | 0 |
| `mhd_w4` | (100, 200, 700) | 26 | 1 — `core_split`@18 | 3 |
| `mhd_w5` | (600, 600, 600) | 26 | 2 — `core_merger`@1, `core_merger`@17 | 5 |
| `mhd_w6` | (300, 800, 500) | 26 | 1 — `core_merger`@16 | 3 |

**7 qualifying events, 156 frames, 19 positive frames, both classes present → conclusive.**
`mhd_w3` contains no event and is reported and retained, exactly as the protocol requires.
Zero windows blocked.

## Result

```
source-A holdout   established 0.519   augmented 0.344
transfer to B      established 0.541   ITD-only 0.471   augmented 0.477
drop vs A holdout  established -0.022  augmented -0.132
```

**H65: not supported.** The preregistered rule required augmented transfer AUC > 0.55 *and*
a drop < 0.20. The drop criterion passes; the **performance criterion fails** — the
augmented model transfers at **0.477, below chance**.

### The small drop is not evidence of successful transfer

This is the result's one genuinely misleading-looking number and it must not be spun. The
augmented drop is *negative* (−0.132), i.e. the model does slightly **better** on source B
than on source A's own holdout — and the established drop is −0.022, essentially flat.

That reads like "the profile transfers stably." It does not mean the transfer succeeded. It
means a model that was already near or below chance on source A stays near or below chance
on source B. **Low degradation of a non-working model is not transfer.** H65 asks whether a
calibrated profile remains *useful*, and 0.477 is not useful.

### Relation to H62 (reported, not re-litigated)

On source B the augmented model (0.477) is again **worse** than established alone (0.541),
consistent with Mission 8's H62 negative. Per the follow-up protocol this comparison is
reported alongside but is **not** claimed as new independent evidence for H62: H65 is a
transfer question, and Mission 8's incremental-value verdict stands on its own holdout
evidence.

## Honest limitations

* Six windows from one dataset at one institution; still cross-physics, not
  cross-institution.
* 26-frame windows are short for a `persistence = 2` event definition; 7 events across 156
  frames is a thin positive class (12% prevalence).
* A single locked evaluation (`evaluations_allowed = 1`), not re-run after inspection.

## What this changes

H65 moves from **inconclusive** to **not supported**. The gap closed here was a collection
artefact, and closing it produced a negative — the calibrated structural profile does not
usefully transfer to a second, physically different external source.
