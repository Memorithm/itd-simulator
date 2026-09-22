# ITD / V888 — two-door environment qualification

Observed: 2026-09-22. Independent application slice: GAME-ENV1.
The 26-milestone V888 research programme remains revision 2026-09-22.3; this is a
parallel environment/oracle result under V888-GAME-FIRST-20260922, not completion
of V888-BOOL-0.2b, 0.3, 0.4 or 1.1. Previous checkpoints remain unchanged.

## What was executed

The first memory/deduction game now has an executable Rust environment, a bounded
current-observation policy interface, exact handwritten sequential controls,
explicit failure scoring and an independent Python/process oracle. No connectome
was read and no parameter was trained.

- ITD code: PR #59, target main, source `3637b1f3e4f18474d4e497eecda083e1cca449a6`.
- Thor execution wrapper: SciRust PR #1507, target master, source `76fe1522b053d66901a459876e63eb6571b0e27a`.
- Successful exact-source Thor run: https://github.com/Memorithm/scirust/actions/runs/35733552596
- Observed runner `tarek-scirust-arm64-01`, hostname `tarek`, architecture aarch64,
  uid 994 (github-runner), Rust 1.89.0, Python 3.12.3.
- Worker SHA-256: `aa29c9e01f9263db1a76146edaad47e1d22cbf7aab8c94b00ab181b4ea570595`.
- Protocol canonical SHA-256: `e3485f7bde31dda5db65fd90a50111b8d0ad1955cda6ff31f356b1b659d32265`.
- Trace SHA-256: `5ee1c0c4662e0a69471f298ce59c345d4a3452b6b037bb0cbfd3bd4c5fc48f85`.
- Artifact 10696602035; ZIP SHA-256 `b7ea5e23844ffa3a110308e87f7f57db7bec1e20467fa1b4964aa729dd175818`.

After retrieval, archive, source-file, protocol and trace hashes were independently
recomputed. The traces contain 5,904 records. These are integrity checks, not signed
build attestations or a separate additional Thor computation.

## Qualification results

12 Rust unit tests and 9 independent Python/process test methods passed before
the pilot. The complete repository manifest verified all 520 tracked files, and
the execution left tracked sources unchanged.

The panel contains 984 complete administrative fixtures across three conditions,
seven distractor counts (0, 1, 2, 4, 8, 16, 32), all eight A/B/R combinations,
exhaustive short distractor strings and six declared long-delay patterns.
Six controls produce 5,904 policy episodes; the entire panel is then replayed,
and every trace byte is identical. The 984 fixtures are environment correctness
cases, not learned validation data or independent animal replicates.

| Condition | Handwritten exact memory control | Current-observation-only control |
|---|---:|---:|
| Memory only | 328 / 328 | 164 / 328 |
| Simultaneous logic | 328 / 328 | 328 / 328 |
| Memory plus logic | 328 / 328 | 164 / 328 |

All four fault controls (early, missing, invalid, timeout) produce explicit failed
outcomes in all 984 fixtures each. No failed trial is dropped and no second choice
can overwrite a failure. Independent timeline, action and outcome mismatch count: 0.
The 123 hidden-cue decision-observation groups are exactly label balanced.

Interpretation: the environment distinguishes tasks requiring observation history
from simultaneous logic. The exact control's 100% is programmed correctness, not
learning. The current-only control's 50% is expected on the balanced hidden-cue
panel, not a statement about a V888 model.

## Source and interface boundary

Code lives in ITD `research/v888_game/`; SciRust supplies only its existing Thor
execution channel with a pinned checkout. There is no duplicated task implementation
inside a SciRust numerical crate and no public shared API promotion.

The Policy interface receives condition, phase and currently visible optional bits.
It has no environment target, previous-clue buffer, episode ID or seed field.
The administrative batch fixture stream and complete audit traces DO contain the
information required to verify episodes; they are not candidate interfaces and must
never be forwarded to a learner. This is not a hostile-process sandbox.

The exact control uses two optional bits (2 direct Rust payload bytes on this build).
The zero-state current-observation control reports 0 payload bytes. Forced diagnostic
controls also count their String configuration storage (29 or 31 bytes); these
numbers exclude allocator overhead, dynamic dispatch, environment and trace memory.
The initial successful source run 35732761184 omitted that forced-control metadata;
final source 3637b1f fixes the accounting and was rerun on Thor. Scores are unchanged.

A delay d is the number of distractors AFTER cue A. A-to-choice separation is d+2
observations, B-to-choice separation is one. Do not call the pilot a learned
32-step memory result. Training feedback is supported after action but no training
was performed. Standard evaluation suppresses policy feedback.
Timeout is an explicit test action, not yet an external wall-clock timer.

The measured 0.6214219620451331-second pilot interval includes two complete process
runs, JSON traces and independent checks. It is not a neural inference speed,
whole-process memory or energy benchmark. No BANC file was downloaded or changed.

## Integration and durable continuation

Both PRs were open at this checkpoint. Exact-source Thor qualification is complete;
repository-wide CI/review and merge status must be refreshed separately. Existing
ITD automatic-merge denial is unchanged. No main or master merge is claimed.

The staging helper in ITD is restricted to this research branch. It created
unreferenced Git blobs for two reviewed fixes and the complete manifest; it did not
move any branch. The changes were inspected and applied with a separate fast-forward
research-branch commit. Frozen core sources were not changed.

Next: retain BOOL-0.2b diversity/partition/port diagnostics and qualify the recurrent
Rust dynamics. Then add a causal candidate adapter, real deadline enforcement and
learning trials. Compare readout-only learning, internal plasticity, frozen updates,
shuffled feedback and learned-parameter reset. Reset transient activity between
independent episodes while retaining only the learned parameters declared by the
protocol. Do not claim a V888 learning curve from this environment result.

The first application remains the memory/deduction game; V888 trading stays deferred.
No protected final holdout, runtime actuation, biological-growth result, topology
advantage, model default or ML maturity score has been promoted.
