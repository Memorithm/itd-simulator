from __future__ import annotations

import pytest

from itd_research.representation_strata import (
    RepresentationKind,
    RepresentationObservationV2,
    RepresentationResourceAccounting,
    RepresentationTransitionV2,
)


def test_exact_accounting_includes_metadata_and_transition_costs() -> None:
    accounting = RepresentationResourceAccounting(
        stored_payload_bits=800,
        metadata_bits=64,
        peak_working_bytes=4096,
        encode_cost=3.0,
        decode_cost=2.0,
        cost_unit="microseconds",
    )

    assert accounting.total_stored_bits == 864
    assert accounting.total_transition_cost == pytest.approx(5.0)


def test_v2_observation_binds_exact_accounting() -> None:
    observation = RepresentationObservationV2(
        representation_id="q8",
        kind=RepresentationKind.UNIFORM_QUANTIZED,
        accounting=RepresentationResourceAccounting(
            stored_payload_bits=800,
            metadata_bits=64,
            peak_working_bytes=4096,
            encode_cost=3.0,
            decode_cost=2.0,
            cost_unit="microseconds",
        ),
        task_error=0.1,
        reconstruction_error=0.05,
    )

    assert observation.accounting.total_stored_bits == 864
    assert observation.accounting.cost_unit == "microseconds"


def test_transition_v2_scalarization_accounts_for_peak_memory() -> None:
    transition = RepresentationTransitionV2(
        source_id="dense",
        target_id="q8",
        fidelity_loss=0.2,
        transition_cost=4.0,
        cost_unit="microseconds",
        peak_working_bytes=128,
        storage_delta_bits=-1024,
    )

    value = transition.scalarized_cost(
        alpha=1.0,
        beta=2.0,
        gamma=0.5,
        delta=0.25,
    )

    assert value == pytest.approx(0.2 + 8.0 + 512.0 + 32.0)


def test_accounting_requires_explicit_cost_unit() -> None:
    with pytest.raises(ValueError, match="cost_unit"):
        RepresentationResourceAccounting(
            stored_payload_bits=8,
            metadata_bits=0,
            peak_working_bytes=0,
            encode_cost=0.0,
            decode_cost=0.0,
            cost_unit="",
        )
