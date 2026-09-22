# ITD — conflict repair checkpoint, 2026-09-22

Author: Memorithm research pipeline. Scope: integration repair requested by the user, not a research or model-capability result.

## Published result

All twelve open ITD feature PRs were reconciled with main `21e03405aa19fbeae6d0c083635b7e6fdb306c24`, retaining their original branches and history, then retargeted from `research/itd-3x-bootstrap` to `main`.

Final read-only verification at **2026-09-22T18:17:38Z** records **12/12 mergeable=true**, the exact expected heads, zero commits behind main, and main itself as each comparison merge base. All twelve PRs remain open and unmerged. No default-branch ref was changed by this intervention.

| PR | Subject | Published head | Full CI observed at checkpoint |
|---|---|---|---|
| #42 | Adapter and campaign contracts | 4f374f9a1cac8f6141110173d0617f2f6d2685b9 | success, run 35765147344 |
| #44 | Representation accounting and graph | ed18b387ac24a8267ff9b8a3c88513d622ccd6dd | success, run 35765202548 |
| #45 | NeuralOperator and auxiliary supervision | 2ebd2db6d9df4fcab0039703ac58509a51eff6f5 | success, run 35765246832 |
| #46 | TDI trajectory adapter | b65e9df4c89678302af37bef56236bf6dcdefa7b | success, runs 35765341122 / 35765312883 |
| #47 | Calibration and selective prediction | d3b64d88e281511dcf472d8287d22d1c277a2eb4 | in progress, run 35765354924 |
| #48 | FLAT reference adapter | a9af1ffc46172171e9ceeb8168fd20b3e60895ce | in progress, run 35765396282 |
| #49 | Elastic shadow evaluation | 7860e37a933ec5150cf3c134a5546c65dc5336ac | in progress, run 35765462800 |
| #50 | NoiseLab adapter | 3229a839a4837ea37fac71c88dd0a1734e0a982a | in progress, run 35765504298 |
| #52 | SciRust ITD parity | 8141216f228768cae6e9ade73147aba847bd29bc | in progress, run 35765546200 |
| #53 | Multi-Algebra Attention adapter | 462a3b1a94b48ab7caa71978858436f352994342 | in progress, run 35765593589 |
| #55 | SciRust-Verify evidence | f6877a4dfc4e208edf52724bc62ed75430915a1a | queued, runs 35766110456 / 35766116829 |
| #56 | Hub orchestration | 5ffcc24e7dabffa5074370bb91ac6c81a170b539 | queued, run 35765705340 |

These are dated observations. Re-read exact heads, base and CI before a later integration decision. Mergeable does not mean all checks have passed or that default integration is complete.

## Diagnosis and resolution

The old feature PRs still targeted the historical bootstrap branch. Isolated merges against actual main identified MANIFEST.sha256 conflicts in all twelve candidates. Three also conflicted in source files:

- #44: itd_research/representation_strata.py;
- #47: itd_research/uq.py;
- #49: itd_research/adaptive_shadow.py.

Each of those three feature-file contents begins with the entire current main file byte for byte, then appends the proposed definitions. This was verified before keeping the full feature version. All other files were three-way merged. The complete manifest was regenerated with the unchanged repository checker, not resolved by blindly taking one side or dropping entries.

All 520 original manifest paths are retained. Except for the three explicitly reviewed append-only files and generated manifest, every original main file is unchanged. Every feature addition in the candidate diff matches the original PR source. No deletions, no frozen ITD V29.18 changes, no game-code modifications, no weakening of tests or scientific boundaries.

The already-stacked campaign runner in #42, transition graph in #44 and auxiliary-supervision additions in #45 are preserved. Their older intermediate merges are not erased or mistaken for main integration.

Each published correction is a merge commit with the previous PR head and the fixed main snapshot as parents. Branch updates were fast-forward only (force=false). No force push, PR replacement, branch deletion, or default-branch merge occurred.

For #55, GitHub initially retained a dirty flag even though its comparison reported behind_by=0 and main as merge_base. The merge commit c5c13581996cdcf16bc6fb92962d4189b286c7a9 was verified to have both expected parents. A subsequent same-tree commit f6877a4dfc4e208edf52724bc62ed75430915a1a refreshed checks without changing a source byte; GitHub then reported mergeable=true. Its tested tree remains 139306f610792cb81d8b5ebcd4f764c4c844c757.

## Validation and reproducible evidence

1. Initial read-only audit on Thor: SciRust run **35763604972**, source d6236320fbbd51ebd5b2e6343a53e9159d5a59f4, artifact **10710853423**. ZIP SHA-256: fcec4e55f6bdb18dbe931e09e868f3194e31009c0b9602a38d426aec8d1427af.
2. Candidate staging/validation on GitHub-hosted Ubuntu with Python 3.12 and the unchanged dependency lock: ITD run **35764678073**, source fcf5c7207d970e58e532b478bbcbf338d74ef36f, artifact **10711303282**. ZIP SHA-256: 4c9b9294fade2c2da061dda154e2f07f02e6be788702e614ddcb3bd724a601cc.
3. Final read-only GitHub head/merge-base/CI collection through Thor: SciRust run **35766195500**, source 15f04bb767fff0179c295eaec0bbdac1e7b55906, artifact **10712815054**. ZIP SHA-256: be69775ee2a3e8328efa81c2cc163cf791cc2e7a6f831fb0153ac7a90542148c.

For every candidate, MANIFEST verification, Ruff, the repository incremental mypy command and all test_itd*.py tests passed before publication. Test counts per PR in table order: 48, 48, 49, 44, 44, 43, 43, 43, 44, 44, 44, 44. Total **538 successful test executions**, including repeated shared tests; this is not 538 distinct tests.

Staging created only unreferenced blobs/trees. It did not move refs or merge PRs. Candidate tree hashes were matched to local git write-tree. Actual commits/ref updates/retargets were applied separately through GitHub connector calls after review.

The downloaded archives were SHA-256 verified in the assistant container. An independent local patch/manifest reconstruction checked all 12 staged candidate diffs, hash correctness, complete preservation of old paths and the three reviewed source exceptions. Those checks were not a second Thor computation. No BANC files were read or changed during this repair task.

The first four full CI results above include Python 3.11/3.12/3.13 jobs and commit policy. Other pending runs are not declared passed, and targeted staging tests are not a substitute for those complete checks.

## SciRust audit scope

Open SciRust PRs #1494, #1497, #1501, #1503, #1504, #1506, #1508 and #1509 were inspected against their reported base and current master. All eight merged locally without textual conflicts at the audited revisions. Some were marked unstable because of checks, not dirty because of Git conflicts. Their heads were not modified under this task. This is not a claim that their CI issues were repaired.

## Durable continuation

This checkpoint advances ITD-30.5 conflict-resolution work only. It does not complete main integration, consumer validation or a neural research milestone. Keep the existing research bootstrap, DYN-REF1, GAME-ENV1, GAME-IO1 and V888-BOOL-0.2b work in scope without rebuilding them.

Before integrating any repaired PR, recheck current main and exact-head CI. Since independent PRs all add entries to the same complete manifest, subsequent main integrations may require another manifest regeneration; never resolve it by discarding another PR's entries. Respect the existing no-automatic-merge rule and do not merge the agent roadmap into main.

Trading remains deferred. No final data access, model promotion, runtime actuation or biological conclusion was introduced.
