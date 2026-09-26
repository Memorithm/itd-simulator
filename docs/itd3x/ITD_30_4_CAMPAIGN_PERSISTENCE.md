# ITD-30.4 — Persistent campaign artifacts and incomplete lifecycle

Status: **implementation slice active**

Research infrastructure only. Frozen ITD V29.18 is unchanged. This slice
does not run a confirmatory study, open a final holdout, or train a model.

## Problem

ITD-30.3 can execute a complete plan in memory. It does not store case
artifacts, and it has no durable record for campaigns that stop early.
Recording a SHA-256 on `SourceIdentity` also does not prove that those
bytes were ever read.

## Contract

A campaign directory contains:

- `plan.json` — frozen `CampaignPlanV1`;
- `ledger.json` — `CampaignLedgerV1` with status `interrupted`,
  `blocked`, `inconclusive` or `completed`;
- `artifacts/<case_id>/output.bin` — exact case output whose SHA-256
  equals the execution digest.

Writes are atomic (`*.tmp` then replace). Reloaded artifacts are hashed
again before a completed ledger can be turned into `CampaignRunV1`.

## Lifecycle

- `completed` covers every planned case in order and may emit a replayable
  `CampaignRunV1`.
- `interrupted` is a strict prefix. Evaluator exceptions are persisted,
  then re-raised. Only this status may resume from the next case.
- `blocked` and `inconclusive` are terminal records. They are not successes
  and cannot be converted into a completed run.
- `CampaignHalt` is the explicit evaluator signal for blocked/inconclusive
  stops. Ordinary exceptions stay exceptions.

## Source and authorization bytes

`verify_source_bytes` hashes supplied payloads and fails if the identity
has no digest or the digest does not match. Persisted campaigns refuse
sources that only name a revision.

A `FinalEvaluationAuthorizationV1` digest is not sufficient. The caller
must also supply the authorization artifact bytes. A match records that
those bytes were hashed; it does not issue scientific permission.

## Out of scope

OS CPU/RAM/time confinement, hostile sandboxing, cryptographic signatures,
external network fetches, BANC/V888 graph reads, and model promotion remain
separate work.
