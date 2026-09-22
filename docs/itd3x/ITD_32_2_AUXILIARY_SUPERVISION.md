# ITD-32.2 — Auxiliary structural supervision

Status: **implementation slice active**

## Research question

Can an ITD-derived auxiliary target improve sample efficiency or downstream quality beyond generic multi-task regularization and established-domain auxiliary targets under matched model/training budgets?

## Required control classes

`AuxiliaryTargetClass` distinguishes:

- ITD-derived targets;
- established-domain auxiliary targets;
- matched random auxiliary controls.

A no-auxiliary arm is represented by `auxiliary_target = None` and must use zero auxiliary loss weight.

## Matched training budgets

`assert_matched_training_budget` requires comparison arms to share:

- model family;
- parameter budget;
- training-work unit;
- exact training-work quantity;
- seed.

This prevents an apparent auxiliary benefit from being attributed to extra compute or capacity.

## Final-data boundary

Auxiliary fitting is forbidden on the final split.

## Sample efficiency

`sample_count_to_threshold` reports the first point on a strictly increasing learning curve that reaches a preregistered primary-metric threshold.

`sample_efficiency_ratio` reports baseline samples divided by candidate samples only when both arms reach that same threshold. If either arm does not reach it, the result is `None` rather than an invented finite advantage.

## Interpretation

A ratio above one may indicate sample-efficiency advantage under the frozen task/protocol; it does not establish that the ITD target is universally useful. The matched random and established-domain controls remain necessary for attribution.
