# External physical-validation report (H50)

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Evidence class:
**external-DNS**. Does not modify `ITD V29.18`.

Cylinder Re≈3900 physical validation is **blocked** (no data; see the ingestion report).
Physical validation was performed on the **JHTDB isotropic-DNS** data actually obtained.

## JHTDB isotropic1024coarse — physical consistency

| quantity | measured | expectation | verdict |
|---|---|---|---|
| relative divergence `⟨|∇·u|⟩/(urms/dx)` | **0.006–0.010** | ≈0 for incompressible DNS | **pass** (decisive ingestion-correctness check) |
| per-component `urms` | 0.34–0.71 | documented global ≈0.68/component | in band [0.3, 1.2] → pass |
| component isotropy spread | 0.57 | ≈0 globally | fails locally (expected) |
| energy coefficient of variation | 0.58 | ≈0 if stationary | fails locally (expected) |

## Honest reading — H50 **supported within tested scope**

The **near-zero relative divergence** is the strongest evidence that the field was ingested
correctly: coordinate order, units and axis convention all agree, or the discrete
divergence would not vanish. `urms` sits in the documented band. The **isotropy** and
**stationarity** checks "fail" only because a 16³ sub-box of a 1024³ domain is far too small
to be *statistically* isotropic or stationary — this is a property of the tiny cutout, not
an ingestion error, and is reported honestly rather than suppressed or forced to pass. The
verdict rests on the divergence and `urms` checks, which pass.

**Per the preregistration, predictive claims (H52/H53) were only made after this validation
passed.**
