# Mission 8 follow-up — making H65 conclusive

Status: **preregistration**, committed before any additional data is fetched and before any
transfer evaluation is run. Not a certified revision; does not modify `ITD V29.18`.

Protocol: `configs/mission8h65/preregistered_protocol.toml`
(SHA-256 `83c20f854bf4cc5e049978f089baf671cafe616009a60e3d8008c76fdac549fa`).
Baseline commit `47f30f4`. Parent protocol
`configs/mission8/preregistered_protocol.toml` (SHA-256 `ddd64804…`).

## The problem being fixed

Mission 8 returned **H65 inconclusive**, and for a reason that is not a scientific finding:
the two JHTDB `mhd1024` windows fetched contained **zero** qualifying Q-criterion topology
events, so the source-B label set was single-class and no ROC-AUC was computable at all.

That is an artefact of data collection. It tells us nothing about whether a structural
profile calibrated on isotropic turbulence transfers to MHD turbulence. This follow-up
fetches enough source-B data to make the question answerable — and commits, in advance, to
reporting whatever answer comes out.

## The methodological trap, and the rule that blocks it

Mission 8 explicitly forbids re-searching dataset windows until a target event appears.
There is a real risk here: "fetch more MHD data until H65 becomes testable" can slide into
"fetch windows one at a time and stop when the number looks good."

The binding rule in the protocol is therefore:

> **Every window listed is fetched and every window is used, whatever it contains —
> including windows with zero events.** The window list is frozen by the preregistration
> commit. No window may be added, dropped, extended or re-rolled after any result is seen.

Six windows at fixed, pre-declared origins on a spread lattice, 48 frames each (up from
Mission 8's 24 and 16, so a *persistent* topology change has room to occur). If a window
fails to fetch, it is reported as blocked with its error and **never silently replaced by a
different origin**.

## What stays unchanged

Everything that would otherwise make this incomparable with the merged Mission 8 result:
the ITD-independent Q-criterion event definition and its parameters (`min_cells=8`,
`persistence=2`), the `ITD_3D_NONREDUNDANT` feature set (`intensity` still excluded), the
`BASELINE_COMPETENT_COMBINED` established baseline, the model, the horizon, and the
source-A development sequences (`iso_run1`, `iso_run2`). The model is calibrated on source
A only and applied to source B **without refitting**.

## Decision rule (fixed before any number is seen)

*Conclusive* requires at least one source-B window with ≥1 qualifying event **and** a
pooled source-B label set containing both classes. If that fails, H65 stays **inconclusive**
and the zero-event counts are published as-is.

If conclusive:

* **supported within tested scope** — augmented transfer AUC > 0.55 **and** transfer drop
  vs the source-A holdout < 0.20;
* **not supported** — conclusive but the above is not met.

The augmented-vs-established comparison is reported alongside for completeness, but H65 asks
whether the calibrated profile *transfers*, not whether ITD adds value. **Mission 8's H62
negative is not re-litigated here** — a favourable H65 would not overturn it, and this
follow-up must not be read as a second attempt at the incremental-value question.

## Honesty constraints carried forward

Both sources remain JHTDB — same institution, same access modality. Any result is
**within-institution cross-physics** transfer (isotropic hydrodynamic → forced MHD), never
a cross-institution generalization claim. Prohibited post-hoc moves are enumerated in the
protocol: changing `min_cells`/`persistence`/`horizon` to manufacture events, switching to
λ₂ because Q yields none, refitting on source B, or reporting only the windows that
contain events.

## Expected cost

Six windows × 48 frames × 24³ = 288 additional JHTDB cutout requests on the public testing
token, plus one locked evaluation. No certified artefact is touched; all work stays under
`itd_research`/`docs/research`/`configs`, and normal CI remains offline.
