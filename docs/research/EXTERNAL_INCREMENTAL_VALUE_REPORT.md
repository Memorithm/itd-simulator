# External incremental-value report (Mission 5, H28/H33)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence classes: **cross-code** (achievable proxy) and **local-solver** (H33).

## Questions

* **H28** — does adding ITD to strong established diagnostics give a preregistered,
  statistically credible improvement on **external** holdouts?
* **H33** — does ITD add **more** incremental value under noise/masking/partial
  observation than on clean complete fields?

## H28 classification: **blocked** (external), with a cross-code proxy

No external labelled holdout is integrable in this offline environment (see
`CYLINDER_RE3900_INTEGRATION_REPORT`, `STRONGLY_VORTICAL_PIV_REPORT`), so H28 cannot be
evaluated on genuinely external data. The achievable **cross-code proxy**
(`SAME_PHYSICS_CROSS_CODE_REPORT`, H29) found: ITD-only transfers across codes far better
than established-only (0.85 vs 0.03), but the `established + ITD` added-value verdict is
**confounded by a below-chance baseline** and established+ITD (0.50) is worse than
ITD-only. So even the proxy does **not** provide a clean "established+ITD beats a
competent established baseline" result. The preregistered 0.02 margin was **not**
lowered.

## H33 classification: **not supported**

On the merger family, the established-vs-established+ITD added value was measured at two
degradation levels:

| condition | AUC established | AUC established+ITD | Δ | 95% CI |
|---|--:|--:|--:|--:|
| clean | 0.991 | 1.000 | +0.007 | [+0.000, +0.016] |
| 10 % noise | 0.930 | 0.927 | **−0.005** | [−0.035, +0.014] |

Adding ITD does **not** produce more incremental value under degradation — the Δ is nil
(and within CI of zero) when clean and slightly *negative* under 10 % noise. Degradation
lowers both feature sets together; it does not open a gap that ITD fills. This is
consistent with the Mission 4 H18 result (no credible added value) and is preserved.

## Consolidated

| hypothesis | verdict |
|---|---|
| H28 external incremental value | **blocked** (no external holdout; cross-code proxy inconclusive/confounded) |
| H33 degradation-specific value | **not supported** |

## Limitations

No external holdout; the cross-code proxy uses two in-repo codes and a below-chance
baseline; H33 tested on one family at two noise levels. The competent-baseline external
test needs the blocked datasets.
