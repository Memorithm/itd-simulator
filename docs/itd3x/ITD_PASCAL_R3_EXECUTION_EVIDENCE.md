# ITD Pascal R3 — serialization/replay execution evidence

Status: completed Development/Validation-only secondary integrity campaign.

Execution source commit: `ebb7fa7cbabc4f333be4a56d034aee2782cb7d8b`.

No protected/final source was opened, generated, or executed. This evidence is
independent of TDI's cost/utility conclusions and authorizes no model-side
promotion.

## Frozen campaign identity

- Plan fingerprint:
  `3dcb36205afd42275ded7f1a3ecdd69f3cb1c184a249932694777566db557773`
- Development source SHA-256:
  `d81fabde1e77c4ae1148f279b311664fdb9ffc763bbf482d3508cf8882a5953d`
  (512 bytes)
- Validation source SHA-256:
  `ab98a02e4f95e2919634b4e7e986107a672d43458c7206ff185fa00a01965f10`
  (2048 bytes)
- Persisted plan SHA-256:
  `887ddae034b2b6c104792da3c9c796c9e25254eac5522c03cf6b86357c1442a4`
  (11522 bytes)
- Persisted ledger SHA-256:
  `6e6f902fbc0b6211f04f5de0e489622bca7b75db165b233782cfd966bd7de50e`
  (14435 bytes)

The exact plan, ledger, and 32 per-case artifacts remain in the persistent
campaign directory
`/home/tarek/research/pascal_dual_bench/itd-r3-evidence-ebb7fa7`.
Replays consume the persisted serialized artifact bytes and retain the original
campaign/case identity; they are not counted as new replications.

## Exact result

- Campaign lifecycle: `completed`
- Executions: 32/32
- Persisted artifacts: 32
- Source verifications: 2
- Exact reconstructed-word mismatch total: 0
- Integrity outcomes: 32 `pass`, 0 `negative`
- Replay digest checks: all true

The campaign therefore establishes only serialization/replay integrity for the
frozen synthetic R3 representation across both preregistered non-final splits,
byte orders, chunk widths, and replay counts. It does not establish Pascal
model utility.

## Qualification

On the exact execution source, repository-manifest verification passed and the
R3 plus R2 integrity suites passed 9/9 tests. Ruff also passed for the R3
implementation and tests. These qualification reruns are software checks, not
fresh scientific replications.

SML-GENIUS remains the owner of model-side Pascal primitives. No promotion into
SBG, MOR, Delta-KV, context memory, or model architecture is authorized by R3.
