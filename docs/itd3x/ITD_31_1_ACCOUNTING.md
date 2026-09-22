# ITD-31.1 — Exact representation resource accounting

Status: **implementation slice active**

## Purpose

Representation comparisons must not treat dense, sparse, quantized or low-rank formats as labels without accounting for their real storage and transition costs.

## Accounting contract

`RepresentationResourceAccounting` records:

- payload bits;
- metadata bits;
- peak working bytes;
- encode cost;
- decode cost;
- the explicit caller-defined cost unit.

Total stored bits always include metadata. Encode/decode costs remain separate and are only combined by an explicit derived property.

## V2 observation

`RepresentationObservationV2` binds one representation family to exact resource accounting plus task and reconstruction error.

## V2 transition

`RepresentationTransitionV2` binds:

- source and target identities;
- fidelity loss;
- transition cost and its unit;
- peak working memory;
- storage delta in bits.

The optional scalarization requires four explicit frozen weights. The implementation does not claim that the scalarization is a mathematical distance or that its terms are naturally commensurate.

## Ecosystem use

SciRust is the preferred source of actual tensor/quantization/sparse/low-rank mechanisms. ITD owns comparative measurement only. ElasticXxx may later consume qualified transition evidence after its own invariant validation.
