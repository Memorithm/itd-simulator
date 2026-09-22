# PORTS-DYN1 — source-bound Boolean dynamics and port sensitivity

Observed 2026-09-22. Owner: ITD V888 research; implementation: SciRust PR #1510.
This is an executed exploratory diagnostic, not game learning or biological validation.

## Exact execution and source

Final candidate: `6b9714622ddd3f7aae960ce1f6349461e3b27b91` on
`Memorithm/scirust/research/v888-ports-dyn1`, based on inspected master
`2d0f74f2b2dcf5ec9f74644aaa54c88b8fadcdb1`. Candidate Git tree:
`b585257d572dc7dd78fe1841685a332b8b253e52`.

Thor workflow **35787751454** completed its four artifact-preparation slots and
qualification job successfully. The qualifying process ran on machine `tarek`,
aarch64, runner `tarek-scirust-arm64-01`, uid 994 (`github-runner`), Rust 1.89.0.
Retained evidence root:
`/mnt/nvme/github-runners/home/v888-research-runs/ports-dyn1-35787751454-1`.

Artifact **10719938845**, 5,893,862 bytes, ZIP SHA-256:
`00967751b3396c5a804425041f3582f19e72681d1e9966ff80b2a88aa9176a4f`.

The library `scripts/v888_dyn01/recurrent.rs` is reused unchanged, not copied into
a new implementation. Its hash matches DYN-REF1 at source
`75f43ec35b1118c98b23bbde8fc8e1d6bfd42036`:
`f3366c06db05569bbd4771d746dc5f8fce020d48c088eb03cc14e431e230415c`.
The binary SHA-256 is
`af720d8889c13e30bc532d4aaf76f8983bd797ed6bc3e7a58131c20b3b56d093`.

Consume all 12 original BOOL-0.2a subsets and all five unit-adjacency arms, without
changing graph membership, original ports, seeds, source IDs, or rejected cases.
Prior receipt SHA-256:
`13389676a618a4c9a4bad32d7102ae630f04e912873f93a04069e0c293aefc13`.
All 12 case receipts and all consumed node/edge/port identities are bound to that
previously qualified scope. These subset graphs are not the full 188,508-node CNS.

## What was implemented and tested

New bounded Rust driver in `scripts/v888_ports01/driver.rs`: exact integer source
IDs, sorted unique directed pairs, deterministic shortest-hop/reachability checks,
source-bound impulse execution, full node-state output and explicit work counters.

Each graph has 17 prescribed port panels: the original panel and 16 ID-ranked
placements fixed before observation. All five arms receive the same panels for a
source case. All 17 triples happened to be distinct within each case; this does not
make panels independent observations. Alternative panels are structural diagnostics
only; only the original ports receive the dynamic probes.

The two executed equations are the existing Boolean affine parity and nonlinear
parity/AND references. Every edge has unit weight and delay one. The AND uses the
first two canonically ordered incoming bits. These are explicit model choices, not
biologically measured conductances, signs, thresholds or delays.

Four trials per model: no stimulus, A only, B only, simultaneous A+B. Stimulus is
present at tick zero only, followed by zero external drive through tick 128.
Activity and pending transmissions reset between trials; parameters stay unchanged.
No target, task label, readout training, internal plasticity or feedback is present.

| Executed qualification | Result |
|---|---:|
| Original recurrent-library Rust tests | 16 passed |
| New Rust source-binding tests | 6 passed |
| Independent process/oracle and location methods | 11 passed |
| Source/control graphs | 60 |
| Structural port configurations | 1,020 |
| Dynamic trials per pass | 480 |
| Complete network-state comparisons per pass | 61,920 |
| Cell updates per pass, summed over graph sizes | 73,313,280 |
| Directed edge visits per simulation pass | 1,315,371,720 |
| Separate reset-probe edge visits | 10,196,680 |
| Independent mismatches | 0 |
| Full Rust replay | byte-identical for all 60 traces |
| Pinned inputs checked before/after | 97 |

The independent oracle gathers incoming values with exact bounded sums followed by
modulo two, whereas Rust scatters along edges. It separately propagates OR reachability
support, verifies affine superposition, and records nonlinear superposition departures.
The 11 process/location methods comprise the prior 8 differential methods and 3 new
artifact-location methods; their parametrized/random subcases are not 11 experiments.

Counters describe one pass. Replay doubles Rust simulation and reset work. Direct
vector payload is not total RSS, hardware energy, or end-to-end cost. The 36.2108-second
qualification observation includes this particular replay/oracle setup; no comparative
speed claim follows from it.

## Measured results

Both original inputs structurally reach their readout in 8 of the 12 V888 references.
The 4 unreachable references are retained: all three ranked-2048 subsets and
`weak_bfs-n512-s17`. At all 17 placements combined, the corresponding counts are:

| Graph arm | Panels with both inputs reaching output / 204 |
|---|---:|
| V888 reference | 126 |
| Edge-count control | 153 |
| Degree control | 130 |
| Degree + reciprocity | 129 |
| Degree + reciprocity + anatomy blocks | 128 |

This is a finite structural diagnostic, not a statistical superiority test or a claim
that the edge-count control learns better. Sampling, placement and graph construction
change route availability and must remain explicit in future game protocols.

