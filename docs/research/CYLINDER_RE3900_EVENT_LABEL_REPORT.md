# External event-label report (H52 labelling) — ITD-independent events

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Does not modify
`ITD V29.18`.

## Cylinder shedding labels — **blocked**

The preferred cylinder-wake labels (lift zero-crossing, shedding phase, pressure-minimum
passage, published core tracks) require the blocked cylinder dataset (no lift/pressure/force
time series were obtained). Status **blocked**.

## The external event actually used (JHTDB) — ITD-independent

Because JHTDB isotropic turbulence has no lift/shedding signal, the event was defined from
**established diagnostics only**, keeping it strictly ITD-independent:

- **event type**: extreme-enstrophy burst.
- **definition**: a frame is positive iff its established enstrophy exceeds the 67th
  percentile of the **development** frames' enstrophy (threshold fixed on development only;
  no holdout-label fitting).
- **independence**: uses only vorticity/enstrophy from established finite-difference
  operators; **no ITD channel** participates in the label.
- **provenance recorded per frame**: `time`, enstrophy value, threshold, source file, index.

## Honesty controls

- The event definition was **fixed in the preregistration before** the final holdout
  evaluation; it was not chosen to flatter ITD.
- An alternative label (`q_positive_fraction` peak) is available; the enstrophy-burst label
  was preregistered as primary. The two are correlated in this stationary-turbulence cutout;
  any disagreement would be preserved and reported, not resolved in ITD's favour.
- The event is genuine but modest: intermittent enstrophy bursts are a real feature of
  isotropic turbulence, though weaker and less cleanly periodic than cylinder shedding —
  a limitation stated plainly.

The labelled event feeds the locked prediction in `EXTERNAL_INCREMENTAL_VALUE_M7_REPORT.md`,
where established diagnostics already predict it perfectly and ITD adds nothing.
