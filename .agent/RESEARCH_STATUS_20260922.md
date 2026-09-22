# ITD / V888 research checkpoint — 2026-09-22

This is a dated observation, not an assertion that branch heads or CI will remain unchanged.
Re-read live sources at the next session. Planning, implementation, branch merge, default-
branch integration, scoped validation and downstream qualification are separate states.

## ITD software

Observed main: `875337007cfcf5a1b2e7245f6e1831fa876fe868`.
ITD V29.18 is unchanged. V30.0-alpha is the research-engine lineage, not a certified
replacement numerical model.

- PR #41 is merged into main, merge `875337007cfcf5a1b2e7245f6e1831fa876fe868`.
- PR #42 is open; head `25656914e2f5305d5bbfd6fc4302ada0e3d994ff`; base is
  `research/itd-3x-bootstrap`, not main.
- PR #43 is merged INTO `research/itd-30-2-evidence-adapters`, merge
  `25656914e2f5305d5bbfd6fc4302ada0e3d994ff`. The campaign runner was not present at
  `itd_research/campaign_runner.py` on the observed main. Earlier wording that merely
  called #43 merged must not be interpreted as default-branch availability.
- PR #44 is open; head `08d5650e61defc4016d6df5f2249908eaf31af0e`; base is the bootstrap
  branch. Its integration and exact-head qualification remain work, not an achievement.

Sources: https://github.com/Memorithm/itd-simulator/pull/41,
https://github.com/Memorithm/itd-simulator/pull/42,
https://github.com/Memorithm/itd-simulator/pull/43,
https://github.com/Memorithm/itd-simulator/pull/44.
The static ITD registry is a programme declaration, not proof that all listed series run.

## V888 data evidence retained

Pinned audit:
https://github.com/Memorithm/scirust/blob/a1c0968b94b90b0fc0d3905126fad6491f777089/docs/V888_SYNAPSE_AUDIT_20260922.md

- Raw v3 synapses: 19,733,123,829 bytes, 198,816,365 rows.
- Raw SHA-256: `0dfb5cf89ba156d076beab2da38d87eaa63dcbe45d76f86b108570fb5b961dd0`.
- Raw GCS object generation: `1786578708197684`; not a developmental date.
- Metadata: 188,508 nodes; edgelist: 13,620,865 directed pairs.
- Both endpoints in metadata: 42,309,621 contacts; exact per-node incoming/outgoing
  totals agree with the v3 edgelist. Pairwise equality and synapse-ID uniqueness are
  not established by that check.
- 50,501 neurons have nonempty hemilineage strings. 259 distinct strings are not
  259 independently certified lineages. Grouped analysis retains missingness.

Successful scoped Thor runs: 35706848881 (phase 0), 35709233870 (full endpoint audit),
35710150870 (induced-node-total reconciliation). The successful runs are evidence of
those scopes, not evidence that a V888 Boolean model has learned a task.

## SciRust integration is still separate

PR #1501 remains open at `d4133656b88dc7be53d81cd682dd38d86f2d8777`.
PR #1502 remains open at `a1c0968b94b90b0fc0d3905126fad6491f777089`.
Source: https://github.com/Memorithm/scirust/pull/1501 and
https://github.com/Memorithm/scirust/pull/1502.
Do not treat a successful data workflow as completion of their repository-wide CI or
as publication of a stable Rust API. CI conclusions were not requalified by this
strategy update.

## Decision recorded today

The user approved V888-BOOL: recurrent Boolean/low-bit computation, controlled stimulation,
verified logical tasks, and artificial growth judged by measured function. Thor remains
the primary execution host; no manual user commands are required for normal operation.

The revised strategy contains 26 dependency-bound milestones. Only V888-DATA-0 is marked
completed, strictly for the retained audit. ITD-30.4 strategy maintenance is active; all
new Boolean/task/growth/consumer milestones remain planned. No newly validated biological
mechanism, task score, speedup or model-quality result is claimed.

Immediate implementation: V888-BOOL-0.1 graph identity/boundary qualification, in parallel
with ITD-30.5 integration diagnosis. First functional target: V888-BOOL-1.1 delayed XOR.
Follow progress in https://github.com/Memorithm/itd-simulator/issues/58.
