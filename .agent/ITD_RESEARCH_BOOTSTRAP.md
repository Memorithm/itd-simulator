# ITD Research Lab — durable research re-entry

Programme revision: **2026-09-22.3**. Engine lineage: **V30.0-alpha / ITD-3X**.
This is a strategy/evidence revision, not a software release or a validated brain model.
Application priority: **V888-GAME-FIRST-20260922**.
Latest parallel application evidence: **GAME-ENV1**, observed 2026-09-22.

## Mandatory read order

On the existing `agent/ecosystem-roadmap` branch, read:

1. `.agent/ITD_SIMULATOR_ECOSYSTEM_ROADMAP.yaml` — ownership and authorization policy.
2. `.agent/ITD_RESEARCH_BOOTSTRAP.md` — this resumption procedure.
3. `.agent/V888_BOOL_PROGRAMME.json` — authoritative milestone dependencies and exit criteria.
4. `.agent/V888_BOOL_RESEARCH_PROGRAMME.md` — scientific design and comparison rules.
5. `.agent/V888_GAME_FIRST_20260922.md` — original user-approved game priority; its not-executed status is historical.
6. `.agent/RESEARCH_STATUS_20260922_GAME_ENV1.md` — latest parallel application execution: environment and controls only.
7. `.agent/RESEARCH_STATUS_20260922_BOOL02A.md` — latest source-graph/control execution checkpoint.
8. `.agent/RESEARCH_STATUS_20260922_BOOL01.md` and `.agent/RESEARCH_STATUS_20260922.md` — preserved earlier observations.

The root AGENTS.md already points to the policy file. Strategy stays off main; do not
merge that branch, replace the frozen core or create an incompatible product registry.
The public ITD-3X document and `default_itd3x_registry()` are historical bootstrap
definitions, not the current execution ledger. Existing 30.x..39.x families and issues persist.

## Re-entry is evidence driven

Resolve current default heads and relevant PR metadata before selecting work. Record
both the head SHA and merge destination. An open PR, temporary merge SHA, research-branch
commit and main integration are distinct. Earlier ITD #43 merged into #42's branch,
not main at that checkpoint. SciRust #1502 was subsequently observed merged into master;
#1505 into its research target. Refresh actual facts rather than assuming transitive integration.

Validate the machine programme using the adjacent stdlib-only `validate_v888_programme.py`
and `test_v888_programme.py`. The validator checks metadata consistency and computes
a canonical fingerprint; it cannot verify live evidence or authorize execution.
An eligible dependency is not permission to read a final holdout or actuate a runtime.

V888-BOOL-0.1 completed source/software graph qualification in Thor run 35717145115.
V888-BOOL-0.2a completed in Thor run 35726122553, source
`b5e0f2a439d6b638a6df295a1cea7cda399c2cae`: 12 subsets, 60 unit-adjacency graphs,
48 changed controls, exact declared invariants and byte-identical replays. Sources
were rehashed before/after. Code is in SciRust PR #1506; refresh its integration status.

**Parent V888-BOOL-0.2 remains active.** Next graph sub-slice: **0.2b**, covering
control diversity/mixing diagnostics, anatomical versus structural partition choice,
and fixed-port reachability/placement sensitivity. Retain sparse and unreachable
cases; do not silently move ports or select favorable seeds. Preserved invariants
are not uniform-null sampling or mixing proof. Anatomical blocks are not functional modules.

The first V888 functional target remains **V888-BOOL-1.1**, delayed XOR, after
qualified dynamics and causal I/O. Foundation integration **ITD-30.5** remains a
separate repair task. Do not infer that any prerequisite completed from GAME-ENV1.

## First application: memory and deduction game

**GAME-ENV1 is now implemented and qualified as an independent environment.**
Do not restart its construction or describe it as merely a proposal unless an actual
regression is identified. ITD PR #59 source `3637b1f3e4f18474d4e497eecda083e1cca449a6`
passed Thor run **35733552596** using SciRust's pinned execution wrapper in PR #1507
(source `76fe1522b053d66901a459876e63eb6571b0e27a`). Both PRs were open at the checkpoint.

The Rust game covers memory-only, simultaneous logic and combined hidden-cue tasks.
12 Rust unit tests and 9 independent process-test methods passed. 984 complete
fixtures times six diagnostic policies produced 5,904 episodes plus byte-identical
replay. The handwritten exact solver scored 328/328 per condition; the current-only
control scored 164/328 on memory and combined, 328/328 on visible logic.
These are programmed environment controls, NOT V888 learning results.

Next application work: connect only qualified recurrent dynamics through the current-
observation interface; add external deadline enforcement and tests against hidden
history/target leakage. Then measure learning on unseen episodes with frozen-learning,
shuffled-feedback and learned-parameter-reset controls. Separate readout learning,
internal plasticity and topology adaptation. Reset transient state independently
from persistent learned parameters. Audit fixtures and replay traces are never learner inputs.

V888 trading, including simulated trading and exchange integration, remains deferred
until a separate later user decision. This does not cancel unrelated trading projects.
No V888 model was run or trained during GAME-ENV1, and no raw dataset was accessed.

## Execution procedure

Use Thor for V888 computation. Confirm actual execution channel and runner/host identity
before claiming a machine operation. Do not ask the user to type routine commands.
If access is missing, record the blocker; do not claim another host's result as Thor.

Current runners can have different HOME values. Shared audited input root is
`/mnt/nvme/github-runners/home/datasets/banc_v888`; BOOL-0.2a outputs are under
`/var/lib/github-runner/v888-research-runs/bool02-35726122553-1`. Recheck paths and
hashes before reuse. GAME-ENV1 evidence is runner-owned under
`$HOME/v888-research-runs/game-env-35733552596-1`; it does not use the BANC data root.
Keep tools and outputs runner-owned, use isolated per-run checkout, and retain failures.
Never change global permissions or delete unrelated artifacts to resolve a tool/HOME mismatch.

Raw 19.73 GB Parquet, induced qualified CSR and unit-adjacency controls are different
representations/scopes. Preserve exact hashes, detector version, integer IDs, node
sets and cut edges. No in-place source filtering/deletion or new connectome ingestion.

Inspect SciRust primitives and consumer bootstraps before dependencies. New executable
dynamics belong in Rust with CPU reference and independent tests. Python is acceptable
for frozen reference, ingestion, metadata and independent oracles, not as a replacement
for the requested Rust neural engine. ITD owns the task; SciRust supplies execution
infrastructure without copying this task into a numerical library.

For every slice retain hypothesis, source/data/protocol identities, tests, resource
budget, outcome, limitations, PR destination and next dependency. Update observations,
not promises; preserve older checkpoints. The core programme JSON remains unchanged
by a parallel application result unless its actual milestone criteria are satisfied.

## Non-negotiable gates

ITD V29.18 and negative Missions 3–8 evidence stay unchanged. No protected-final tuning,
hidden answer/history, cross-trial leakage, biological causality inferred from adult
allometry, model quality inferred from source tests, or uniform-null claims from switches.

Existing ITD automatic-merge denial is preserved. No new final-study, default-model,
runtime-actuation or merge authority is created. Exact-head CI and applicable review
remain separate from a successful scoped Thor run. Never copy credentials, raw data or
private consumer implementation details into public handoffs or strategy files.
