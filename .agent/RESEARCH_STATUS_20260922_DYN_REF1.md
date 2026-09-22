# ITD / V888 — DYN-REF1 recurrent-reference checkpoint

Observed 2026-09-22. Author: Memorithm research pipeline.
Core programme remains revision 2026-09-22.3. This independent preparatory reference for BOOL-0.3 does not complete the V888 subset/control, game-integration or learning milestones. All earlier checkpoints remain unchanged.

## Implemented and executed

The first recurrent numerical core is now implemented in Rust and qualified on synthetic circuits. Three explicitly different families are available: discrete LIF, signed bounded integer integration and Boolean recurrence. Boolean recurrence has separate affine parity and nonlinear parity-plus-AND variants. No BANC graph was used and no learner was trained.

- Repository: Memorithm/scirust, PR #1509, target master.
- Research branch: research/v888-dyn-ref1.
- Executed source: `75f43ec35b1118c98b23bbde8fc8e1d6bfd42036`.
- Successful Thor CPU run: https://github.com/Memorithm/scirust/actions/runs/35761411608
- Observed runner: `tarek-scirust-arm64-01`; hostname `tarek`; architecture `aarch64`; uid 994, github-runner.
- Rust 1.89.0 (29483883e, 2025-08-04); Python 3.12.3.
- Worker SHA-256: `b716145988986bdc77790eab484749def379bbdce30332333ff2b1893b2196e7`.
- Protocol canonical SHA-256: `476f2737edf90173597a6d13299753f3fbf97653a00340608d04b13d47580de0`.
- Fixtures canonical SHA-256: `d252f9640e4bdc73275d4a6c35f9881f933e25c38b8dc3634c16709a7c34fd1a`.
- Trace SHA-256: `fc0d3054f7bb4096ff8f18bde571d9818d4a3e2e93c9f3153541fc3b9bf6bf20`.
- Artifact 10709639798; ZIP SHA-256: `dea5b888055feaace9f847345891703bdbd9dd8089250dab0bee0a1de9a05fe9`.

The archive, retained source, protocol, fixture and trace hashes were recomputed after retrieval in the assistant container. All 152 retained traces were compared again with the independent Python oracle locally. This was not a second Thor run or a signed build attestation.

## Results and meaning

16 Rust unit tests and 8 independent process-test methods passed. The latter include 13 invalid configuration/topology/budget subcases and five malformed/truncated/oversized record cases. The complete synthetic panel contains 152 cases: 32 seeded graph/drive scenarios across four variants, explicit delays of 1, 2, 7 and 64 updates, programmed recurrent pulse cycles and quiescent controls.

Per full panel pass: 9,576 network ticks and 58,832 neuron updates. These counts exclude replays and additional unit/process test executions. Every spike, integer state, refractory counter and work counter agrees exactly with the independent full-history target-gather oracle. Floating LIF state uses the frozen absolute and relative tolerances 1e-12. Observed mismatches: zero. Complete output traces are byte-identical on replay on this host/source/toolchain.

A deliberately constructed two-node recurrent cycle retains a circulating pulse for all 128 tested updates after a single initial stimulus. The quiescent counterpart stays silent. This demonstrates correct recurrent state propagation in a known circuit, NOT learned memory, a retention limit, or an observation about V888. Positive-delay tests verify absence of same-tick cascading. Reset removes delayed activity while preserving immutable model parameters and edges.

Integer tests verify truncation toward zero for negative potentials and clipping only AFTER signed contribution summation. Clipping, arriving active-edge signals, complete edge visits, spikes and refractory nodes are counted. Work-budget failure is rejected before observable state/history commits. The Boolean nonlinear term is explicit; it is not inferred from the connectome.

## Model and resource boundary

The stage consists of a reusable numerical module and a separate administrative test driver in scripts/v888_dyn01. It is a candidate for later scirust-sim integration, not a new public crate/API or a second task implementation. No existing game.rs, GAME-IO1 interface or product default was modified.

All models use synchronous fixed-step execution and scan every edge. They are not accelerated event schedulers. Delays are model update counts, not measured physiological time. Signs/weights/thresholds are supplied synthetic model assumptions, not contact multiplicities relabelled as conductance.

State/spike histories are stored in byte arrays, not packed bits. The reference keeps numeric scratch even in Boolean mode and counts it in its direct vector-payload bound. That bound excludes allocator overhead, Vec headers, stack, caller inputs, traces and OS memory. No process-memory, energy or GPU benchmark was performed. The recorded Python qualification interval, 0.5654316230211407 seconds, includes its tests, process calls, replays and oracle work; it is not a V888 inference speed.

No weights, thresholds or rules are trainable in this reference. Reset separates transient activity from immutable parameters but does not implement learned checkpoint persistence. No reward, readout or game candidate is attached.

## Failure history and integration

Initial run 35760925848 passed all 16 recurrent Rust tests but failed to compile the diagnostic driver due to an unmatched JSON format brace. Run 35761064943 compiled the Rust library/driver and passed those tests, then stopped at a missing closing bracket in the Python fixture encoder. Both were corrected without weakening any equation, test or protocol. Final run 35761411608 passed.

At the checkpoint PR #1509 is open. General PR-associated CI was queued and Workspace Rustdoc was running; other observed checks had passed. This report records exact-source Thor qualification, not general-CI completion or a master merge. No merge was performed.

The previously observed ITD #60 has now been verified merged into #59's research branch, not main. Do not infer transitive default-branch integration from that merge.

## Next implementation

Do not rebuild GAME-ENV1, GAME-IO1 or DYN-REF1. Retain and finish BOOL-0.2b graph-control diversity, partition and port-reachability diagnostics; bind any V888 input to the qualified source/subset hashes. Reuse the tested recurrent equations, with explicitly declared model parameter mapping, when constructing the first source-bound candidate.

Then connect a reviewed candidate through the existing current-observation protocol. Explicit learned-state/checkpoint retention, bounded readout training, internal plasticity, update-free controls, shuffled feedback and trained-parameter reset remain separate implementation and experimental steps. The first task remains the memory/deduction game and delayed XOR. A successful synthetic circuit does not authorize topology-advantage or learning claims.

V888 trading is still deferred. ITD V29.18, the 26-milestone ledger, raw external data, protected final-evaluation, default-model, runtime-actuation and existing ITD merge boundaries remain unchanged.
