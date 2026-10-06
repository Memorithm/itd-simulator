# ITD Pascal R5 — cold-process relocation/replay integrity preregistration

Status: prospective Development/Validation-only secondary integrity slice.

R5 is independent of the TDI Pascal cost/utility programme. It does not import
TDI effect directions, thresholds, or promotion criteria. It does not authorize
confirmatory/final evaluation and does not modify model architecture.

## Question

Can a persisted Pascal campaign be stopped, moved to a different filesystem
root, reopened by a fresh process, and replayed/resumed without changing any
scientific identity, source-byte identity, case result, artifact digest, or
canonical ledger content?

R5 tests persistence portability and replay integrity. It is not a speed,
memory, model-quality, or operation-cost experiment.

## Frozen non-final design

Development uses a synthetic source with n=6 and K=64.

Validation uses an independently generated synthetic source with n=11 and
K=2048.

Each split contains six deterministic case identities fixed by the case-plan
generator before execution. The case count, ordering, parameters, and source
bytes are frozen before Development begins.

For each split, execute one uninterrupted reference campaign and two relocation
arms:

- relocation A after the first two completed cases;
- relocation B after the first five completed cases.

The relocation destination names are fixed by the implementation preflight and
must differ from the original campaign root. Relocation changes only the storage
root. It must not regenerate protocol, plan, source, case, artifact, or ledger
identity.

Each resumed arm must be opened by a fresh process. A replay of already
completed cases is an integrity operation and must not be counted as a new
scientific replication.

## Required identities

Before execution, persist and bind SHA-256 identities for:

- this protocol;
- the complete Development and Validation plans;
- the exact Development and Validation source bytes;
- the implementation source set;
- every completed case artifact;
- every canonical ledger snapshot used as a relocation boundary.

The persistent ledger is authoritative. No absolute storage-root path may
participate in a scientific fingerprint or case identity.

## Matched comparisons

For each relocation arm compare with its split-matched uninterrupted reference:

1. protocol fingerprint;
2. plan fingerprint;
3. verified source SHA-256;
4. ordered case identities;
5. per-case output SHA-256 values;
6. persisted artifact bytes;
7. final canonical ledger bytes;
8. completed-case count;
9. duplicate-case count;
10. skipped-case count.

All equality checks are exact. No tolerance is allowed.

A clean relocation requires every identity and byte comparison to match, with
zero duplicate and zero skipped cases.

## Fail-closed integrity probes

Development additionally executes three preregistered integrity probes from a
persisted relocation boundary:

- remove one required persisted artifact;
- add one undeclared artifact that conflicts with the persisted case namespace;
- replace the persisted source bytes while retaining the old declared source
  digest.

Each probe must fail closed before any additional case execution. The failure
record and the pre-probe ledger/artifacts are retained. Such outcomes are
integrity errors/inconclusive evidence, not successful replications and not
scientific negative results.

## Replay and persistence rules

A replay consumes the persisted case and ledger identities. It must not silently
regenerate completed evidence. Reopening the same completed campaign never
increments the claimed replication count.

All Development/Validation outputs, including clean, negative, failed, and
inconclusive outcomes, remain in the evidence dossier.

## Execution order

1. commit this protocol and its manifest identity;
2. implement and qualify source/plan/ledger relocation handling without running
   scientific cases;
3. freeze exact case plans and source-byte hashes;
4. run Development reference and relocation arms;
5. retain Development evidence;
6. only with unchanged protocol/implementation and intact Development integrity,
   run the independently declared Validation arms;
7. freeze a complete evidence manifest.

## Protected/final boundary

R5 defines Development and Validation only. It creates no protected/final
fixture, case plan, authorization object, or source digest. Protected/final data
must not be opened, generated, inspected, or executed under R5.

## Interpretation boundary

A clean R5 result would establish only cold-process relocation/replay integrity
for the frozen synthetic campaigns. It does not establish Pascal model utility
or performance and is not a rerun of R2, R3, or R4.

SML-GENIUS remains the owner of model-side Pascal primitives. R5 authorizes no
promotion into SBG, MOR, Delta-KV, context memory, or model architecture.