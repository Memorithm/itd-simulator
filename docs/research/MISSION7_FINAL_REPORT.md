# Mission 7 final report — external evidence acquisition and independent replication

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Preregistration `configs/mission7/preregistered_protocol.toml`
(SHA-256 `35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`), committed
before final external evaluation. No experiment was tuned after inspecting final results;
success margins were not lowered; a below-chance baseline is never used as evidence; the
event was never chosen to flatter ITD; the mean-PIV control is never presented as
coherent-vortex validation.

## The central question and honest answer

*Does ITD provide reproducible structural, diagnostic or predictive information on
genuinely external fluid-dynamics data generated independently of this repository?*

**For the first time, ITD was tested on genuine external data — and it adds no
incremental value over a competent established baseline.** On a Johns Hopkins Turbulence
Database (JHTDB) isotropic-DNS sequence, the established diagnostics alone already predict
the (ITD-independent) enstrophy event perfectly (AUC 1.000) and **adding ITD changes the
held-out AUC by exactly 0.000** (H53 **not supported**). ITD's only channel that tracks
the event, `intensity`, is ~redundant with enstrophy (rank correlation +0.994). This
confirms the Mission 4–6 conclusion — no ITD superiority, no credible incremental value —
now on **real external DNS** rather than local simulation. The infrastructure hypotheses
(ingestion, physics, full-volume, reproducibility, independent replication) **succeeded**;
the coherent-vortex and cross-source hypotheses remain **blocked** for lack of a suitable
fetchable dataset.

## What changed vs Mission 6: real external data

Mission 6 was network-blocked and could integrate no external data. This Mission 7
development session had outbound HTTPS, and **two genuinely independent external sources
were downloaded and checksum-verified**:

| source | institution | class | evidence level reached |
|---|---|---|---|
| **JHTDB isotropic1024coarse** | Johns Hopkins | external-DNS | **E9** (predictive development on a locked temporal holdout) |
| **biofilm PIV** (Zenodo 1175014) | USNA / U. Virginia | experimental-PIV | **E6** (physical statistics), used as a shear control only |

Normal CI stays offline; the network steps are manual (`repro/mission7/commands.sh`).

## H49–H60 verdicts

| id | hypothesis | verdict | key evidence |
|---|---|---|---|
| H49 | verified external ingestion + provenance | **supported** | JHTDB 16- & 48-frame sequences + biofilm PIV downloaded, SHA-256 verified, provenance manifests |
| H50 | external physical consistency | **supported** | JHTDB relative divergence 0.006–0.010 (solenoidal → correct coord/unit/axis ingestion); `urms` in range |
| H51 | ITD interpretable on external data | **supported** | ITD `intensity` ∝ enstrophy (ρ=+0.994); channels finite and physically sensible |
| H52 | ITD predicts an external event with lead time | **not supported** | ITD tracks the event only via the enstrophy-redundant `intensity`; non-redundant channels don't |
| H53 | established+ITD beats competent established | **not supported** | added value **+0.000** on the locked external holdout (established already AUC 1.000) |
| H54 | ITD carries reproducible complementary info | **partially supported** | some ITD channels are rank-distinct from enstrophy (|ρ|<0.3), but which ones varies by sequence; descriptive only |
| H55 | calibration transfers to a second source | **blocked** | the two secured sources differ in dimensionality (3D DNS vs 2D PIV); no comparable second source |
| H56 | OOD sensible under real shifts | **partially supported** | detector flags local→external DNS shift (0.9 → 1.0e5, 1.2e5×); magnitude so extreme it recalls the M4 uninformative-distance problem |
| H57 | ITD agrees with documented coherent vortices | **blocked** | no time-resolved coherent-vortex PIV secured; the biofilm control is shear-dominated, not vortex |
| H58 | full-volume handles real external 3D | **supported** | real 32³ JHTDB volume processed in ~170 ms, optimized path **bitwise-equal** to reference |
| H59 | independent user reproduces one result | **supported** | reproduction bundle + deterministic offline fixture campaign (checksum pinned) |
| H60 | reproduced on a second environment | **supported within tested scope** | re-run on Python 3.13.12 + numpy 2.5.1: identical verdicts, max relative difference **1.6e-16** |

