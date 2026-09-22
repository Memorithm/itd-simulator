# ITD Research Lab — durable research re-entry

Core programme revision: **2026-09-22.3**. Engine lineage: **V30.0-alpha / ITD-3X**.
Application priority: **V888-GAME-FIRST-20260922**.
Latest parallel application evidence: **GAME-IO1**, observed 2026-09-22.
These are strategy/evidence observations, not a software release or validated brain model.

## Mandatory read order

On the existing `agent/ecosystem-roadmap` branch, read:

1. `.agent/ITD_SIMULATOR_ECOSYSTEM_ROADMAP.yaml` — ownership and authorization policy.
2. `.agent/ITD_RESEARCH_BOOTSTRAP.md` — this resumption procedure.
3. `.agent/V888_BOOL_PROGRAMME.json` — authoritative neural milestone dependencies and exit criteria.
4. `.agent/V888_BOOL_RESEARCH_PROGRAMME.md` — scientific design and comparison rules.
5. `.agent/V888_GAME_FIRST_20260922.md` — original game priority; its not-executed label is historical.
6. `.agent/RESEARCH_STATUS_20260922_GAME_IO1.md` — latest application execution: process bridge and direct-child lifecycle only.
7. `.agent/RESEARCH_STATUS_20260922_GAME_ENV1.md` — preserved environment/control qualification.
8. `.agent/RESEARCH_STATUS_20260922_BOOL02A.md` — latest source-graph/control checkpoint.
9. `.agent/RESEARCH_STATUS_20260922_BOOL01.md` and `.agent/RESEARCH_STATUS_20260922.md` — preserved earlier observations.

The root AGENTS.md points to the policy file. Strategy stays off main; do not merge
that branch, replace the frozen core or create an incompatible registry. Public
ITD-3X documents and default_itd3x_registry() are historical bootstrap definitions,
not the live execution ledger. Existing 30.x..39.x families and issues persist.

## Re-entry is evidence driven

Resolve real default heads and relevant PR metadata before selecting work. Record
both head SHA and merge destination. Open PRs, temporary merge SHAs, research-branch
commits and main integration are distinct. Earlier ITD #43 merged into #42's branch,
not main at that checkpoint. SciRust #1502 was observed merged into master and #1505
into its research target. Never assume transitive integration; refresh actual facts.

Validate the machine programme with adjacent validate_v888_programme.py and
test_v888_programme.py when it changes. They check consistency and fingerprints,
not external execution or authority. An eligible dependency grants neither final
holdout access nor runtime actuation. Parallel game results do not complete neural
milestones merely because the infrastructure now executes.

## Qualified source/control work and remaining graph work

V888-BOOL-0.1 qualified the source graph in Thor run 35717145115.
V888-BOOL-0.2a passed in run 35726122553 on
`b5e0f2a439d6b638a6df295a1cea7cda399c2cae`: 12 subsets, 60 unit-adjacency graphs,
48 changed controls, verified declared invariants and byte-identical replays.
Sources were rehashed before/after; code is in SciRust #1506. Refresh integration.

**Parent V888-BOOL-0.2 remains active.** Next graph sub-slice is **0.2b**: control
diversity/mixing diagnostics, anatomical versus structural partitions and fixed-port
reachability/placement sensitivity. Retain sparse and unreachable cases. Do not move
ports or select favorable seeds silently. Preserved invariants are not uniform-null
sampling or mixing proof; anatomical blocks are not inferred functional modules.

V888-BOOL-0.3 recurrent dynamics and 0.4 neural causal-I/O qualification remain open.
The first V888 functional target is 1.1 delayed XOR, not yet an observed result.
Foundation integration ITD-30.5 remains separate; game infrastructure does not finish it.

## First application: memory and deduction game

**Do not reconstruct GAME-ENV1 or GAME-IO1 from scratch.**

GAME-ENV1: ITD #59 source `3637b1f3e4f18474d4e497eecda083e1cca449a6` passed Thor
run 35733552596 using SciRust #1507 wrapper source
`76fe1522b053d66901a459876e63eb6571b0e27a`. Rust environment, exact and current-only
controls, three diagnostic conditions, 12 Rust tests, 9 independent methods, 984
fixtures and 5,904 control episodes plus replay. Programmed control scores are not learning.

