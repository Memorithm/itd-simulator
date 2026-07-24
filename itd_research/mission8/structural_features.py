"""ITD structural feature extraction and existing-channel feature groups (Mission 8).

Wraps the certified-adjacent :func:`evaluate_itd3d` (no certified core is touched) to
extract per-frame channels and defines the Mission-8-locked feature groups from the
already-implemented 3D ITD channel set -- no new channel is invented. ``intensity`` is
kept only as ``ITD_MAGNITUDE_CONTROL``, a redundancy/consistency control, never the
primary evidence (Mission 7 found it ~redundant with enstrophy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d
from itd_research.mission8.statistics import temporal_rate

FloatArray: TypeAlias = NDArray[np.float64]

# Existing 3D ITD channels only (itd_research.diagnostics_3d.itd_3d.ITD3DResult fields).
ITD_MAGNITUDE_CONTROL: tuple[str, ...] = ("intensity",)
ITD_STRUCTURAL: tuple[str, ...] = ("localization", "heterogeneity", "roughness")
ITD_ORIENTATION: tuple[str, ...] = ("orientation_dispersion",)
_TEMPORAL_BASE: tuple[str, ...] = ITD_STRUCTURAL + ITD_ORIENTATION
ITD_3D_NONREDUNDANT: tuple[str, ...] = (
    "localization", "heterogeneity", "roughness", "orientation_dispersion",
    "helicity_mean", "normalized_helicity", "stretching_rate",
)
ITD_ALL_EXISTING: tuple[str, ...] = ITD_MAGNITUDE_CONTROL + ITD_3D_NONREDUNDANT


def _static_channel_names() -> tuple[str, ...]:
    return ITD_ALL_EXISTING


@dataclass(frozen=True)
class StructuralTrajectory:
    """Per-frame ITD channel values (static) plus derived temporal-rate channels."""

    times: list[float]
    channels: dict[str, list[float]]        # static channel -> values per frame
    temporal: dict[str, list[float]]        # "d_<channel>_dt" -> centered finite differences

    def as_dict(self) -> dict[str, object]:
        return {"times": self.times, "channels": self.channels, "temporal": self.temporal}

    def matrix(self, names: tuple[str, ...]) -> FloatArray:
        """Column-stack requested channel/temporal names in the given order."""
        columns = []
        for name in names:
            if name in self.channels:
                columns.append(np.asarray(self.channels[name], dtype=np.float64))
            elif name in self.temporal:
                columns.append(np.asarray(self.temporal[name], dtype=np.float64))
            else:
                raise KeyError(f"unknown structural feature {name!r}")
        return np.column_stack(columns) if columns else np.empty((len(self.times), 0))


def compute_structural_trajectory(
    frames: list[tuple[float, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]],
) -> StructuralTrajectory:
    """Compute per-frame ITD channels from a sequence of ``(time, u, v, w, x, y, z)``."""
    times: list[float] = []
    channels: dict[str, list[float]] = {name: [] for name in _static_channel_names()}
    for time, u, v, w, x, y, z in frames:
        result = evaluate_itd3d(u, v, w, x, y, z, "finite").as_dict()
        times.append(time)
        for name in _static_channel_names():
            channels[name].append(float(result[name]))
    temporal = {f"d_{name}_dt": temporal_rate(channels[name], times) for name in _TEMPORAL_BASE}
    return StructuralTrajectory(times=times, channels=channels, temporal=temporal)


FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "ITD_MAGNITUDE_CONTROL": ITD_MAGNITUDE_CONTROL,
    "ITD_STRUCTURAL": ITD_STRUCTURAL,
    "ITD_ORIENTATION": ITD_ORIENTATION,
    "ITD_TEMPORAL": tuple(f"d_{name}_dt" for name in _TEMPORAL_BASE),
    "ITD_3D_NONREDUNDANT": ITD_3D_NONREDUNDANT,
    "ITD_ALL_EXISTING": ITD_ALL_EXISTING,
}
