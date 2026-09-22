# ITD-31.2 — Representation transition graph planning

Status: **implementation slice active**

## Research question

Does modelling representation changes as a directed measured graph provide a useful planning advantage over choosing a target format directly under the same frozen resource/fidelity scalarization?

## Graph contract

`RepresentationTransitionGraph` stores declared representation node identities and unique directed `RepresentationTransitionV2` edges.

The graph explicitly does not assume:

- symmetry;
- transitivity;
- triangle inequalities;
- metric-space or manifold structure.

All transition-cost terms in one graph must use the same declared transition-cost unit.

## Scalarization

`ScalarizationWeights` freezes non-negative weights for:

- fidelity loss;
- transition cost;
- storage delta;
- peak working memory.

At least one weight must be positive. The weights operationalize one experiment only; they do not create a universal distance.

## Baselines and planner

`direct_path` implements the direct source-to-target baseline when an edge exists.

`shortest_path` uses deterministic Dijkstra search because all edge costs are non-negative by contract. Equal-cost paths are broken lexicographically by node identity so repeated runs return the same path.

`path_advantage` reports direct cost minus planned cost only when both paths exist.

## Falsification value

The programme remains falsified for a task when direct/flat format selection performs as well as graph planning under frozen budgets and controls. A lower graph path cost is only an operational result under the declared scalarization.