GAME-IO1: ITD #60 source `7edca8e40b715061104e3c33b19f6b1f4e998aad` passed Thor
run **35741738443**, through SciRust #1508 wrapper
`39ebdd0c2589547eb0b453c6275a0832c3fb68ba`. The bridge transmits only current
observations to a separate trusted worker; administrative input and audit traces are
not worker inputs. It enforces bounded versioned frames, request identities and a
real exchange deadline, keeps failed episodes in the denominator, and reaps direct
children/joins I/O threads. Training feedback follows action; evaluation sends none.

23 Rust tests (12 existing and 11 new), 11 independent process tests, 264 fixtures,
528 policy episodes and 528 semantic replays passed. PID/timing are excluded from
semantic replay. GAME-ENV1 regression also passed. These are infrastructure and
handwritten-control results: no connectome, neural dynamics or learning was executed.

PR #60 targets #59's branch, NOT main. SciRust #1508 targets master. PRs were open
at the checkpoint; source-pinned Thor success and general CI/review/merge are separate.
Read the dated IO1 report for hashes, limitations and the latest observed CI state.

The process bridge is NOT a hostile-code filesystem/network/CPU/RAM sandbox. Workers
must be trusted and single-process; descendant isolation is not provided. The response
deadline excludes OS spawn and cleanup. Each episode starts a fresh process; persistent
learned-checkpoint transfer is not implemented. Never describe post-action feedback
transport as learning or claim trained parameters survive that fresh-process reset.

Next application work: qualify recurrent Rust reference dynamics and the intended
consumer, then add explicit model-state/checkpoint retention and appropriate worker
isolation. Preserve separate transient-state reset and persistent learned parameters.
Use the existing observation protocol rather than forwarding fixtures/history/targets.
Measure unseen-episode learning with frozen-update, shuffled-feedback and trained-
parameter-reset controls. Separate readout learning, internal plasticity and topology
adaptation. A replay animation is not an attribution or learning result.

V888 trading, including simulation and exchange integration, remains deferred until
a separate later user decision. This does not cancel unrelated ecosystem trading work.

## Execution procedure

Use Thor for V888 computation. Confirm actual channel, source and runner identity;
never relabel local-container execution as Thor or ask the user for routine commands
when connected tools can execute. Missing access is a reported blocker, not a claim.

Runners can have different HOME values. Shared audited input root is
`/mnt/nvme/github-runners/home/datasets/banc_v888`; BOOL-0.2a outputs are under
`/var/lib/github-runner/v888-research-runs/bool02-35726122553-1`. Recheck source hashes,
paths and read permissions before reuse. Application evidence is runner-owned under
`$HOME/v888-research-runs/game-env-35733552596-1` and
`$HOME/v888-research-runs/game-io1-35741738443-1`. Game qualifications do not access BANC.
Keep tools/output runner-owned, isolate per-run checkouts and preserve failed evidence.
Do not fix HOME/tool mismatches by changing global permissions or deleting artifacts.

Raw 19.73 GB Parquet, qualified induced CSR and unit-adjacency controls are different
scopes. Preserve hashes, detector version, integer IDs, node sets and every relevant
cut edge. No raw source deletion/in-place filtering or another connectome ingestion.

Inspect SciRust primitives and consumer bootstraps before dependencies. Executable
neural dynamics belong in Rust with CPU references and independent oracles. Python
may support frozen reference, ingestion, metadata and independent checks; it is not
a substitute for the requested Rust neural engine. ITD owns the game. SciRust's
existing Thor channel does not justify copying task logic into its numerical crates.
The current domain-neutral transport module is research staging, not a promoted shared API.

For each slice retain hypothesis, identities, tests, budgets, outcomes, limitations,
PR target and next dependency. Update after observations, never promises. Preserve
older checkpoints and change core milestone status only when its criteria are met.

## Non-negotiable gates

ITD V29.18 and negative Missions 3–8 evidence stay unchanged. No protected-final
selection, target/history leakage, cross-trial state leakage, hardware/model-quality
claims from compilation, biological causality from adult allometry, or uniform-null
claims from switches. Negative/equivalent/inconclusive outcomes remain first class.

ITD's existing automatic-merge denial is preserved. No new final-study, default-model,
runtime-actuation or merge authority is created. Exact-head CI and applicable review
remain separate from scoped Thor evidence. Never publish credentials, raw data or
private consumer implementation in shared strategy or handoff documents.
