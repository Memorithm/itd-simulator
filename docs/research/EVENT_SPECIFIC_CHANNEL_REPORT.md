# Event-specific channel report (Mission 4, H25)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **local-solver**. The expected structure was **not** assumed — the
numbers are reported as found.

## Question (H25)

Do different event classes require different ITD (and established) channel subsets?

## Method

Per-channel held-out AUC: a single-feature logistic predictor is trained on the
development runs and scored on the held-out runs, one channel at a time, separately for
each event family (merger, Taylor–Green breakdown). Labels are ITD-independent.

## Results — per-channel held-out AUC

**Merger (co-rotating pairing):**

| channel | AUC | | channel | AUC |
|---|--:|---|---|--:|
| localization | 0.92 | | roughness | 0.82 |
| vorticity_flatness | 0.92 | | swirl_mean | 0.78 |
| heterogeneity | 0.89 | | palinstrophy | 0.56 |
| q_positive_fraction | 0.89 | | temporal_deformation | 0.54 |
| sign_mixing | 0.88 | | intensity / enstrophy / vorticity_rms | **0.44** |

**Taylor–Green breakdown (enstrophy-production peak):**

| channel | AUC | | channel | AUC |
|---|--:|---|---|--:|
| sign_mixing | 0.99 | | enstrophy / vorticity_rms | 0.98 |
| intensity | 0.98 | | palinstrophy | 0.95 |
| heterogeneity / localization / roughness | 0.98 | | swirl_mean | 0.89 |
| structure_score | 0.98 | | q_positive_fraction | 0.88 |
| — | — | | temporal_deformation | 0.38 |

## H25 classification: **supported within tested scope**

The predictive channel structure **differs by event class**:

* **Merger** is best predicted by **structural** channels — `localization`,
  `vorticity_flatness`, `heterogeneity` (~0.9) — while the **magnitude** channels
  (`intensity`, `enstrophy`, `vorticity_rms`) are the *worst*, at 0.44 (below chance:
  they anti-predict, because a viscous merger dissipates enstrophy). This matches the
  Mission 3 finding that magnitude channels point the wrong way for mergers.
* **Taylor–Green breakdown** is predicted by **almost every** channel (~0.98) —
  because the event is *defined* by an enstrophy quantity, so magnitude channels catch
  it trivially. The one consistent failure is `temporal_deformation` (0.38).

So the "right" channels are event-dependent: structural/localization channels for the
merger, magnitude channels for the enstrophy-defined breakdown. This is reported as
observed; it was not optimised to match a preconceived mapping, and `temporal_
deformation` — which a naive expectation might favour for a transient event — is the
weakest channel on *both* families.

## Limitations

Single-channel AUC ignores channel interactions (a channel weak alone can help in
combination); two event families only; the Taylor–Green ceiling reflects an
enstrophy-defined label. A full nested channel-selection study across more event
classes (reconnection, shedding, fragmentation) needs the external datasets that are
currently blocked. No globally optimal ITD vector is claimed.
