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

from itd_v29_core.spatial_geometry import RectilinearGeometry, SpatialGeometry
from itd_v29_core.spatial_operators import (
    bounded,
    numerical_vorticity_with_boundary,
    scalar_gradient_with_boundary,
    spatial_mean,
)
from itd_v29_core.structural_metrics import structural_metrics
from itd_v29_core.simulation_engine import simulate
from itd_v29_core.periodic_transport import (
    transport_previous_vorticity_periodic,
)
from itd_v29_core.geometric_transforms import (
    BilinearTransformPlan,
    rotation_matrix,
    transform_coordinates,
)
from itd_v29_core.spatial_scaling import (
    inverse_scale_coordinates,
    scale_length,
    scale_spatial_geometry,
)
from itd_v29_core.reference_frames import (
    galilean_source_coordinates,
    translating_frame_source_coordinates,
)
from itd_v29_core.multiscale_structure import derive_multiscale_profile
from itd_v29_core.material_interval import material_vorticity_interval
from itd_v29_core.material_deformation import simulate_material_deformation

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


# ---------------------------------------------------------------------------
# Transport (semi-Lagrangian) fixtures.
# ---------------------------------------------------------------------------
TNX, TNY = 8, 6
TX_COORDS = np.array(
    [k * (2.0 * math.pi / TNX) for k in range(TNX)], dtype=np.float64
)
TY_COORDS = np.array(
    [k * (2.0 * math.pi / TNY) for k in range(TNY)], dtype=np.float64
)


def _tprev(i: int, j: int) -> float:
    x = TX_COORDS[j]
    y = TY_COORDS[i]
    return (
        math.sin(x) * math.cos(y)
        + 0.3 * math.cos(2.0 * x - y)
    )


def transport_velocity(x, y, t):
    """A smooth 2*pi-periodic transport velocity (wrapping is a no-op)."""
    return (
        0.4 * np.cos(x + 0.2 * t) * np.sin(y),
        -0.4 * np.sin(x) * np.cos(y - 0.1 * t),
    )


def _tprev_sharp(i: int, j: int) -> float:
    """Smooth base plus a localized spike so the cubic overshoots and the
    local limiters genuinely activate."""
    x = TX_COORDS[j]
    y = TY_COORDS[i]
    spike = 2.5 if (i == 2 and j == 3) else 0.0
    return math.sin(x) * math.cos(y) + spike


TRANSPORT_COMBOS = (
    ("BILINEAR", "MIDPOINT", "bilinear_periodic", "midpoint_time_velocity"),
    ("BILINEAR", "RK4", "bilinear_periodic", "rk4_backtrace"),
    ("CUBIC", "MIDPOINT", "cubic_periodic", "midpoint_time_velocity"),
    ("CUBIC", "RK4", "cubic_periodic", "rk4_backtrace"),
)

LIMITER_COMBOS = (
    ("CUBIC", "MIDPOINT", "cubic_periodic", "midpoint_time_velocity"),
    ("CUBIC", "RK4", "cubic_periodic", "rk4_backtrace"),
    ("BOUNDED", "MIDPOINT", "cubic_local_bounded_periodic", "midpoint_time_velocity"),
    ("BOUNDED", "RK4", "cubic_local_bounded_periodic", "rk4_backtrace"),
    ("SUMPRES", "MIDPOINT", "cubic_local_sum_preserving_periodic", "midpoint_time_velocity"),
    ("SUMPRES", "RK4", "cubic_local_sum_preserving_periodic", "rk4_backtrace"),
)


