# Mission 5 final report — genuine external cross-code validation

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration `configs/mission5/preregistered_protocol.toml`
(SHA-256 `1142668b6a119cb95890e97ad11401479b6c22eae01454b8e5c099e015b45fbb`), committed
before final evaluation. No result was tuned after inspecting the final holdout; the
0.02 added-value margin was not lowered.

## Central question and honest answer

*Does ITD carry additional, transferable, operationally useful information across
independent solvers, datasets and measurement systems when the physical event is held
constant?* On the **achievable** evidence: ITD shows its **first genuinely promising
transfer result** (it survives a change of numerical method better than established
diagnostics), but this is **confounded by a below-chance baseline**, does not add clean
value, and the strongest tests (external, cross-institution, annotated vortical PIV)
remain **blocked** by data/tooling unavailable here.

## Correcting the Mission 4 confound

Mission 4 compared a 2D merger against a plane of a 3D breakdown, confounding solver,
dimensionality, event, family, label, and mechanism. Mission 5 separated them with a
**second independent 3D solver** (finite-difference projection vs pseudo-spectral) and
ran the **same** Taylor-Green physics through both — a genuine cross-code test.

## H27–H36 verdicts

| id | hypothesis | verdict | evidence class | dev → holdout |
|---|---|---|---|---|
| H27 | external labelled-event prediction | **blocked** | external-DNS | — (no data) |
| H28 | external incremental value | **blocked** | external | — (cross-code proxy confounded) |
| H29 | same-physics cross-code transfer | **partially supported** | cross-code | spectral → finite-difference |
| H30 | cross-institution transfer | **blocked** | cross-institution | — (one source) |
| H31 | near-OOD abstention | **partially supported** | local-solver | merger band → subtle shifts |
| H32 | strongly-vortical PIV agreement | **blocked** | experimental-PIV | — (no data) |
| H33 | degradation-specific ITD value | **not supported** | local-solver | merger clean vs 10% noise |
| H34 | event-profile stability | **partially supported** | cross-code | spectral vs FD Taylor-Green |
| H35 | full-volume ITD-3D feasibility | **supported within scope** | performance | 32³/48³/64³ |
| H36 | Rust ↔ Python equivalence | **supported within scope** | software-equivalence | fixture oracle |

## Key numbers

* **H29** (cross-code): energy trajectory correlation **0.9997**, enstrophy-peak event
  time differs **31%**. Cross-code held-out AUC: established-only **0.03** (anti-
  transfer), ITD-only **0.85**, established+ITD 0.50. ITD transfers better than
  established across codes, **but** the added-value margin is met only via a below-chance
  baseline and established+ITD < ITD-only → partially supported, with caveat.
* **H31** (near-OOD): detection AUC 0.99, selective risk 0.42 → 0.001 at 91% in-domain
  coverage, **but unnecessary abstention 0.85** — the detector over-abstains on subtle
  circulation/resolution shifts → partially supported.
* **H33**: added value +0.007 (clean) → −0.005 (10% noise) → not supported.
* **H34**: channel-importance rank correlation 0.47, top-3 overlap 0.67 → partially
  supported.
* **H35**: 32³ 173 ms, 48³ 427 ms, 64³ 992 ms p95, ≤ 0.1 GB, all 11 channels
  full-volume → supported.
* **H36**: Rust reproduces the Python diagnostics subset within 1e-9, offline → supported
  (subset only; not the V29.18 signature).

## The twelve final questions

1. **Predicts a genuinely external event?** No — blocked (no external labelled dataset
   integrable in CI); the achievable held-out events are local-solver.
2. **Adds value beyond strong established diagnostics?** No clean win — the cross-code
   added-value is confounded by a below-chance baseline, and H33 shows no gain under
   degradation.
3. **Transfers across solvers for the same physics?** **Yes, better than established
   diagnostics** (ITD-only 0.85 vs 0.03) — the most positive result — but combined
   established+ITD does not, and it rests on a small two-code sample.
4. **Transfers across independent sources?** Unknown — blocked (one source).
5. **More useful under degraded observation?** No (H33 not supported).
6. **Near-OOD abstention works?** Partially — it cuts risk but over-abstains on subtle
   shifts.
7. **Strongly-vortical PIV supports ITD?** Blocked (no such data).
8. **Event-conditioned profiles stable?** Partially (rank corr 0.47, top-3 overlap 2/3).
9. **Full-volume ITD-3D real-time?** Yes within envelope for 32³/48³/64³ on this CPU.
10. **Rust reproduces Python?** Yes for the diagnostics subset within 1e-9; not the
    V29.18 signature.
11. **Advanced beyond IRL-4?** No — no external qualification data integrated; the Rust
    reference and product-contract work are IRL-6-direction interface artifacts, not a
    maturity-band change.
12. **New certified revision justified?** **No.** V29.18 unchanged; all work experimental.

## Honest bottom line

Mission 5 delivers ITD's first encouraging signal — **cross-code transferability**
(ITD survives a change of numerical method better than established diagnostics) — while
being explicit that it is confounded, not additive, small-sample, and unconfirmed on
genuinely external data. The engineering deliverables (independent second solver,
near-OOD campaign, full-volume 3D benchmark, offline Rust equivalence, profile registry)
are solid; the decisive external tests (H27/H28/H30/H32) are blocked with a documented
unblocking path (the Re=3900 cylinder wake). Negatives and blocks are preserved.
