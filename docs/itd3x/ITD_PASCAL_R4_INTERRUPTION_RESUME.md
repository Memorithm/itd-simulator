# ITD Pascal R4 — interruption/resume ledger integrity preregistration

Status: prospective Development/Validation-only secondary integrity slice. No R4 campaign has been executed under this protocol. No protected/final access is authorized.

R4 is designed independently from the TDI Pascal cost/utility programme. It does not import TDI conclusions, thresholds, effect directions, or promotion criteria. It also does not reinterpret completed R2/R3 evidence as a new replication.

## Frozen research question

Does an interrupted Pascal integrity campaign resume from its exact persisted prefix without changing campaign identity, source identity, case identity, artifact bytes, or final non-final outcome relative to a matched uninterrupted control?

R4 is a campaign-integrity study. It is not a latency, throughput, memory-efficiency, model-quality, or operation-cost experiment.

## Frozen non-final sources

- Development: deterministic packed-u16 Pascal/subset-zeta source, `n=7`, `K=128`.
- Validation: independently declared deterministic packed-u16 Pascal/subset-zeta source, `n=9`, `K=512`.
- Each split has its own exact source-byte SHA-256 identity.
- Source bytes are verified immediately before execution and again before resume.
- No final fixture bytes are generated or opened. A schema-required final identity, if needed by implementation, must remain a no-digest sentinel and must not be materialized.

## Frozen matched design

For each split, execute one uninterrupted control campaign and three interrupted/resumed campaigns with interruption after the following completed-prefix lengths:

- prefix 1;
- prefix 4;
- prefix 7.

Each campaign contains 8 deterministic cases over the same declared source bytes. The case set, order, identifiers, and work units are frozen before execution. The interrupted arms differ from the matched control only by the declared interruption boundary and subsequent resume operation.

The complete R4 matrix therefore contains 8 campaign runs: 2 uninterrupted matched controls and 6 interrupted/resumed arms. Resuming a run is not a new replication and must retain the original campaign and case identities.

## Primary exact integrity variables

For each interrupted/resumed arm compare against its matched uninterrupted control:

1. final plan fingerprint equality;
2. final protocol fingerprint equality;
3. exact ordered case-id equality;
4. exact per-case output SHA-256 equality;
5. exact persisted artifact-byte equality;
6. exact source-verification identity and digest equality;
7. completed ledger status after resume;
8. zero duplicated or skipped case executions.

All comparisons are exact. No tolerance is permitted.

## Interruption and resume semantics

The interruption is deliberate and must occur only after the frozen prefix has been durably persisted. The pre-resume ledger must have lifecycle status `interrupted`, cover exactly the planned prefix, and pass persisted-artifact verification.

Resume must use the existing ITD campaign-store resume path. It must continue from the next planned case, reverify the declared source bytes, preserve the plan fingerprint, and retain all previously persisted artifacts byte-for-byte.

A resumed campaign must never regenerate completed prefix cases and present them as new evidence.

## Fail-closed provenance probes

The following probes are preregistered as integrity checks, not as scientific replications:

- source bytes changed before resume;
- persisted artifact bytes changed before resume;
- plan fingerprint or persisted plan changed before resume.

Each probe must fail closed and retain an `inconclusive` or explicit integrity-error record according to the existing campaign-store contract. Probe failure must not be rewritten as a successful or negative scientific result.

## Negative and inconclusive preservation

A validly proven mismatch between an interrupted/resumed arm and its matched uninterrupted control is retained as negative integrity evidence.

A provenance failure, unverifiable source, corrupt artifact, inconsistent ledger prefix, plan mismatch, duplicate case, missing case, or non-replayable persisted state is retained as inconclusive/integrity failure. Nothing is deleted or silently rerun to manufacture a clean result.

## Persistent evidence

Each R4 campaign directory must retain:

- canonical protocol and plan identities;
- exact Development or Validation source verification;
- persistent ledger before interruption and after resume;
- every case artifact and SHA-256;
- interruption boundary;
- resume event identity;
- matched-control comparison record;
- terminal lifecycle status.

Canonical result bytes and their SHA-256 must be recorded for every completed matched comparison.

## Protected/final boundary

R4 contains Development and Validation only. It authorizes no confirmatory/final work, no protected population access, and no final authorization object. Protected/final bytes must not be generated, inspected, opened, or executed.

## Interpretation boundary

A clean R4 result would establish only interruption/resume ledger integrity for the frozen synthetic non-final Pascal campaigns. It would not establish Pascal model utility.

SML-GENIUS remains the owner of model-side Pascal primitives. R4 authorizes no promotion into SBG, MOR, Delta-KV, context memory, or model architecture. Any such handoff requires a separate prospective protocol owned by the destination project.
