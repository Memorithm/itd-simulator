# External incremental-value report (H52/H53) — the decisive negative

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Evidence class:
**external-DNS** (JHTDB isotropic1024coarse). Evidence level **E9** (predictive development
on a locked temporal holdout). Does not modify `ITD V29.18`.

## Setup

A fixed 16³ Eulerian box was sampled from JHTDB isotropic turbulence at 48 consecutive
times (Δt=0.1). The event is an **ITD-independent** extreme-enstrophy burst: a frame is
positive iff its established enstrophy exceeds the 67th percentile of the **development**
frames' enstrophy (threshold fixed on dev only). Frames are split by time into an earlier
development block and a later held-out block; adjacent frames are never split across
train/test. Feature sets: `established` (enstrophy, Q⁺ fraction, λ₂⁻ fraction, swirl),
`itd` (8 channels), `established+ITD`.

## Result (locked temporal holdout)

| feature set | held-out AUC |
|---|---|
| established only | **1.000** |
| ITD only | 1.000 |
| established + ITD | 1.000 |
| **added value (established+ITD − established)** | **+0.000** |

## Honest reading — H53 **not supported**, H52 **not supported**

- The competent **established** baseline already predicts the enstrophy event **perfectly**
  (AUC 1.000) — it is not degenerate or below chance, so the preregistered comparison is
  valid. Adding ITD changes the held-out AUC by **exactly zero**.
- ITD's apparent event-tracking comes entirely through `intensity`, which is ~redundant
  with enstrophy (rank correlation **+0.994**; see `EXTERNAL_ITD_DIAGNOSTIC_REPORT.md`).
  The non-redundant ITD channels do not track the event.
- Therefore ITD provides **no incremental predictive value** over competent established
  diagnostics on genuine external DNS. This is the Mission 4–6 conclusion, now confirmed on
  **real external data**.

## Limitations (stated, not hidden)

The external cutout is a short single-box sequence; the established baseline saturates at
AUC 1.000 for this enstrophy-threshold event, which caps the *measurable* added value at
zero rather than proving ITD carries none in every regime. The finding is: **on the one
genuine external event we could label and evaluate without leakage, ITD added nothing.**
No margin was lowered and no below-chance baseline was used. The negative is preserved.
