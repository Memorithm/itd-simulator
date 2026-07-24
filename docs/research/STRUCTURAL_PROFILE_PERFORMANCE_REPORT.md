# Structural profile performance report (H74)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Design

`itd_research.mission8.profiles` declares named structural profiles (flow family, event
type, required established/ITD channels), every primary profile excluding `intensity` by
default (`excluded_channels=("intensity",)`), mirroring Mission 5's profile-driven
computation but scoped to Mission 8's structural/topological work.
`benchmark_profile` compares a "full" path (always computes every established +
structural channel) against a "profile" path (computes only the channels the declared
profile actually requires), and separately checks the two paths are numerically identical
on every channel they share.

## Result (real JHTDB data, `external_vortex_merger` profile, 4 frames, `iso_run1`)

```
full_p95_ms                  = 2313.57
profile_p95_ms                = 2508.30
speedup                        = 0.92×   (profile path is SLOWER, not faster)
max_abs_diff_shared_channels  = 0.0
equivalence_level              = bitwise_equal
```

**H74 (profile-driven computation reduces cost) is not supported.** The profile path is
numerically **bitwise-identical** to the full path on every shared channel (both call the
exact same `compute_baseline_trajectory`/`compute_structural_trajectory` functions with
the same inputs — no drift, no approximation), but it is not faster: there is no internal
short-circuiting inside `evaluate_itd3d` or `compute_baseline_trajectory` to skip
individual channels the profile doesn't need. Since the `external_vortex_merger` profile
requires the full `BASELINE_COMPETENT_COMBINED` and the full `ITD_3D_NONREDUNDANT` sets
anyway (see `profiles.REGISTRY`), the profile path here computes exactly what the full
path computes, plus its own bookkeeping overhead — hence the measured *slowdown*, not
speedup.

## What would be needed for a real speedup

A profile that requires a genuine *strict subset* of channels, combined with per-channel
short-circuiting inside `compute_baseline_trajectory`/`compute_structural_trajectory` (so
unneeded connected-component or gradient work is skipped, not merely unused). Neither
exists today. This is reported as an honest architectural gap, not hidden behind an
optimistic benchmark on a profile that happens to need everything anyway.

## Consistent with the fixture (offline CI) run

The bounded offline fixture campaign (`python -m itd_research.mission8 validate`) shows
the same qualitative result on manufactured data (`speedup ≈ 0.92-0.96×`,
`equivalence_level = bitwise_equal`) — the finding is not an artifact of the specific real
sequence tested.
