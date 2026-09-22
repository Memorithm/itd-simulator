# ITD — issue audit and execution checkpoint, 2026-09-22

Scope: user-directed issue handling. This report distinguishes concrete software repairs from unfinished scientific series. It is not a new neural-learning or biological result.

## Integrated corrections

PR **#64** merged into main at **2026-09-22T20:07:16Z**.

- Prior main: `7ba33919d47232a093c882a8ee4b531ecc0f1aeb`.
- Tested candidate: `a4a64df8bf80953bbfd55739513806d2d7212898`.
- Resulting main commit: `8bb6448dec5835dfc99d44a8148c7bc795eea84a`.
- Candidate and merge tree: `96ff0686039ce71deb9968a8ecf0af414e96926c`.
- GitHub independently reports **#61, #62 and #63 closed, state_reason=completed** following the merge. They were not closed before integration.

### #61 — serialized roles and result guards

Plain `final` strings could bypass enum-identity checks in selection boundaries; a string `blocked` could bypass the no-observations invariant. Valid serialized roles/classes are now normalized before checks, unknown values fail, and common search freeze flags require real booleans. The repair applies to protocol, campaign and relevant Forge/NeuralOperator/auxiliary/TDI/NoiseLab/MAA adapters. MAA can still retain upstream frozen-final evidence; retention does not authorize selection or execution.

### #62 — evidence identity and recorded work

Results can now be checked against their actual campaign, and campaigns against the actual protocol and implementation. Supplying `protocol=` to the runner validates source roles, work unit and budget before evaluation. Restored runs recheck the same per-case and total reported-work constraints as live evaluation. Caller collections are copied to tuples so later list mutation does not change validated identity.

Compatibility boundary: omitted `protocol=` retains legacy metadata-only behavior. Identity digests are not signatures or authenticated approvals; recorded work is not OS CPU/RAM/time containment. Valid tuple-based V1 serialization is retained. Full persistence, cryptographic approval and input byte verification are separate tasks.

### #63 — undefined UQ metrics

Risk at zero coverage is `None`; false confidence without OOD samples is `None`. Actual measured zero remains 0. The integrator rejects undefined risk endpoints. Correctness/OOD labels reject truthy strings and numbers, accepting Python and NumPy booleans. Length checks support NumPy arrays, and stable scaled means avoid intermediate overflow of finite results. This is an intentional research-API correction, documented in `docs/itd3x/ITD_30_6_EVIDENCE_INTEGRITY.md`; historical outputs are not silently reinterpreted.

## Validation actually observed

GitHub-hosted Ubuntu/Python 3.12 qualification **35777138511**, helper source `e186c11f7704fe0cecb89b921bd8a3cb8a156dd5`, passed:

- canonical manifest: **565 paths**;
- Ruff;
- mypy: **160 source files**;
- **178 tests** across the ITD-series and protocol suites, including **60 added parametrized test cases**;
- no tracked source changes from tests;
- exact local/remote Git-tree and candidate patch agreement.

Artifact **10716428497**, ZIP SHA-256 `4d6848ef3d763388c91731a30931f0e890435d6aa368ddaac4cb1d792827ffc1`.

Complete candidate PR CI **35777422652** also finished successfully before merge: Python **3.11, 3.12 and 3.13**, full V29.18 validation, dependency audit and commit policy. All four jobs were inspected. A post-merge run, if present, is a separate execution and must be read rather than inferred from this result.

Local assistant-container checks: old-source regression panel 55 failures/28 passes, then 178 passing targeted/protocol tests after correction; representative old/new valid V1 serializations/fingerprints unchanged; all 565 manifest digests recalculated. The 55 failing cases include new API expectations and are not 55 distinct bugs. An extra full-local pytest attempt hit the tool time limit; its first failure was a missing local PYTHONPATH, not a changed numerical result, and the exact deterministic-process test passed when run with the repository environment. The full-local suite is NOT claimed passed. The complete locked-environment CI above is the full validation evidence.

