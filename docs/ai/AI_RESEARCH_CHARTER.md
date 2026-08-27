# ITD AI Research Laboratory Charter

Status: **open research charter**. This document does not revise or recertify `ITD V29.18`.

## 1. Purpose

ITD Simulator is extended as a general experimental laboratory for falsifiable questions in artificial intelligence and scientific machine learning.

The repository started from one concrete question in fluid dynamics: whether the existing ITD channels provide diagnostic or predictive information beyond competent established diagnostics. Missions 3–8 produced a negative answer within the evaluated domains. That result remains part of the scientific record.

The negative result does **not** answer different questions about representation learning, auxiliary supervision, robustness, anomaly detection, forecasting, control, learned spatial structure, multimodal signals, or other data domains. Those questions require separate hypotheses and separate experiments.

The laboratory therefore has two simultaneous responsibilities:

1. preserve the closed evidence and frozen V29.18 reference implementation;
2. make the validation machinery reusable for new AI hypotheses without assuming that ITD must help.

## 2. Non-goals

The laboratory must not:

- declare ITD a universal observable, universal complexity measure, or generally useful AI representation without evidence;
- reinterpret the Missions 3–8 negative result as positive;
- choose datasets, labels, baselines, or metrics because they make ITD look favourable;
- weaken established baselines in order to manufacture incremental value;
- tune on final holdouts;
- silently convert exploratory findings into confirmatory claims;
- modify `ITD V29.18` merely to improve a downstream benchmark;
- require every research line to use ITD if an ITD-free control is scientifically necessary.

## 3. Research-unit contract

Every confirmatory AI study should define, before final evaluation:

- a falsifiable hypothesis;
- the target domain and data provenance;
- an ITD-independent target or ground truth where applicable;
- at least one competent established baseline;
- the exact ITD-derived, learned, raw, or comparison representations under test;
- train/development/validation/final-holdout roles;
- leakage controls;
- metrics and uncertainty estimation;
- an explicit decision rule;
- compute and evaluation budgets;
- random seeds and determinism expectations;
- failure, blocked, inconclusive, and negative-result conditions;
- the distinction between exploratory and confirmatory evidence.

A study is successful when it produces a reliable answer, including a reliable negative answer.

## 4. Comparison ladder

Where technically meaningful, representation experiments should compare a ladder rather than a single ITD model:

1. trivial or persistence baseline;
2. competent established-domain baseline;
3. raw-data model;
4. ITD-only representation;
5. established + ITD;
6. raw + ITD;
7. learned representation without ITD;
8. learned representation with ITD-derived auxiliary information.

Not every problem requires every rung. Omissions must be justified before final evaluation.

## 5. Open AI research families

The initial programme is intentionally broader than the old fluid-diagnostic question.

### 5.1 Representation value

Does an ITD-derived representation improve sample efficiency, generalization, calibration, robustness, compression, or downstream accuracy compared with competent alternatives?

### 5.2 Auxiliary supervision

Can predicting ITD-derived quantities as auxiliary targets improve a model even when those quantities are not themselves strong standalone predictors?

### 5.3 Learned local and multiscale structure

Can local, patchwise, graph, spectral, or multiscale descendants of the original global signatures provide useful structured representations without retroactively changing the meaning of V29.18?

Any such construction is a new research representation, not a certified ITD revision unless a separate revision process later justifies that claim.

### 5.4 Forecasting and temporal modelling

Do ITD-derived temporal signals add value for forecasting state transitions, regime changes, rare events, degradation, or failure horizons?

### 5.5 Anomaly and change detection

Can ITD-derived features detect distributional, structural, or temporal changes earlier or more robustly than established signal-processing and learned baselines?

### 5.6 OOD, uncertainty, and abstention

Can structural representations improve shift detection, uncertainty calibration, selective prediction, or safe abstention under controlled domain shifts?

### 5.7 Control and adaptive systems

Can an ITD-derived observation or latent state improve a controller's decisions, time-to-decision, intervention cost, or robustness when compared with controllers using established observations?

### 5.8 Compression and resource-aware AI

Can ITD-derived structure help decide what information may be compressed, quantized, dropped, recomputed, moved, or retained while preserving declared task invariants?

### 5.9 Additional physical and signal domains

The laboratory may later test domains beyond fluid dynamics, including vibration and other time-series or field data, but each domain requires its own established baselines, units, ground truth, data provenance, and preregistered claims. Transfer of conclusions from fluid dynamics is prohibited without evidence.

## 6. First AI mission

The first implementation mission should answer a deliberately narrow question before adding large models:

> On a deterministic benchmark with leakage-safe splits, do existing ITD-derived representations add measurable value to competent classical and learned baselines for a clearly defined prediction or representation task?

The mission should establish the reusable AI experiment schema, model adapter boundary, result schema, provenance record, grouped statistics, and negative-result handling. Simple transparent models remain useful as controls, but deep or representation-learning models must no longer be prohibited merely because they are complex; instead they must be bounded, reproducible, and compared fairly.

## 7. Relationship to the ecosystem

### SciRust

SciRust is the preferred ecosystem source for scientific algorithms when its implementations are relevant and validated for the study: statistics, optimization, signal processing, causal methods, numerical methods, and future SciML primitives.

ITD Simulator must not duplicate a SciRust capability without an explicit reason. Experimental adapters may consume SciRust during research, while any production/runtime dependency decision remains a separate architectural question.

### ElasticXxx

ElasticXxx provides a natural downstream systems question: whether evidence produced by this laboratory can improve adaptive resource decisions while preserving explicit invariants.

Candidate experiments include representation choice, precision, memory use, batching, model selection, observation cost, diagnostic experiments, and controlled adaptation. ITD Simulator supplies experimental evidence; ElasticXxx remains responsible for its own trusted validation and actuation boundaries.

No result in this repository is automatically a runtime policy for ElasticXxx.

## 8. Repository boundaries

The frozen scientific core remains:

- `itd_v29_core/`
- `itd_v29.py`
- `itd_simulator/`
- `MODEL_REVISION = ITD V29.18`

The historical post-V29 fluid-diagnostic research remains evidence, not an open backlog to rerun.

New AI work will live in an isolated research namespace and must preserve the one-way dependency boundary: the certified core must never import the AI research layer.

## 9. Evidence ladder

Results should be labelled by evidence strength, for example:

- unit/software oracle;
- manufactured analytical or synthetic task;
- controlled simulation;
- public benchmark;
- external real-world dataset;
- cross-source replication;
- cross-domain replication;
- prospective or experimental measurement.

A high score on a manufactured fixture proves software behaviour, not external scientific utility.

## 10. Reuse before reinvention

The laboratory should reuse the strongest infrastructure already built in this repository where scientifically appropriate:

- manufactured oracles;
- preregistered protocols;
- saturation checks;
- grouped resampling/statistics;
- leakage-safe source-level splits;
- degradation sweeps;
- OOD and abstention evaluation;
- provenance manifests and checksums;
- reproduction bundles;
- deterministic software-validation fixtures.

Domain-specific assumptions must not be copied blindly from fluid dynamics.

## 11. Long-term criterion

The long-term objective is not to prove that one fixed ITD formula is useful everywhere. It is to make ITD Simulator a rigorous place to ask:

> Which structural representations, measurements, learned features, and interventions provide non-redundant useful information for an AI system, under which conditions, at what cost, and with what uncertainty?

That question is deliberately compatible with negative results and with an ecosystem in which SciRust supplies reusable scientific capabilities and ElasticXxx consumes validated evidence for adaptive systems research.
