# Industrial-readiness model (IRL-0..9)

Status: **research/process document**. Not a certification, not a certified revision;
does not modify `ITD V29.18`. It defines the maturity scale the reports use and is the
reference for `docs/research/INDUSTRIAL_READINESS_GAP_REPORT.md`.

## Purpose

To describe ITD software maturity **honestly** on an explicit scale, and to separate
"scientifically validated" from "compliant with a standard." These are different
things: a diagnostic can be scientifically sound and still be nowhere near
qualification for a regulated deployment. This model never asserts compliance; it
reports a level and the gaps above it.

## The scale

| IRL | meaning |
|---:|---|
| 0 | idea / equations only |
| 1 | reference implementation, ad hoc checks |
| 2 | deterministic implementation with an automated test suite |
| 3 | oracle-anchored numerics + offline reproducible CI |
| 4 | falsifiable validation against independent diagnostics, honest scope |
| 5 | external empirical validation (DNS/PIV) at matched conditions |
| 6 | documented interfaces + performance envelope + versioned data contracts |
| 7 | quality-managed process (reviews, change control, requirements trace) |
| 8 | sector standard gap-closed, independent V&V, safety case |
| 9 | formally certified for a regulated deployment |

The achieved level is the **highest rung whose criteria are all met**; a single
unmet lower criterion caps the level regardless of higher-rung work. The rubric is
evaluated in code (`itd_research.industrial.readiness`) against observable repository
facts, so the level is reproducible, not asserted.

## What each level does and does not mean

* **IRL ≤ 4** is a *scientific* maturity band: the method is implemented
  deterministically, checked against analytical oracles, and validated as falsifiable
  hypotheses against independent diagnostics — with negative results reported.
* **IRL 5–6** is an *engineering* band: matched-condition external validation,
  documented interfaces, and versioned data contracts.
* **IRL 7–9** is a *qualification* band: it is a **process and compliance** effort
  (quality management, independent V&V, a safety case, accredited certification), not
  a numerical-accuracy effort. No amount of validation moves a project into this band;
  only a qualified process does.

## Named standards (never claimed as satisfied)

ISO 9001, ISO/IEC 17025, IEC 61508, ISO 26262, DO-178C, IEC 62304. Each is addressed
only as a **gap analysis** in the gap report. Scientific validation contributes
evidence toward, but does not constitute, any of these.

## Use

Run `python -m itd_research.industrial assess --output <dir>` to regenerate the
machine-readable assessment. The narrative interpretation lives in the gap report.
