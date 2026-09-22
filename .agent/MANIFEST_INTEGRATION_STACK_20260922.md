# ITD manifest integration stack — 2026-09-22

## Latest result: integration completed

Read `.agent/PR_INTEGRATION_COMPLETED_20260922_1926.md` before the historical staging record below. The ten previously open PRs #44, #45, #46, #47, #48, #49, #50, #52, #53 and #56 are now integrated into main `7ba33919d47232a093c882a8ee4b531ecc0f1aeb`. GitHub's open-PR endpoint returned an empty array after the final merge. The final tree is exactly `5d769c75e9b4ff55c57ef77a429264afc922876e`, the tested cumulative source.

Four PRs were merged individually after full candidate CI; #56 then integrated the remaining six as an explicitly disclosed cumulative normal merge after its complete CI 35771720841 passed. All constituent head commits remain ancestors. No PR was merely closed without integration, and no automatic-merge setting was enabled. The post-merge main run remains a separate observation recorded in the completion report.

Do not reapply these repairs or treat the older open/queued states below as current. Refresh actual main for new work. The remainder of this document preserves the pre-integration evidence.

---

Scope: user-requested resolution of recurring PR conflicts. This is not a neural research result or permission to auto-merge.

## Why the preceding repair did not last

The earlier repair aligned twelve independent PRs with main 21e03405aa19fbeae6d0c083635b7e6fdb306c24. PR #42 was subsequently merged at 933851d5e5b2de659b059728f4e41a9a1d85b3ea, and #55 at 747e32ad5992fd71256b8fbf309376a9427cb0d8. The remaining generated manifests conflicted again. A prior mergeable observation was therefore not sufficient evidence that the entire sequence could be integrated without further conflicts.

## Published correction

All ten remaining PR branches were updated by fast-forward-only ref changes. Targets remain main; no branch was deleted or force-pushed. All ten were then individually read through GitHub's PR endpoint and reported mergeable=true, with the expected new head and main 747e32ad5992fd71256b8fbf309376a9427cb0d8 as their target snapshot.

The heads are now a cumulative integration stack, not independent parallel additions:

| PR | Published head | Targeted tests at this cumulative step |
|---|---|---:|
| 44 | 2ca6f5167d0c58459ce6076ce0170bac91f6e08d | 62 |
| 45 | 25315012580ed851695cc8952a03c3ff0ead3b81 | 72 |
| 46 | bec74c7b9af72008053f0b815c899fa1ae145da1 | 77 |
| 47 | 71034d45be425a124359cf4d29a2681ca2198bb6 | 82 |
| 48 | 2569c7628be2b2c62763b49ecd146e7c40a08fc8 | 86 |
| 49 | 3ec90f6e815bdd938282d8ee9706e6f42fa5b79a | 90 |
| 50 | 50c713c739e25b7d6ee9f7e0663c6014c490eb7f | 94 |
| 52 | b4906cdba11bb427725f97ff74990ba6c3219472 | 99 |
| 53 | 213e52165a977bfeb6bc5c8c9edc69fb34eb3f56 | 104 |
| 56 | af79dfc5830899afe6f3b7c899b0ce724486e606 | 109 |

Each new head has its prior PR head and the preceding stack head as parents; the first uses current main as its second parent. The top (#56) therefore includes all ten feature patches. This expanded cumulative scope is disclosed in comments on every PR. It is not a Hub-only change while its predecessors remain outside main.

## Validation actually performed

GitHub-hosted Ubuntu/Python 3.12 run **35771215462**, staging source **8f71d2db6691a7dc7603f65aaad8661dd190da04**, completed successfully. This was NOT a Thor execution.

For every step:
- only MANIFEST.sha256 conflicts were automatically resolved; any source conflict would stop the procedure;
- the unchanged repository manifest checker regenerated and verified the complete index;
- the candidate tree exactly matched the union of the fixed main tree and original feature deltas;
- Ruff, incremental mypy and test_itd*.py passed;
- tests did not change tracked source files;
- remote blob/tree identities matched locally computed Git identities.

There were **875 successful test executions**, counting shared tests repeatedly; the final cumulative step contains **109 targeted tests**. These are not a substitute for full CI.

Crucially, all TEN normal merge commits were then rehearsed sequentially against an isolated local main: **zero conflicts**, expected source tree at every step, and valid manifest after every merge WITHOUT regenerating it again during the rehearsal.

Artifact **10713853286**, archive SHA-256 **5e98a8569e8a23aaff8f66131f7899b5556b508f99d595179f4305fbddf71b3b**, contains staged.json, summary.json, per-step manifests, patches and test logs plus sequential merge logs. The archive and manifests were rehashed independently in the assistant container. Each non-manifest incremental patch was compared with the previous repair's retained patch: identical for all ten PRs. This independent check is not a second CI/Thor run.

No feature algorithm, frozen V29.18 code, existing game, dataset, test, or manifest-verification rule was weakened or replaced. Only generated manifests were reconciled; existing patches and their ancestry were retained. The staging helper/workflows remain on the repair branch, not in the feature stack.

## Exact integration boundary and continuation

All ten PRs remain open at the direct-read checkpoint. No default-branch merge was performed. Normal merge commits preserve the tested stack ancestry; squash/rebase are NOT the integration sequence qualified here. Review cumulative scope and exact-head CI before integration. Unrelated future changes to main still require fresh verification; this report is not a guarantee about arbitrary future source changes.

At the last direct CI reads, #44's PR CI **35771544866** was in progress and #56's **35771720841** was queued. Do not describe complete CI as green from staging tests. A separate read-only status job **35771800860** was queued; its completion is not assumed. Direct GitHub PR reads, not that queued job, support the mergeable=true observation above.

For the next session, read this report alongside PR_CONFLICT_REPAIR_20260922.md. Do NOT recreate independent branch repairs against the old 21e034 snapshot. Resolve live main, each head and their ancestry. The prepared sequence is #44 -> #45 -> #46 -> #47 -> #48 -> #49 -> #50 -> #52 -> #53 -> #56, all targeting main. The final head includes the full batch, which must be made explicit in any integration decision.

No automatic-merge policy, holdout authorization, runtime actuation, model promotion, or neural milestone status was changed. Trading remains deferred. Preserve DYN-REF1, GAME-ENV1, GAME-IO1 and the outstanding BOOL-0.2b work.
