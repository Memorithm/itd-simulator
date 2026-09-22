# GAME-IO1: bounded causal process bridge

Research slice after GAME-ENV1. This is transport/lifecycle qualification, not V888 dynamics or learned task performance. Frozen `game.rs` is reused without modification.

## Executables and authority

`process_game.rs` hosts the private environment. A child process receives only current observations through anonymous stdin/stdout pipes. The child command has no shell, cleared ambient environment (only LC_ALL=C), an initially empty working directory and no inherited administrator stdin. Direct process address spaces are separate. This is NOT a filesystem/network/CPU/RAM sandbox: only trusted single-process workers are supported, no descendants or process escape. Raw data is not used.

CLI: `process-game --batch exact|current|early|hang|hang_reset|exit|truncated|oversize|stale|invalid|env_probe|pid_probe DEADLINE_MS EMPTY_DIRECTORY`. These diagnostic workers reuse the handwritten controls, not a neural model. `--external ABSOLUTE_EXECUTABLE DEADLINE_MS EMPTY_DIRECTORY` starts a separately supplied trusted worker with no arguments. The administrator provides six-field fixture lines to the parent only: condition A B R distractors-or-dash train|eval.

## Wire v1

ASCII, LF-terminated, at most 128 payload bytes, no CR, NUL or extra fields. A missing bit is `-`, not `0`. Only one request is in flight.

- `RESET 0 v1` -> `ACK 0 v1` (1 second startup-exchange budget).
- `OBS seq condition phase a b rule distractor` -> `ACT seq wait|0|1|missing`.
- After an action, and only in training mode on a usable transport: `FEEDBACK seq 0|1` -> `ACK seq`.

The sequence begins at 1 after reset, increments per request and cannot be reused. It exposes observation position but not fixture identity, future episode length or RNG seed. Private target/history/administrator fields are absent. Evaluation sends no feedback. One scored action remains final, including premature choices and protocol failures.

## Deadlines, failures and lifecycle

An I/O thread performs bounded write/flush/read while the parent uses a monotonic receive deadline. Thus a sleeping worker cannot block the environment indefinitely. EOF, partial frames, oversized output, invalid encoding, stale sequence and invalid action are explicit failed results. The response deadline covers the exchange, not OS spawn, process termination, scheduling or whole-experiment time. Parent elapsed time includes that overhead. The outer qualification has its own wall-clock watchdog.

On completion/failure, kill and wait on the DIRECT child; drop channels and join the transport thread. Cleanup failure aborts the batch rather than silently accumulating workers. This does not certify descendant containment. Worker stderr goes to null, avoiding an unread stderr pipe; external stderr diagnosis requires a separately bounded collector.

Each episode gets a fresh process and reset. Persistent learned checkpoint transfer is not yet implemented: training feedback delivery is not a claim of learning or preservation of learned parameters. A later version must distinguish transient reset from persistent parameter state explicitly.

## Qualification

Frozen panel: three conditions; all eight input/rule tuples; distractor lengths 0,1,4,16,32,64; all-zero and alternating sequences (only one empty sequence). Duplicate short patterns are retained. Exact and current-only workers each receive the identical wire sequence. Entire panel replay compares semantic fields; PID/timing are explicitly excluded. Tests exercise real hung workers, reset timeout, crash, truncation, oversized frames, stale responses, ambient-environment canary, independent episodes, feedback ordering and invalid administrator fixtures. Direct child PIDs are checked absent after return on Linux.

Counters are enqueued request bytes and received valid frame bytes; they are not network throughput, neural inference work or memory usage. Exact programmed success and current-only failure are controls, not V888 results. Parent BOOL-0.2, dynamics and learning gates remain unchanged. Trading remains deferred.
