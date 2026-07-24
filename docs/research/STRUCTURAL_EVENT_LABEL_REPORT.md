# Structural event label report (H61-H74 event definition)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Definition (ITD never participates)

The primary structural event is a **topology change**: a persistent change in the count
of connected Q-criterion-positive (`Q > 0`) 3D regions, detected by
`itd_research.mission8.vortex_regions.detect_topology_events` on the
`itd_research.mission8.event_labels.label_structural_events` region-count series
(`min_cells=8`, `persistence=2`). A drop in count is `core_merger`; a rise is
`core_split`. An alternative `lambda2 < 0` label is computed purely for disagreement
reporting (never used to relabel or override the Q-based primary label).

## A bug found and fixed before any report was written

`detect_topology_events`'s original persistence rule only required the **post**-change
region count to persist for `persistence` frames. A one-frame count blip that reverts
(e.g. `2,2,1,2,2`) was therefore correctly rejected at the dip's onset (the dip itself
does not persist) but incorrectly accepted at the **recovery** point (the frame right
after the dip *does* look like a stable new 2-frame run) — contradicting the module's own
documented intent ("a transient dip or spike is not an event"). Fixed by also requiring
the **pre**-change value to have already been stable for `persistence` frames before the
transition (`tests/test_mission8.py::test_detect_topology_events_requires_sustained_change_not_a_transient_blip`
pins this). The fix was made, tested against the manufactured oracles (all 13 pass
unchanged — the clean step-transition oracles B/C never exercised the bug), and applied
**before** the primary holdout evaluation or any interpretive report was written or
finalized — the same discipline used earlier in this mission for the H61-verdict
computation fix in `prediction.py`.

## Event counts (corrected detector, real JHTDB data)

| sequence | events | types (frame) |
|---|---|---|
| `iso_run1` | 2 | `core_split`@2, `core_split`@23 |
| `iso_run2` | 1 | `core_merger`@8 |
| `iso_topo` | 1 | `core_merger`@10 |
| `iso_run3` | 0 | — |
| `mhd_topo` | 0 | — |
| `mhd_topo_run2` | 0 | — |

The corrected detector is **more conservative** than the buggy version (it found more
events per sequence, some spurious). Two consequences, reported honestly rather than
hidden:

* `iso_run3` and both `mhd1024` sequences have **zero** qualifying events at
  `min_cells=8`/`persistence=2`. This blocks cross-source transfer testing on real data
  (see `CROSS_SOURCE_STRUCTURAL_TRANSFER_REPORT.md`) — not because ITD fails to
  transfer, but because no qualifying event exists in the fetched MHD cutouts under this
  definition.
* Of the 4 event *instances* used in the descriptive H64 check, 2 come from the same
  sequence (`iso_run1`) — only **3 independent sequences**, not 4 independent events,
  contribute; every downstream report states this explicitly rather than treating n=4 as
  4 independent units.

## Q vs. λ₂ disagreement

`label_structural_events` also computes a λ₂-based region-count series and event list for
comparison. Disagreements (`q_only`, `lambda2_only` frame sets) are reported in the
returned dict for every sequence and are **never** resolved in ITD's favor — ITD does not
appear anywhere in this labelling path.

## Uncertainty

Every `StructuralEvent.event_uncertainty` equals the persistence window half-width (2
frames = 0.2 physical time units at `dt=0.1`), stated explicitly rather than treated as
exact.
