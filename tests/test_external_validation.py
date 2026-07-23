"""Tests for the external-validation comparison, transport, and experiment layer."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.external_validation import synthetic_flows as sf
from itd_research.external_validation.comparison import (
    compare_scalar_fields,
    connected_components,
    pearson_correlation,
    region_overlap,
    spearman_correlation,
    threshold_region,
)
from itd_research.external_validation.experiments import (
    analytical_cases,
    external_piv_case,
    run_case,
    synthetic_cfd_cases,
)
from itd_research.external_validation.experiments_3d import (
    aggregate_3d_channels,
    analytical_3d_cases,
    fluctuation_intensity,
    intermittency_factor,
    laminar_reference_profile,
    run_3d_comparison,
    temporal_intermittency,
    transition_markers,
)
from itd_research.external_validation.hypotheses import (
    equal_enstrophy_separation,
    vortex_merger_sequence,
)
from itd_research.external_validation.transport import (
    translate_periodic,
    transport_decomposition,
    transport_decomposition_3d,
)

_PIV_FIXTURE = "tests/fixtures/external/biofilm_piv_excerpt.npz"


# --------------------------------------------------------------------------- #
# Comparison metrics.                                                         #
# --------------------------------------------------------------------------- #


def test_region_overlap_known_masks() -> None:
    a = np.array([[True, True, False], [False, True, False]])
    b = np.array([[True, False, False], [False, True, True]])
    overlap = region_overlap(a, b)
    # intersection = 2, union = 4 -> jaccard 0.5; dice = 2*2/(3+3) = 2/3
    assert overlap.jaccard == pytest.approx(0.5)
    assert overlap.dice == pytest.approx(2.0 / 3.0)
    assert overlap.a_in_b == pytest.approx(2.0 / 3.0)


def test_region_overlap_disjoint_and_identical() -> None:
    a = np.array([[True, False], [False, False]])
    b = np.array([[False, True], [False, False]])
    assert region_overlap(a, b).jaccard == 0.0
    assert region_overlap(a, a).jaccard == pytest.approx(1.0)


def test_threshold_region_sign_and_quantile() -> None:
    field = np.array([[-2.0, -1.0, 0.5], [1.0, 2.0, 3.0]])
    positive = threshold_region(field, sign="positive")
    assert positive.tolist() == [[False, False, True], [True, True, True]]
    # top 50% by value: threshold is the 0.5-quantile (=1.0); >= keeps {1,2,3}
    top = threshold_region(field, quantile=0.5)
    assert int(np.count_nonzero(top)) == 3


def test_threshold_region_honours_mask() -> None:
    field = np.array([[1.0, 2.0], [3.0, 4.0]])
    mask = np.array([[True, True], [False, True]])
    region = threshold_region(field, sign="positive", mask=mask)
    assert region.tolist() == [[True, True], [False, True]]


def test_threshold_region_rejects_ambiguous_rule() -> None:
    field = np.zeros((3, 3))
    with pytest.raises(ValueError):
        threshold_region(field)
    with pytest.raises(ValueError):
        threshold_region(field, sign="positive", quantile=0.5)


def test_connected_components_counts_and_sizes() -> None:
    mask = np.array(
        [
            [True, False, True, True],
            [True, False, False, True],
            [False, False, False, False],
            [True, True, False, True],
        ]
    )
    count, sizes = connected_components(mask, connectivity=4)
    assert count == 4
    assert sizes == (3, 2, 2, 1)


def test_connected_components_connectivity_matters() -> None:
    mask = np.array([[True, False], [False, True]])
    assert connected_components(mask, connectivity=4)[0] == 2
    assert connected_components(mask, connectivity=8)[0] == 1


def test_pearson_perfect_and_constant() -> None:
    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert pearson_correlation(a, 2.0 * a) == pytest.approx(1.0)
    assert pearson_correlation(a, -a) == pytest.approx(-1.0)
    assert pearson_correlation(a, np.ones_like(a)) is None


def test_spearman_monotone_but_nonlinear() -> None:
    a = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    b = np.exp(a)  # strictly increasing, so Spearman is exactly 1
    assert spearman_correlation(a, b) == pytest.approx(1.0)
    # Pearson is not 1 for a nonlinear monotone map.
    assert pearson_correlation(a, b) < 0.999


def test_spearman_handles_ties() -> None:
    a = np.array([[10.0, 20.0], [20.0, 30.0]])
    b = np.array([[1.0, 2.0], [2.0, 3.0]])
    # identical tie structure -> perfect rank correlation
    assert spearman_correlation(a, b) == pytest.approx(1.0)


def test_compare_scalar_fields_keys() -> None:
    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    result = compare_scalar_fields(a, a)
    assert set(result) == {"pearson", "spearman"}
    assert result["pearson"] == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Transport versus deformation.                                              #
# --------------------------------------------------------------------------- #


def test_translate_periodic_matches_roll_for_integer_shift() -> None:
    grid = sf.periodic_grid_2d(16, 2.0 * np.pi)
    field = np.sin(grid.xx) * np.cos(2.0 * grid.yy)
    shifted = translate_periodic(field, shift_x=3.0, shift_y=0.0)
    assert np.allclose(shifted, np.roll(field, 3, axis=1), atol=1e-10)


def test_translate_periodic_roundtrip() -> None:
    grid = sf.periodic_grid_2d(24, 2.0 * np.pi)
    field = np.cos(grid.xx) * np.cos(grid.yy)
    there = translate_periodic(field, shift_x=1.7, shift_y=-0.6)
    back = translate_periodic(there, shift_x=-1.7, shift_y=0.6)
    assert np.allclose(back, field, atol=1e-10)


def test_transport_compensation_reduces_translation_response() -> None:
    grid = sf.periodic_grid_2d(64, 2.0 * np.pi)
    pattern = np.sin(grid.xx) * np.cos(grid.yy)
    u0, v0, dt = 1.0, 0.4, 0.05
    dx, dy = grid.spacing
    shifted = translate_periodic(pattern, shift_x=u0 * dt / dx, shift_y=v0 * dt / dy)
    decomposition = transport_decomposition(
        pattern,
        shifted,
        u0 * np.ones_like(pattern),
        v0 * np.ones_like(pattern),
        grid.x,
        grid.y,
        dt,
        "periodic",
    )
    assert decomposition.eulerian_rms > 0.1
    assert decomposition.residual_fraction < 0.1  # translation largely removed


def test_transport_stationary_field_has_zero_eulerian_change() -> None:
    grid = sf.periodic_grid_2d(16, 2.0 * np.pi)
    pattern = np.sin(grid.xx)
    decomposition = transport_decomposition(
        pattern, pattern, np.zeros_like(pattern), np.zeros_like(pattern),
        grid.x, grid.y, 0.1, "periodic",
    )
    assert decomposition.eulerian_rms == pytest.approx(0.0, abs=1e-12)


def test_transport_rejects_bad_dt() -> None:
    grid = sf.periodic_grid_2d(8, 2.0 * np.pi)
    zero = np.zeros(grid.shape)
    with pytest.raises(ValueError):
        transport_decomposition(zero, zero, zero, zero, grid.x, grid.y, 0.0, "periodic")


# --------------------------------------------------------------------------- #
# Synthetic flows and the shear-versus-rotation invariants.                  #
# --------------------------------------------------------------------------- #


def _by_name(cases):  # type: ignore[no-untyped-def]
    return {case.name: case for case in cases}


def test_simple_shear_has_vorticity_but_no_rotation() -> None:
    case = _by_name(analytical_cases())["simple_shear"]
    result = run_case(case)
    assert result.diagnostics["vorticity_rms"] > 0.1
    assert result.regions["rotation_fraction"] == pytest.approx(0.0)
    assert result.regions["jaccard_highomega_rotation"] == pytest.approx(0.0)
    assert result.itd["intensity"] > 0.1  # ITD intensity is shear-inflated


def test_rigid_rotation_is_all_rotation() -> None:
    result = run_case(_by_name(analytical_cases())["rigid_rotation"])
    assert result.regions["rotation_fraction"] > 0.99
    assert result.itd["heterogeneity"] == pytest.approx(0.0, abs=1e-9)


def test_pure_strain_has_no_vorticity() -> None:
    result = run_case(_by_name(analytical_cases())["pure_strain"])
    assert result.diagnostics["vorticity_rms"] < 1e-9
    assert result.regions["rotation_fraction"] == pytest.approx(0.0)


def test_vortex_counts_via_connected_components() -> None:
    cases = _by_name(analytical_cases())
    assert run_case(cases["lamb_oseen"]).regions["rotation_components"] == 1.0
    assert run_case(cases["vortex_pair"]).regions["rotation_components"] == 2.0


def test_stuart_concentration_controls_rotation() -> None:
    grid = sf.finite_grid_2d(64, 48, (0.0, 2.0 * np.pi), (-2.5, 2.5))
    u_shear, v_shear = sf.stuart_vortices(grid, concentration=1.0)
    # C=1 is the pure shear layer: v is identically zero.
    assert np.allclose(v_shear, 0.0, atol=1e-12)
    u_roll, v_roll = sf.stuart_vortices(grid, concentration=4.0)
    assert np.max(np.abs(v_roll)) > 0.1  # roll-up produces cross-stream velocity


def test_stuart_rejects_subcritical_concentration() -> None:
    grid = sf.finite_grid_2d(8, 8, (0.0, 2.0 * np.pi), (-1.0, 1.0))
    with pytest.raises(ValueError):
        sf.stuart_vortices(grid, concentration=0.5)


def test_synthetic_cases_all_run() -> None:
    for case in synthetic_cfd_cases():
        result = run_case(case)
        assert result.category == "synthetic"
        assert result.shape[0] >= 3 and result.shape[1] >= 3


# --------------------------------------------------------------------------- #
# External PIV fixture.                                                       #
# --------------------------------------------------------------------------- #


def test_external_piv_fixture_loads_and_is_shear_dominated() -> None:
    result = run_case(external_piv_case(_PIV_FIXTURE))
    assert result.category == "external"
    # A mean turbulent boundary layer: large vorticity, single-signed (low mixing).
    assert result.diagnostics["vorticity_rms"] > 1.0
    assert result.itd["sign_mixing"] < 0.05
    # High-vorticity region does not coincide with the rotation region.
    assert result.regions["jaccard_highomega_rotation"] < 0.5


# --------------------------------------------------------------------------- #
# Hypothesis demonstrations H1 and H2.                                        #
# --------------------------------------------------------------------------- #


def test_equal_enstrophy_but_itd_vector_separates() -> None:
    result = equal_enstrophy_separation()
    assert result["enstrophy_matched"] is True
    assert result["enstrophy_a"] == pytest.approx(result["enstrophy_b"], rel=1e-6)
    # The scalar (enstrophy) is identical; the ITD localization is not close.
    assert result["localization_ratio"] > 10.0
    assert result["heterogeneity_ratio"] > 2.0


def test_vortex_merger_transition_two_to_one() -> None:
    frames = vortex_merger_sequence()
    counts = [int(frame["significant_rotation_regions"]) for frame in frames]
    assert max(counts) >= 2  # two distinct vortices early
    assert counts[-1] == 1  # merged into one at the end
    # The count is monotone non-increasing across the merge (no spurious splitting).
    assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))


def test_vortex_merger_first_frame_has_no_temporal_deformation() -> None:
    frames = vortex_merger_sequence()
    # The first frame has no predecessor, so temporal deformation is exactly zero.
    assert frames[0]["itd_temporal_deformation"] == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------------------- #
# 3D ITD candidate vs established 3D diagnostics.                             #
# --------------------------------------------------------------------------- #


def test_abc_flow_3d_is_maximally_helical_and_rotation_criteria_agree() -> None:
    cases = {case.name: case for case in analytical_3d_cases()}
    abc = cases["abc_flow"]
    assert abc.itd3d["normalized_helicity"] == pytest.approx(1.0, abs=1e-6)
    # Q>0 and lambda2<0 both mark rotation, so they should largely agree.
    assert abc.regions["jaccard_q_lambda2"] > 0.5


def test_transport_3d_translation_reduces_and_stationary_is_zero() -> None:
    from itd_research.diagnostics_3d.analytical_fields import periodic_grid_3d

    grid = periodic_grid_3d(16, 2.0 * np.pi)
    pattern = np.sin(grid.xx) * np.cos(grid.yy) * np.cos(grid.zz)
    # stationary: no Eulerian change
    zero = np.zeros_like(pattern)
    stat = transport_decomposition_3d(
        pattern, pattern, zero, zero, zero, grid.x, grid.y, grid.z, 0.1, "periodic"
    )
    assert stat.eulerian_rms == pytest.approx(0.0, abs=1e-12)
    # integer-cell translation along x, advected by the matching uniform velocity
    dx = float(grid.x[1] - grid.x[0])
    shifted = np.roll(pattern, 1, axis=2)  # content moves toward +x
    u0 = (dx / 0.05) * np.ones_like(pattern)
    moved = transport_decomposition_3d(
        pattern, shifted, u0, zero, zero, grid.x, grid.y, grid.z, 0.05, "periodic"
    )
    assert moved.eulerian_rms > 0.1
    assert moved.residual_fraction < 0.35  # transport largely compensated


def test_transport_3d_rejects_bad_shapes() -> None:
    from itd_research.diagnostics_3d.analytical_fields import periodic_grid_3d

    grid = periodic_grid_3d(8, 2.0 * np.pi)
    zero = np.zeros(grid.shape)
    with pytest.raises(ValueError):
        transport_decomposition_3d(
            zero, zero, zero, zero, zero, grid.x, grid.y, grid.z, 0.0, "periodic"
        )


def test_fluctuation_intensity_zero_for_homogeneous_profile() -> None:
    from itd_research.diagnostics_3d.analytical_fields import finite_grid_3d

    grid = finite_grid_3d(12, -1.0, 1.0)
    # a pure y-profile (varies only with y) has no fluctuation about its z/x mean
    smooth = np.tanh(grid.yy)
    assert fluctuation_intensity(smooth) == pytest.approx(0.0, abs=1e-12)
    # adding z/x structure raises the fluctuation intensity above zero
    perturbed = smooth + 0.3 * np.sin(grid.xx) * np.cos(grid.zz)
    assert fluctuation_intensity(perturbed) > 0.1


def test_transition_markers_laminar_vs_turbulent_like() -> None:
    from itd_research.diagnostics_3d.analytical_fields import finite_grid_3d

    grid = finite_grid_3d(16, -1.0, 1.0)
    zero = np.zeros(grid.shape)
    laminar_u = np.tanh(2.0 * grid.yy)  # smooth shear, no 3D structure
    laminar = transition_markers(laminar_u, zero, zero, grid.x, grid.y, grid.z, "finite")
    # deterministic multi-scale perturbation stands in for turbulent structure
    turb_u = laminar_u + 0.4 * np.sin(3 * grid.xx) * np.cos(3 * grid.zz) * np.cos(2 * grid.yy)
    turb_v = 0.4 * np.cos(3 * grid.xx) * np.sin(3 * grid.zz)
    turbulent = transition_markers(turb_u, turb_v, zero, grid.x, grid.y, grid.z, "finite")
    assert set(laminar) == {
        "fluctuation_intensity", "vorticity_rms", "rotation_fraction_q",
        "itd_intensity", "itd_localization",
    }
    assert laminar["fluctuation_intensity"] == pytest.approx(0.0, abs=1e-12)
    assert turbulent["fluctuation_intensity"] > laminar["fluctuation_intensity"] + 0.1


def test_temporal_intermittency_detects_a_burst() -> None:
    from itd_research.diagnostics_3d.analytical_fields import finite_grid_3d

    grid = finite_grid_3d(12, -1.0, 1.0)
    zero = np.zeros(grid.shape)
    base = np.tanh(2.0 * grid.yy)  # smooth laminar-like shear
    burst = base + 0.5 * np.sin(3 * grid.xx) * np.cos(3 * grid.zz) * np.cos(2 * grid.yy)
    # frames: quiet, quiet, BURST, quiet
    frames = [
        (base, zero, zero, grid.x, grid.y, grid.z),
        (base, zero, zero, grid.x, grid.y, grid.z),
        (burst, 0.3 * burst, zero, grid.x, grid.y, grid.z),
        (base, zero, zero, grid.x, grid.y, grid.z),
    ]
    summary = temporal_intermittency(frames)
    assert summary["peak_frame"] == 2  # the burst frame
    assert summary["max_over_min"] > 5.0  # strong temporal modulation
    assert len(summary["fluctuation_intensity"]) == 4  # type: ignore[arg-type]


def test_intermittency_factor_rises_from_laminar_to_turbulent() -> None:
    rng_free = np.linspace(0.0, 1.0, 8)  # deterministic wall-normal profile
    ny, nz, nx = 8, 24, 4
    profile = rng_free  # laminar u(y)
    laminar = np.broadcast_to(profile[None, :, None], (nz, ny, nx)).copy()
    reference = laminar_reference_profile([laminar, laminar])
    # deterministic "turbulent" perturbation added to a chosen number of columns
    def make(turbulent_columns: int) -> np.ndarray:
        field = laminar.copy()
        pert = np.zeros((nz, ny, nx))
        idx = np.arange(nz) < turbulent_columns
        pert[idx] = 0.5  # strong, uniform-per-column perturbation
        return field + pert
    threshold = 0.1
    gamma_none = intermittency_factor([make(0)], reference, threshold)
    gamma_half = intermittency_factor([make(12)], reference, threshold)
    gamma_all = intermittency_factor([make(24)], reference, threshold)
    assert gamma_none == pytest.approx(0.0)
    assert gamma_half == pytest.approx(0.5)
    assert gamma_all == pytest.approx(1.0)


def test_aggregate_3d_channels_summary() -> None:
    summary = aggregate_3d_channels(analytical_3d_cases())
    assert summary["n_samples"]["value"] == 2.0
    assert "stretching_rate" in summary and "jaccard_q_lambda2" in summary
    assert set(summary["stretching_rate"]) == {"mean", "std", "min", "max"}


def test_rigid_rotation_3d_has_no_orientation_dispersion_or_stretching() -> None:
    from itd_research.diagnostics_3d import analytical_fields as af

    grid = af.finite_grid_3d(17, -2.0, 2.0)
    u, v, w = af.linear_velocity(af.rigid_rotation_gradient(1.3), grid)
    result = run_3d_comparison(
        u, v, w, grid.x, grid.y, grid.z, "finite", "rigid", "analytical", "solid body"
    )
    assert result.itd3d["orientation_dispersion"] == pytest.approx(0.0, abs=1e-9)
    assert result.itd3d["stretching_rate"] == pytest.approx(0.0, abs=1e-9)
    assert result.regions["rotation_fraction_q"] > 0.99  # rotation everywhere


def test_external_piv_field_to_case_crops_masked_region() -> None:
    from itd_research.external_validation.experiments import field_to_case
    from itd_research.io.field_data import FieldData2D, FieldMetadata

    x = np.linspace(0.0, 1.0, 6)
    y = np.linspace(0.0, 1.0, 5)
    u = np.ones((5, 6))
    v = np.zeros((5, 6))
    mask = np.ones((5, 6), dtype=bool)
    mask[0, :] = False  # invalid first row
    u[0, :] = np.nan
    field = FieldData2D(x=x, y=y, u=u, v=v, mask=mask,
                        metadata=FieldMetadata("t", "m", "m/s"))
    case = field_to_case(field, "cropped", "desc")
    assert case.u.shape == (4, 6)  # first row dropped
    assert np.all(np.isfinite(case.u))
