# ITD Research Lab — durable research re-entry

## Latest integration checkpoint — read before repairing or integrating PRs

Read `.agent/MANIFEST_INTEGRATION_STACK_20260922.md` alongside the older
`.agent/PR_CONFLICT_REPAIR_20260922.md`. After #42 and #55 entered main, the remaining
manifests conflicted again. The ten remaining heads are now a tested cumulative
stack (#44 -> #45 -> #46 -> #47 -> #48 -> #49 -> #50 -> #52 -> #53 -> #56), all targeting
main. Source-preserving repairs and TEN sequential normal merge commits were rehearsed
successfully in run 35771215462. The top includes the entire batch, not only Hub.
Do not recreate independent repairs against the obsolete 21e034 snapshot. Refresh live
heads and CI, retain merge ancestry, and distinguish mergeable=true from full CI and
actual main integration. No automatic-merge authority or neural milestone was changed.

Core programme revision: **2026-09-22.3**. Engine lineage: **V30.0-alpha / ITD-3X**.
Application priority: **V888-GAME-FIRST-20260922**.
Latest independent reference evidence: **DYN-REF1**, observed 2026-09-22.
Latest application interface evidence: **GAME-IO1**, observed 2026-09-22.
These are scoped evidence observations, not a release or a validated V888 learner.

## Mandatory read order

On the existing `agent/ecosystem-roadmap` branch, read:

1. `.agent/ITD_SIMULATOR_ECOSYSTEM_ROADMAP.yaml` — authorization and ownership policy.
2. `.agent/ITD_RESEARCH_BOOTSTRAP.md` — this resumption procedure.
3. `.agent/V888_BOOL_PROGRAMME.json` — authoritative neural dependencies and exit criteria.
4. `.agent/V888_BOOL_RESEARCH_PROGRAMME.md` — scientific design and controls.
5. `.agent/V888_GAME_FIRST_20260922.md` — original first-game priority; its not-executed label is historical.
6. `.agent/RESEARCH_STATUS_20260922_DYN_REF1.md` — latest recurrent reference, synthetic circuits only.
7. `.agent/RESEARCH_STATUS_20260922_GAME_IO1.md` — game process bridge and direct-child lifecycle.
8. `.agent/RESEARCH_STATUS_20260922_GAME_ENV1.md` — game environment and handwritten controls.
9. `.agent/RESEARCH_STATUS_20260922_BOOL02A.md` — latest source-graph/control checkpoint.
10. `.agent/RESEARCH_STATUS_20260922_BOOL01.md` and `.agent/RESEARCH_STATUS_20260922.md` — preserved earlier observations.

The root AGENTS.md points to the policy file. Strategy stays off main. Do not merge
this branch, replace the frozen core or create an incompatible registry. Public
ITD-3X documents and default_itd3x_registry() are historical bootstrap definitions,
not the live execution ledger. Existing 30.x..39.x families and issues persist.

## Re-entry is evidence driven

Resolve actual default heads and relevant PR metadata before selecting work. Record
both source SHA and merge destination. Open PRs, temporary merge SHAs, research-branch
commits and main integration are distinct. ITD #60 was observed merged into #59's
research branch, not main. Earlier ITD #43 also merged into an intermediate branch.
SciRust #1502 was observed merged into master and #1505 into its research target.
Refresh live facts rather than assuming transitive integration or copying old PR status.

Validate the machine programme with validate_v888_programme.py and test_v888_programme.py
when it changes. They check consistency/fingerprints, not live evidence or authorization.
An eligible dependency grants neither final access nor runtime actuation. Independent
reference/environment results do not complete neural integration or learning milestones.

## Source/control work and remaining graph work

V888-BOOL-0.1 qualified source graph identity in Thor run 35717145115.
V888-BOOL-0.2a passed in run 35726122553 on source
`b5e0f2a439d6b638a6df295a1cea7cda399c2cae`: 12 subsets, 60 unit-adjacency graphs,
48 changed controls, independently verified invariants and byte-identical replays.
Sources were rehashed before/after. Code is in SciRust #1506; refresh integration.

**Parent V888-BOOL-0.2 remains active.** Finish **0.2b**: control diversity/mixing
diagnostics, anatomical versus structural partitions, and fixed-port reachability.
Retain sparse and unreachable cases; do not silently change ports or choose favorable
seeds. Invariant preservation does not prove uniform-null sampling or chain mixing.
Anatomical blocks are not independently identified functional modules.

## Recurrent reference: do not start the numerical core again

**DYN-REF1 is implemented and qualified on synthetic circuits.**
SciRust PR #1509, research/v888-dyn-ref1, source
`75f43ec35b1118c98b23bbde8fc8e1d6bfd42036`, passed Thor run **35761411608**.
The reusable Rust core is in scripts/v888_dyn01/recurrent.rs; driver.rs is only an
administrative differential-test surface, never the game learner interface.

Available reference families: discrete LIF, signed bounded integer integration,
affine Boolean parity, and nonlinear Boolean parity/AND. Explicit synchronous ticks,
delays 1..64, reset/refractory/clip rules, checked work/payload budgets and immutable
parameter versus transient-state separation are implemented. 16 Rust tests and
8 independent process methods passed. The 152-case panel covered 9,576 ticks and
58,832 neuron updates per pass, with zero oracle mismatches and exact trace replay.
The designed pulse-cycle retains activity for 128 tested updates; that is an oracle,
not a learned-memory claim or a result from the V888 graph.

The stage is a candidate for later scirust-sim reuse, not a new public API or crate.
It is fixed-step, scans all edges and retains numeric scratch even in Boolean mode.
No event-driven speedup, bit-packed memory, physiological calibration, game learning
or BANC model execution is established. Source and result identities are in the dated
checkpoint. PR #1509 was open and general CI queued at that checkpoint; refresh it.

DYN-REF1 is an independent preparation for **BOOL-0.3**, not completion of it.
Graph/port diagnostics, source-bound model integration and **BOOL-0.4** remain open.
First V888 functional target: **BOOL-1.1 delayed XOR**. ITD-30.5 foundation integration
remains separate. Do not change those statuses from a synthetic equation test.

## First application: memory and deduction game

**Do not reconstruct GAME-ENV1 or GAME-IO1.**

GAME-ENV1: ITD #59 source `3637b1f3e4f18474d4e497eecda083e1cca449a6` passed Thor
run 35733552596 using SciRust #1507 wrapper source
`76fe1522b053d66901a459876e63eb6571b0e27a`. Rust game, three conditions, exact/current-
only controls, 12 Rust tests, 9 independent methods, 984 fixtures, 5,904 episodes
and replay. Programmed control scores are not learning.

GAME-IO1: ITD #60 source `7edca8e40b715061104e3c33b19f6b1f4e998aad` passed Thor
run 35741738443 using SciRust #1508 wrapper source
`39ebdd0c2589547eb0b453c6275a0832c3fb68ba`. Only current observations enter the worker;
fixtures, hidden clues, targets and RNG seeds are not transmitted. Bounded frames,
request IDs, monotonic exchange deadlines and direct-child/thread cleanup are tested.
Training feedback follows the action; standard evaluation sends none. 23 Rust tests,
11 independent process methods, 528 episodes and semantic replay passed; previous
GAME-ENV1 regression passed too. PID/time are excluded from semantic replay.

The bridge is NOT a hostile-code filesystem/network/CPU/RAM sandbox. Workers must
be trusted single-process programs. Escaped descendants are not contained; spawn
and cleanup are outside the response deadline. Fresh worker per episode currently
means no learned-checkpoint transfer. Do not claim persistent learning from feedback
transport or confuse a reset method with trained checkpoint serialization.

Next computational steps: finish the outstanding graph/port diagnostics, bind a
source-identified graph and explicit model parameter mapping to the tested recurrent
core, then connect the candidate to the existing current-observation protocol.
Implement learned-state/checkpoint retention separately from transient reset. Measure
unseen-episode learning with frozen-update, shuffled-feedback and parameter-reset
controls. Separate readout learning, internal plasticity and topology adaptation.
A replay animation or synthetic circuit does not prove learning or topology advantage.

V888 trading, including simulation and exchange integration, remains deferred until
a separate user decision. This does not cancel unrelated ecosystem trading work.

## Execution procedure

Use Thor for V888 computation. Confirm actual channel, host, source and runner identity.
Never relabel assistant-container validation as Thor or ask the user for routine
commands when connected tools can execute. Missing access is an explicit blocker.

Runners may have different HOME values. Shared audited source root:
`/mnt/nvme/github-runners/home/datasets/banc_v888`. Prior subset outputs:
`/var/lib/github-runner/v888-research-runs/bool02-35726122553-1`. Recheck hashes,
paths and read permissions. New evidence is runner-owned under `$HOME/v888-research-runs`;
DYN-REF1 uses `dyn-ref1-35761411608-1` and does not access the BANC root.
Isolate per-run checkout/tools/output. Keep failures. Do not change global permissions
or delete artifacts to repair a HOME/tool mismatch.

Raw Parquet, qualified induced CSR and unit-adjacency arms are different scopes.
Preserve source hashes, detector version, exact integer IDs and every relevant cut
edge. No raw source deletion, in-place filtering or another connectome ingestion.

Inspect SciRust and consumer bootstraps before shared dependencies or API promotion.
Neural execution belongs in Rust with CPU references and independent oracles. Python
may support ingestion, metadata and independent checks, not replace the Rust engine.
ITD owns the game; SciRust hosts reusable computation without copying task logic into
numerical crates. A research module is not automatically a promoted shared product.

Retain hypotheses, exact source/data/protocol, tests, budgets, outcomes, limitations,
PR destination and next dependency for each slice. Update after observation, not a
promise. Preserve previous checkpoints and only advance core milestones on their
actual exit criteria. Generic reuse does not transfer model-default authority.

## Non-negotiable gates

ITD V29.18 and negative Missions 3–8 findings remain frozen in scope. No protected-final
selection, hidden history/targets, cross-trial state leakage, hardware/model-quality
claim from compilation, biological causality from adult allometry, or uniform-null
claim from graph switches. Negative/equivalent/inconclusive outcomes remain valid.

Existing ITD automatic-merge denial is preserved. No new final-study, default-model,
runtime-actuation or merge authority is created. Exact-head CI and applicable review
are separate from scoped Thor evidence. Never publish credentials, raw data or private
consumer implementation in shared handoffs or strategy files.
