# ITD-35.1 — FLAT reference-semantics adapter

Status: **implementation slice active**

## Verified upstream contract

FLAT-ATTENTION exposes a deterministic scalar Rust `forward_reference` oracle using online softmax. Its core MHA shape is batch × heads × sequence × head_dim, and forward produces both the context tensor and per-query log-sum-exp values.

ITD-35.1 binds that reference semantics only.

## Input identity

`FlatReferenceCase` records:

- exact Memorithm/FLAT-ATTENTION source revision;
- batch/head/sequence/head-dimension geometry;
- causal flag;
- optional explicit softmax scale;
- Q, K and V SHA-256 identities;
- exact reference symbol.

The host oracle itself is not artificially constrained by the portable WGSL head-dimension cap.

## Output identity

`FlatReferenceResult` records exact hashes for:

- context output;
- log-sum-exp output.

## Explicit non-claims

Reference-oracle evidence cannot authorize:

- a hardware performance claim;
- WGPU/device routing;
- kernel promotion;
- a speedup claim;
- an attention-quality superiority claim.

Those require separate FLAT qualification and ITD mechanistic comparison protocols.

## Next work

ITD-35.2 will bind Multi-Algebra Attention research records separately so Boolean/F2/Zhegalkin/max-plus evidence is never conflated with standard forward_reference semantics.
