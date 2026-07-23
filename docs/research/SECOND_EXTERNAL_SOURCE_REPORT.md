# Second external source report (H55) — cross-source transfer

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Does not modify
`ITD V29.18`.

## Two genuinely independent external sources secured

| # | source | institution | class | dimensionality |
|---|---|---|---|---|
| 1 | JHTDB isotropic1024coarse | Johns Hopkins | external-DNS | 3D, time-resolvable |
| 2 | biofilm PIV (Zenodo 1175014) | USNA / U. Virginia | experimental-PIV | 2D, time-averaged |

These are **genuinely independent institutions and evidence classes** (a numerical DNS
database and an experimental PIV archive), not two subsets of one repository — which is
what H55 requires in spirit.

## H55 — cross-source transfer **blocked**

A calibration-transfer test (develop on source A, apply to source B) requires the two
sources to live in a **comparable feature space**. They do not: source 1 is a **3D**
velocity field (ITD-3D channels: helicity, stretching, orientation dispersion, …), source 2
is a **2D time-averaged** field (no third component, no time axis, so no vorticity-vector or
temporal-deformation channels). The ITD feature vectors are therefore not commensurable, and
a numeric transfer AUC between them would be meaningless.

**Verdict: H55 blocked** — two independent external sources were obtained, but not two
*comparable* time-resolved 3D sources, so cross-source calibration transfer could not be
evaluated. This is reported honestly rather than forced with an apples-to-oranges number.
The path to unblock H55 is a second time-resolved 3D external source (e.g. a JHTDB channel
or transitional-boundary-layer cutout, or the blocked cylinder DNS).
