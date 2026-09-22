# V888-BOOL and V888-GROWTH — research programme

Author: Memorithm research programme. Revision **2026-09-22.1**.
Status: user-authorized research plan; Boolean computation on V888 is **not yet validated**.
Canonical machine plan: `V888_BOOL_PROGRAMME.json`. Tracking: ITD issue #58.

## Objective and separate questions

Build and test a dynamic computational system derived from the audited BANC v888
connectome. The intended product of this research is useful Boolean/low-bit recurrence,
not a claim that the recorded animal has been revived or faithfully reproduced.

Keep three questions separate:

- DATA: what source graph is actually represented, and which identities/filters are verified?
- BOOL: can the defined dynamics solve temporal Boolean tasks, and does V888 topology help?
- GROWTH: can artificial growth/pruning improve measured function, and what independent
  biological developmental evidence supports or contradicts a proposed mechanism?

Success at data ingestion is not success at computation. A working Boolean task is not
a topology advantage. A simulated causal intervention is not biological causality.

## Persistent ITD-3X coverage

| Family | Continued responsibility | V888 contribution |
| --- | --- | --- |
| ITD-30.x | Protocols, adapters, campaign lifecycle | Durable ledger and integration repair |
| ITD-31.x | Representation and exact storage | Graph identity, low-bit state, topology overhead |
| ITD-32.x | AI and SciML; NeuralOperator retained | Boolean tasks, reservoir/readout, consumer evaluation |
| ITD-33.x | Trajectories and TDI comparison | Stimulation/state records, retention and adult descriptors |
| ITD-34.x | UQ and selective decisions | Error/coverage, uncertainty and fresh confirmation |
| ITD-35.x | Structured operators, FLAT and MAA | Topology ablations and mask proposals |
| ITD-36.x | Adaptive systems | Artificial grow/prune/regrow and shadow policies |
| ITD-37.x | NoiseLab perturbations | State corruption, lesions, jitter and recovery |
| ITD-38.x | Bounded Forge search | Discrete rules/topologies, development-only |
| ITD-39.x | Rust parity, evidence and Hub | CPU reference, portable acceleration and dossiers |

Existing families and umbrella issues are not closed or renumbered. V888-BOOL and
V888-GROWTH use separate slice IDs to avoid collisions with ITD, SML, SBG, CSP or MAA.

## Development ladder: 26 milestones

The JSON is authoritative for dependencies, owners, lifecycle and exit criteria.

| Group | Milestones | Deliverable |
| --- | --- | --- |
| Source / foundation | V888-DATA-0; ITD-30.4; ITD-30.5 | Audit retained, bootstrap maintained, PR dependency chain reconciled |
| V888-BOOL-0.x | 0.1 graph; 0.2 subsets/controls; 0.3 dynamics; 0.4 I/O | Exact-source runnable reference with bounded, causal stimulation |
| V888-BOOL-1.x | 1.0 truth tables; 1.1 delayed XOR; 1.2 memory; 1.3 composition | Verified useful logical tasks |
| V888-BOOL-2.x | 2.0 topology; 2.1 perturbation; 2.2 precision; 2.3 confirmation | Attribution, robustness and independent confirmation |
| V888-BOOL-3.x | 3.0 search; 3.1 growth/pruning; 3.2 regrowth | Bounded artificial structural adaptation |
| V888-BOOL-4.x | 4.0 SML; 4.1 FLAT; 4.2 Elastic | Independently qualified consumer handoffs |
| V888-BOOL-5.x | 5.0 scale; 5.1 dossiers | Measured Thor execution, replay and evidence transfer |
| V888-GROWTH | 1 adult allometry; 2 developmental evidence; 3 synthesis | Separate biological and model-level conclusions |

### Source gate

Use BANC materialization v888, detector v3, exact file hashes and object generations.
Never treat an upstream download path or a materialization date as biological time.
The audited induced graph has 188,508 metadata nodes, 13,620,865 directed pairs and
42,309,621 contacts; the retained raw table contains 198,816,365 records. Its current
measured size is 19,733,123,829 bytes, not the earlier approximately 5.6 GB estimate.
See the pinned audit linked in the dated status ledger.

Per-node reconciliation does not prove pairwise equality or unique synapse IDs.
Qualify the pairwise representation or explicitly retain its remaining discrepancies.
Keep unknown endpoints and cut-edge counts as boundary data; do not invent neuron types.

### Dynamics gate

Compare three explicitly separate models on the same declared source scope:

1. simplified LIF numeric reference;
2. binary spikes with bounded integer accumulators/weights;
3. genuinely Boolean recurrent states with bounded nonlinear functions.