def emit_transport() -> None:
    prev = np.empty((TNY, TNX), dtype=np.float64)
    for i in range(TNY):
        for j in range(TNX):
            prev[i, j] = _tprev(i, j)

    x_mesh, y_mesh = np.meshgrid(TX_COORDS, TY_COORDS, indexing="xy")
    prev_time, cur_time = 0.5, 0.9

    emit("// ---- transport fixtures (periodic grid TNY x TNX) ----")
    emit(f"pub const TNY: usize = {TNY};")
    emit(f"pub const TNX: usize = {TNX};")
    flat("TX_COORDS", TX_COORDS)
    flat("TY_COORDS", TY_COORDS)
    flat("TPREV", prev)
    scalar("T_PREV_TIME", prev_time)
    scalar("T_CUR_TIME", cur_time)

    for interp_tag, traj_tag, interp, traj in TRANSPORT_COMBOS:
        result = transport_previous_vorticity_periodic(
            prev,
            x_mesh,
            y_mesh,
            TX_COORDS,
            TY_COORDS,
            prev_time,
            cur_time,
            transport_velocity,
            transport_interpolation=interp,
            transport_trajectory_method=traj,
        )
        flat(f"T_{interp_tag}_{traj_tag}", result)

    # Limiter fixtures on a sharp field (spike) so the cubic overshoots and the
    # convex / sum-preserving limiters do real work. Emitted for both the sharp
    # and the smooth field.
    sharp = np.empty((TNY, TNX), dtype=np.float64)
    for i in range(TNY):
        for j in range(TNX):
            sharp[i, j] = _tprev_sharp(i, j)
    flat("TPREV_SHARP", sharp)

    for field_tag, field in (("SHARP", sharp), ("SMOOTH", prev)):
        for interp_tag, traj_tag, interp, traj in LIMITER_COMBOS:
            result = transport_previous_vorticity_periodic(
                field,
                x_mesh,
                y_mesh,
                TX_COORDS,
                TY_COORDS,
                prev_time,
                cur_time,
                transport_velocity,
                transport_interpolation=interp,
                transport_trajectory_method=traj,
            )
            flat(f"TL_{field_tag}_{interp_tag}_{traj_tag}", result)
    emit()


def run_transport_scenarios(grid_size: int, time_steps: int) -> None:
    cfg = Config(grid_size=grid_size, time_steps=time_steps)
    coords = np.linspace(cfg.domain_min, cfg.domain_max, cfg.grid_size, dtype=np.float64)
    x, y = np.meshgrid(coords, coords, indexing="xy")
    spacing = float(coords[1] - coords[0])
    times = np.linspace(0.0, cfg.duration, cfg.time_steps, dtype=np.float64)

    cases = (
        ("COHERENT", coherent_vortex, "bilinear_periodic", "midpoint_time_velocity"),
        ("MULTI", multi_vortex_field, "cubic_periodic", "rk4_backtrace"),
    )
    emit(f"// ---- transport-compensated engine indices (grid={grid_size}) ----")
    for up, vf, interp, traj in cases:
        r = simulate(
            up.lower(),
            vf,
            x,
            y,
            times,
            spacing,
            cfg,
            boundary_mode="periodic",
            temporal_deformation_mode="transport_compensated",
            transport_velocity_function=vf,
            transport_interpolation=interp,
            transport_trajectory_method=traj,
        )
        scalar(f"TC_{up}_INTENSITY", r["intensity_index"])
        scalar(f"TC_{up}_STRUCTURE", r["structure_index"])
        scalar(f"TC_{up}_COUPLED", r["coupled_index"])
        ci = r["component_indices"]
        scalar(f"TC_{up}_TMP", ci["temporal_deformation"])
        scalar(
            f"TC_{up}_EUL_IDX", r["temporal_deformation_eulerian_index"]
        )
        scalar(
            f"TC_{up}_COMP_IDX",
            r["temporal_deformation_compensated_index"],
        )
        print(
            f"[TC] {up.lower():9s} I={r['intensity_index']:.10f} "
            f"S={r['structure_index']:.10f} "
            f"comp={r['temporal_deformation_compensated_index']:.10f}"
        )
    emit()


# ---------------------------------------------------------------------------
# Geometric-transform fixtures (rotation / reflection covariance of a field).
# ---------------------------------------------------------------------------
GTX = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float64)  # nx=5, dx=0.5
GTY = np.array([0.0, 0.4, 0.8, 1.2], dtype=np.float64)  # ny=4, dy=0.4
GT_ANGLE = 0.37
GT_ORIGIN = (1.0, 0.6)


def _gfield(fn) -> np.ndarray:
    out = np.empty((GTY.size, GTX.size), dtype=np.float64)
    for i in range(GTY.size):
        for j in range(GTX.size):
            out[i, j] = fn(float(GTX[j]), float(GTY[i]))
    return out


