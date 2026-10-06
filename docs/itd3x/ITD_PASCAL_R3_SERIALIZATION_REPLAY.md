# ITD Pascal R3 — serialization/replay integrity preregistration

Status: Development/Validation-only secondary replication/integrity slice.

This protocol is independent of the TDI Pascal cost/utility programme. It does
not import TDI conclusions, thresholds, or decision criteria into its design. It
does not authorize confirmatory/final evaluation and does not modify ITD V29.18
or any model architecture.

## Question

Can a deterministic packed-`u16` Pascal/subset-zeta table be serialized,
chunked, persisted, reconstructed, and replayed byte-exactly across independently
declared transport layouts without changing its canonical scientific payload?

R3 is an integrity/replay experiment, not a speed, memory, model-quality, or
operation-cost experiment.

## Frozen non-final design

- Development split: `n=8`, `K=256`.
- Validation split: `n=10`, `K=1024`.
- Element representation: unsigned 16-bit words.
- Byte orders: little-endian and big-endian.
- Chunk widths: `1`, `3`, `7`, and `31` serialized elements.
- Replay counts: one replay and two replays.
- Cross-product per split: 2 byte orders x 4 chunk widths x 2 replay counts.
- Total: 16 Development cases + 16 Validation cases = 32 preregistered cases.

No adaptive search is permitted. Case ordering may be deterministic but must not
change the frozen case set. No case may be added, removed, or reclassified after
observing results.

## Canonical payload and matched controls

For each case, the canonical in-memory `u16` table is the source payload. The
matched control is direct canonical re-materialization from the same declared
Development or Validation source bytes without serialization/chunk transport.

The experimental path serializes the identical canonical payload using the
declared byte order and chunk width, persists the serialized bytes, reconstructs
the table, then performs the declared replay count.

Primary integrity variables:

1. exact reconstructed-word mismatch count;
2. exact canonical-payload SHA-256 equality;
3. exact serialized-source SHA-256 equality before replay;
4. exact replay-artifact SHA-256 equality across repeated replay of the same case;
5. exact ledger/campaign fingerprint agreement.

All variables are exact. No tolerance or approximate equality is allowed.

## Fingerprints, source bytes, and ledger

Before execution, the protocol and complete case plan must be serialized
canonically and assigned SHA-256 fingerprints. Development and Validation source
bytes must each have their own SHA-256 identity and must be verified immediately
before case execution.

Every case must persist:

- protocol fingerprint;
- plan fingerprint;
- split/source identity and verified SHA-256;
- case identity and frozen parameters;
- canonical payload digest;
- serialized-byte digest;
- reconstructed payload digest;
- replay artifact digest(s);
- terminal state;
- exact mismatch count;
- timestamps/sequence data required by the existing ITD campaign ledger.

The existing persistent ledger is authoritative. Replays must consume persisted
case artifacts and ledger identities rather than silently regenerating evidence.

## Failure, negative, and inconclusive preservation

A scientific mismatch is retained as a negative integrity result when the
declared source bytes, protocol fingerprint, plan fingerprint, and execution
preconditions are all valid.

Any provenance or execution-integrity drift — including source-byte mismatch,
protocol/plan fingerprint mismatch, missing or conflicting ledger identity,
corrupt persisted artifact, undeclared case parameters, or replay that cannot be
traced to the persisted source artifact — terminates the affected case or
campaign as `INCONCLUSIVE`.

Negative and inconclusive artifacts must be retained. They must not be rewritten
as successful cases, deleted from summaries, or rerun and presented as a fresh
replication.

## Replay rule

Replay is an integrity operation, not a new experiment. Replaying an already
completed R3 case must preserve the original campaign/case identity and must not
increase the claimed replication count.

## Protected/final boundary

R3 contains Development and Validation cases only. It creates no protected/final
fixture bytes, no final case plan, and no final authorization object. Protected
or final populations must not be opened, inspected, generated, or executed under
this protocol.

## Interpretation boundary

A zero-mismatch R3 campaign would establish only serialization/replay integrity
for this frozen synthetic Pascal representation. A mismatch would be preserved
as negative evidence when provenance is valid; provenance drift would remain
`INCONCLUSIVE`.

R3 does not establish Pascal model utility and does not authorize promotion into
SML-GENIUS, SBG, MOR, Delta-KV, context memory, or model architecture. Any
model-side handoff requires a separate prospective protocol owned by the
destination project.
