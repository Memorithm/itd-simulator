"""CLI: ``python -m itd_research.spectral3d validate [--quick|--full] --output DIR``.

Runs the Gate-A validation suite for the 3D spectral solver (derivative oracles,
projection, viscous decay, inviscid conservation, Taylor-Green, ABC, vorticity
-budget closure, a resolution study, and checkpoint-restart determinism), writes a
JSON report, and exits non-zero if any Gate-A invariant fails.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)
from itd_research.spectral3d.checkpoint import load_checkpoint, save_checkpoint
from itd_research.spectral3d.grids import spectral_grid_3d
from itd_research.spectral3d.initial_conditions import (
    abc_flow_velocity,
    taylor_green_velocity,
)
from itd_research.spectral3d.operators import (
    curl,
    divergence,
    gradient_scalar,
    project_solenoidal,
)
from itd_research.spectral3d.simulation import simulate
from itd_research.spectral3d.vorticity_budget import vorticity_budget


def _operator_errors(nodes: int) -> dict[str, float]:
    grid = spectral_grid_3d(nodes)
    xx, yy, zz = grid.mesh()
    dx, _, _ = gradient_scalar(np.sin(xx), grid)
    _, dy, _ = gradient_scalar(np.sin(2.0 * yy), grid)
    _, _, dz = gradient_scalar(np.cos(3.0 * zz), grid)
    u, v, w = abc_flow_velocity(grid)
    cx, cy, cz = curl(u, v, w, grid)
    pu, pv, pw = project_solenoidal(*abc_flow_velocity(grid), grid)
    return {
        "ddx_error": float(np.max(np.abs(dx - np.cos(xx)))),
        "ddy_error": float(np.max(np.abs(dy - 2.0 * np.cos(2.0 * yy)))),
        "ddz_error": float(np.max(np.abs(dz + 3.0 * np.sin(3.0 * zz)))),
        "abc_curl_error": float(
            max(np.max(np.abs(cx - u)), np.max(np.abs(cy - v)), np.max(np.abs(cz - w)))
        ),
        "projection_divergence_linf": float(np.max(np.abs(divergence(pu, pv, pw, grid)))),
    }


def _viscous_decay_error(nodes: int) -> float:
    grid = spectral_grid_3d(nodes)
    _, yy, _ = grid.mesh()
    u = np.sin(yy)
    zero = np.zeros_like(u)
    result = simulate((u, zero, zero), grid, 0.1, 0.005, steps=200, record_every=200)
    amplitude = float(np.max(np.abs(result.velocity[-1][0])))
    expected = float(np.exp(-0.1 * result.times[-1]))
    return abs(amplitude - expected) / expected


def _resolution_study(sizes: tuple[int, ...]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for nodes in sizes:
        grid = spectral_grid_3d(nodes)
        start = time.perf_counter()
        result = simulate(taylor_green_velocity(grid), grid, 0.0, 0.004, steps=100, record_every=100)
        runtime = time.perf_counter() - start
        energy_drift = abs(result.energy[-1] - result.energy[0]) / result.energy[0]
        rows.append({
            "nodes": float(nodes),
            "inviscid_energy_drift": energy_drift,
            "enstrophy_growth": result.enstrophy[-1] / result.enstrophy[0],
            "max_divergence_linf": float(max(result.divergence_linf)),
            "runtime_seconds": runtime,
        })
    return rows


def _checkpoint_roundtrip(output: Path, overwrite: bool) -> dict[str, object]:
    grid = spectral_grid_3d(16)
    warmed = simulate(taylor_green_velocity(grid), grid, 0.01, 0.005, steps=20, record_every=20).velocity[-1]
    path = output / "spectral3d_checkpoint.npz"
    if path.exists() and not overwrite:
        path.unlink()
    checksum = save_checkpoint(path, warmed, grid, 0.1, 0.005, 0.01)
    restored = load_checkpoint(path)
    identical = all(
        np.array_equal(a, b) for a, b in zip(warmed, restored.velocity, strict=True)
    )
    # continue from the checkpoint and from the in-memory field; must match
    a = simulate(warmed, grid, 0.01, 0.005, steps=10, record_every=10).velocity[-1]
    b = simulate(restored.velocity, grid, 0.01, 0.005, steps=10, record_every=10).velocity[-1]
    restart_deterministic = all(np.array_equal(x, y) for x, y in zip(a, b, strict=True))
    return {
        "checksum": checksum,
        "load_identical": identical,
        "restart_deterministic": restart_deterministic,
    }


def _validate(quick: bool, output: Path, overwrite: bool) -> tuple[dict[str, object], list[str]]:
    grid = spectral_grid_3d(32)
    inviscid = simulate(taylor_green_velocity(grid), grid, 0.0, 0.004, steps=150, record_every=50)
    energy_drift = max(abs(e - inviscid.energy[0]) / inviscid.energy[0] for e in inviscid.energy)
    enstrophy_growth = inviscid.enstrophy[-1] / inviscid.enstrophy[0]

    viscous = simulate(taylor_green_velocity(grid), grid, 0.01, 0.005, steps=150, record_every=150).velocity[-1]
    after = simulate(viscous, grid, 0.01, 0.002, steps=1, record_every=1).velocity[-1]
    budget = vorticity_budget(viscous, after, 0.002, grid, 0.01)

    sizes = (16, 24, 32) if quick else (16, 24, 32, 48, 64)
    report: dict[str, object] = {
        "environment": environment_metadata(),
        "operator_errors": _operator_errors(24),
        "viscous_decay_relative_error": _viscous_decay_error(16),
        "inviscid_energy_drift": energy_drift,
        "inviscid_enstrophy_growth": enstrophy_growth,
        "max_divergence_linf": float(max(inviscid.divergence_linf)),
        "vorticity_budget": budget.as_dict(),
        "resolution_study": _resolution_study(sizes),
        "checkpoint": _checkpoint_roundtrip(output, overwrite),
    }

    failures: list[str] = []
    ops = report["operator_errors"]
    assert isinstance(ops, dict)
    for key in ("ddx_error", "ddy_error", "ddz_error", "abc_curl_error", "projection_divergence_linf"):
        if ops[key] > 1e-10:
            failures.append(f"Gate A: {key} = {ops[key]:.2e} > 1e-10")
    if report["viscous_decay_relative_error"] > 1e-6:  # type: ignore[operator]
        failures.append("Gate A: viscous decay error > 1e-6")
    if energy_drift > 1e-8:
        failures.append(f"Gate A: inviscid energy drift {energy_drift:.2e} > 1e-8")
    if enstrophy_growth <= 1.0:
        failures.append("Gate A: Taylor-Green enstrophy did not grow (stretching missing)")
    if report["max_divergence_linf"] > 1e-9:  # type: ignore[operator]
        failures.append("Gate A: divergence not controlled")
    if budget.closure_fraction > 0.05:
        failures.append(f"Gate A: vorticity-budget closure {budget.closure_fraction:.3f} > 0.05")
    checkpoint = report["checkpoint"]
    assert isinstance(checkpoint, dict)
    if not (checkpoint["load_identical"] and checkpoint["restart_deterministic"]):
        failures.append("Gate A: checkpoint restart not deterministic")
    return report, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.spectral3d")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="run the Gate-A solver validation suite")
    mode = validate.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    validate.add_argument("--output", required=True)
    validate.add_argument("--overwrite", action="store_true")
    arguments = parser.parse_args(argv)

    directory = prepare_output_directory(arguments.output)
    report, failures = _validate(quick=not arguments.full, output=directory, overwrite=arguments.overwrite)
    write_json(directory, "spectral3d_validation.json", report, overwrite=True)
    if failures:
        print("spectral3d Gate-A FAILED:")
        for message in failures:
            print(f"  - {message}")
        return 1
    budget = report["vorticity_budget"]
    assert isinstance(budget, dict)
    print(
        f"spectral3d Gate-A PASSED (divergence {report['max_divergence_linf']:.1e}, "
        f"budget closure {budget['closure_fraction']:.3f})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
