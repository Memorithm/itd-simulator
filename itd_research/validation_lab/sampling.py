"""Sub-cube channel sampling from 3D flows (research).

A flow field is partitioned into equal sub-cubes; the channel superset is
evaluated on each sub-cube (finite-domain boundary), giving a data matrix with one
row per sub-cube and provenance labels (which flow, which family) that downstream
studies use to prevent leakage (sub-cubes of the same flow never split across
train/test).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.validation_lab.candidates import channel_superset, evaluate_channels
from itd_research.validation_lab.flows import LabFlow

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class ChannelSamples:
    """A channel data matrix with per-row flow/family provenance."""

    channels: tuple[str, ...]
    matrix: FloatArray
    flow_labels: tuple[str, ...]
    family_labels: tuple[str, ...]


def sample_channels_from_flows(
    flows: list[LabFlow], subcubes_per_axis: int = 4
) -> ChannelSamples:
    """Evaluate the channel superset on sub-cubes of every flow."""
    if subcubes_per_axis < 1:
        raise ValueError("subcubes_per_axis must be >= 1.")
    channels = channel_superset()
    rows: list[list[float]] = []
    flow_labels: list[str] = []
    family_labels: list[str] = []
    for flow in flows:
        nodes = flow.u.shape[0]
        block = nodes // subcubes_per_axis
        if block < 5:
            raise ValueError("sub-cubes too small (need >= 5 nodes per axis).")
        for i in range(subcubes_per_axis):
            for j in range(subcubes_per_axis):
                for k in range(subcubes_per_axis):
                    xs = slice(i * block, (i + 1) * block)
                    ys = slice(j * block, (j + 1) * block)
                    zs = slice(k * block, (k + 1) * block)
                    values = evaluate_channels(
                        flow.u[xs, ys, zs], flow.v[xs, ys, zs], flow.w[xs, ys, zs],
                        flow.coordinates[xs], flow.coordinates[ys], flow.coordinates[zs],
                        "finite",
                    )
                    rows.append([values[name] for name in channels])
                    flow_labels.append(flow.name)
                    family_labels.append(flow.family)
    return ChannelSamples(
        channels=channels,
        matrix=np.array(rows, dtype=np.float64),
        flow_labels=tuple(flow_labels),
        family_labels=tuple(family_labels),
    )
