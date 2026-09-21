# ITD-32.1 — NeuralOperator research adapter

Status: **implementation slice active**

## Verified upstream scope

The current Memorithm/NeuralOperator repository exposes deterministic Burgers 1D and Darcy 2D research tasks, including FNO/DeepONet/PINO-style comparisons, OOD families, rollout and physics-residual evaluation.

ITD-32.1 does not duplicate those solvers or training loops. It defines the evidence boundary needed to compare structural representations fairly.

## Sample identity

Each operator sample binds:

- task family;
- split role;
- exact source revision;
- input SHA-256;
- target SHA-256;
- declared resolution;
- distribution label.

Final samples reject selection/fitting access.

## Model identity

Each model binds:

- model identifier and family;
- exact source revision;
- optional checkpoint SHA-256.

## Evaluation case

Each case combines exactly one sample, AI comparison arm, model identity and representation identity.

## Prediction record

Observed results bind:

- exact prediction SHA-256;
- relative L2 error;
- optional physics residual;
- inference cost;
- explicit inference-cost unit.

These fields are measurements only. They do not assert that an ITD-derived representation is useful.

## Next work

The next experiment layer will construct fair raw / established / ITD / learned / combined comparison ladders over deterministic Development and Validation populations before any final evaluation.
