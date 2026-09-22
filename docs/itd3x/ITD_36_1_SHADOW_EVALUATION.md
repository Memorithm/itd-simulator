# ITD-36.1 — ElasticXxx shadow-policy evaluation

Status: **implementation slice active**

## Purpose

ITD must evaluate adaptive decisions before any downstream runtime is allowed to actuate them.

## Shadow realization

`ShadowRealization` compares one non-actuating candidate decision against an observed counterfactual or replay outcome.

It records:

- baseline quality;
- realized candidate quality;
- baseline cost;
- realized candidate cost;
- invariant-violation status.

Derived measurements expose realized quality/cost deltas and absolute prediction errors against the original `ShadowDecision` estimates.

## Explicit regret

Regret is not defined until a `ShadowUtilityContract` is supplied.

The contract freezes:

- quality direction (higher/lower is better);
- quality weight;
- cost weight;
- invariant-violation penalty.

At least one weight must be positive. The utility does not pretend that quality, cost and invariant penalties are naturally commensurate.

`ShadowRegretEvaluation` compares the realized shadow decision with an explicitly supplied oracle/comparator outcome and reports non-negative regret.

## Safety boundary

Every object in this slice exposes `actuates = False`. ITD only measures evidence. ElasticXxx remains responsible for validating invariants and performing any future physical transition.
