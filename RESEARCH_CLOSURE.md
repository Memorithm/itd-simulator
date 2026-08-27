# Research closure — Missions 3–8 fluid-diagnostic line

Status: **scoped closure note**. This document closes the Missions 3–8 fluid-diagnostic research line. It is not a certified revision and does not modify `ITD V29.18` (`MODEL_REVISION` unchanged).

The original closure remains valid for the question actually tested. It must not be read as a claim that every possible ITD-derived representation, every artificial-intelligence use, every signal domain, or every future learned extension has been tested and rejected.

New AI and scientific-machine-learning questions are governed separately by [`docs/ai/AI_RESEARCH_CHARTER.md`](docs/ai/AI_RESEARCH_CHARTER.md). Reopening the *same* fluid-diagnostic claim still requires genuinely new evidence as described below.

Read this before reopening any research question in `itd_research/` or `docs/research/`.
Those directories contain ~90 documents that read like an *open* fluid-diagnostic programme. They are not. The question they were built to answer has been answered.

## The question that is closed

> Does the existing ITD formulation provide reproducible diagnostic or predictive information about fluid-dynamic structure that competent established diagnostics do not already capture?

## The answer: no — within the evaluated domains, on the evidence assembled

The verdict has been stable since Mission 6 and was confirmed on genuinely external data in
Missions 7 and 8.

**Mission 7** — first test on real external data (JHTDB DNS). The established baseline
already predicted the ITD-independent event perfectly (AUC 1.000), and adding ITD changed
the held-out AUC by **exactly +0.000**. ITD's only tracking channel, `intensity`, was
~redundant with enstrophy (ρ = +0.994).

**Mission 8** — the obvious objection to Mission 7 was that the task was *saturated*: no
method could improve on a perfect baseline. Mission 8 therefore required a preregistered
saturation screen and tested a genuinely **unsaturated** structural/topological task
(established development AUC **0.709**, well below the 0.98 exclusion gate). ITD still
failed, and worse than "no help":

| | established | ITD-only | established + ITD |
|---|---|---|---|
| external holdout | 0.519 | **0.246** (below chance) | **0.344** |

Added value **−0.168**, 95 % CI **[−0.175, −0.153]** — entirely negative. Adding the
existing non-magnitude ITD channels *degrades* a competent structural baseline.

**H65 follow-up** — the one remaining "inconclusive" was a data-collection artefact, not a
finding. Six preregistered windows (156 frames, 7 events) resolved it: the calibrated
profile transfers at **0.477 augmented AUC, below chance**. Not supported.

Across Missions 3–8: ITD predicts some *controlled internal* events; it did not beat
competent established baselines; universal thresholds were not supported; cross-flow
transfer was weak; cross-code evidence was promising but confounded; near-OOD abstention
over-abstained; external incremental value was zero, then negative.

## What this closure does not answer

The experiments above were designed around fluid-diagnostic and event-prediction questions. They do not establish answers to materially different research questions such as:

- whether ITD-derived quantities are useful auxiliary training targets;
- whether an ITD-derived representation changes sample efficiency, calibration, robustness, compression, or learned latent structure;
- whether local, patchwise, graph, spectral, or multiscale descendants carry information absent from the existing global per-snapshot scalars;
- whether ITD-derived temporal representations help forecasting, anomaly detection, change detection, or control;
- whether a learned representation can use ITD information differently from the transparent classical models used as primary controls in the historical programme;
- whether structural representations help resource-aware or adaptive AI decisions;
- whether related constructions are useful in other signal domains such as vibration.

Those are new hypotheses. They require new baselines, leakage controls, datasets, model classes, decision rules, and holdouts. A positive result in one of them would not retroactively overturn the Missions 3–8 negative result; a negative result would be equally valid evidence.

## What would — and would not — change the closed fluid-diagnostic conclusion

