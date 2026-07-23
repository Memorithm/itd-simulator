"""Explicit ITD-3D candidate definitions and channel evaluation (research, H12).

The current experimental 3D candidate is treated as one hypothesis among several.
A fixed **superset** of channels is evaluated from a 3D velocity field (reusing the
validated ``evaluate_itd3d``), and each named candidate is an explicit subset of
that superset. Ablation (H12) compares candidates on downstream tasks; no candidate
is aggregated into a scalar and none is certified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.itd_3d import evaluate_itd3d

FloatArray: TypeAlias = NDArray[np.float64]

# Superset (excludes vorticity_rms, which is sqrt of intensity by construction).
_SUPERSET: tuple[str, ...] = (
    "intensity",
    "heterogeneity",
    "localization",
    "roughness",
    "orientation_dispersion",
    "helicity_mean",
    "normalized_helicity",
    "stretching_rate",
)


def channel_superset() -> tuple[str, ...]:
    """The full ordered set of channel names available to candidates."""
    return _SUPERSET


def evaluate_channels(
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    boundary_mode: str = "periodic",
) -> dict[str, float]:
    """Evaluate the full channel superset on a 3D velocity field."""
    result = evaluate_itd3d(u, v, w, x, y, z, boundary_mode).as_dict()
    return {name: float(result[name]) for name in _SUPERSET}


@dataclass(frozen=True)
class Candidate:
    """A named ITD-3D candidate: an explicit ordered subset of the superset."""

    name: str
    channels: tuple[str, ...]
    description: str

    def vector(self, channel_values: dict[str, float]) -> FloatArray:
        """Extract this candidate's channel vector from a superset evaluation."""
        return np.array([channel_values[name] for name in self.channels], dtype=np.float64)


CANDIDATES: dict[str, Candidate] = {
    "A": Candidate(
        name="ITD3D-Research-A",
        channels=_SUPERSET,
        description="full candidate: all eight channels (the current experimental set)",
    ),
    "B": Candidate(
        name="ITD3D-Research-B",
        channels=("intensity", "localization", "orientation_dispersion", "stretching_rate", "normalized_helicity"),
        description="compact candidate: magnitude + structure + the genuinely-3D channels",
    ),
    "C": Candidate(
        name="ITD3D-Research-C",
        channels=("orientation_dispersion", "normalized_helicity", "stretching_rate", "localization"),
        description="orientation/stretching-focused candidate (drops magnitude channels)",
    ),
}
