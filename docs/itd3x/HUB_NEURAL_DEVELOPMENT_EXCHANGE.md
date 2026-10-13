# ITD / Hub / NeuralOperator Development exchange v1

Contract: `itd.hub-neural-development@1.0.0`.

`research-rs/hub-neural-bridge` publishes the first executable Rust exchange for
the research integration surface. It accepts exactly identified immutable
Development bytes materialized by Hub, calls ITD's existing periodic diagnostic
subset and NeuralOperator's published conservative isotropic Darcy residual,
and emits a separate declared output file for Hub's immutable artifact store.
The new workspace is separate from the existing offline `itd-rs` reference and
Python V29.18 package/runtime. No frozen scientific source, oracle or final
evaluation protocol is changed.

## Ownership and exact sources

- Hub daemon/API/materialization/provenance owner:
  `Memorithm/scirust-hub@01cf5f1e6d96573d57eef8d2aea22a5a8b0da02f`.
- NeuralOperator library owner, pinned in Cargo.toml and Cargo.lock:
  `Memorithm/NeuralOperator@2eba990da4779aeecfea1c4c288d8a6e552c48d8`.
- ITD library/bridge source: exact checkout SHA passed as `ITD_SOURCE_SHA` at
  compilation; the dedicated workflow verifies it against Git HEAD. This is
  build provenance in the qualified environment, not remote-host attestation.

The component program is the built bridge; its fixed shell-free argv is
`["{params}", "{input:fields}", "{output:observation}"]`. The input and output
capability ports are `fields` and `observation`; declared output path is
`observation.json`. Hub records the output under `file:observation`.
Registration is metadata only; the qualification actually submits and executes
runs through `/api/v1/runs` and `/api/v1/executions`.

## Bounded input and split contract

The strict parameter object binds contract version, `split=development`, three
exact source SHAs and ordinary SHA-256 of the complete input bytes. Unknown
fields, stale sources and other splits fail before the process opens the input
path. The strict input JSON has schema version 1, Development split, rows,
columns, positive finite spacing and lengths, and five finite row-major fields:
`velocity_u`, `velocity_v`, `solution`, `permeability`, `forcing`. It is limited
to 256 KiB and 4096 points. The adapter validates shape, bounds and finite values
before calling either owner. NeuralOperator retains its own positivity,
numerical and budget checks.

The operator/campaign retains input-selection authority: an independently
selected Development pin must not be copied from arbitrary final data.
This exchange neither opens a holdout vault nor authorizes final-label access.
The existing Python reference dataclasses remain typed research metadata; this
is the corresponding executable Rust slice, not a silent transport retrofit
or replacement of certified V29.18.

## Qualification

The required dedicated workflow builds the exact Hub, compiles the exact ITD
candidate with Rust 1.89 and the locked NeuralOperator dependency, and explicitly
executes the ignored real-daemon integration test. No Hub mock or kernel stub
participates. The synthetic 6x8 Development fixture has `u=-y`, `v=x`, quadratic
Darcy solution, unit permeability and forcing. Independent analytical checks
require ITD periodic subset `[2.5, sqrt(5), 1.52, 1.75, 2.52]` and every Darcy
interior residual `-5`. Replacing forcing by `2` requires every residual `-6`;
both input and output identities change, while the velocity diagnostics remain
unchanged. Two actual runs on the identical immutable input must return
byte-identical observations under different Hub run IDs.

The test checks original input artifact identity in Hub's run provenance, the
complete declared output bytes, and owner `portable-digest` results. Ordinary
raw SHA-256 and Hub's domain-separated CAS digest are distinct values; neither
is substituted for the other. A final request with a nonexistent input path
must be refused for its split before filesystem access. Unit controls also
reject wrong code/digest/shape/schema. The retained artifact includes source
SHAs, built binary hashes, input bytes, original run records, portable digests,
and unchanged/changed observations. No key or credential is retained.

```sh
ITD_SOURCE_SHA=<exact-checkout> cargo test --locked --manifest-path research-rs/Cargo.toml
ITD_SOURCE_SHA=<exact-checkout> ITD_HUB_BINARY=<exact-built-Hub> \
  cargo test --locked --manifest-path research-rs/Cargo.toml --test hub_e2e -- --ignored --nocapture
```

Scope is a finite Development transport/consumer qualification. The ITD
diagnostic subset is not the certified finite-boundary/multiscale signature;
Darcy residual evaluation is not a solver, training run, accuracy comparison or
generalization result. Local supervised process execution is not an OS sandbox,
worker attestation or proof of Hub ML maturity. No runtime policy, default model,
hardware performance or scientific promotion follows from run success.
