"""Command-line external-validation runner: ``python -m itd_research.external_validation``.

Runs the deterministic ITD-versus-established-diagnostics suite on analytical
oracles, synthetic CFD-like flows, and a licensed experimental PIV field, plus a
transport-compensation (H3) demonstration. It writes JSON/CSV artifacts and a
manifest into an explicitly chosen output directory, never writing outside it and
refusing to overwrite unless asked. In ``--quick`` mode it also checks a set of
shear-versus-rotation invariants and exits non-zero on any violation, so CI
detects regressions.

    python -m itd_research.external_validation --quick --output /tmp/itd-extval
    python -m itd_research.external_validation --output /tmp/itd-extval \
        --piv-npz /data/biofilm_piv_full.npz
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from itd_research.external_validation import synthetic_flows as sf
from itd_research.external_validation.experiments import (
    ExperimentResult,
    analytical_cases,
    external_piv_case,
    run_suite,
    synthetic_cfd_cases,
)
from itd_research.external_validation.experiments_3d import (
    analytical_3d_cases,
    external_3d_case,
)
from itd_research.external_validation.hypotheses import (
    equal_enstrophy_separation,
    vortex_merger_sequence,
)
from itd_research.external_validation.spectral_ns import (
    energy_enstrophy,
    gaussian_vortex_pair,
    simulate_vorticity,
    spectral_grid,
    velocity_from_vorticity,
)
from itd_research.external_validation.transport import (
    translate_periodic,
    transport_decomposition,
)
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_csv,
    write_json,
    write_manifest,
)

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PIV = _ROOT / "tests" / "fixtures" / "external" / "biofilm_piv_excerpt.npz"


def _transport_demonstration() -> dict[str, object]:
    """Pure-translation test: transport compensation must shrink the Eulerian change."""
    grid = sf.periodic_grid_2d(64, 2.0 * np.pi)
    pattern = np.sin(grid.xx) * np.cos(grid.yy)
    u_advect, v_advect, delta_time = 1.0, 0.4, 0.05
    dx, dy = grid.spacing
    shifted = translate_periodic(
        pattern, shift_x=u_advect * delta_time / dx, shift_y=v_advect * delta_time / dy
    )
    decomposition = transport_decomposition(
        pattern,
        shifted,
        u_advect * np.ones_like(pattern),
        v_advect * np.ones_like(pattern),
        grid.x,
        grid.y,
        delta_time,
        "periodic",
    )
    record: dict[str, object] = dict(decomposition.as_dict())
    record["case"] = "pure_translation_taylor_pattern"
    record["advecting_velocity"] = [u_advect, v_advect]
    record["delta_time"] = delta_time
    return record


def _spectral_ns_demonstration() -> dict[str, object]:
    """Run the in-environment NS solver: conservation + transport-vs-deformation.

    A short inviscid run checks energy/enstrophy conservation (solver validation);
    a viscous step checks that the transport-compensated residual recovers the
    exact viscous material derivative ``nu*laplacian(omega)`` on genuine dynamics.
    """
    grid = spectral_grid(48, 2.0 * np.pi)
    x = grid.coordinates
    omega0 = gaussian_vortex_pair(grid, circulation=2.0, core=0.6, separation=1.6)

    inviscid = simulate_vorticity(omega0, grid, 0.0, 0.002, steps=150, record_every=150)
    energy0, enstrophy0 = energy_enstrophy(inviscid.vorticity[0], grid)
    energy1, enstrophy1 = energy_enstrophy(inviscid.vorticity[-1], grid)
    energy_drift = abs(energy1 - energy0) / energy0
    enstrophy_drift = abs(enstrophy1 - enstrophy0) / enstrophy0

    viscosity = 0.01
    warmed = simulate_vorticity(omega0, grid, viscosity, 0.001, steps=200, record_every=200).vorticity[-1]
    delta_time = 0.001
    after = simulate_vorticity(warmed, grid, viscosity, delta_time, steps=1, record_every=1).vorticity[-1]
    u, v = velocity_from_vorticity(warmed, grid)
    decomposition = transport_decomposition(warmed, after, u, v, x, x, delta_time, "periodic")
    expected = viscosity * np.fft.ifft2(-grid.k_squared * np.fft.fft2(warmed)).real
    residual_rms = decomposition.residual_rms
    viscous_match = (
        float(np.sqrt(np.mean((decomposition.material_residual - expected) ** 2))) / residual_rms
        if residual_rms > 0.0 else 0.0
    )
    return {
        "energy_drift": energy_drift,
        "enstrophy_drift": enstrophy_drift,
        "eulerian_rms": decomposition.eulerian_rms,
        "advective_rms": decomposition.advective_rms,
        "residual_rms": residual_rms,
        "residual_fraction": decomposition.residual_fraction,
        "viscous_match_relative_error": viscous_match,
    }


def _check_invariants(results: list[ExperimentResult]) -> list[str]:
    """Return a list of violated shear-versus-rotation invariants (empty = all pass)."""
    by_name = {result.name: result for result in results}
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    if "rigid_rotation" in by_name:
        r = by_name["rigid_rotation"]
        require(r.regions["rotation_fraction"] > 0.99, "rigid_rotation: rotation_fraction should be ~1")
        require(r.diagnostics["vorticity_rms"] > 0.1, "rigid_rotation: vorticity_rms should be > 0")
        require(abs(r.itd["heterogeneity"]) < 1e-6, "rigid_rotation: ITD heterogeneity should be ~0")
    if "pure_strain" in by_name:
        r = by_name["pure_strain"]
        require(r.diagnostics["vorticity_rms"] < 1e-9, "pure_strain: vorticity_rms should be ~0")
        require(r.regions["rotation_fraction"] < 1e-9, "pure_strain: rotation_fraction should be 0")
    if "simple_shear" in by_name:
        r = by_name["simple_shear"]
        require(r.diagnostics["vorticity_rms"] > 0.1, "simple_shear: vorticity_rms should be large")
        require(r.regions["rotation_fraction"] < 1e-9, "simple_shear: rotation_fraction should be 0")
        require(r.regions["jaccard_highomega_rotation"] < 1e-9,
                "simple_shear: high-vorticity/rotation overlap should be 0")
        require(r.itd["intensity"] > 0.1, "simple_shear: ITD intensity should be non-zero (shear-inflated)")
    if "lamb_oseen" in by_name:
        r = by_name["lamb_oseen"]
        require(0.0 < r.regions["rotation_fraction"] < 0.5, "lamb_oseen: rotation_fraction in (0,0.5)")
        require(r.regions["rotation_components"] == 1.0, "lamb_oseen: exactly one rotation component")
    if "vortex_pair" in by_name:
        r = by_name["vortex_pair"]
        require(r.regions["rotation_components"] == 2.0, "vortex_pair: exactly two rotation components")
    if "taylor_green" in by_name:
        r = by_name["taylor_green"]
        require(0.3 < r.regions["rotation_fraction"] < 0.7,
                "taylor_green: rotation_fraction near one half")
    return failures


def _summary_rows(results: list[ExperimentResult]) -> list[list[object]]:
    rows: list[list[object]] = []
    for r in results:
        rows.append([
            r.category,
            r.name,
            r.shape[0] * r.shape[1],
            r.diagnostics["vorticity_rms"],
            r.diagnostics["q_mean"],
            r.regions["rotation_fraction"],
            r.regions["jaccard_highomega_rotation"],
            int(r.regions["rotation_components"]),
            r.itd["intensity"],
            r.itd["heterogeneity"],
            r.itd["localization"],
            r.itd["roughness"],
            r.itd["sign_mixing"],
        ])
    return rows


def _maybe_plot(results: list[ExperimentResult], directory: Path, overwrite: bool) -> Path | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("matplotlib not available; skipping --plots.")
        return None
    names = [r.name for r in results]
    rotation = [r.regions["rotation_fraction"] for r in results]
    jaccard = [r.regions["jaccard_highomega_rotation"] for r in results]
    figure, axis = plt.subplots(figsize=(10, 4))
    index = np.arange(len(names))
    axis.bar(index - 0.2, rotation, width=0.4, label="rotation fraction (Q>0)")
    axis.bar(index + 0.2, jaccard, width=0.4, label="Jaccard(high |omega|, Q>0)")
    axis.set_xticks(index)
    axis.set_xticklabels(names, rotation=60, ha="right", fontsize=7)
    axis.set_ylabel("fraction / overlap")
    axis.set_title("Vorticity magnitude vs rotation across flows")
    axis.legend(fontsize=8)
    figure.tight_layout()
    target = directory / "rotation_overlap.png"
    if target.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite {target}")
    figure.savefig(target, dpi=120)
    plt.close(figure)
    return target


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="itd_research.external_validation",
        description="Deterministic ITD-vs-established-diagnostics external-validation suite.",
    )
    parser.add_argument("--output", required=True, help="output directory (created if absent).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="run the suite and check invariants (default).")
    mode.add_argument("--full", action="store_true", help="same suite; alias reserved for larger runs.")
    parser.add_argument("--piv-npz", default=None,
                        help="path to an external PIV .npz (default: the committed excerpt fixture).")
    parser.add_argument("--jhtdb-npz", default=None,
                        help="path to a 3D DNS .npz (from fetch_jhtdb_cutout.py) for the 3D case.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--plots", action="store_true", help="also write a summary figure (needs matplotlib).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    directory = prepare_output_directory(arguments.output)

    cases = analytical_cases() + synthetic_cfd_cases()
    piv_path = Path(arguments.piv_npz) if arguments.piv_npz else _DEFAULT_PIV
    external_note = "committed CC-BY excerpt" if piv_path == _DEFAULT_PIV else str(piv_path)
    if piv_path.exists():
        cases.append(external_piv_case(piv_path))
    else:
        print(f"external PIV field not found at {piv_path}; running without the external case.")

    results = run_suite(cases)
    transport = _transport_demonstration()
    spectral_ns = _spectral_ns_demonstration()
    h1 = equal_enstrophy_separation()
    merger = vortex_merger_sequence()

    comparison_3d = analytical_3d_cases()
    if arguments.jhtdb_npz and Path(arguments.jhtdb_npz).exists():
        comparison_3d.append(external_3d_case(arguments.jhtdb_npz))

    payload: dict[str, object] = {
        "environment": environment_metadata(),
        "external_piv_source": external_note,
        "results": [result.as_dict() for result in results],
        "comparison_3d": [result.as_dict() for result in comparison_3d],
        "transport_h3": transport,
        "spectral_ns": spectral_ns,
        "equal_enstrophy_h1": h1,
        "vortex_merger_h2": merger,
    }
    artifacts = [
        write_json(directory, "external_validation.json", payload, overwrite=arguments.overwrite),
        write_csv(
            directory,
            "external_validation_summary.csv",
            [
                "category", "name", "cells", "vorticity_rms", "q_mean",
                "rotation_fraction", "jaccard_highomega_rotation", "rotation_components",
                "itd_intensity", "itd_heterogeneity", "itd_localization",
                "itd_roughness", "itd_sign_mixing",
            ],
            _summary_rows(results),
            overwrite=arguments.overwrite,
        ),
    ]
    if arguments.plots:
        figure_path = _maybe_plot(results, directory, arguments.overwrite)
        if figure_path is not None:
            artifacts.append(figure_path)

    write_manifest(directory, artifacts, environment_metadata(),
                   name="external_validation_manifest.json", overwrite=arguments.overwrite)

    failures = _check_invariants(results)
    # H1: equal enstrophy, the ITD vector must still separate the two fields.
    if not h1["enstrophy_matched"]:
        failures.append("equal_enstrophy_h1: enstrophy was not matched")
    if not (isinstance(h1["localization_ratio"], float) and h1["localization_ratio"] > 5.0):
        failures.append("equal_enstrophy_h1: ITD localization should separate the fields (>5x)")
    # H2: the significant-rotation-region count must drop from two to one at merger.
    region_counts: list[int] = []
    for frame in merger:
        value = frame["significant_rotation_regions"]
        if isinstance(value, int):
            region_counts.append(value)
    if not (region_counts and max(region_counts) >= 2 and region_counts[-1] == 1):
        failures.append("vortex_merger_h2: significant rotation regions should go 2 -> 1")
    # In-environment NS solver: inviscid conservation and the transport residual
    # must recover the exact viscous material derivative on genuine dynamics.
    if spectral_ns["energy_drift"] > 1e-6 or spectral_ns["enstrophy_drift"] > 1e-6:  # type: ignore[operator]
        failures.append("spectral_ns: inviscid energy/enstrophy not conserved")
    if spectral_ns["viscous_match_relative_error"] > 0.20:  # type: ignore[operator]
        failures.append("spectral_ns: transport residual does not recover nu*laplacian(omega)")
    # 3D: the ABC/Beltrami oracle must give normalized helicity 1 and Q>0 ~ lambda2<0.
    for result in comparison_3d:
        if result.name == "abc_flow":
            if abs(result.itd3d["normalized_helicity"] - 1.0) > 1e-6:
                failures.append("comparison_3d abc_flow: normalized helicity should be 1")
            if result.regions["jaccard_q_lambda2"] < 0.5:
                failures.append("comparison_3d abc_flow: Q>0 and lambda2<0 should largely agree")

    if failures:
        print("external-validation invariants FAILED:")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"external-validation suite: {len(results)} 2D + {len(comparison_3d)} 3D cases, "
          f"invariants PASSED (H3 residual fraction {transport['residual_fraction']:.3f}; "
          f"H1 localization ratio {h1['localization_ratio']:.1f}x).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
