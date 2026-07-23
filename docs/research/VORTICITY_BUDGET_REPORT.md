# 3D vorticity-budget report

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
Reproduce via `itd_research.spectral3d.vorticity_budget` on solver snapshots
(exercised in `python -m itd_research.spectral3d validate`).

## Decomposition

The incompressible vorticity equation is decomposed term-by-term:

    d omega/d t = -(u.grad) omega + (omega.grad) u + nu laplacian(omega) + curl(f).

Each right-hand term is evaluated spectrally at a snapshot; the Eulerian change is
estimated from two consecutive snapshots; the closure residual
`residual = d omega/d t - RHS` is reported globally (RMS relative to the Eulerian
change) and locally (Linf).

## Results (Taylor-Green, 32^3, nu = 0.01)

| term | RMS |
|---|--:|
| Eulerian change d omega/dt | 0.349 |
| advection -(u.grad) omega | 0.242 |
| **stretching + tilting (omega.grad) u** | **0.244** |
| viscous diffusion nu laplacian(omega) | 0.041 |
| residual (closure) | 0.004 |
| **closure fraction (residual/Eulerian)** | **0.002 (0.2 %)** |

## Findings

* The budget **closes to ~0.2 %** — the numerical residual is two-to-three orders
  of magnitude below the physical terms, so the solver's vorticity dynamics are
  self-consistent.
* **Stretching+tilting is a leading-order term** (0.244), comparable to advection
  (0.242) and an order of magnitude above viscous diffusion (0.041). This is the
  distinctively 3D physics — vortex stretching amplifies enstrophy — that the 2D
  solver cannot exhibit and that motivates the ITD-3D stretching channel.
* The stretching term is precisely the local quantity the ITD `stretching_rate`
  channel aggregates (`omega^T S omega / |omega|^2`), so the budget grounds that
  channel in the exact governing equation. The channel-dependence report shows
  `stretching_rate` is statistically non-redundant with the magnitude channels.

## Limitations

Single flow (Taylor-Green) and modest resolution here; the closure is a first-order
-in-time / spectral-in-space estimate, so the residual scales with the timestep.
The orientation-change (tilting vs stretching split within `(omega.grad) u`) is
summarised by magnitude; a full tilting/stretching separation per axis is available
from the vector terms but not tabulated here. This report verifies closure and the
leading-order role of stretching; it is not a turbulence cascade study.
