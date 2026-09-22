# ITD-39.2 — SciRust-Verify evidence-dossier binding

Status: **implementation slice active**

## Ownership

SciRust-Verify owns verification execution, provenance normalization, evidence integrity, scope and verification verdicts. ITD owns the scientific interpretation of ITD experiments.

## Preserved overall verdicts

The adapter preserves these distinct dossier outcomes without flattening:

- `PASS`;
- `PASS_WITH_GAPS`;
- `FAIL`.

`PASS_WITH_GAPS` is never converted into a clean pass.

## Preserved claim verdicts

Individual claims retain the SciRust-Verify vocabulary:

- `VERIFIED`;
- `FAILED`;
- `NOT_VERIFIED`;
- `SKIPPED`;
- `UNSUPPORTED`.

Required/optional status is retained per claim.

## Dossier identity

`SciRustVerifyDossierRef` binds:

- exact SciRust-Verify source revision;
- run identity;
- bundle SHA-256;
- report SHA-256;
- plan SHA-256;
- overall verdict;
- claim evaluations;
- limitations;
- whether integrity checking was actually performed.

A nominal `PASS` is not considered a clean pass when bundle integrity was not checked.

## ITD linkage

`ItdDossierBinding` adds exact ITD protocol and campaign fingerprints and can fail closed when dossier integrity has not been checked.

## Non-claims

A verification dossier cannot by itself authorize:

- an ITD scientific conclusion;
- a formal-proof claim;
- universal determinism;
- V30 scientific-model promotion.

These boundaries follow SciRust-Verify's own documented scope.