A path need not transmit a one under XOR. In the 12 references, for the two separate
single-input affine probes, OR support reaches the readout at 2,015 input/tick positions.
Actual parity output is one at 1,017 of them and zero at 998: even-path cancellation
under the declared equation, not loss of source edges. These positions are dependent
and are not a binomial sample of neuronal reliability.

Example: `weak_bfs-n2048-s29`, original A port. Shortest directed path length is three,
but the affine output first becomes one at tick six. Support is already present at
tick three. With the nonlinear equation it first becomes one at tick three. This is
an observed dependence on the model rule, not a learned improvement.

The nonlinear equation violates affine superposition at the readout in 8/12 references,
exactly the eight references with both original routes available. The affine equation
passes its superposition identity everywhere. A designed AND gate is not evidence of
learned deduction.

### Post-hoc state-separability diagnostic

A separate descriptive analysis of the retained traces (not a preregistered task
score) compares the four complete states produced by the four stimuli. In all nine
weak-BFS references, the four states remain distinct at every measured tick 0..128
under both equations. This includes the 512-node reference with an unreachable chosen
output: distinguishable internal states need not be observable at that output.

The sparse ranked-2048 controls are informative negative cases. At tick 128, seeds 17
and 43 have only two distinct stimulus-conditioned states under either equation;
seed 29 has four under affine parity but only three under the nonlinear equation.
Nonlinearity does not automatically preserve information better. None of these four-
stimulus observations is a measured learning capacity or a guarantee under distraction.

## Runner portability and retained failures

Two Thor service accounts have different HOME values and artifact access. One run
could read the original subset root while another could not. No existing source
permissions, ownership, sudo policy, or global machine configuration was changed.
An attempted read as the old owner was denied by existing sudo policy and was not
bypassed; that fallback was removed from the final code.

Authorized producer slots now make a new bounded read-only cache on the same host
under `/dev/shm/memorithm-v888-bool02-<receipt-sha256>`. Only the 97 required receipts,
node tables, edge tables and ports are copied, at most 128 MiB. Consumer independently
checks all hashes again. The raw Parquet, qualified large CSR and cut-edge artifacts
are not copied into this cache or uploaded as workflow artifacts. Preparation slots
that cannot read a source explicitly report ready=false; their successful scheduling
alone is not qualification. The mandatory consuming job must pass the full checks.

The effective execution protocol differs from the checked-in protocol only in input
location. Both are retained and compared. Checked-in canonical protocol SHA-256:
`8e9b25437297c28889fa2c4725142512910a2f2910bcae75645d00ffd78cce87`.
Effective canonical protocol SHA-256:
`29b86026a8c827cba9ae0327eb8f767115fe8d01376de0749a640f4a62db9b51`.

An earlier direct-source pass **35787051213**, source
`49696214c04da786490f9cdba2b2419c1e9cdf40`, also succeeded. Artifact **10720157477**,
ZIP SHA-256 `121c5620616d946fd64c543dfcb2f4333395ef0c0775c84245407b740219f1be`.
All 60 final traces, all case/port results and consumed identities match this earlier
run exactly. This is two executions on Thor, not independent biological replication.

The assistant container independently rehashed both archives, all 60 final compressed
trace payloads, the library and protocol; compared source identities with the retained
BOOL-0.2a receipts; recalculated aggregate counts; and compared the two complete result
sets. Those archive analyses are not additional Thor executions.

Initial compiler type-inference and subsequent runner-location failures remain in
GitHub. The final head was rerun; no test or scientific guard was disabled.

## Integration and continuation

SciRust #1510 targets master, not an intermediate branch. At this checkpoint it remains
open: scoped Thor qualification succeeded, but general CI 35787756716 is queued,
Workspace Rustdoc 35787756533 is running and SOUP 35787756498 is queued. Rustfmt diagnostic,
API lexicon and FLAT advisory passed. Refresh exact-head CI and mergeability before
integration; do not equate the scoped execution with complete repository CI.

Do not rebuild GAME-ENV1, GAME-IO1, DYN-REF1 or these source bindings. Port reachability
and source-bound Boolean impulse execution are now measured for this frozen panel.
Parent BOOL-0.2 remains active for null diversity/mixing and partition sensitivity;
full BOOL-0.3 also retains non-Boolean/reference and game-interface requirements.

Next executable application work is the current-observation encoder/readout binding
and persistent learned-state checkpoint, separately from transient activity reset.
Retain original-port failures as controls. Any structurally informed or multi-node
readout must be declared as a new matched-budget policy, not silently selected from
these observed successes. First learn only a bounded readout with recurrent parameters
fixed, then compare separately with internal plasticity. Use unseen episodes, frozen-
update, shuffled-feedback and parameter-reset controls. No learner or learning curve
has been executed here, and no protected final holdout is authorized.

Reusable graph-to-dynamics and influence diagnostics may inform SML-GENIUS and FLAT
sparse routing after their own qualified handoffs. No downstream default or API
promotion occurs in this slice. ITD V29.18, the existing game, raw BANC files, final-data
rules and deferred trading priority remain unchanged.
