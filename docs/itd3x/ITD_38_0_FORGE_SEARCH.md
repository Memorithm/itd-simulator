# ITD-38.0 — Forge bounded search adapter

Status: **implementation slice active**

## Search authority

Forge may search candidates only inside an ITD-declared non-final search domain.

`ForgeSearchContractV1` freezes:

- exact Memorithm/Forge source identity;
- Development or Validation role;
- search domain and candidate schema;
- search-space SHA-256;
- objective-schema SHA-256;
- maximum candidate count;
- compute budget and unit;
- deterministic base seed.

Final ITD data is structurally rejected.

## Verify before measure

`ForgeCandidateEvidence` permits objective observations only when `verification_passed` is true. This preserves Forge's verify/measure separation so an incorrect fast candidate cannot obtain a meaningful objective vector.

## Pareto result

`ForgeSearchResultV1` binds the exact search contract fingerprint, evaluated-candidate count, Pareto candidate identities and Pareto-front SHA-256.

The result is rejected if it exceeds the frozen maximum candidate count.

## Scientific boundary

Forge search evidence cannot authorize an ITD confirmatory claim. A selected candidate must leave the search surface and enter the appropriate frozen ITD evaluation protocol before any confirmatory interpretation.
