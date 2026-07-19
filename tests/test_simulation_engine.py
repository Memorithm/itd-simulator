from __future__ import annotations

import numpy as np
import pytest

from compare_scenarios import Config
from itd_v29_core.simulation_engine import simulate


def mesh(size: int = 9) -> tuple[np.ndarray, np.ndarray, float]:
    coordinates = np.linspace(-1.0, 1.0, size)
    x, y = np.meshgrid(coordinates, coordinates, indexing="xy")
    return x, y, float(coordinates[1] - coordinates[0])


def zero_curvature(x: np.ndarray, y: np.ndarray, time: float) -> np.ndarray:
    del time
    return np.zeros(np.broadcast_shapes(x.shape, y.shape))


def test_solid_rotation_matches_manual_intensity_oracle() -> None:
    x, y, spacing = mesh()

    def solid_rotation(
        grid_x: np.ndarray, grid_y: np.ndarray, time: float
    ) -> tuple[np.ndarray, np.ndarray]:
        del time
        return -grid_y, grid_x

    result = simulate(
        "solid",
        solid_rotation,
        x,
        y,
        np.array([0.0, 0.25, 1.0]),
        spacing,
        Config(grid_size=x.shape[0], time_steps=3, duration=1.0),
        curvature_function=zero_curvature,
    )
    # omega = d(x)/dx - d(-y)/dy = 2, hence <omega^2 exp(0)> = 4.
    np.testing.assert_allclose(result["intensity_rate"], 4.0, rtol=0.0, atol=1.0e-14)
    assert result["intensity_index"] == pytest.approx(4.0, abs=1.0e-14)
    assert result["structure_index"] == pytest.approx(0.0, abs=1.0e-14)


def test_zero_velocity_has_zero_intensity_and_structure() -> None:
    x, y, spacing = mesh()

    def zero_velocity(
        grid_x: np.ndarray, grid_y: np.ndarray, time: float
    ) -> tuple[np.ndarray, np.ndarray]:
        del time
        return np.zeros_like(grid_x), np.zeros_like(grid_y)

    result = simulate(
        "zero",
        zero_velocity,
        x,
        y,
        [0.0, 1.0],
        spacing,
        Config(grid_size=x.shape[0], time_steps=2, duration=1.0),
        curvature_function=zero_curvature,
    )
    assert result["intensity_index"] == 0.0
    assert result["structure_index"] == 0.0
    assert result["coupled_index"] == 0.0


def test_simulator_rejects_invalid_mesh_callable_and_outputs() -> None:
    x, y, spacing = mesh()
    cfg = Config(grid_size=x.shape[0], time_steps=2, duration=1.0)
    with pytest.raises(ValueError):
        simulate("bad", None, x, y, [0.0, 1.0], spacing, cfg)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        simulate("bad", lambda a, b, t: (a, b), x[:-1], y, [0.0, 1.0], spacing, cfg)
    with pytest.raises(ValueError):
        simulate(
            "bad",
            lambda a, b, t: (np.zeros((3, 3)), np.zeros((3, 3))),
            x,
            y,
            [0.0, 1.0],
            spacing,
            cfg,
        )

    def nonfinite(
        grid_x: np.ndarray, grid_y: np.ndarray, time: float
    ) -> tuple[np.ndarray, np.ndarray]:
        del time
        values = np.full_like(grid_x, np.nan)
        return values, np.zeros_like(grid_y)

    with pytest.raises(ValueError):
        simulate("bad", nonfinite, x, y, [0.0, 1.0], spacing, cfg)
