# Strongly vortical PIV report (Mission 5, H32)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Evidence class: **experimental-PIV** (attempted).

## Question (H32)

Do ITD channels or predictions agree with independently documented vortex events in a
**time-resolved, coherent-vortex** PIV dataset?

## H32 classification: **blocked** (evidence unavailable)

H32 requires a **strongly-vortical, time-resolved** PIV dataset with **independent**
vortex evidence (core coordinates, expert annotations, pressure minima, phase-locked
references, or a published shedding frequency). None is available or committed here:

* the one committed external PIV field (biofilm, Zenodo 1175014) is a **time-averaged
  mean** of a **shear-dominated** boundary layer — deliberately kept as the **OOD/shear
  control**, never used as positive vortex validation (Mission 4 found whole-field ITD
  intensity uncorrelated with rotation strength there, agreement only inside vortices);
* no cylinder-wake / vortex-ring / swirling-jet / tip-vortex PIV is integrated
  (`blocked-by-{network,licence,size}`);
* CI has no network, so no such dataset can be fetched here.

## Unblocking path

Integrate a time-resolved coherent-vortex PIV/PTV set — the **Re=3900 cylinder wake** is
the priority (`CYLINDER_RE3900_INTEGRATION_REPORT`) — via the manual, network-enabled
workflow, then apply the temporal protocol: annotate event times from
lift/pressure/core-tracks (ITD-independent), and test whether ITD channels change before
the event, reporting whole-field vs vortex-region behaviour, lead time, uncertainty, and
preprocessing sensitivity.

## Limitations

No time-resolved vortical PIV was evaluated. The report states the blockage and path; it
makes no claim that PIV supports or refutes ITD. The Mission 3/4 shear-PIV negative/
partial result stands.
