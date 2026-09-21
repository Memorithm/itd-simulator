# ITD-30.2 — Cross-repository adapters and evidence envelopes

Status: **implementation slice active**

## Purpose

ITD Research Lab needs to consume and export evidence across the Memorithm ecosystem without silently taking ownership of external semantics.

ITD-30.2 therefore binds every cross-repository transfer to:

- an exact repository/source identity;
- a versioned adapter contract;
- an explicit information-flow direction;
- declared input and output schemas;
- a named semantics owner;
- protocol and campaign fingerprints;
- a payload SHA-256;
- an evidence-strength class;
- a human-readable scope and limitations.

## Supported ecosystem identities

The bootstrap contract recognizes:

- Memorithm/TDI;
- Memorithm/FLAT-ATTENTION;
- Memorithm/scirust;
- Memorithm/ElasticXxx;
- Memorithm/NeuralOperator;
- Memorithm/NoiseLab;
- Memorithm/Forge;
- Memorithm/SciRust-Verify;
- Memorithm/scirust-hub.

Recognition does not imply compatibility or scientific validity. Every run still requires an exact source revision.

## Non-transferable authority

An evidence envelope deliberately has no field capable of authorizing:

- downstream runtime actuation;
- access to a protected final holdout;
- promotion of a research result to a certified scientific model;
- adoption of an external component's scientific or runtime semantics by ITD.

`authorizes_runtime_policy` and `authorizes_final_holdout_access` are hard-coded false properties.

## Evidence classes

The contract labels evidence by actual scope:

1. software oracle;
2. manufactured task;
3. controlled simulation;
4. public benchmark;
5. external real-world evidence;
6. cross-source replication;
7. cross-domain replication;
8. prospective measurement.

These classes describe evidence provenance/strength only. They are not verdicts.

## Next slice

ITD-30.3 will place these identities around a bounded deterministic campaign runner and replay record.