Sub-reports: `CYLINDER_RE3900_SOURCE_AND_LICENSE_REPORT`, `CYLINDER_RE3900_INGESTION_REPORT`,
`CYLINDER_RE3900_PHYSICAL_VALIDATION_REPORT`, `CYLINDER_RE3900_EVENT_LABEL_REPORT`,
`EXTERNAL_ITD_DIAGNOSTIC_REPORT`, `EXTERNAL_INCREMENTAL_VALUE_M7_REPORT`,
`SECOND_EXTERNAL_SOURCE_REPORT`, `EXTERNAL_PIV_PTV_REPORT`, `EXTERNAL_OOD_ABSTENTION_REPORT`,
`MISSION7_REPRODUCIBILITY_REPORT`, `INDEPENDENT_REPLICATION_REPORT`.

## The twelve final questions — answered explicitly

1. **Was a genuine external dataset integrated?** Yes — JHTDB DNS (primary) and biofilm PIV
   (control), both downloaded and checksum-verified this session.
2. **Were its fields physically validated?** Yes — JHTDB is solenoidal to ~0.6–1.0% relative
   divergence, confirming correct coordinate/unit/axis ingestion; `urms` in range.
3. **Was an event labelled independently of ITD?** Yes — an extreme-enstrophy burst defined
   from established vorticity only, with a development-set threshold.
4. **Does ITD predict the external event?** Only via the enstrophy-redundant `intensity`
   channel; the established baseline already predicts it (AUC 1.000). H52 not supported.
5. **Does ITD add value beyond competent established diagnostics?** No — added value +0.000
   on the locked external holdout (H53 not supported).
6. **Does ITD carry reproducible complementary information?** Partially — a few channels are
   statistically distinct from enstrophy, but not consistently and with no predictive payoff.
7. **Does the result transfer to a second source?** Blocked — the two real sources differ in
   dimensionality; no comparable independent second source was secured.
8. **Does strongly vortical PIV/PTV support ITD?** Blocked — no coherent-vortex time-resolved
   PIV obtained; the biofilm control is shear-dominated and is not used as vortex evidence.
9. **Does external OOD abstention reduce risk?** Partially — it flags the local→external shift,
   but the extreme distance magnitude echoes the Mission 4 uninformative-distance problem.
10. **Can another environment reproduce the result?** Yes — Python 3.13 + numpy 2.5 reproduced
    identical verdicts to 1.6e-16.
11. **Has industrial maturity advanced beyond IRL-4?** No — real external evidence now exists,
    but it is a **negative** for incremental value; maturity is not advanced by a null result.
12. **Is a new certified revision justified?** No.

## Guardrail compliance

`itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, oracles, hashes,
reference summaries **unchanged** (the diff touches only research/docs/tests/tools/configs/
repro). One-way dependency preserved. **No** V29.19/V30/certified ITD-3D/universal
threshold/production ITD proposed. Mission 3–6 negatives preserved, including Mission 6's
competent-baseline negative — now **extended to genuine external DNS**.

## Net conclusion

Mission 7 delivered what Mission 6 could not: **real external evidence**. The verdict is a
clean, preregistered **negative** for the scientific question — ITD provides no reproducible
incremental diagnostic or predictive value over competent established diagnostics on genuine
external DNS — accompanied by solid, reproducible, independently-replicated **infrastructure**
(verified ingestion, physical validation, full-volume feasibility, a reproduction bundle).
Nothing was forced positive. No certified revision is justified.

## Reproduction

`repro/mission7/` (offline fixture is deterministic; network steps regenerate JHTDB/biofilm
from source). Determinism: `PYTHONHASHSEED=0`, single-thread BLAS, float64,
`numpy.default_rng(seed)`. Bounded offline form runs in `run_validation.sh` step 26.
