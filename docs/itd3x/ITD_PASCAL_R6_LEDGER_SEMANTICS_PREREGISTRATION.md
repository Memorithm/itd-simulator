# ITD Pascal R6 — prospective scientific-ledger vs lifecycle-ledger integrity

Status: preregistration only. Secondary Development/Validation-safe integrity study,
independent of TDI, and a **new** R6 campaign. No R6 execution is authorized
until this document, case-plan bytes, implementation bytes, and fingerprints
are frozen and qualified. No protected/final evaluation is authorized.

## Motivation without retrospective repair

R5 retained a negative result for **full byte-exact ledger equality** at
Development prefix 2, caused by distinct terminal `reason` strings between
a continuous and a resumed campaign. R6 tests a prospectively separate
question: whether the canonical scientific portion of a persisted campaign
ledger survives a cold relocation/restart exactly while lifecycle annotations
remain independently observable. R5 is not reclassified as a pass.

## Frozen non-final design

- Development source geometry: `n=7`, `K=128`; six cases.
- Validation source geometry: `n=9`, `K=512`; six cases.
- Packed representation: 12 gates in a `u16`, 16 distinct ANF terms per gate.
- Within each split, case IDs are in strictly ascending canonical order:
  `{dev,val}-n{7,9}-r6-ledger-case-{00..05}`.
- Cases 0..5 are exact and deterministic; plan/source generators and the
  byte-level schema must be committed and hashed **before** execution.
- Matched arms: uninterrupted control, cold relocation/restart after completed
  prefix 2, cold relocation/restart after completed prefix 4.
- Execution order: complete the control first, then prefix-2 arm, then
  prefix-4 arm for **Development only**; Validation uses the identical method
  only after Development gates hold and its evidence is frozen.
- One frozen plan per split; no adaptive case additions, exclusions, or
  parameter changes following observation.

The two relocation arms must use fresh processes and move the identical
persistent plan, source, ledger, and artifact tree bytes between isolated
paths. A replay consumes persisted identities and artifacts; it does not
silently regenerate completed evidence. A restart is not a new replication.

## Canonical endpoints (defined before observations)

**Primary endpoint — scientific-ledger equality.** Parse each ledger as
strict JSON with duplicate-key rejection; validate the complete original
structure and declared `ledger_version`. Construct a canonical projection
by removing **only** the top-level field `reason` from a deep copy and
serializing with UTF-8, lexicographically sorted keys, no insignificant
whitespace, and exact JSON scalar semantics. No other field may be changed,
rounded, sorted as a list, omitted or defaulted. Compare the resulting
canonical bytes and their SHA-256 values across matched arms.

**Secondary endpoint — full raw ledger bytes.** Retain and SHA-256-hash the
unmodified full ledger bytes from every arm. Report full raw equality as
true/false with both digests, including any difference in `reason`. Failure
of raw equality is **not** silently converted to full equality. The exact
`reason` values and all other lifecycle/provenance metadata remain
persisted and visible in the dossier.

**Other mandatory exact endpoints.** Compare source SHA-256 before every
execution/restart; protocol/plan fingerprints; six ordered case IDs;
byte-identical per-case artifact digests; count of completed cases; zero
duplicates/skips; and full pre/post relocation tree fingerprints.

## Outcome semantics

- PASS only if all 12 Development/Validation scientific-ledger paired
  comparisons (six per split, two relocation arms per split) are byte-exact,
  all source/plan/protocol identities verify, all case outputs match, and
  every declared case executes exactly once.
- NEGATIVE when a scientific-ledger mismatch or artifact mismatch occurs
  with valid preconditions and provenance. Retain offending raw and projected
  bytes, fingerprints and case IDs.
- INCONCLUSIVE / FAIL-CLOSED when source verification, protocol fingerprint,
  plan identity, ledger schema, artifact integrity, relocation tree
  verification, fresh-process assertion, or replay identity fails. Never
  classify provenance drift as scientific success or negative evidence.
- Always report secondary raw-ledger differences as observed, regardless
  of PASS/NEGATIVE/INCONCLUSIVE on the primary endpoint.

No case or failure may be excluded as an outlier. R5 negative evidence and
full original raw ledgers must remain immutable and separate.

## Persistence and handoff

Use the existing ITD-30 campaign/ledger/store/source-verification
infrastructure. Before Development, commit and hash the R6 protocol, complete
Development and Validation case-plan bytes, source generator, exact
serialization implementation and tests. Preflight must verify source-byte
tampering is rejected; duplicate JSON keys are rejected; case order and
fingerprints cannot drift; only `reason` is excluded by the canonical
projection; all other field mutations remain detectable.

Retain every control/restart raw ledger and canonical projection, SHA-256,
source bytes, complete artifact hashes, and terminal status. Do not rerun R3,
R4 or R5 as fresh replication. No TDI-derived cost, performance or utility
conclusions enter R6's design.

## Strict boundary

No protected/final population may be opened, generated or executed; no
confirmatory or final work is authorized. SML-GENIUS owns model-side Pascal
primitives. R6 authorizes no propagation into SBG, MOR, Delta-KV, context,
KV cache or model architecture without a distinct prospective protocol.
