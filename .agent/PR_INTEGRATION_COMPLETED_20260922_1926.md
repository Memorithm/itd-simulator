# ITD — completed PR integration, 2026-09-22

Author: Memorithm integration pipeline. Scope: user-requested repair and integration, not a neural research result.

## Final observed result

After the final merge at 2026-09-22T19:26:43Z, GitHub's live `pulls?state=open&per_page=100` endpoint returned an empty array. The ten previously open PRs are integrated: #44, #45, #46, #47, #48, #49, #50, #52, #53 and #56. Closed-PR records confirm `merged=true` for the constituent PRs, including the originally reported #48. They were not merely closed or left with an old mergeable flag.

Final main: `7ba33919d47232a093c882a8ee4b531ecc0f1aeb`.
Final Git tree: `5d769c75e9b4ff55c57ef77a429264afc922876e`.
This is exactly the validated final cumulative tree, verified again from the live main branch after integration.

## Actual merge operations

| Direct PR merge | Successful complete candidate CI | Resulting main commit |
|---|---|---|
| #44 | push run 35771542001 | 3dad5dbb06a5fa48353995ec6e0cb6001b198f6e |
| #45 | push run 35771556308 | 70fece43f2f9dc43a00f05fc9ce837b671609e98 |
| #46 | push run 35771571145 | 96824f63659416d731e2fd449c9fddca5eb00fad |
| #47 | push run 35771598143 | 3bbf734d251c7740e00ed389fc01ee437de84a3e |
| #56, remaining cumulative scope | PR run 35771720841 | 7ba33919d47232a093c882a8ee4b531ecc0f1aeb |

The last candidate, `af79dfc5830899afe6f3b7c899b0ce724486e606`, includes #48, #49, #50, #52, #53 and #56 after the first four integrations. That expanded scope was stated in #56's description before merging. A normal merge retains their head commits as ancestors; GitHub consequently marked those constituent PRs merged. There were five direct merge API operations in this execution, not ten separately invoked merges.

All direct merge calls used the expected candidate head SHA and merge method `merge`. No squash, rebase, force-push, branch deletion, manual PR closure or auto-merge setting was used. Concurrent source-branch updates were detected: two non-fast-forward writes were rejected, their verified equivalent cumulative commits were retained, and the unused newly created commits were not substituted for them.

## Validation and preservation

The complete final candidate CI passed Python 3.11, 3.12 and 3.13, full V29.18 validation, the dependency audit and commit policy. This qualifies the cumulative source content. It does not assert that every redundant or intermediate push/PR run had finished before the aggregate integration.

Staging run 35771327552, source b545da29337dbc3fa29d125678c4c9517e978073, regenerated manifests with the unchanged repository checker and verified the exact union of original feature deltas. Only MANIFEST.sha256 conflicts were allowed; any source conflict would stop staging. Ruff, mypy and cumulative test_itd*.py tests passed at all ten steps: 875 successful executions including repeated common tests; 109 targeted tests at the final step.

An independently inspected rehearsal in run 35771215462, source 8f71d2db6691a7dc7603f65aaad8661dd190da04, also verified all ten sequential normal merges without conflicts or additional manifest rewriting. Both staging runs produced the same ten candidate trees and manifests.

In the assistant container, archived source hashes were checked, every staged patch was reversed in sequence back to the exact starting main tree, and the repository manifest checker passed after every reverse step. All 562 final file digests were also recalculated. These local checks are not Thor executions.

Starting main was 747e32ad5992fd71256b8fbf309376a9427cb0d8, after #42 and #55, with 529 manifest entries. The final manifest has 562 entries and SHA-256 `0a52a5246118b49eec68fcabb26b8d1397f861bc637721bd6cde1df704ad6b2f`. No old path was discarded; proposed source changes were preserved rather than rewritten to silence conflicts. Frozen V29.18 and existing game sources are unchanged by the repair. No BANC data was read or modified.

Verified evidence archives:
- run 35771327552, artifact 10714715881, SHA-256 `44df14675f123822b1c79694921be6cbf0ee3abb90bc0d161b772de3851b4aa7`;
- run 35771215462, artifact 10713853286, SHA-256 `5e98a8569e8a23aaff8f66131f7899b5556b508f99d595179f4305fbddf71b3b`.

## Continuation

The post-merge main CI run 35773833596 was in progress at this checkpoint; its result is not inferred from the successful pre-merge candidate CI. The main tree itself matches the tested candidate exactly.

This closes the reported recurring-conflict backlog at the observed revision. Do not reopen or reapply these already-integrated feature PRs. New work must start from refreshed actual main, not the obsolete independent repair branches. Preserve the historical MANIFEST_INTEGRATION_STACK_20260922.md and PR_CONFLICT_REPAIR_20260922.md reports as dated observations.

The research programme, DYN-REF1, GAME-ENV1, GAME-IO1, outstanding V888-BOOL-0.2b work, frozen scientific lineage, final-data rules and deferred trading priority are unchanged. No standing automatic-merge, deployment, actuation or model-promotion authority is created by this user-directed integration.
