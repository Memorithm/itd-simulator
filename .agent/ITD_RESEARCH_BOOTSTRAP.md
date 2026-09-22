# ITD Research Lab — durable research re-entry

Programme revision: **2026-09-22.3**. Engine lineage: **V30.0-alpha / ITD-3X**.
This is a strategy/evidence revision, not a software release or a validated brain model.

## Mandatory read order

On the existing `agent/ecosystem-roadmap` branch, read:

1. `.agent/ITD_SIMULATOR_ECOSYSTEM_ROADMAP.yaml` — ownership and authorization policy.
2. `.agent/ITD_RESEARCH_BOOTSTRAP.md` — this resumption procedure.
3. `.agent/V888_BOOL_PROGRAMME.json` — authoritative milestone dependencies and exit criteria.
4. `.agent/V888_BOOL_RESEARCH_PROGRAMME.md` — scientific design and comparison rules.
5. `.agent/RESEARCH_STATUS_20260922_BOOL02A.md` — latest scoped execution observation.
6. `.agent/RESEARCH_STATUS_20260922_BOOL01.md` and `.agent/RESEARCH_STATUS_20260922.md` — preserved earlier checkpoints, not live state.

The root AGENTS.md already points to the policy file. Strategy stays off main; do not
merge that branch, replace the frozen core or create an incompatible product registry.
The public ITD-3X document and `default_itd3x_registry()` are historical bootstrap
definitions, not the current execution ledger. Existing 30.x..39.x families and issues persist.

## Re-entry is evidence driven

Resolve current default heads and relevant PR metadata before selecting work. Record
both the head SHA and merge destination. An open PR, temporary merge SHA, research-branch
commit and main integration are distinct. Earlier ITD #43 merged into #42's branch,
not main at that checkpoint. SciRust #1502 has since been observed merged into master;
#1505 merged into its research target. Refresh these facts rather than assuming transitive integration.

Validate the machine programme using the adjacent stdlib-only `validate_v888_programme.py`
and `test_v888_programme.py`. The validator checks metadata consistency and computes
a canonical fingerprint; it cannot verify live evidence or authorize execution.
An eligible dependency is not permission to read a final holdout or actuate a runtime.

V888-BOOL-0.1 completed source/software graph qualification in Thor run 35717145115.
V888-BOOL-0.2a completed in Thor run **35726122553**, source
`b5e0f2a439d6b638a6df295a1cea7cda399c2cae`: 12 source subsets, 60 unit-adjacency
reference/control graphs, 48 changed controls, exact declared invariants and byte-identical
replays. The graph, accepted qualification envelope and metadata were rehashed before/after.
Code is in SciRust PR #1506; a successful research run does not establish full CI or merge.

**Parent V888-BOOL-0.2 remains active.** The next sub-slice is **0.2b**: control diversity
and mixing diagnostics, anatomical versus structural partition choice, and fixed-port
reachability/placement sensitivity. The pilot found sparse rank-only subsets and some
readout ports unreachable from their inputs. Retain these cases; do not move ports or
select favorable seeds silently. Changed edges plus preserved invariants are not a
uniform null-ensemble or mixing proof. Anatomical region blocks are not functional modules.

The first functional target remains **V888-BOOL-1.1**, delayed XOR, after independent
dynamics and causal-I/O gates. Foundation integration **ITD-30.5** is separate repair
work, not an excuse to label blocked downstream integrations completed.

## Execution procedure

Use Thor for V888 computation. Confirm the actual execution channel and runner/host
identity before claiming a machine operation. Do not ask the user to run routine
commands. If access is missing, record the blocker without claiming execution or
substituting another host for an unreported hardware result.

The current runner uses a different HOME from historical data runs. Shared audited input
root is `/mnt/nvme/github-runners/home/datasets/banc_v888`; latest derived outputs are
under `/var/lib/github-runner/v888-research-runs/bool02-35726122553-1`. Verify paths,
source hashes and read permissions before reuse. Keep compiler tools and new outputs
runner-owned; never fix an absent tool or HOME mismatch by changing global permissions
or deleting unrelated artifacts. Use isolated per-run checkout and retain failure evidence.

Keep raw data external. Verify exact hashes/generation, integer IDs, detector version,
filter policy and node set before import. The raw 19.73 GB table, the induced qualified
CSR and unit-adjacency control arms are different representations/scopes. No in-place
filtering or deletion of raw sources is allowed. Preserve every relevant cut boundary edge.

Inspect current SciRust primitives and consumer bootstraps before adding dependencies.
New executable dynamics belong in Rust with CPU reference and independent tests first.
Python remains acceptable for frozen scientific reference, metadata validation, ingestion
and independent oracles; it is not the requested Rust simulation engine.

For every slice, retain the hypothesis, source/data/protocol identities, tests, resource
budget, outcome, limitations, PR target and next dependency. Preserve failed hypotheses.
Update the ledger after observations, not promises. Add a new dated checkpoint and
update this read-order pointer; never erase prior observations or copy stale status into a new date.

## Non-negotiable gates

ITD V29.18 remains frozen; Missions 3–8 negative evidence remains closed in scope.
No final-holdout tuning, hidden answer/history in encoder/readout, or cross-trial leakage.
No compile-only to hardware/model-quality inference, adult allometry to biological
causality inference, or uniform-null inference from an invariant-preserving graph generator.

Existing ITD autonomous-merge denial is preserved. This programme grants neither
final-study authorization nor automatic merge permission. Default product changes
require applicable exact-head CI and repository review policy.

Public cross-repository handoffs contain only agreed interface/experiment descriptions;
never copy private consumer implementation details, credentials or raw data into ITD.
