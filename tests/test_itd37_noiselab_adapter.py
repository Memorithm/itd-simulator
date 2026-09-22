from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.noiselab_adapter import (
    NoiseInterventionRef,
    PerturbationResponseRecord,
)


def _intervention(role: SplitRole = SplitRole.DEVELOPMENT) -> NoiseInterventionRef:
    return NoiseInterventionRef(
        intervention_id="noise-1",
        role=role,
        source=SourceIdentity("Memorithm/NoiseLab", "noise-test"),
        family="ou_process",
        seed=7,
        intervention_site="input",
        parameters_sha256="a" * 64,
        raw_observation_sha256="b" * 64,
        perturbed_observation_sha256="c" * 64,
        filtered_observation_sha256=None,
    )


def test_noiselab_adapter_preserves_raw_observation() -> None:
    intervention = _intervention()

    assert intervention.raw_observation_preserved is True
    assert intervention.authorizes_causal_claim is False


def test_noiselab_adapter_rejects_final_material() -> None:
    with pytest.raises(ValueError, match="final perturbation material"):
        _intervention(SplitRole.FINAL)


def test_perturbation_response_remains_noncausal_measurement() -> None:
    record = PerturbationResponseRecord(
        intervention=_intervention(),
        amplitude=0.2,
        structural_delta=0.1,
        task_error_delta=0.05,
        uncertainty_delta=0.03,
        response_unit="normalized_delta",
    )

    assert record.authorizes_causal_claim is False
    assert record.response_unit == "normalized_delta"


def test_noiselab_adapter_rejects_wrong_source() -> None:
    with pytest.raises(ValueError, match="Memorithm/NoiseLab"):
        NoiseInterventionRef(
            intervention_id="noise-1",
            role=SplitRole.DEVELOPMENT,
            source=SourceIdentity("other/repo", "test"),
            family="test",
            seed=0,
            intervention_site="input",
            parameters_sha256="a" * 64,
            raw_observation_sha256="b" * 64,
            perturbed_observation_sha256="c" * 64,
        )
