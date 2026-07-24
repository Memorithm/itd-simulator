# Strongly vortical PIV/PTV report, Mission 8 (H72)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.

## Requirement (unchanged from Missions 3/4/6/7)

A dataset that is time-resolved, vortex-dominated (not shear/mean-flow-dominated),
provides vector fields with masks/quality indicators, has a known cadence, carries
independent vortex evidence (core tracks, circulation, or expert labels), and has clear,
legal, open provenance. Ideally volumetric (so a genuine 3D λ₂/Q comparison is possible);
a 2D planar dataset is acceptable only if never presented as volumetric evidence.

## Genuine attempt made this mission

Two targeted web searches were run this session (not a repeat of Mission 7's search):

1. *"open dataset time-resolved PIV vortex shedding vortex core tracking public repository
   zenodo"* — surfaced the **VIVALDy** dataset (arXiv 2509.24965, Institut Pprime,
   Poitiers): time-resolved 2D PIV of an elastically-mounted cylinder undergoing
   vortex-induced vibration, streamwise/crosswise velocity fields, sampling well above the
   shedding frequency (time-resolved, genuinely vortex-dominated). **No public data
   repository or download link was found** in the paper listings or HAL archive entry
   located this session; a follow-up search for the dataset's availability likewise found
   no confirmed open repository — only a pointer to contacting the authors directly.
2. *"time-resolved tomographic PTV vortex ring public dataset download CC-BY"* —
   surfaced literature on scanning Tomo-PIV/PTV vortex-ring transition studies (references
   to Sun/Brücker-style vortex-ring tomographic work), but **no confirmed open,
   downloadable, CC-licensed dataset** — only academic papers describing the technique,
   not a data release.

## Verdict: blocked (unchanged)

No dataset meeting the required characteristics was secured. This mirrors Missions 3, 4,
6 and 7's finding: the one experimental PIV field this repository holds (biofilm
boundary-layer PIV, Zenodo 1175014, from Mission 7) remains a **shear-dominated mean-flow
control**, never presented as coherent-vortex evidence. H72 is **blocked**, not forced
into a positive or negative predictive claim, and the strict-vs-repaired PIV distinction
established in Mission 7 is preserved unchanged (no volumetric λ₂ claim is made from any
planar field; no shear-dominated field is treated as coherent-vortex validation).

## What would unblock this

A time-resolved, ideally tomographic/volumetric PIV or PTV dataset of an unambiguously
vortex-dominated flow (a wake, a ring, a jet) with an open license and either core-track
annotations or a clear circulation/vorticity-based ground truth independent of ITD. None
was located this session; this remains an open acquisition task for a future mission.
