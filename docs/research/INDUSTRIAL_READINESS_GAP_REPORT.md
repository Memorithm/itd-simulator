# Industrial-readiness gap report (H16)

Status: **research/process report**. Not a certification and not a certified revision;
does not modify `ITD V29.18`. Reproduce with `python -m itd_research.industrial assess
--output <dir>` (runs in CI, step 15/15 of `run_validation.sh`). Scale defined in
`docs/industrial/INDUSTRIAL_READINESS_MODEL.md`.

## Question (H16, falsifiable)

Is the ITD software **industrially certifiable today**?

## Assessment: **IRL-4** (falsifiable validation against independent diagnostics)

The rubric is evaluated against observable repository facts:

| IRL | requirement | status | evidence |
|---:|---|---|---|
| 2 | deterministic implementation + test suite | met | deterministic core, pytest, Rust oracle fixtures |
| 3 | oracle-anchored numerics + offline CI | met | Gate-A oracles, fixed seeds/threads, offline `run_validation.sh` |
| 4 | falsifiable validation vs independent diagnostics | met | H1–H16 as falsifiable questions with negative/partial verdicts |
| 5 | external empirical validation at matched conditions | **partial** | DNS/PIV on queried/synthetic data; no governed matched-condition raw dataset |
| 6 | documented interfaces + performance envelope + data contracts | **partial** | real-time envelope (H15) + Rust interface spec; data contract partial |
| 7 | quality-managed process (reviews, change control, trace) | **unmet** | no requirements-traceability matrix, CM plan, or controlled review records |
| 8 | sector-standard gap-closed, independent V&V, safety case | **unmet** | no independent V&V, no safety case |
| 9 | formally certified | **unmet** | no accredited certification |

## H16 classification: **not supported (as a certification claim)**

ITD software is **not industrially certifiable today**. It is a scientifically
validated research tool at **IRL-4**, with partial progress into IRL-5/6. The claim
"industrially certifiable" fails; the honest, scoped statement is: *"IRL-4, on a
defined path toward IRL-5/6, with IRL-7+ (qualification) being a process effort not
yet begun."*

## Named-standard gap analysis (all: not satisfied)

| standard | scope | key missing artefacts |
|---|---|---|
| ISO 9001 | quality management | documented QMS, controlled records, management review, internal audit |
| ISO/IEC 17025 | test/calibration competence | uncertainty budget, method-validation records, accreditation |
| IEC 61508 | functional safety (E/E/PE) | hazard & risk analysis, SIL allocation, safety lifecycle, independent assessment |
| ISO 26262 | road-vehicle safety | item definition, ASIL decomposition, safety case, tool qualification |
| DO-178C | airborne software | DAL assignment, full traceability, MC/DC coverage, DER review |
| IEC 62304 | medical device software | safety classification, risk-management file, SOUP analysis |

## Path forward (what would raise the level)

* **→ IRL-5:** a governed external DNS/PIV dataset with checksums and a fetch script,
  quantitative matched-condition comparison in the authoritative path (see the dataset
  inventory and PIV expansion report).
* **→ IRL-6:** freeze the ITD channel/data interface (the Rust interface spec is the
  start), publish the performance envelope as a versioned contract.
* **→ IRL-7+:** a quality-managed process — requirements traceability, change control,
  independent review records — then, only for a *specific* deployment, the relevant
  sector standard's full lifecycle and an independent safety/verification case.

## Limitations

The rubric is a self-assessment, deliberately conservative (any unmet lower criterion
caps the level). It reflects this repository, not a product organization; a real
qualification effort is scoped to a specific deployment and regulator and is out of
scope for a research prototype. No statement here should be read as compliance.
