# ITD-30.3 — Bounded deterministic campaign runner

Status: **implementation slice active**

## Contract

A campaign is no longer an informal script. It is represented by a versioned plan binding:

- one CampaignIdentityV1;
- an ordered immutable case list;
- each case's split role and exact input source identity;
- a declared work quantity per case;
- one campaign-wide work unit and maximum total budget.

## Execution

`run_bounded_campaign` executes the caller-supplied evaluator in the declared case order and verifies:

- returned case identity matches the requested case;
- per-case work does not exceed the frozen case budget;
- accumulated work does not exceed the campaign budget;
- the resulting execution order exactly matches the plan;
- the run fingerprint remains bound to the plan fingerprint.

Evaluator exceptions are not converted into successes or silently skipped.

## Final-evaluation boundary

A plan containing a final-split case fails closed unless a `FinalEvaluationAuthorizationV1` is supplied.

The authorization must bind:

- the exact protocol fingerprint used by the campaign;
- the exact preregistered final source identity;
- an external authorization SHA-256 identity.

This contract records authorization identity; it does not create scientific permission by itself.

## Replay

`CampaignRunV1.assert_replay_of` requires both the exact plan fingerprint and exact ordered case identities.

## Next work

Persistent result/artifact layout, blocked/inconclusive execution records
and source-byte verification are implemented in ITD-30.4. Adapter-specific
runners remain separate work.
