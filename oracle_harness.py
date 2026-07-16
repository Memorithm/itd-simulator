#!/usr/bin/env python3
"""Golden-oracle harness for the SciRust ITD port.

Runs the ITD V29 numerical core (operators + engine) and emits a
self-contained Rust fixture file (`oracle_data.rs`) with inputs and
expected outputs, so the Rust port can be validated against the
reference implementation to a tight numerical tolerance.

Run from the itd-simulator repository root:

    python3 oracle_harness.py /path/to/oracle_data.rs
"""

from __future__ import annotations

import math
import sys

import numpy as np

from itd_v29_core.spatial_geometry import RectilinearGeometry
from itd_v29_core.spatial_operators import (
    bounded,
    numerical_vorticity_with_boundary,
    scalar_gradient_with_boundary,
    spatial_mean,
)
from itd_v29_core.structural_metrics import structural_metrics
from itd_v29_core.simulation_engine import simulate

from compare_scenarios import (
    Config,
    calm_field,
    coherent_vortex,
    curvature_field,
    multi_vortex_field,
)


# ---------------------------------------------------------------------------
# Reproducible input fields (identical formulas will be rebuilt in Rust).
# ---------------------------------------------------------------------------
NY, NX = 5, 6
DX, DY = 0.5, 0.3


def build_field(fn) -> np.ndarray:
    out = np.empty((NY, NX), dtype=np.float64)
    for i in range(NY):
        for j in range(NX):
            out[i, j] = fn(i, j)
    return out


FIELD_A = build_field(
    lambda i, j: math.sin(0.7 * i + 0.3) * math.cos(0.5 * j - 0.2)
    + 0.11 * i
    - 0.07 * j
    + 0.4
)
FIELD_B = build_field(
    lambda i, j: math.cos(0.35 * i) * math.sin(0.45 * j + 0.15)
    - 0.06 * i
    + 0.05 * j
)
VX = build_field(
    lambda i, j: math.cos(0.4 * i) * math.sin(0.6 * j) + 0.2 * i - 0.1 * j
)
VY = build_field(
    lambda i, j: math.sin(0.5 * i + 0.1) - 0.3 * math.cos(0.35 * j) + 0.04 * i * j
)

X_COORDS = np.array([0.0, 0.4, 1.0, 1.3, 2.1, 2.2], dtype=np.float64)
Y_COORDS = np.array([0.0, 0.5, 0.9, 1.7, 2.0], dtype=np.float64)
RECT = RectilinearGeometry(X_COORDS, Y_COORDS)


# ---------------------------------------------------------------------------
# Rust emission helpers.
# ---------------------------------------------------------------------------
_LINES: list[str] = []


def emit(line: str = "") -> None:
    _LINES.append(line)


def f(x: float) -> str:
    x = float(x)
    if x != x:
        return "f64::NAN"
    if x == math.inf:
        return "f64::INFINITY"
    if x == -math.inf:
        return "f64::NEG_INFINITY"
    return repr(x)


def flat(name: str, arr: np.ndarray) -> None:
    values = ", ".join(f(v) for v in np.asarray(arr, dtype=np.float64).ravel())
    emit(f"pub static {name}: &[f64] = &[{values}];")


def scalar(name: str, value: float) -> None:
    emit(f"pub const {name}: f64 = {f(value)};")