def emit_transforms() -> None:
    scalar_field = _gfield(
        lambda x, y: math.sin(1.3 * x) * math.cos(0.9 * y) + 0.2 * x - 0.1 * y
    )
    vx = _gfield(lambda x, y: math.cos(0.8 * x) + 0.3 * y)
    vy = _gfield(lambda x, y: math.sin(0.6 * y) - 0.2 * x)

    emit("// ---- geometric-transform fixtures ----")
    emit(f"pub const GT_NY: usize = {GTY.size};")
    emit(f"pub const GT_NX: usize = {GTX.size};")
    flat("GTX", GTX)
    flat("GTY", GTY)
    flat("GT_SCALAR", scalar_field)
    flat("GT_VX", vx)
    flat("GT_VY", vy)
    scalar("GT_ANGLE", GT_ANGLE)
    flat("GT_ORIGIN", np.array(GT_ORIGIN, dtype=np.float64))

    # A handful of rotation matrices (row-major 2x2 -> 4 values).
    rot_angles = (0.0, math.pi / 6.0, -1.2, GT_ANGLE)
    flat("GT_ROT_ANGLES", np.array(rot_angles, dtype=np.float64))
    for k, ang in enumerate(rot_angles):
        flat(f"GT_ROT_{k}", rotation_matrix(ang))

    q = rotation_matrix(GT_ANGLE)

    # transform_coordinates over the (flattened, row-major) target grid.
    tx_mesh, ty_mesh = np.meshgrid(GTX, GTY, indexing="xy")
    scx, scy = transform_coordinates(tx_mesh, ty_mesh, q)
    flat("GT_COORD_SX", scx)
    flat("GT_COORD_SY", scy)

    plan = BilinearTransformPlan(GTX, GTY, q, origin=GT_ORIGIN, fill_value=0.0)
    assert not plan.uses_exact_node_map, "generic rotation must not be node-aligned"
    flat("GT_T_SCALAR", plan.transform_scalar(scalar_field))
    tvx, tvy = plan.transform_vector(vx, vy)
    flat("GT_T_VX", tvx)
    flat("GT_T_VY", tvy)

    # Exact node map: square grid, 90-degree rotation about the centre.
    sq = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float64)  # 5x5, d=1
    sqf = np.empty((sq.size, sq.size), dtype=np.float64)
    for i in range(sq.size):
        for j in range(sq.size):
            sqf[i, j] = (
                math.sin(0.7 * sq[j])
                + math.cos(0.5 * sq[i])
                + 0.1 * sq[j] * sq[i]
            )
    q90 = rotation_matrix(math.pi / 2.0)
    plan90 = BilinearTransformPlan(sq, sq, q90, origin=(2.0, 2.0), fill_value=0.0)
    assert plan90.uses_exact_node_map, "90-deg rotation about centre is node-aligned"
    emit(f"pub const GT_SQ_N: usize = {sq.size};")
    flat("GT_SQ", sq)
    flat("GT_SQF", sqf)
    flat("GT_SQ_ROT90", plan90.transform_scalar(sqf))
    emit()


# ---------------------------------------------------------------------------
# Covariance fixtures (spatial scaling + reference frames).
# ---------------------------------------------------------------------------
COV_X = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float64)
COV_Y = np.array([0.2, 0.7, 1.1, 1.6, 2.3], dtype=np.float64)


def emit_covariance() -> None:
    a = 1.75
    origin = (0.3, -0.4)

    emit("// ---- covariance (spatial scaling + reference frames) fixtures ----")
    flat("COV_X", COV_X)
    flat("COV_Y", COV_Y)
    scalar("COV_A", a)
    flat("COV_ORIGIN", np.array(origin, dtype=np.float64))

    sx, sy = inverse_scale_coordinates(COV_X, COV_Y, a, origin)
    flat("COV_INV_SX", sx)
    flat("COV_INV_SY", sy)

    scalar("COV_LEN_IN", 0.8)
    scalar("COV_LEN_OUT", scale_length(0.8, a))

    uniform = scale_spatial_geometry(SpatialGeometry(0.5, 0.3), a, origin)
    scalar("COV_SCALED_DX", uniform.dx)
    scalar("COV_SCALED_DY", uniform.dy)

    rect = scale_spatial_geometry(RectilinearGeometry(COV_X, COV_Y), a, origin)
    flat("COV_SCALED_RX", rect.x_coordinates)
    flat("COV_SCALED_RY", rect.y_coordinates)

    frame_velocity = (0.4, -0.25)
    time, reference_time = 1.3, 0.5
    flat("COV_C", np.array(frame_velocity, dtype=np.float64))
    scalar("COV_T", time)
    scalar("COV_T0", reference_time)
    gsx, gsy = galilean_source_coordinates(
        COV_X, COV_Y, time, frame_velocity, reference_time
    )
    flat("COV_GAL_SX", gsx)
    flat("COV_GAL_SY", gsy)

    displacement = (0.15, 0.6)
    flat("COV_B", np.array(displacement, dtype=np.float64))
    tsx, tsy = translating_frame_source_coordinates(
        COV_X, COV_Y, 0.0, lambda _t: np.array(displacement, dtype=np.float64)
    )
    flat("COV_TRANS_SX", tsx)
    flat("COV_TRANS_SY", tsy)
    emit()


