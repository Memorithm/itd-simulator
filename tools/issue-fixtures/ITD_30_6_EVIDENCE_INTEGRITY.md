# ITD-30.6 / ITD-34.1 — evidence integrity corrections

Research infrastructure; no change to frozen ITD V29.18, no new model or result.
Scope: issues #61, #62, #63, under #33 and #36, with selection guards shared by
#29, #35, #38 and #39. Baseline reviewed: 7ba33919d47232a093c882a8ee4b531ecc0f1aeb.

## Selection and result classification

Valid serialized split roles are converted to `SplitRole` before policy checks.
Unknown values fail construction (or the protocol selection call). `final`
remains prohibited for selection/training/search, including a plain string from
JSON. Campaign final cases still require the existing explicit authorization
metadata before the evaluator is invoked. MAA evidence can still *describe* a
frozen final result; role normalization does not grant final execution authority.
Study class and outcome are normalized before result invariants, so `blocked`
can never carry observations just because its value arrived as a string.
Search freeze flags require actual booleans, not nonempty strings or 0/1 integers.
This is input-contract validation for trusted code, not a hostile-object sandbox.

## Bindings and replay accounting

Use all three checks when accepting an experiment result:

```python
campaign.assert_matches_protocol(protocol)
result.assert_matches_protocol(protocol)
result.assert_matches_campaign(campaign)
```

A result and campaign must agree on their exact protocol digest, and a campaign
must identify the implementation declared in that protocol. Merely passing the
protocol-only result check has never established the campaign link.

Supply the actual protocol at execution time:

```python
run = run_bounded_campaign(plan, evaluator, protocol=protocol)
run.assert_replay_of(plan)
```

This validates implementation, source identity for each case's declared split,
work unit and plan budget before evaluation. A plan may use a smaller budget,
not a larger one than its protocol. Legacy calls omitting `protocol` retain their
metadata-only behavior for compatibility; they do NOT establish source/protocol
conformance. SourceIdentity declares identity; payload hashing/verification and
external approval remain the responsibility of their respective input boundary.
An authorization digest is neither a signature nor a newly issued permission.

Both live and restored records now validate per-case accounting and total work.
Replaying a saved record with the correct digest/order but too much work fails.
`assert_replay_of` validates a record against its plan; it does not rerun the
computation or authenticate the claimed output digest. Work is reported by the
evaluator and checked after it returns; this does not impose OS CPU/RAM/time
limits. Callback exceptions remain visible and are not converted into success.

Caller lists for protocol splits/metrics, campaign adapters, cases, executions,
result observations and limitations are copied into tuples at construction.
Their subsequent mutation cannot alter the validated object or its fingerprint.
Existing valid tuple-based V1 dictionary/JSON layouts are unchanged.

## Undefined UQ values: intentional research-API correction

`SelectiveRiskPoint.selective_risk` is now `None` at zero coverage.
`false_confidence` is `None` without OOD samples. Both remain zero when a real,
nonempty denominator supports a measured zero. Standard dataclass JSON encoding
therefore represents absence as `null`, never NaN or a fabricated perfect score.
Callers must check for `None`; do not replace it by zero for model ranking.
Existing archived outputs keep their original interpretation and source identity.

Trapezoidal integration rejects a supplied undefined risk instead of silently
interpolating from an invented origin. Explicitly select and report a measured
coverage interval. A partial interval is not a full risk-coverage area.
Correctness and OOD flags accept Python `bool` and NumPy `bool_`, rejecting strings,
integers, missing values and NaNs. NumPy sequences use length-based emptiness checks.
Positive integer bin counts are required. Scaled non-negative means and split
trapezoid terms avoid overflow of intermediate sums for finite results.

## Reuse and remaining work

These guards are reused inside the ITD adapters; no downstream repository source
was copied or silently upgraded. Their consumers retain scientific/actuation
ownership. They are prerequisites for trustworthy game/learner evidence, not
learning evidence. Persistent campaign artifact storage, authenticated permissions,
full adapter execution, UQ localization, V888 port diagnostics and persistent
learned checkpoints remain separate open research work. Trading remains deferred.
