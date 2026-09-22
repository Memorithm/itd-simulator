# ITD-37.0 — NoiseLab perturbation adapter

Status: **implementation slice active**

## Principle

ITD-37 follows NoiseLab's rule: characterize before filtering.

Every intervention preserves the exact raw-observation identity before any perturbation or optional filtering output is considered.

## Intervention identity

`NoiseInterventionRef` binds:

- non-final split role;
- exact Memorithm/NoiseLab source revision;
- noise/process family;
- explicit seed;
- intervention site;
- parameters SHA-256;
- raw observation SHA-256;
- perturbed observation SHA-256;
- optional filtered observation SHA-256.

## Response record

`PerturbationResponseRecord` attaches measured amplitude, structural delta, task-error delta and uncertainty delta to one exact intervention.

## Scientific boundary

Neither the intervention nor its response can authorize a causal claim. Association and controlled response remain measurements until a separately designed causal intervention protocol justifies stronger language.

Final perturbation material is not accepted by the ITD-37.0 adapter.
