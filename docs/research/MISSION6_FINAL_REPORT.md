# Mission 6 final report — transferability, calibrated abstention, external evidence, Rust expansion

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration `configs/mission6/preregistered_protocol.toml`
(SHA-256 `3e8329adbd8ca84bf5e0ff42f8b6cea6e3a575be55e98d5acfe7c889acaf0f4f`), committed
before final evaluation. No experiment was tuned after inspecting final results; the 0.02
added-value margin was not lowered; **a below-chance baseline is never used as evidence**;
signs were never reversed after viewing holdout labels.

## Central questions and honest answers

**Q1 — Does ITD preserve transferable structural information between numerical methods
after fair (amplitude/scale) normalization, i.e. against a *competent* established
baseline?** **No.** The Mission 5 cross-code advantage (ITD ~0.85 vs a below-chance 0.03
established baseline) **does not survive**. Given the established baseline its best fair
shot (a normalization selected on development to maximize *its* transfer), the competent
baseline is not above chance on the holdout, the two transfer directions disagree sharply,
and in the one working direction ITD merely **ties** the raw established diagnostic. The
Mission 5 headline is reproduced as a single fragile corner of a 24-cell grid that
evaporates when the direction flips or the features are normalized. The advantage was, as
the preregistration anticipated, **normalization and small-sample noise, not structure**.

**Q2 — Can the product reduce confidence intelligently under domain shift without
unnecessarily rejecting useful data?** **Partially.** A three-state accept / reduce /
abstain policy with per-axis severity **eliminates** the Mission 5 over-abstention
(unnecessary abstention 0.00 vs ~0.58–0.85), and per-axis attribution localizes the shift
axis in a way a global radius cannot. But under the preregistered utility (false-confidence
cost 4×) and the transparent pre-committed calibration, the three-state policy **does not
beat** binary abstention on total utility — it trades over-abstention for residual false
confidence — and the ranking is **not robust** across resolution. The narrow goal is met;
the broader one is not.

## H37–H48 verdicts

| id | hypothesis | verdict | evidence class |
|---|---|---|---|
| H37 | ITD-only stays predictive across codes (larger, controlled) | **not supported** (above chance in one direction only) | cross-code |
| H38 | ITD beats a **competent** established baseline | **not supported** | cross-code |
| H39 | competent + ITD beats competent-only by the margin | **not supported** | cross-code |
| H40 | transfer useful in **both** directions | **not supported** (severe asymmetry) | cross-code |
| H41 | transfer useful across resolution changes | **inconclusive** (base transfer already fails) | cross-code |
| H42 | survives temporal-alignment policies | **inconclusive** (base transfer already fails) | cross-code |
| H43 | per-axis detector localizes axis/severity better than global | **partially supported** (attribution yes; severity no) | local-solver |
| H44 | three-state beats binary abstention on utility | **not supported** (and not robust) | local-solver |
| H45 | unnecessary abstention drops far below ~0.85, risk controlled | **supported** (0.00; with a false-confidence caveat) | local-solver |
| H46 | real cylinder subset integrated outside CI | **blocked** (attempted; no network) | external-DNS |
| H47 | Rust reproduces a defined V29.18 2D subset within tolerance | **supported within the periodic subset** | software-equivalence |
| H48 | full-volume latency improves, numerics preserved | **supported** (bitwise-equal, up to ~1.16×) | performance |

Sub-reports: `H29_COMPETENT_BASELINE_REPORT`, `H29_BIDIRECTIONAL_TRANSFER_REPORT`,
`CROSS_CODE_CHANNEL_STABILITY_REPORT`, `SHIFT_AWARE_OOD_REPORT`,
`CONFIDENCE_DEGRADATION_REPORT`, `RISK_COVERAGE_ABSTENTION_REPORT`,
`CYLINDER_RE3900_INTEGRATION_STATUS`, `FULL_VOLUME_OPTIMIZATION_REPORT`,
`RUST_V29_EQUIVALENCE_REPORT`.

## Twelve questions the mission asked — answered

1. **Does the Mission 5 cross-code signal survive a competent baseline?** No (H38).
2. **Was the Mission 5 baseline below chance, and did that inflate the result?** Yes —
   0.03; the +0.82 gap over it was never valid evidence, and Mission 6 does not use it.
3. **Is the transfer symmetric across code direction?** No — fd→spectral works, spectral→fd
   is below chance for every feature set (H40).
4. **Does any ITD channel subset transfer stably?** No — the normalization × direction grid
   is noise-dominated; no subset is robust (channel-stability report).
5. **Does adding ITD to a competent baseline add credible value?** No — CI does not exclude
   0 with an above-chance baseline; the one positive number is over a chance baseline and
   is not claimable (H39).
6. **Can a per-axis detector say *which* axis shifted?** Yes — plausible attributions
   (circulation→intensity, resolution→sign_mixing, viscosity→roughness) global cannot give
   (H43).
7. **Is per-axis severity a better ordinal severity measure than global Mahalanobis?** No —
   comparable, slightly worse on the viscosity sweep (H43 partially supported).
8. **Does three-state abstention cut the Mission 5 ~0.85 over-abstention?** Yes — to 0.00
   (H45).
9. **Does three-state beat binary on total utility?** No, under the preregistered costs and
   pre-committed calibration; and the ranking flips with resolution (H44).
10. **Was any threshold retuned to make three-state win?** No — the risk-coverage curve
    shows the utility-optimal point is at lower coverage, but retuning after the fact is
    prohibited and was not done.
11. **Is the external cylinder evidence in yet?** No — blocked-in-CI (no network); contract,
    schema, and provenance are in place with no fabricated checksums (H46).
12. **Did any optimization or Rust change alter authoritative numbers?** No — full-volume is
    bitwise-equal to the reference; Rust matches Python within 1e-9 on the periodic subset;
    the certified core is untouched.

## Guardrail compliance

- `itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, oracles, hashes, and
  reference summaries **unchanged**. One-way dependency preserved (research → core).
- **No** V29.19 / V30 / certified ITD-3D / universal ITD profile or threshold /
  production-certified ITD was created or proposed.
- Mission 3/4/5 negatives **preserved**: ITD adds no significant value over strong
  baselines; thresholds/component maps are not universal; cross-flow transfer is weak; the
  M5 cross-code result was promising **but confounded** — and Mission 6 now shows it does
  not survive a competent, bidirectional, normalization-robust test.
- No arbitrary ITD channels were added; the transfer/abstention questions were resolved
  (negatively) first.

## Net conclusion

Mission 6's decisive result is a **clean, preregistered negative**: the most promising
Mission 5 finding (cross-code structural transfer) does not survive a fair, bidirectional,
normalization-robust analysis. On the product side, shift-aware three-state abstention
**solves the specific over-abstention problem** but does not, under honest costs, beat
binary abstention overall. The engineering deliverables (Rust subset, bitwise-equivalent
full-volume optimization) are solid and equivalence-verified. Nothing was forced positive.

## Reproduction

Determinism: `PYTHONHASHSEED=0`, single-thread BLAS, float64, `numpy.default_rng(seed)`.
Bounded offline forms run in `run_validation.sh` (steps 23–25). Full campaigns:
`python -m itd_research.cross_code campaign`, `python -m itd_research.ood_shift run`,
`python -m itd_research.full_volume optimize`. Rust: `cargo test --workspace` in `itd-rs/`.
