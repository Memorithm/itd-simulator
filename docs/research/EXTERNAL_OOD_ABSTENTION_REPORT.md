# External OOD / abstention report (H56)

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Evidence class:
**external-DNS** vs **local-solver**. Does not modify `ITD V29.18`.

## Test — does the OOD detector flag a real local→external shift?

An OOD reference (the Mission 4 transparent Mahalanobis detector) was fit on **local**
synthetic Taylor-Green ITD features, then used to score the **external JHTDB DNS** ITD
features — a genuine `local_solver → external_DNS` shift.

| group | mean Mahalanobis score |
|---|---|
| in-domain (local synthetic) | 0.9 |
| external DNS (JHTDB) | ≈ 1.0e5 |
| ratio | ≈ **1.2e5×** |

## Honest reading — H56 **partially supported**

- The detector **correctly and decisively flags** the external DNS as out-of-distribution
  relative to the local reference — the desired behaviour: a model developed on local flows
  should not silently extrapolate to real turbulence.
- **But** the distance magnitude (~10⁵) is so extreme that it reproduces the **Mission 4
  finding**: when in- and out-of-distribution sets are astronomically far apart, the OOD
  score is *uninformative* about calibration — it only says "very different", offering no
  graded severity that the shift-aware three-state policy (Mission 6) could use to reduce
  confidence intelligently. Under any reasonable threshold, every external frame abstains.

So the detector is *safe* (it never confidently predicts on the external data) but *blunt*
(it cannot distinguish a mild external shift from a severe one at this magnitude). Utility
weights were **not** tuned on any external holdout. Binary abstention here would abstain on
100% of external frames; a graded policy has nothing to grade because the local reference is
simply not a meaningful basis for real turbulence.

**Verdict: H56 partially supported** — external shift detection works; graded calibration
does not, for the same reason Mission 4 documented. Reported without inflation.
