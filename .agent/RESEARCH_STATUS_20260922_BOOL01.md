# ITD / V888 — execution checkpoint after BOOL-0.1

Observed: 2026-09-22. Programme ledger revision: **2026-09-22.2**.
The scientific design in V888_BOOL_RESEARCH_PROGRAMME.md remains revision 2026-09-22.1; this is an evidence/lifecycle update, not a changed task hypothesis or software release.
Previous checkpoint: RESEARCH_STATUS_20260922.md, retained unchanged.

## Completed on the Thor-labelled ARM64 execution channel

**V888-BOOL-0.1 completed source/software graph qualification.**

- Run: https://github.com/Memorithm/scirust/actions/runs/35717145115
- Executed source: `d61ffb6a79ebe975c1d867ad1a728fd01126fde0`.
- Observed runner: `tarek-scirust-arm64-01`; hostname `tarek`; architecture `aarch64`; Rust 1.89.0.
- Full raw endpoint records read: 198,816,365.
- Metadata nodes: 188,508.
- Directed reference pairs: 13,620,865.
- Induced contacts: 42,309,621.
- Mismatching directed pair multiplicities: **0**.
- Unexpected induced-pair records: **0**.
- Seven Rust tests and eight independent Python/process/Arrow/readback methods passed, including twelve seeded random-multiset controls.
- Canonical CSR: 166,466,540 bytes; SHA-256 `385111a69cc8a1d748c0bdfd9b0b738c51fe83cde98f45762553435a2d15a2a4`.
- Graph/source/filter identity: `3cfbed6392a097865147ac08fae65f36a986b2ba6d386b1f5d61b9cfbefd1dd9`.
- Node-map SHA-256: `eaa481b3aef42f63fb9e2e8f9c27d1405c073c54d11cbcd656ca9432904f425a`.
- Artifact 10689412746; ZIP SHA-256 `f6758eb1ebc8e540703134433804b3317502222abcff99509c11b1cc053368f3`.

The artifact ZIP digest, canonical graph-identity fingerprint and canonical protocol fingerprint were independently recomputed after retrieval. Raw source hashes also matched the preserved Phase-0 manifest. This is not a signed build attestation.

The earlier V888-DATA-0 record remains an accurate historical node-total-only result. BOOL-0.1 is the new, stronger pairwise result; do not erase or silently reinterpret the older audit.

## Runtime and data preservation

The qualified graph resides under `$HOME/datasets/banc_v888/analysis/bool01-35717145115-1/graph.csr` on the execution host. The process resolved this path to `/ota_keep/mnt-nvme-r38.4/github-runners/home/datasets/banc_v888/analysis/bool01-35717145115-1/graph.csr`. Verify the graph hash and actual host/path before reuse.

The raw 19,733,123,829-byte Parquet stays external and unchanged. The CSR is an induced graph with fewer fields, not a lossless compression of the entire raw table. No new raw dataset was downloaded.

The qualification interval was 234.63493113406003 seconds. Rust child peak RSS was 645,932 KiB and Python peak RSS 761,924 KiB; these are separate process maxima, not simultaneous machine-wide memory, energy or a speedup comparison.

First run 35716816008 was blocked at checkout by a non-writable pre-existing artifact. Its tests and raw scan did not run. Unique per-run checkout removed the collision without deleting that artifact or changing global permissions.

## Actual code integration

Implementation and result are on **SciRust PR #1505**, targeting `research/v888-growth-thor-20260922`, the branch of #1502. This is not a claim of integration into master. Required final-head CI and applicable review/merge policies remain separate from the scoped successful Thor run.

Pinned report: https://github.com/Memorithm/scirust/blob/1d60f1a3811902ade528b6e70f69d7344b79ebd8/docs/V888_BOOL_0_1_RESULT_20260922.md

Earlier ITD PR #43 merged into the branch of #42 rather than main. ITD-30.5 remains a separate integration repair; this execution does not declare that repair or any unrelated PR complete. Refresh actual heads before using those foundations.

## Next implementation, not a running job

**V888-BOOL-0.2: deterministic subsets and topology controls.**

Use the qualified graph identity above, preserve original node IDs, record seed/sampling policy and every cut boundary edge, then validate the invariants achieved by edge-count, directed-degree, reciprocity and module-matched controls. Fix input/output placement, state/readout and resource budgets across comparison arms. Do not claim a matched control solely from the generator name.

The first functional target remains V888-BOOL-1.1, delayed XOR, after subset, dynamic and causal I/O gates. No Boolean-task result, topology advantage, physiological reconstruction, growth mechanism, final holdout, runtime actuation or model/default promotion is established by this checkpoint.

## Strategy validation

The updated programme still has 26 milestones and ten ITD families. Five stdlib-only strategy test methods, including 22 invalid-mutation subcases, passed in the assistant's local validation container, not as an additional Thor simulation. Canonical programme SHA-256: `6942c511df1f81727c6d0c84e66529b8563be1149d7cc30de9b148c8d5e3a82c`.

The frozen ITD V29.18 boundary and explicit denials of automatic merge, final access, actuation and model promotion are unchanged.