**Would not.** A cross-institution replication (see `docs/research/EXTERNAL_SOURCE_PROSPECTS.md`
and `docs/research/COMPRESSIBILITY_DECISION_NOTE.md`). Every external result rests on JHTDB, and The Well
(Flatiron Institute) is a credible independent source. But Mission 8's H65 already tested
hydrodynamic → MHD transfer: a Mission 9 would add an independent *institution*, not new
physics. It would make this negative **more robust, not different**. Worth doing for rigour;
not a path to a different answer.

**Would.** Only genuinely new evidence directed at the same fluid-diagnostic claim:

1. **Time-resolved, vortex-dominated experimental PIV/PTV** with open provenance — H72,
   blocked since Mission 3 across repeated searches (`STRONGLY_VORTICAL_PIV_M8_REPORT.md`).
   Simulation data cannot answer an experimental-validation question, however independent
   its institution.
2. **A spatial (per-cell) ITD channel** — H69 is blocked *architecturally*: every existing
   ITD-3D channel is a global per-snapshot scalar, so region-level localization cannot be
   tested at all. Inventing one to make the old hypothesis testable was forbidden by Mission 8's
   protocol, and rightly: a channel designed to pass a test is not evidence for the old claim.

**Do not reopen this same fluid-diagnostic line without (1) or (2).** Re-running the existing pipeline on more simulation data will reproduce the existing negative at real cost. This restriction does not prohibit separately preregistered AI research whose target question is different.

## What retains value, independent of the closed ITD claim

The scientific conclusion is negative; the **infrastructure is not**. What was built here is
a reusable validation and comparison laboratory, applicable to other diagnostics and to new AI research questions when domain assumptions are reviewed:

- manufactured 3D oracles with known ground truth (`itd_research/mission8/fixtures.py`),
  which caught five real bugs during Mission 8 alone;
- deterministic 3D region/topology machinery (connected components with periodic
  wraparound, IoU/Dice/centroid metrics, persistence-gated topology events);
- a **preregistered saturation screen** — the safeguard that turned Mission 7's
  uninformative "perfect baseline" into Mission 8's decisive test;
- grouped statistics that never treat adjacent frames as independent units;
- shift-aware OOD with three-state abstention;
- verified external ingestion with checksums, provenance manifests and reproduction bundles
  (`repro/mission7/`, `repro/mission8/`, `repro/mission8h65/`).

Mission 8's own conclusion recommended preserving exactly this, and repositioning ITD as an
**experimental diagnostics framework** rather than a validated observable. The AI research charter extends that methodological role without changing the old evidence.

## Honest record of what went wrong along the way

Kept deliberately, because a clean-looking record invites less scrutiny than it deserves:

- a topology-event detector fired spurious events on transient blips — fixed, with a
  regression test, and all affected numbers recomputed before any report was written;
- a determinism claim ("two runs produce identical output") was too strong — wall-clock
  benchmark fields legitimately vary;
- a replacement test then demanded **bit-exact digests across machines**, which floating-point
  arithmetic cannot honour; CI rejected it, and the contract was corrected;
- an acquisition protocol preregistered 48 frames per window without checking the dataset's
  time range, which caps at 26.

Each is documented where it occurred rather than quietly removed.

## Status of the certified core

`ITD V29.18` (`itd_v29_core/`, `itd_v29.py`, `itd_simulator/`) is **untouched** by the entire
research line and remains frozen. The one-way dependency was enforced throughout and is
tested (`tests/test_research_boundaries.py`): the core never imports `itd_research`.

No certified revision was ever justified by this research. `MODEL_REVISION` remains
`ITD V29.18`. Future AI research must preserve the same principle: an experiment may consume the frozen core, but the core must not depend on the experiment layer.

## Reproducing the closing result

```bash
# offline, deterministic, ~10-30 s (also run as run_validation.sh step 27)
python -m itd_research.mission8 validate --config configs/mission8/ci.toml --output /tmp/m8
```

Note the offline fixture's verdicts are **the opposite** of the real-data finding — it is a
manufactured, trivially-predictable oracle for code verification only, tagged
`"synthetic-code-verification (NOT external evidence)"`. The real-data path requires the
manual JHTDB fetch documented in `repro/mission8/README.md`.

Full argument: `docs/research/MISSION8_FINAL_REPORT.md`.