# ---------------------------------------------------------------------------
# Operator fixtures.
# ---------------------------------------------------------------------------
def emit_operators() -> None:
    emit("// ---- shared input fields (row-major, NY x NX) ----")
    emit(f"pub const NY: usize = {NY};")
    emit(f"pub const NX: usize = {NX};")
    scalar("DX", DX)
    scalar("DY", DY)
    flat("FIELD_A", FIELD_A)
    flat("FIELD_B", FIELD_B)
    flat("VX", VX)
    flat("VY", VY)
    flat("X_COORDS", X_COORDS)
    flat("Y_COORDS", Y_COORDS)
    emit()

    # gradient: uniform finite (anisotropic dx != dy)
    gy, gx = scalar_gradient_with_boundary(FIELD_A, (DX, DY), "finite")
    flat("GRAD_UF_GY", gy)
    flat("GRAD_UF_GX", gx)
    # gradient: uniform periodic
    gy, gx = scalar_gradient_with_boundary(FIELD_A, (DX, DY), "periodic")
    flat("GRAD_UP_GY", gy)
    flat("GRAD_UP_GX", gx)
    # gradient: rectilinear finite (non-uniform)
    gy, gx = scalar_gradient_with_boundary(FIELD_A, RECT, "finite")
    flat("GRAD_RECT_GY", gy)
    flat("GRAD_RECT_GX", gx)
    emit()

    # vorticity
    flat("VORT_UF", numerical_vorticity_with_boundary(VX, VY, (DX, DY), "finite"))
    flat(
        "VORT_UF_ISO",
        numerical_vorticity_with_boundary(VX, VY, DX, "finite"),
    )
    flat("VORT_UP", numerical_vorticity_with_boundary(VX, VY, (DX, DY), "periodic"))
    flat("VORT_RECT", numerical_vorticity_with_boundary(VX, VY, RECT, "finite"))
    emit()

    # spatial mean
    scalar("MEAN_UF", spatial_mean(FIELD_A, (DX, DY), "finite"))
    scalar("MEAN_UP", spatial_mean(FIELD_A, (DX, DY), "periodic"))
    scalar("MEAN_RECT", spatial_mean(FIELD_A, RECT, "finite"))
    emit()

    # bounded map
    flat(
        "BOUNDED_IN",
        np.array([0.0, 0.25, 1.0, 3.0, 10.0, 1234.5], dtype=np.float64),
    )
    flat(
        "BOUNDED_OUT",
        np.array(
            [bounded(v) for v in (0.0, 0.25, 1.0, 3.0, 10.0, 1234.5)],
            dtype=np.float64,
        ),
    )
    emit()

    # structural metrics (uniform finite, with a previous field + dt)
    dt = 0.25
    m = structural_metrics(
        FIELD_A,
        (DX, DY),
        FIELD_B,
        dt,
        structural_length=0.5,
        boundary_mode="finite",
    )
    scalar("SM_DT", dt)
    scalar("SM_LEN", 0.5)
    for key in (
        "heterogeneity",
        "localization",
        "roughness",
        "sign_mixing",
        "temporal_deformation",
        "structure_score",
    ):
        scalar(f"SM_{key.upper()}", m[key])
    emit()


# ---------------------------------------------------------------------------
# Scenario fixtures.
# ---------------------------------------------------------------------------
SCENARIOS = (
    ("calm", calm_field),
    ("coherent", coherent_vortex),
    ("multi", multi_vortex_field),
)


def run_scenarios(grid_size: int, time_steps: int, tag: str) -> None:
    cfg = Config(grid_size=grid_size, time_steps=time_steps)
    coords = np.linspace(cfg.domain_min, cfg.domain_max, cfg.grid_size, dtype=np.float64)
    x, y = np.meshgrid(coords, coords, indexing="xy")
    spacing = float(coords[1] - coords[0])
    times = np.linspace(0.0, cfg.duration, cfg.time_steps, dtype=np.float64)

    emit(f"// ---- scenarios {tag} (grid={grid_size}, steps={time_steps}) ----")
    for name, vf in SCENARIOS:
        r = simulate(name, vf, x, y, times, spacing, cfg)
        up = name.upper()
        scalar(f"SC_{tag}_{up}_INTENSITY", r["intensity_index"])
        scalar(f"SC_{tag}_{up}_STRUCTURE", r["structure_index"])
        scalar(f"SC_{tag}_{up}_COUPLED", r["coupled_index"])
        ci = r["component_indices"]
        scalar(f"SC_{tag}_{up}_HET", ci["heterogeneity"])
        scalar(f"SC_{tag}_{up}_LOC", ci["localization"])
        scalar(f"SC_{tag}_{up}_ROU", ci["roughness"])
        scalar(f"SC_{tag}_{up}_SGN", ci["sign_mixing"])
        scalar(f"SC_{tag}_{up}_TMP", ci["temporal_deformation"])
        # a few sampled nodal series values (small grid only)
        if tag == "SMALL":
            idxs = [1, time_steps // 2, time_steps - 1]
            emit(
                f"pub static SC_{tag}_{up}_SAMPLE_IDX: &[usize] = &["
                + ", ".join(str(k) for k in idxs)
                + "];"
            )
            flat(
                f"SC_{tag}_{up}_SAMPLE_INTENSITY_RATE",
                np.asarray(r["intensity_rate"])[idxs],
            )
            flat(
                f"SC_{tag}_{up}_SAMPLE_HET",
                np.asarray(r["heterogeneity"])[idxs],
            )
            flat(
                f"SC_{tag}_{up}_SAMPLE_ROU",
                np.asarray(r["roughness"])[idxs],
            )
        print(
            f"[{tag}] {name:9s} I={r['intensity_index']:.12f} "
            f"S={r['structure_index']:.12f} C={r['coupled_index']:.12f}"
        )
    emit()


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "oracle_data.rs"
    emit("// AUTO-GENERATED from ITD V29 via numpy. Do not edit by hand.")
    emit("// Regenerate with: python3 oracle_harness.py <out>")
    emit("// Included via `mod oracle_data { include!(...) }` in tests/oracle.rs.")
    emit()
    emit_operators()
    run_scenarios(41, 41, "SMALL")
    run_scenarios(161, 401, "FULL")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_LINES) + "\n")
    print(f"wrote {out_path} ({len(_LINES)} lines)")


if __name__ == "__main__":
    main()
