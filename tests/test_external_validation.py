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
from itd_research.external_validation.hypotheses import (
    equal_enstrophy_separation,
    vortex_merger_sequence,
)
from itd_research.external_validation.transport import (
    translate_periodic,
    transport_decomposition,
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