The first helper qualification stopped on one Ruff import-formatting error. It was fixed without weakening the check and the final candidate was rerun. Helper files/workflows stayed on a repair branch; they are not part of #64. Staging created only unreferenced objects; the reviewed commit/branch/PR/merge were separate connector operations.

Preservation: all **562 original manifest paths retained**; **546 existing file digests unchanged**, 16 intentionally changed contract/test files, 3 added files. Final manifest SHA-256 `e9d49a31c35bcf5f03d9eb080b60aa7acfda64d1ca9a93733105dafc7c32e6e5`. No frozen V29.18, game/Rust implementation, dependency lock, CI rule or BANC source data changed. No Thor computation or neural training was performed for this issue repair.

## Eleven umbrella issues reviewed and updated

Each original issue received an individual dated comment separating integrated contracts from the remaining exit criteria. They remain OPEN deliberately; source-code integration does not complete an experiment programme.

| Issue | Verified implemented baseline | Remaining executable work |
|---|---|---|
| #26 ITD-35 | FLAT/MAA evidence adapters and structured reference controls | Source-bound mechanistic attention/operator comparisons, ablations and spectral qualifications; no hardware/superiority inference from metadata |
| #29 ITD-33 | Trajectory schema, normalized state deformation and non-final TDI adapter | Real trajectory comparisons, grouped uncertainty, interventions and separately owned adaptive semantics |
| #33 ITD-30 | Protocol/result/campaign/adapter/runner contracts, integrated conflict backlog; #61/#62 now repaired | Persistent artifact/result lifecycle, interrupted/blocked campaigns and separately authenticated approval/input verification |
| #34 ITD-31 | Representation accounting and directed transition planner | Actual measured SciRust formats, OOD transfer/path stability, conditional Elastic consumer qualification |
| #35 ITD-32 | Comparison ladder, NeuralOperator and auxiliary-supervision contracts | Actual Burgers/Darcy learning comparisons with no-auxiliary/random controls; learned local/graph/spectral structure |
| #36 ITD-34 | Calibration/risk curves; #63 now repaired | Matched shift/abstention campaigns, explicit denominator/coverage reporting, spatial uncertainty/error localization |
| #37 ITD-36 | Non-actuating decisions and shadow evaluation | Frozen-observation counterfactual policy replay, measured representation/precision transitions, later model/compute adaptation |
| #38 ITD-37 | NoiseLab provenance adapter | Executed perturbation-response maps and matched null/intervention tests, preserving raw evidence |
| #39 ITD-38 | Bounded Forge contract and repaired selection boundary | Actual development-only candidate search versus matched controls, then frozen independent evaluation |
| #40 ITD-39 | SciRust parity, Verify and Hub evidence contracts | Source-pinned oracle/parity execution and real dossier/orchestration integration; general primitive promotion only after qualification |
| #58 V888 | Previously qualified source/subset controls, game environment/process bridge and synthetic recurrent reference | BOOL-0.2b ports/control diagnostics, source-bound graph dynamics, game connection, learned checkpoint retention and unseen-episode learning |

The implemented baseline in this table was inspected on main 7ba33919 before this repair. The current correction adds input/evidence integrity, not demonstrations of downstream model performance. Resolve current upstream repository APIs and revisions when a consumer is actually connected.

## Resume without restarting completed work

Read this checkpoint with the existing bootstrap and machine programme. Do not reopen #61–63 or reconstruct the old conflicting PR chain. New implementation branches start from refreshed actual main, with one canonical manifest regenerated from all staged paths. Keep the agent roadmap out of main.

For the neural programme, the next dependency remains **V888-BOOL-0.2b**, followed by explicit graph-to-dynamics binding. Do not rebuild GAME-ENV1, GAME-IO1 or DYN-REF1. Readout learning, internal plasticity and structural adaptation must remain separate comparisons; simulated interventions are not biological growth evidence. Trading remains deferred.

The reviewed finite merge does not enable GitHub auto-merge or change standing deployment, final-data, model-promotion or runtime-actuation authority. Future scientific and integration decisions still require actual source, evidence and exact-head checks.
