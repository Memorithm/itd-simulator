from __future__ import annotations

import pytest

from itd_research.trajectory_schema import (
    TrajectoryDescriptorKind,
    TrajectoryPoint,
    TrajectorySeries,
)


def test_trajectory_series_is_strictly_ordered() -> None:
    series = TrajectorySeries(
        "run-1",
        (
            TrajectoryPoint(0, TrajectoryDescriptorKind.STATE_DEFORMATION, 0.1, "ratio", "tdi-state-v1"),
            TrajectoryPoint(1, TrajectoryDescriptorKind.STATE_DEFORMATION, 0.2, "ratio", "tdi-state-v1"),
        ),
    )
    assert series.descriptor is TrajectoryDescriptorKind.STATE_DEFORMATION


def test_trajectory_series_rejects_mixed_semantics() -> None:
    with pytest.raises(ValueError, match="source semantics"):
        TrajectorySeries(
            "run-1",
            (
                TrajectoryPoint(0, TrajectoryDescriptorKind.MEMORY_CHURN, 1.0, "events", "memory-v1"),
                TrajectoryPoint(1, TrajectoryDescriptorKind.MEMORY_CHURN, 2.0, "events", "memory-v2"),
            ),
        )