# ---------------------------------------------------------------------------
# Multiscale-profile fixtures (derived from one structural_length = 1 run).
# ---------------------------------------------------------------------------
def emit_multiscale() -> None:
    cfg = Config(grid_size=21, time_steps=9)
    coords = np.linspace(cfg.domain_min, cfg.domain_max, cfg.grid_size, dtype=np.float64)
    x, y = np.meshgrid(coords, coords, indexing="xy")
    spacing = float(coords[1] - coords[0])
    times = np.linspace(0.0, cfg.duration, cfg.time_steps, dtype=np.float64)
    r = simulate(
        "coherent", coherent_vortex, x, y, times, spacing, cfg, structural_length=1.0
    )
    lengths = np.array([0.25, 0.5, 1.0, 2.0], dtype=np.float64)
    profile = derive_multiscale_profile(r, lengths)

    emit("// ---- multiscale profile fixtures (reference run at ell = 1) ----")
    emit(f"pub const MS_NODES: usize = {np.asarray(r['intensity_rate']).size};")
    flat("MS_INTENSITY_RATE", np.asarray(r["intensity_rate"]))
    flat("MS_HETEROGENEITY", np.asarray(r["heterogeneity"]))
    flat("MS_LOCALIZATION", np.asarray(r["localization"]))
    flat("MS_UNIT_ROUGHNESS", np.asarray(r["roughness"]))
    flat("MS_SIGN_MIXING", np.asarray(r["sign_mixing"]))
    flat("MS_TDEF_INTERVAL", np.asarray(r["temporal_deformation_interval"]))
    flat("MS_INTERVAL_DT", np.asarray(r["temporal_interval_dt"]))
    flat("MS_WEIGHTS", np.asarray(r["structural_weights"], dtype=np.float64))
    scalar("MS_INTENSITY_INDEX", r["intensity_index"])
    scalar("MS_TDEF_INDEX", r["temporal_deformation_index"])
    emit(f"pub const MS_LENGTH_COUNT: usize = {lengths.size};")
    flat("MS_LENGTHS", lengths)
    flat("MS_SIGNATURES", np.asarray(profile["structural_signatures"]))
    flat("MS_STRUCTURE_IDX", np.asarray(profile["structure_indices"]))
    flat("MS_COUPLED_IDX", np.asarray(profile["coupled_indices"]))
    flat("MS_RAW_ROUGH_IDX", np.asarray(profile["raw_roughness_indices"]))
    emit()


