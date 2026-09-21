from __future__ import annotations

import pytest

from itd_research.representation_strata import (
    RepresentationKind,
    RepresentationObservation,
    RepresentationTransition,
)


def test_representation_accounting_includes_metadata() -> None:
    observation = RepresentationObservation(
        representation_id="q8",
        kind=RepresentationKind.UNIFORM_QUANTIZED,
        stored_payload_bits=800,
        metadata_bits=64,
        peak_working_bytes=256,
        task_error=0.1,
        reconstruction_error=0.05,
    )

    assert observation.total_stored_bits == 864


def test_transition_scalarization_is_explicit_and_directed() -> None:
    transition = RepresentationTransition(
        source_id="dense",
        target_id="q8",
        fidelity_loss=0.2,
        transition_cost=3.0,
        storage_delta_bits=-1024,
    )

    assert transition.scalarized_cost(alpha=1.0, beta=2.0, gamma=0.5) == pytest.approx(
        0.2 + 6.0 + 512.0
    )


def test_transition_rejects_invalid_costs() -> None:
    with pytest.raises(ValueError, match="fidelity_loss"):
        RepresentationTransition(
            source_id="dense",
            target_id="q8",
            fidelity_loss=float("nan"),
            transition_cost=1.0,
            storage_delta_bits=-8,
        )
