# Partial-observation / degradation structural report (H66-H68)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Design

Rebuild each sequence's baseline + structural trajectories and ITD-independent events
from **degraded raw frames** at each preregistered level, then rerun the same
established-vs-augmented holdout comparison as the primary test, reporting established-
only, ITD-only, combined, and the **ITD-specific added value** at every level — H66/H67/H68
require the ITD-specific effect, never "the combined model stayed accurate" alone.
Development = `iso_run1`, `iso_run2`; holdout = `iso_topo`, `iso_run3`; bootstrap = 500 per
level (reduced from the preregistered 2000 for compute-time reasons — an explicit,
acknowledged deviation, stated here rather than hidden).

**Deviation from the full preregistered level list**: only a bounded subset of levels was
evaluated (noise `{0.0, 0.05}`, mask `{0.0, 0.20}`, downsample `{1, 2}`, partial
observation `{full, central_crop}`), not the complete preregistered grids, for compute-time
reasons. Stated explicitly, not hidden.

## Result (corrected event detector — see `MISSION8_REPRODUCIBILITY_REPORT.md`)

| kind | level | established | ITD-only | augmented | added value (95% CI) |
|---|---|---|---|---|---|
| noise | 0.0 | 0.519 | 0.246 | 0.344 | −0.168 [−0.175, −0.153] |
| noise | 0.05 | 0.008 | 0.129 | 0.016 | +0.006 [+0.000, +0.008] |
| mask | 0.0 | 0.519 | 0.246 | 0.344 | −0.168 [−0.175, −0.153] |
| mask | 0.20 | NaN | NaN | NaN | inconclusive |
| downsample | 1× | 0.519 | 0.246 | 0.344 | −0.168 [−0.175, −0.153] |
| downsample | 2× | 0.331 | 0.384 | 0.343 | −0.018 [−0.269, +0.198] |
| partial obs. | full | 0.519 | 0.246 | 0.344 | −0.168 [−0.175, −0.153] |
| partial obs. | central_crop | NaN | NaN | NaN | inconclusive |

**No level shows H66/H67/H68 supported.** The `noise=0.05` added value (+0.006) is
positive but its CI (`[0.000, 0.008]`) does not reach the preregistered `0.02` margin —
"not supported" under the locked decision rule, and in absolute terms the established
baseline itself has collapsed to near-chance (0.008) at that noise level, so this is a
near-degenerate comparison, not a genuine ITD advantage under noise. `downsample=2×`'s CI
(`[−0.269, +0.198]`) is wide enough to include zero by a wide margin — inconclusive, not
a positive finding.

## An honest, structural (not merely statistical) finding: `mask=0.20` and `central_crop`

At `mask=0.20` and `partial_observation=central_crop`, the holdout AUC is **NaN** — not a
weak signal, but *no computable signal at all*. Under the corrected, ITD-independent
event definition, sufficient masking/cropping removes the pre/post persistence the event
label itself requires: some sequences' degraded region-count series never sustain a
change for `persistence=2` frames, collapsing the training or holdout label set to a
single class. This means H67/H68 (partial observation / degradation) are blocked at these
levels by **event-definition scarcity under degradation**, distinct from a prediction
failure — a genuinely useful methodological finding for future missions (a partial-
observation or noise study on this event type needs either a coarser persistence
threshold or a richer holdout to remain testable at these degradation levels).

## Conclusion

Across every tested degradation level, existing ITD structural channels show no
reproducible, margin-exceeding incremental value — and several degradation levels make
the ITD-independent event itself unobservable rather than merely hard to predict.
