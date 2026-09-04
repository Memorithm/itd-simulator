# ITD AI experiment protocol v1

Status: **research infrastructure only**

`itd_research.experiment_schema` defines a small canonical contract for future ITD AI experiments. It is deliberately independent from the frozen ITD V29.18 core and from any particular TDI, ADA or FLAT mechanism.

## Purpose

The protocol binds, before a final evaluation:

- one explicit falsifiable hypothesis and comparison;
- exact implementation provenance;
- distinct development, validation and final source identities;
- named primary, secondary and diagnostic metrics;
- one explicit bounded compute quantity and its unit;
- one declared uncertainty procedure;
- a canonical JSON representation and SHA-256 protocol fingerprint.

This makes an experiment contract externally bindable without treating an ITD descriptor as scientific truth or silently changing the final data source after selection.

## Leakage boundary

`ExperimentProtocolV1.assert_selection_allowed(...)` accepts development and validation roles but rejects the final role. `assert_final_evaluation(...)` requires the exact preregistered final source identity.

The schema does not contain data rows, labels, model outputs, thresholds, fitted parameters or final results. It therefore cannot itself execute or authorize a confirmatory experiment.

## Metric boundary

A metric has a role and a direction. Diagnostic metrics are required to remain `descriptive`; they cannot be declared `higher_is_better` or `lower_is_better` in this generic contract. This prevents structural ITD diagnostics from silently becoming optimization objectives before a task-level experiment justifies that use.

At least one primary metric is mandatory, but this module does not choose which metric should be primary for a particular scientific mission.

## Compute and uncertainty

The compute budget carries an explicit caller-defined unit and a finite positive maximum. The schema does not pretend that tokens, solver steps, verifier calls, FLOPs and wall-clock time are interchangeable.

The uncertainty contract records a named method, confidence level and paired/unpaired status. It does not select a method for a future mission; that choice remains part of preregistration.

## Cross-repository use

The canonical protocol fingerprint can later be referenced by ADA, TDI, Forge, FLAT-ATTENTION or evidence tooling as an immutable experiment identity. Such a reference does not transfer semantic ownership to ITD and does not make the external result an ITD result.

## Non-claims

This increment does not:

- modify ITD V29.18 or any historical fluid result;
- add TDI-8.3 adaptive-compute observables;
- create or consume a TDI confirmatory holdout;
- define a new attention semantic;
- establish usefulness of any ITD descriptor;
- choose final task populations, thresholds, sample sizes or uncertainty methods;
- claim model quality, performance, novelty or generalization.
