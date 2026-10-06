#!/usr/bin/env python3
"""Emit a compact, deterministic V29 result for independent-process checks."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_compare_scenarios = importlib.import_module("compare_scenarios")
Config = _compare_scenarios.Config
coherent_vortex = _compare_scenarios.coherent_vortex
multi_vortex_field = _compare_scenarios.multi_vortex_field
simulate = importlib.import_module("itd_v29_core.simulation_engine").simulate


def array_digest(values: object) -> str:
    array = np.ascontiguousarray(np.asarray(values, dtype="<f8"))
    return hashlib.sha256(array.tobytes()).hexdigest()


def main() -> None:
    cfg = Config(grid_size=21, time_steps=17, duration=1.25)
    coordinates: np.ndarray = np.linspace(
        cfg.domain_min, cfg.domain_max, cfg.grid_size, dtype=np.float64
    )
    x: np.ndarray
    y: np.ndarray
    x, y = np.meshgrid(coordinates, coordinates, indexing="xy")
    times: np.ndarray = np.linspace(
        0.0, cfg.duration, cfg.time_steps, dtype=np.float64
    )
    spacing = float(coordinates[1] - coordinates[0])

    report: dict[str, object] = {
        "dtype": "float64",
        "grid_size": cfg.grid_size,
        "time_steps": cfg.time_steps,
    }
    for name, velocity in (
        ("coherent", coherent_vortex),
        ("multi", multi_vortex_field),
    ):
        result = simulate(name, velocity, x, y, times, spacing, cfg)
        report[name] = {
            "coupled_index": float(result["coupled_index"]),
            "intensity_index": float(result["intensity_index"]),
            "intensity_rate_sha256": array_digest(result["intensity_rate"]),
            "structure_index": float(result["structure_index"]),
            "structure_rate_sha256": array_digest(result["structure_rate"]),
        }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