# ---------------------------------------------------------------------------
# Material-derivative interval fixtures.
# ---------------------------------------------------------------------------
def emit_material() -> None:
    mny, mnx = 5, 6
    mdx, mdy = 0.5, 0.3

    def mbuild(fn) -> np.ndarray:
        out = np.empty((mny, mnx), dtype=np.float64)
        for i in range(mny):
            for j in range(mnx):
                out[i, j] = fn(i, j)
        return out

    prev = mbuild(lambda i, j: math.sin(0.6 * i) * math.cos(0.4 * j) + 0.1 * i)
    cur = mbuild(
        lambda i, j: math.sin(0.6 * i + 0.2) * math.cos(0.4 * j - 0.1)
        + 0.1 * i
        + 0.05 * j
    )
    mvx = mbuild(lambda i, j: 0.3 * math.cos(0.5 * j) + 0.1 * i)
    mvy = mbuild(lambda i, j: -0.2 * math.sin(0.4 * i) + 0.05 * j)
    dt = 0.25
    res = material_vorticity_interval(
        prev, cur, mvx, mvy, (mdx, mdy), dt, boundary_mode="finite"
    )

    emit("// ---- material-derivative interval fixtures ----")
    emit(f"pub const MAT_NY: usize = {mny};")
    emit(f"pub const MAT_NX: usize = {mnx};")
    scalar("MAT_DX", mdx)
    scalar("MAT_DY", mdy)
    scalar("MAT_DT", dt)
    flat("MAT_PREV", prev)
    flat("MAT_CUR", cur)
    flat("MAT_VX", mvx)
    flat("MAT_VY", mvy)
    flat("MAT_TEMPORAL", res["temporal_tendency"])
    flat("MAT_ADVECTIVE", res["advective_tendency"])
    flat("MAT_MATERIAL", res["material_tendency"])
    scalar("MAT_REF_RMS", res["reference_rms"])
    scalar("MAT_PREV_RMS", res["previous_rms"])
    scalar("MAT_CUR_RMS", res["current_rms"])
    scalar("MAT_EUL_RATE", res["eulerian_rate"])
    scalar("MAT_ADV_RATE", res["advective_rate"])
    scalar("MAT_MAT_RATE", res["material_rate"])
    emit()


# ---------------------------------------------------------------------------
# Material-deformation orchestration fixtures.
# ---------------------------------------------------------------------------
def emit_material_deformation() -> None:
    cfg = Config(grid_size=21, time_steps=9)
    coords = np.linspace(cfg.domain_min, cfg.domain_max, cfg.grid_size, dtype=np.float64)
    x, y = np.meshgrid(coords, coords, indexing="xy")
    spacing = float(coords[1] - coords[0])
    times = np.linspace(0.0, cfg.duration, cfg.time_steps, dtype=np.float64)

    cases = (
        ("DEFAULT", multi_vortex_field, None),
        ("SEP", multi_vortex_field, coherent_vortex),
    )
    emit("// ---- material-deformation orchestration fixtures (grid=21, steps=9) ----")
    for tag, velocity, advection in cases:
        r = simulate_material_deformation(
            "multi",
            velocity,
            x,
            y,
            times,
            spacing,
            cfg,
            advection_velocity_function=advection,
        )
        assert r["material_eulerian_consistency_error"] < 1.0e-12
        flat(f"MD_{tag}_EUL_IV", np.asarray(r["material_eulerian_rate_interval"]))
        flat(f"MD_{tag}_ADV_IV", np.asarray(r["material_advective_rate_interval"]))
        flat(f"MD_{tag}_MAT_IV", np.asarray(r["material_deformation_interval"]))
        flat(f"MD_{tag}_EUL_NODAL", np.asarray(r["material_eulerian_rate"]))
        flat(f"MD_{tag}_ADV_NODAL", np.asarray(r["material_advective_rate"]))
        flat(f"MD_{tag}_MAT_NODAL", np.asarray(r["material_deformation"]))
        scalar(f"MD_{tag}_EUL_IDX", r["material_eulerian_rate_index"])
        scalar(f"MD_{tag}_ADV_IDX", r["material_advective_rate_index"])
        scalar(f"MD_{tag}_MAT_IDX", r["material_deformation_index"])
        scalar(f"MD_{tag}_CONSISTENCY", r["material_eulerian_consistency_error"])
        scalar(f"MD_{tag}_BASE_INTENSITY", r["intensity_index"])
        scalar(f"MD_{tag}_BASE_STRUCTURE", r["structure_index"])
        print(
            f"[MD] {tag:7s} eul={r['material_eulerian_rate_index']:.10f} "
            f"adv={r['material_advective_rate_index']:.10f} "
            f"mat={r['material_deformation_index']:.10f}"
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
    emit_transport()
    run_transport_scenarios(41, 41)
    emit_transforms()
    emit_covariance()
    emit_multiscale()
    emit_material()
    emit_material_deformation()
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_LINES) + "\n")
    print(f"wrote {out_path} ({len(_LINES)} lines)")


if __name__ == "__main__":
    main()
