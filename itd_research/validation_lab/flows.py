"""Deterministic 3D flow catalogue for the validation laboratory (research).

Each entry is a named, family-labelled 3D velocity field on a periodic box,
generated analytically or by the local spectral solver with an explicit seed. The
catalogue spans laminar/coherent, transitional, and turbulent families so that
channel-dependence, ablation, and transfer studies run on a controlled, fully
deterministic set (no network, no external data).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.spectral3d import (
    abc_flow_velocity,
    corotating_tubes,
    isotropic_seed,
    simulate,
    spectral_grid_3d,
    taylor_green_velocity,
)

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class LabFlow:
    """A named, family-labelled 3D velocity field with its coordinates."""

    name: str
    family: str
    u: FloatArray
    v: FloatArray
    w: FloatArray
    coordinates: FloatArray


def lab_flows(nodes: int = 32) -> list[LabFlow]:
    """Build the deterministic 3D flow catalogue at the given resolution."""
    grid = spectral_grid_3d(nodes)
    coords = grid.coordinates
    flows: list[LabFlow] = []

    def add(name: str, family: str, field: tuple[FloatArray, FloatArray, FloatArray]) -> None:
        flows.append(LabFlow(name, family, field[0], field[1], field[2], coords))

    # laminar / coherent
    add("abc", "laminar_coherent", abc_flow_velocity(grid))
    add("taylor_green", "laminar_coherent", taylor_green_velocity(grid))
    add("corotating_tubes", "laminar_coherent",
        corotating_tubes(grid, circulation=2.0, core=0.5, separation=1.6))

    # transitional: evolved Taylor-Green (enstrophy production) and a merging pair
    tg_evolved = simulate(taylor_green_velocity(grid), grid, 0.01, 0.004, steps=250, record_every=250).velocity[-1]
    add("taylor_green_evolved", "transitional", tg_evolved)
    tubes_evolved = simulate(
        corotating_tubes(grid, circulation=3.0, core=0.5, separation=1.3), grid, 0.005, 0.003,
        steps=200, record_every=200,
    ).velocity[-1]
    add("merging_tubes", "transitional", tubes_evolved)

    # turbulent (under-resolved at these sizes, stated): decaying isotropic seeds
    for seed in (1, 2, 3):
        add(f"isotropic_seed_{seed}", "turbulent", isotropic_seed(grid, seed=seed, peak_wavenumber=5.0))
    decayed = simulate(isotropic_seed(grid, seed=4, peak_wavenumber=5.0), grid, 0.01, 0.003,
                       steps=200, record_every=200).velocity[-1]
    add("isotropic_decayed", "turbulent", decayed)
    return flows