Specify synchronous or event ordering, update ties, delay bins, reset, refractory rules,
initial conditions, overflow/saturation and termination/event budgets. Multiplicity is
not measured conductance. Excitation/inhibition, delays and thresholds remain declared
model assumptions unless independently constrained; retain uncertain transmitter labels.

Pure affine GF(2) composition stays affine; nonlinear Boolean tasks need explicit
nonlinearity such as AND interactions or threshold rules. Bound nonlinear degree/fan-in
and rule storage rather than allowing an unmeasured truth-table explosion.

Start with topology frozen and only a bounded readout trained. Readout-only,
weight-adaptation, rule-search and rewiring experiments must remain separate arms.

### First functional campaign

Primary target: `y[t] = a[t-d] XOR b[t]`.
Proposed exploratory delay grid: 1, 2, 4, 8, 16 and 32 updates; these are design values,
not achieved retention horizons. Freeze the actual grid, seeds, port placement, distractors,
trial resets, encoding and readout budget before running a comparison.

The encoder must not compute the label or supply old bits. The readout receives only
declared current features. No hidden delay line or input-history buffer is free: any
such state is part of the model and resource budget. Test that future inputs cannot
change past outputs and that trials do not leak state into each other.

Truth tables for AND/OR/XOR/NOT/majority/multiplexing qualify basic semantics, not
connectomic advantage. Exhaust bounded sequential spaces where feasible and label
finite-horizon verification separately from statistical tests on unseen sequences.

Follow with write/hold/overwrite/erase, interference, long-delay retention and
contextual temporal predicates. Constraint-search proposals require an exact verifier;
failure to find a solution is not an UNSAT certificate.

### Controls and measurements

Use direct exact sequential logic/shift registers, no-reservoir readout, a small
conventional recurrent model, random sparse graphs and topology-matched graph families.
Match directed degrees, reciprocity and modules separately; verify achieved constraints
rather than trusting generator names. Match N/E, readout capacity, encoding, precision,
port-selection search, training budget and total evaluation budget.

Report task quality and topology attribution as separate verdicts. Use paired seeds,
task/sequence-level uncertainty and multiplicity-aware comparisons; neurons within a
single graph are not independent biological replicates. A fixed real graph has no
between-animal replication merely because many seeds were simulated.

Record exact payload plus metadata bits, peak working memory, active nodes/edges,
events, integer/Boolean/numeric operations by category, scheduler overhead, initialization,
encoding, simulation, readout and total wall time. Integer/bit packing is not a measured
speedup. Keep real-device energy unavailable unless actually measured with a documented
method. Initial subset sizes must fit a declared budget; never assume the full raw
synapse table is required at every timestep.

### Search, growth and deployment

Forge searches frozen development domains only; it does not own the held-out conclusion.
Growth experiments compare fixed topology, weight-only adaptation and grow/prune/rewire
at matched final capacity AND cumulative compute/training budgets. Specify credit,
resource limits, topology-edit logs and rollback. Increased node count is not success;
use verified memory horizon, task capacity, robustness or a declared Pareto criterion.

SML integration is a consumer experiment, not a model release. Keep existing consumer
namespaces, bounded-state/memory constraints and no raw-data inference dependency.
FLAT owns mask and numerical attention semantics; preserve negative MAA findings and
dense-reference output diagnostics. Elastic receives evidence-only shadow recommendations;
a separate policy review is needed for actuation. Verify/Hub adapters are qualified
interfaces, not assumed capabilities. CPU Rust first, optional WGPU/Vulkan later; no
mandatory new NVIDIA-specific software stack.

### Scientific gates and stop/redesign rules

Preserve positive, negative, equivalent, inconclusive and blocked outcomes. Redesign
when success comes from encoder/decoder leakage, unequal resources, hidden state,
unqualified dynamics or a post-hoc metric. Do not promote a V888-specific advantage that
vanishes under the strongest matched controls. A null topology advantage need not erase
a useful generic engine: promote that engine only under its own evidence scope.

Before a confirmatory run, separately freeze and authorize source, policy, hypotheses,
primary metrics, task groups, budget, uncertainty, exclusions and fresh final identities.
The strategy JSON grants no final access, runtime actuation, model promotion or auto-merge.

Adult morphology remains cross-sectional. V888-GROWTH uses per-metric valid counts,
region/side/hemilineage/neuromere groups and detector-consistent synapse counts. Published
primary developmental literature may inform hypotheses; adding any other raw connectome
requires a separate source decision. No causal biological growth law is established here.
