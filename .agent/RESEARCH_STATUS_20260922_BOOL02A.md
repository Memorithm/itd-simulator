# ITD / V888 — checkpoint after BOOL-0.2a

Observed: 2026-09-22. Programme ledger revision: **2026-09-22.3**.
Previous checkpoints RESEARCH_STATUS_20260922_BOOL01.md and RESEARCH_STATUS_20260922.md remain unchanged. This is an execution/lifecycle update, not a software release or model-quality promotion.

## Completed scoped execution

V888-BOOL-0.2a completed the subset/control-invariant pilot on the Thor CPU channel.
Parent V888-BOOL-0.2 remains ACTIVE; null-ensemble diversity/mixing and partition/port sensitivity are not qualified.

- Run: https://github.com/Memorithm/scirust/actions/runs/35726122553
- Executed source: `b5e0f2a439d6b638a6df295a1cea7cda399c2cae`.
- Runner: `tarek-scirust-arm64-01`; hostname `tarek`; architecture aarch64; account ghrunner; Rust 1.89.0.
- 8 Rust test methods and 10 independent Python/process methods passed; synthetic tests include 12 seeds and both selection policies.
- 12 real-source cases: weak-neighbor BFS sizes 128/512/2048 for seeds 17/29/43, plus rank-only size 2048 for the same seeds.
- 5 graph arms per case: reference, edge-count, directed-degree, per-node reciprocal-degree and anatomical-region-block controls.
- 60 graphs generated and 60 complete replays; every output-file digest agrees.
- 48 control graphs differ from their respective reference; no unchanged real-data control occurred.
- Independent readback verified every selected internal pair/weight and every cut-edge record.
- All declared edge-count, degree, reciprocity and block-count constraints passed independent recounts.

Artifact **10693064194** ZIP SHA-256:
`f425f0d3b5052bc9d994d923d5f4e5458a54364d4c66a15b35bfa4e67edb1908`.
Protocol canonical SHA-256:
`4aeee08d94f6e1253d5ce73feab788efb2c5610620763585865d6966b255d2a1`.
Worker SHA-256:
`e9b5b208b88bc5f8d313c5591d11b7e829131c05437f430a638bc37671722028`.

The ZIP digest and protocol fingerprint were independently recomputed after retrieval. The twelve case records agree with the consolidated report. These are evidence-consistency checks, not a signed build attestation or second full-data run.

## Observations that change the next experiment

At 2048 selected nodes, weak-BFS subsets contain 19,903 / 131,570 / 65,739 internal pairs for seeds 17/29/43. Rank-only subsets contain 1,601 / 1,768 / 1,769 pairs and 923 / 892 / 930 isolated nodes. Sampling policy therefore changes graph structure substantially in this panel; these are descriptive observations, not a biological scaling law.

Both fixed input ports can reach the fixed readout in 8 of the 12 reference cases. Neither input reaches it for the weak-BFS 512-node seed-17 case and all three rank-only cases. No ports or seeds were replaced after observation. A weakly connected subgraph with no isolated nodes can still have unsuitable directed routes for the fixed I/O placement.

The edge-count-only controls have 437 / 377 / 363 isolated nodes in the three rank-only cases, whereas degree-preserving controls retain the source counts 923 / 892 / 930. An edge-count-only comparator cannot isolate detailed topology effects by itself.

Anatomical blocks contain two or three region labels in BFS samples and four in rank-only samples. These are metadata labels, not independently inferred functional modules or preserved modularity. All five arms use unit adjacency, with actual contact multiplicities retained in a separate table. No conductance, sign, delay or dynamics was inferred.

## Durable continuation

The next sub-slice inside V888-BOOL-0.2 is **0.2b**:

- quantify changed-edge fraction and between-chain/seed diversity as diagnostics, without presenting a finite chain as uniformly mixed;
- compare explicit anatomical and structural partition choices, with achieved matching constraints recorded;
- characterize directed reachability and fixed-port placement sensitivity before adding a task-dependent readout;
- retain the existing 0.2a observations, including sparse and disconnected cases;
- freeze new sampling/port hypotheses before observing a new functional campaign.

The first functional target remains V888-BOOL-1.1 delayed XOR, after the dynamics and causal-I/O gates. No task result or topology superiority is established. Artificial growth and developmental causality remain later, separate questions.

## Data and runtime

Input graph SHA-256 remains `385111a69cc8a1d748c0bdfd9b0b738c51fe83cde98f45762553435a2d15a2a4`.
Shared input root: `/mnt/nvme/github-runners/home/datasets/banc_v888`.
Runner-owned outputs: `/var/lib/github-runner/v888-research-runs/bool02-35726122553-1`.

Graph, prior accepted qualification and metadata were rehashed before and after the pilot. No source mutation or fresh dataset download. Full graph/subset/control/boundary data remain on Thor; artifacts contain compact reports, hashes, source code and test logs only.

The measured pilot interval was 64.21146608493291 seconds, including hashing, generation, replay and independent oracles. Python and largest-child high-water RSS counters both report 611,804 KiB; neither is a simultaneous whole-machine total nor an intrinsic isolated Rust memory benchmark. The 8 GiB address-space cap is configured, not measured consumption.

Initial runner attempt 35725633924 stopped before compilation because the new non-root runner had no rustc on PATH and a different HOME. Attempt 35725859724 was rejected during workflow validation. The successful source separates shared read-only data, runner-owned compiler installation and runner-owned output. No global permission changes or deletion of existing artifacts.

## Integration and evidence locations

New code: **SciRust PR #1506**, target master. Scoped successful CPU execution does not imply general CI completion or merge. Refresh exact-head checks and review state before any integration decision.

Pinned detailed result:
https://github.com/Memorithm/scirust/blob/7ed5ecc42096cdd19e766b89bfd62705408a2888/.agent/V888_BOOL_02A_RESULT_20260922.md

At this checkpoint SciRust #1502 was observed merged into master (`190157b9b736209536c48d476a45c4509623c691`), while #1505 was observed merged into its research branch (`a43910bdc0a32031dc23dcb7eb952ccc2d92415c`). Do not conflate these destinations. ITD-30.5 and unrelated PR integration work are not declared completed here.

## Programme validation

The updated machine programme retains 26 milestones and ten ITD families. Five strategy test methods, including 22 invalid-mutation subcases, passed in the assistant local container, not as a second Thor computation. Programme canonical SHA-256: `659db480e424e610850afe367aab6f89829e128d133738dd49962a9941d27c8d`.

The frozen ITD V29.18 boundary, negative historical findings and denials of automatic merge, final access, actuation and model promotion are unchanged. No consumer capability or ML maturity score is promoted.
