# ITD-AI — Representation Strata Research Programme

Status: **open AI research line; ITD V29.18 remains frozen; no scientific claim established**.

## Conjecture

Dense, sparse, low-rank, quantized, compressed and mixed representations can be modeled usefully as strata of a common representation space, with explicit transitions whose fidelity, structural distortion and resource cost can be measured. Under this model, representation choice becomes a constrained path/planning problem rather than a fixed format decision.

A provisional form is:

`R = union_k M_k`

with a transition cost between representations such as

`d_R(a,b) = alpha * task_distortion + beta * transition_cost + gamma * storage_delta`

where every term must be operationally defined by the experiment rather than assumed to be a mathematical metric.

## Primary null

A stratified representation model provides no predictive or decision advantage over treating formats as a flat categorical choice once model capacity, fidelity and resource features are included directly.

## Why ITD-AI

The ITD AI laboratory is explicitly open to falsifiable work on representation value, learned spatial/multiscale structure, compression/resource-aware AI, forecasting, OOD and abstention. This programme remains isolated from the certified/frozen ITD V29.18 scientific model.

## Stage map

- **IRS-0** — freeze representation families, tasks, transition graph, fidelity/resource observables and baselines.
- **IRS-1** — deterministic synthetic matrices/tensors with exact reconstruction and task oracles.
- **IRS-2** — measure within-stratum and cross-stratum distortions under matched storage/compute budgets.
- **IRS-3** — compare flat format selection against graph/path-based transition planning.
- **IRS-4** — OOD transfer: determine whether learned transition preferences survive new data geometry.
- **IRS-5** — adapter-level transfer to ElasticXxx only after an independently qualified result.

## Required representations

At minimum: dense full precision, uniform quantization, structured sparsity, low-rank factorization and one mixed representation. Additional entropy-coded or residual forms may be added only with explicit accounting.

## Required baselines

Flat categorical selector, storage-only selector, task-error-only selector, random legal path, direct source->target transition and shortest-path planners under frozen scalarizations.

## Primary measurements

Task error/fidelity, exact stored bits or bytes including metadata, encode/decode transition cost, peak working memory, structural diagnostics, path stability, OOD regret and whether triangle-like/path-consistency properties empirically hold or fail.

## Falsification targets

The programme should actively search for:
- non-transitive preferences between representations;
- path dependence where `A -> B -> C` differs materially from `A -> C`;
- discontinuities at sparsity/rank/precision boundaries;
- cases where any proposed distance violates symmetry or triangle-like behavior;
- regimes where a flat categorical model predicts outcomes as well as the stratified model.

## Ecosystem boundary

SciRust is the preferred source for mature tensor, linear algebra, quantization, sparse and low-rank primitives and independent numerical oracles. ElasticXxx is a downstream target for qualified transition contracts and adaptive policies. ITD-AI owns the experiment and must not modify SciRust or ElasticXxx semantics to manufacture support.

## Evidence rule

No observed embedding, visualization or fitted distance is a proof that the representation space is a manifold, metric space or stratified space in the mathematical sense. Stronger terminology requires separately established assumptions or formal results.