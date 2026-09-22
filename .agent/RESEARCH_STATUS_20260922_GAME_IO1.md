# ITD / V888 — GAME-IO1 process-bridge checkpoint

Observed 2026-09-22. Author: Memorithm research pipeline.
Parallel application slice after GAME-ENV1. Core programme revision remains 2026-09-22.3: no neural milestone is declared complete by this transport result.

## Executed sources and host

- ITD implementation: PR #60, branch research/v888-game-process-io-v1, source `7edca8e40b715061104e3c33b19f6b1f4e998aad`.
- PR #60 targets the branch of PR #59, not main. Its base is `3637b1f3e4f18474d4e497eecda083e1cca449a6`.
- Thor wrapper: SciRust PR #1508, branch research/itd-game-io1-thor, source `39ebdd0c2589547eb0b453c6275a0832c3fb68ba`, target master.
- Successful Thor run: https://github.com/Memorithm/scirust/actions/runs/35741738443
- Runner: tarek-scirust-arm64-01; hostname tarek; aarch64; uid 994 github-runner; Rust 1.89.0; Python 3.12.3.
- Worker binary SHA-256: `f418fb06c190b986cc83a77eb07efe7b9d454533345ccc82c43ecfb880677a40`.
- Protocol canonical SHA-256: `3303427eff0a33760f8e6c183e9acb277efbb3494708bab9d4a8d21cc2069087`.
- Trace SHA-256: `51fd7aba7fcb11997a623ed01cdd30a9ae82366788340ac64da33ea939c6d186`.
- Artifact 10699683801, ZIP SHA-256 `87cf9aefc605410485e3b76554e7dad0286a6e79d15db0d88faaf5a6f81a2099`.

The artifact was retrieved and its ZIP digest, canonical protocol, traces and source-file hashes were recomputed independently in the assistant container. The retained Rust/Python sources match the locally written files. This is integrity evidence, not a signed build attestation or another Thor execution.

## Implemented behavior

The private game environment runs in a parent process. A trusted child receives only a versioned current-observation ASCII protocol over anonymous pipes. Administrative fixtures, prior clues, target, RNG seed and evaluation/training mode are not sent to the child. A monotonically increasing request sequence prevents accepting stale replies. Frame payload is at most 128 bytes, with one exchange in flight. No shell or inherited ambient environment is used; the working directory is initially empty.

The exchange deadline covers writing, flushing and reading through a dedicated I/O thread. Real sleeping child processes were terminated at the configured deadline. EOF, truncated/oversized/invalid frames, stale replies and early actions remain explicit failed episodes. Direct children are killed and waited on, channels closed and I/O threads joined; a cleanup failure aborts the batch.

Training feedback is transmitted only after the scored action; standard evaluation sends none. A failed transport does not receive another action opportunity. Feedback delivery is not learning.

## Qualification results

23 Rust unit methods passed (12 retained environment tests and 11 new frame/protocol tests). Eleven independent Python/process methods passed, including real 80 ms action-deadline tests, 1-second reset deadline, process crash, oversized/truncated output, stale response, environment canary, independent episodes, spawn failure and post-action feedback ordering.

The frozen panel has 264 administrative fixtures across memory, visible logic and combined memory/logic; lengths 0,1,4,16,32,64; all eight A/B/R tuples and two declared noise patterns (one empty sequence). Duplicate short patterns are intentionally retained. Two handwritten policies produce 528 episodes and 528 complete replays.

- Zero independent timeline/action/outcome/accounting mismatches.
- Semantic replay is exact. PID and elapsed time are explicitly excluded, so this is not byte-identical raw runtime tracing.
- All direct children were reaped and all transport threads joined. Linux /proc absence checks passed after returns.
- Exact and current-only workers received identical request sequences: SHA-256 `26e0d4a4266250c8c1042bc7d9056f97f9e54e137065f4b88f4a30f154a2264e` for each policy's full request panel.
- Exact control: 88/88 in each condition. Current-only: 44/88 memory, 88/88 visible logic, 44/88 combined.
- The previous GAME-ENV1 independent regression also passed: 984 fixtures, 5,904 control episodes and replay.
- Repository manifest verified 526 entries before and after. All 520 prior entries and frozen game.rs remain unchanged.

The process pilot interval was 2.4025395098142326 seconds, including both policies and replays, process startups, IPC, cleanup, traces and Python checks. It is not a neural-inference benchmark, memory measurement, energy result or speedup.

## Important limitations

Separate process memory, an empty working directory and cleared environment are NOT a filesystem/network/security sandbox. Workers must be trusted, single-process and must not spawn descendants. Escaped children, hostile same-user file access and OS CPU/RAM containment are not qualified. Exchange deadlines exclude OS spawn, termination and scheduling overhead; an outer qualification watchdog is separate.

Each episode starts a fresh worker. Persistent learned-checkpoint transfer is not implemented. Later learning integration must explicitly preserve declared learned parameters while resetting transient activity. The current diagnostic workers acknowledge feedback but do not learn. The healthy diagnostic tests use the separately spawned same executable; an independent healthy external model binary remains a consumer qualification task.

No BANC graph was read, no recurrent neural dynamics was executed, no learner was trained, and no topology advantage or growth mechanism was inferred. Administrative fixtures and audit traces are not candidate interfaces. Trading remains deferred.

## Integration and next work

PRs #60 and SciRust #1508 remain open at this checkpoint. Scoped Thor success does not mean repository-wide CI completion or main/master integration. ITD PR-associated general CI run 35741696869 was still in progress at the checkpoint; refresh it before reporting later status. No merge was performed.

Do not restart GAME-ENV1 or GAME-IO1. Retain BOOL-0.2b topology/port diagnostics and qualify the recurrent Rust reference dynamics next. Candidate integration then uses the public observation protocol, with explicit model-state/checkpoint semantics, trustworthy runtime isolation appropriate to the candidate, and separate learning evaluations. Preserve frozen-learning, shuffled-feedback and learned-parameter-reset controls. No existing holdout, automatic-merge, runtime-actuation or model-promotion authority is changed.
