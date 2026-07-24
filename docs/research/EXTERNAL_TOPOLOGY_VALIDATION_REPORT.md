# External topology validation report (H64)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Question

Independent of whether ITD *predicts* a topology-change event (H61/H62), does any ITD
channel move in a **consistent direction** around an ITD-independent core-merger/split
event — a purely descriptive check, `itd_research.mission8.descriptive.
evaluate_topology_response_consistency` (pre/post-event mean shift, window = 2 frames,
consistency = fraction sharing the majority sign, threshold 80%).

## Result (real data, all 4 isotropic sequences, 4 event instances)

```
helicity_mean        : 4/4 events, 100% sign-consistent (all NEGATIVE), mean |shift| = 1.97
normalized_helicity  : 4/4 events, 100% sign-consistent (all NEGATIVE), mean |shift| = 0.19
stretching_rate      :               75% sign-consistent
localization         :               50% (coin-flip)
heterogeneity        :               50% (coin-flip)
roughness            :               50% (coin-flip), large but directionless swings
orientation_dispersion:              50% (coin-flip)

verdict: supported within tested scope
reasoning: helicity_mean and normalized_helicity show >= 80% sign-consistent response.
```

**H64 is supported within tested scope for two channels**: `helicity_mean` and
`normalized_helicity` both **decrease** at every one of the 4 observed core-merger/split
instances. This is the session's one clean, reproducible-looking descriptive signal.

## Why this is NOT evidence for H61/H62

A consistent qualitative response is a *necessary*, not *sufficient*, condition for
predictive value — and the primary predictive test (`EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md`)
already found ITD-only AUC below chance and the augmented model worse than established
alone. The two are not contradictory: a channel can move in a repeatable direction around
an event while still not separating event frames from non-event frames well enough to
improve a classifier, especially once an established model already captures most of the
same information via correlated magnitude/structural channels (see the H63 non-redundancy
result below).

## Honest limitations — this is NOT 4 independent replications

Of the 4 event instances, **2 come from the same sequence** (`iso_run1`, both
`core_split` events); only 3 independent DNS sequences are represented. A "100%
sign-consistent across 4 instances" claim rests on effectively **3 independent units**,
one of which is double-counted. This is stated explicitly rather than treated as strong
statistical evidence — it is a suggestive, reproducible-looking pattern worth flagging for
future, larger-n investigation, not a validated result.

## Relation to H63 (non-redundancy)

The pooled non-redundancy check (`itd_research.mission8.localization.evaluate_nonredundancy`,
112 pooled frames, 12 positive labels across all 4 sequences) found `helicity_mean` and
`normalized_helicity` have low Spearman correlation with enstrophy (−0.074, +0.170) — so
their consistent response is not merely a repackaging of the magnitude signal — but their
**partial correlation with the event label after controlling for enstrophy** is small
(−0.020, +0.011), well below the preregistered non-triviality threshold (0.1). **H63 is
not supported for any channel** (see `EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md`'s
companion analysis, full table below): a channel can be descriptively distinct from
enstrophy and still carry no incremental predictive information about the event.

```
channel                spearman_vs_enstrophy  partial_corr_vs_event|enstrophy
localization                     0.078                     -0.089
heterogeneity                     0.196                     -0.062
roughness                         0.534 (correlated)         0.163
orientation_dispersion            0.298 (borderline)          0.034
helicity_mean                    -0.074                     -0.020
normalized_helicity                0.170                      0.011
stretching_rate                    0.734 (correlated)        -0.056

non_redundant_channels: []
verdict: not supported
```
