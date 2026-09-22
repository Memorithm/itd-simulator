# Les deux portes — environment reference v1

Owner: ITD Research Lab. Application decision: `V888-GAME-FIRST-20260922`.
This independent environment/oracle slice does not complete V888-BOOL-0.3, 0.4 or 1.1.
No connectome, learned parameters, trading data or runtime actuation is used.

## Executable contract

`game.rs` is a standalone Rust 1.89 / edition 2021 reference with no third-party
crates and no unsafe code. `Policy::act` receives only a copied `Observation`.
The private episode state is not available through that interface. This is an
accidental-leakage/type boundary, not a hostile-process security sandbox.

The diagnostic stdin batch format supplies condition, A, B, R, distractor bits,
control name and train/eval mode to the ADMINISTRATOR. Never forward that format,
its command line, a trace identifier or the environment RNG to a candidate.
A future subprocess adapter must send only serialized Observation payloads and
must enforce actual wall-clock timeouts. The current Timeout action tests scoring
semantics; it is not a timer implementation.

Timeline for delay d: cue A; d distractors; cue B; choice. Thus A-to-choice distance
is d+2 observations and B-to-choice distance is one, not d. All conditions have
the same timeline for a given d. Hidden operands use None/null, not zero.

| Condition | Observation policy | Correct door |
|---|---|---|
| memory | A briefly visible; no A/B/R at choice | A |
| logic | A/B/R visible simultaneously only at choice | A XOR B XOR R |
| combined | A then B briefly visible; only R at choice | A XOR B XOR R |

Wait is required before choice. Early, missing, malformed and timed-out actions
terminate as explicit failures. There is only one scored attempt; no retry may
replace failure. Training feedback is emitted only after the action. Evaluation
feedback is absent; audit success/reason remains outside the policy interface.

## Controls and independent verification

The exact sequential control stores two optional bits. It is hand-written and is
NOT evidence of learning. The current-observation control has no recurrent state.
It solves simultaneous logic; on complete counterbalanced memory/combined panels,
every current decision payload has equally many door-0 and door-1 targets.

The source-frozen `protocol.json` specifies the finite environment qualification:
all eight A/B/R combinations; seven delay values; exhaustive distractor sequences
through delay 4, then six declared long-delay patterns; six diagnostic controls.
`qualify.py` independently reconstructs the timeline and uses a truth-table lookup
rather than the Rust scoring implementation. Every failure stays in the denominator.

Twelve Rust unit methods and nine independent process-test methods are defined.
The pilot additionally repeats every administrative record and compares complete
trace bytes, not just totals. Non-final fixtures only; no training takes place.
Policy payload byte counts describe direct control storage, not whole-process RAM,
allocator overhead, dynamic dispatch, traces or environment memory. Full timing
includes JSON reporting and oracle costs and is not an inference-speed benchmark.

## Build and evidence ownership

The SciRust Thor workflow checks out a pinned ITD source revision; it supplies
execution infrastructure only and does not copy the task into a SciRust library.
The environment and interpretation remain owned by this repository. A prospective
TDI/SML/NoiseLab adapter must have its own reviewed contract and tests.

Raw BANC data are not read or changed by this environment qualification. ITD V29.18
is unchanged. Product CI, final evaluation, training and model promotion are separate.

## Next integration

Retain BOOL-0.2b control/port diagnostics. Build/qualify the Rust recurrent dynamics,
then a causal policy adapter using current observations only. Record learning curves
separately for readout training, internal plasticity and later topology changes;
include frozen, feedback-shuffled and learned-parameter-reset controls. A visual
replay must identify the actual controller and must not label this exact solver V888.
