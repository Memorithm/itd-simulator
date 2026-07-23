# Mission 7 — external evidence acquisition and independent replication (preregistered spec)

Status: **preregistration**. Written *before* final external evaluation. Not a certified
revision; does not modify `ITD V29.18`. Machine-readable protocol
`configs/mission7/preregistered_protocol.toml`
(SHA-256 `35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`). Once final
evaluation begins, `[final_holdout]` and the locked decisions are **immutable**.

## The strategic pivot

Mission 6 delivered a decisive preregistered negative: ITD's apparent Mission 5 cross-code
advantage did not survive competent baselines, bidirectional transfer or fair
normalization. The limiting factor is **no longer missing code — it is missing
independent evidence**. Mission 7 therefore stops manufacturing local Taylor-Green / merger
/ synthetic experiments and instead asks:

> **Does ITD provide reproducible structural, diagnostic or predictive information on
> genuinely external fluid-dynamics data generated independently of this repository?**

A negative, partial or **blocked** answer is acceptable and is preserved verbatim. No
experiment is tuned after inspecting final results; success margins are not lowered; a
below-chance baseline is never used as evidence; the event definition is never chosen to
flatter ITD.

## The key environment change

Mission 6 was **network-blocked** in CI and could not download the cylinder dataset. This
Mission 7 *development session* has outbound HTTPS through the agent proxy, so **genuine
external ingestion is achievable here**. Normal CI remains offline and never touches the
network. Two real external sources were reached and verified in this session:

| source | institution | class | what it is |
|---|---|---|---|
| **JHTDB isotropic1024coarse** | Johns Hopkins (JHTDB) | external-DNS | forced isotropic turbulence, 3D velocity, time-resolvable via the public GetVelocity service |
| **biofilm PIV** (Zenodo 1175014) | USNA / U. Virginia | experimental-PIV | 2D **time-averaged** boundary-layer mean + Reynolds stresses (CC-BY-4.0) |

These are genuinely independent institutions and two distinct evidence classes. The
biofilm PIV is **shear-dominated and time-averaged**: it is a physical-validation,
cross-source and OOD **control**, and is **never** presented as coherent-vortex-event
validation (Mission 7 §14).

## Honestly blocked targets

- **cylinder Re≈3900** — the authoritative time-resolved DNS source is a GB-scale record
  behind a publication; no manageable, redistribution-clear file was fetchable this
  session. The Mission 6 workflow/contract remains in place; status **blocked**.
- **time-resolved coherent-vortex PIV** — classic small cylinder-wake snapshot mirrors
  (dmdbook / PyDMD / databook) returned 403/404; no small redistributable coherent-vortex
  PIV was secured. Status **blocked**. Consequently **H57 is expected blocked** and is not
  claimed from the shear control.

## Evidence ladder (report the achieved level)

`E0 metadata → E1 raw verified → E2 parsed → E3 coords/units → E4 snapshot → E5 short
sequence → E6 physical statistics → E7 diagnostics → E8 event labelled → E9 predictive
development → E10 locked external holdout`. Every report states the level reached.

## Method (locked; see the TOML for the machine form)

Ingestion is checksum-verified with configurable security/resource limits (path traversal,
archive bombs, size/frame/dimension caps, NaN/inf, endianness, axis, timestamp order).
**Physical validation precedes any predictive claim**: JHTDB isotropy / solenoidality /
`urms` range / energy stationarity; biofilm near-wall monotonicity. Events are defined
from **established diagnostics only** (extreme-enstrophy burst), never from ITD. Prediction
uses locked temporal partitions (adjacent frames never split), competent baselines
(persistence, simple scalar, established, ITD, established+ITD), a preregistered 0.02
added-value margin with CI excluding 0, and reports lead time / false alarms / misses.
OOD/abstention is tested under real source, resolution and measurement shifts with binary
and three-state policies reported separately; utility weights are not tuned on the holdout.

## Hypotheses H49–H60 and gates

| id | question | gate |
|---|---|---|
| H49 | verified external ingestion with provenance | AD |
| H50 | external physical consistency within tolerance | AE |
| H51 | ITD physically interpretable on external data | AD |
| H52 | ITD predicts an independent external event with lead time | AG |
| H53 | established+ITD beats competent established on an external holdout | AH |
| H54 | an ITD channel carries reproducible complementary information | AD |
| H55 | calibration transfers to a second independent source | AI |
| H56 | OOD/abstention sensible under real shifts | AK |
| H57 | ITD agrees with documented coherent vortices in PIV/PTV | AJ |
| H58 | full-volume pipeline handles real external 3D within envelopes | AD |
| H59 | independent user reproduces one external result | AL |
| H60 | result reproduced on a second environment/person | AL |

Verdicts: `supported within tested scope | partially supported | not supported |
inconclusive | blocked`. **No gate authorizes a certified revision.**

## Guardrails

`itd_v29_core/`, `itd_v29.py`, `MODEL_REVISION`, `itd_simulator/`, oracles, hashes,
reference summaries unchanged; one-way dependency (research → core); no new revision; no
V29.19/V30/certified ITD-3D/universal threshold/production ITD. Mission 3–6 negatives
preserved, including Mission 6's competent-baseline negative.

## Reports produced

`MISSION7_FINAL_REPORT`, `CYLINDER_RE3900_SOURCE_AND_LICENSE_REPORT`,
`CYLINDER_RE3900_INGESTION_REPORT`, `CYLINDER_RE3900_PHYSICAL_VALIDATION_REPORT`,
`CYLINDER_RE3900_EVENT_LABEL_REPORT`, `EXTERNAL_ITD_DIAGNOSTIC_REPORT`,
`EXTERNAL_INCREMENTAL_VALUE_M7_REPORT`, `SECOND_EXTERNAL_SOURCE_REPORT`,
`EXTERNAL_PIV_PTV_REPORT`, `EXTERNAL_OOD_ABSTENTION_REPORT`,
`MISSION7_REPRODUCIBILITY_REPORT`, `INDEPENDENT_REPLICATION_REPORT`. Each states its
evidence class, the achieved evidence level, data source, limitations, negatives and
blocked items. Where the cylinder-specific report has no cylinder data, it records the
blocked status and the JHTDB/biofilm evidence obtained instead.
