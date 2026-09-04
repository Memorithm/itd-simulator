"""Qualification tests for the generic ITD AI experiment protocol."""

from __future__ import annotations

import importlib
import sys

import pytest

from itd_research.experiment_schema import (
    ComputeBudget,
    ExperimentProtocolV1,
    HypothesisContract,
    MetricContract,
    MetricDirection,
    MetricRole,
    SourceIdentity,
    SplitIdentity,
    SplitRole,
    UncertaintyContract,
)


def source(name: str) -> SourceIdentity:
    return SourceIdentity(
        source=name,
        revision=f"{name}-revision-1",
        sha256="a" * 64,
    )


def protocol() -> ExperimentProtocolV1:
    return ExperimentProtocolV1(
        experiment_id="attention-control-v1",
        hypothesis=HypothesisContract(
            hypothesis_id="H-AI-1",
            statement="candidate differs from the competent control",
            comparison="candidate versus control under the same task contract",
        ),
        implementation=source("implementation"),
        splits=(
            SplitIdentity(SplitRole.DEVELOPMENT, source("development")),
            SplitIdentity(SplitRole.VALIDATION, source("validation")),
            SplitIdentity(SplitRole.FINAL, source("final")),
        ),
        metrics=(
            MetricContract(
                name="task_accuracy",
                role=MetricRole.PRIMARY,
                direction=MetricDirection.HIGHER_IS_BETTER,
                unit="fraction",
            ),
            MetricContract(
                name="mean_localization",
                role=MetricRole.DIAGNOSTIC,
                direction=MetricDirection.DESCRIPTIVE,
                unit="fraction",
            ),
        ),
        compute_budget=ComputeBudget(unit="reference_steps", maximum=10_000.0),
        uncertainty=UncertaintyContract(
            method="paired-bootstrap-preregistered-placeholder",
            confidence_level=0.95,
            paired=True,
        ),
    )


def test_protocol_has_stable_canonical_identity() -> None:
    first = protocol()
    second = protocol()
    assert first.canonical_json() == second.canonical_json()
    assert first.fingerprint() == second.fingerprint()
    assert len(first.fingerprint()) == 64


def test_split_order_does_not_change_protocol_identity() -> None:
    first = protocol()
    reordered = ExperimentProtocolV1(
        experiment_id=first.experiment_id,
        hypothesis=first.hypothesis,
        implementation=first.implementation,
        splits=tuple(reversed(first.splits)),
        metrics=first.metrics,
        compute_budget=first.compute_budget,
        uncertainty=first.uncertainty,
    )
    assert first.fingerprint() == reordered.fingerprint()


def test_final_split_cannot_be_used_for_selection() -> None:
    current = protocol()
    current.assert_selection_allowed(SplitRole.DEVELOPMENT)
    current.assert_selection_allowed(SplitRole.VALIDATION)
    with pytest.raises(ValueError, match="final split"):
        current.assert_selection_allowed(SplitRole.FINAL)


def test_final_evaluation_requires_exact_frozen_source() -> None:
    current = protocol()
    current.assert_final_evaluation(current.split(SplitRole.FINAL).source)
    with pytest.raises(ValueError, match="frozen final split"):
        current.assert_final_evaluation(source("other-final"))


def test_split_identities_must_be_distinct_and_complete() -> None:
    current = protocol()
    duplicate = source("same")
    with pytest.raises(ValueError, match="split identities must differ"):
        ExperimentProtocolV1(
            experiment_id=current.experiment_id,
            hypothesis=current.hypothesis,
            implementation=current.implementation,
            splits=(
                SplitIdentity(SplitRole.DEVELOPMENT, duplicate),
                SplitIdentity(SplitRole.VALIDATION, duplicate),
                SplitIdentity(SplitRole.FINAL, source("final")),
            ),
            metrics=current.metrics,
            compute_budget=current.compute_budget,
            uncertainty=current.uncertainty,
        )

    with pytest.raises(ValueError, match="exactly one development"):
        ExperimentProtocolV1(
            experiment_id=current.experiment_id,
            hypothesis=current.hypothesis,
            implementation=current.implementation,
            splits=(
                SplitIdentity(SplitRole.DEVELOPMENT, source("development")),
                SplitIdentity(SplitRole.VALIDATION, source("validation")),
            ),
            metrics=current.metrics,
            compute_budget=current.compute_budget,
            uncertainty=current.uncertainty,
        )


def test_diagnostic_metric_cannot_be_an_optimization_direction() -> None:
    with pytest.raises(ValueError, match="diagnostic metrics must remain descriptive"):
        MetricContract(
            name="itd_descriptor",
            role=MetricRole.DIAGNOSTIC,
            direction=MetricDirection.HIGHER_IS_BETTER,
            unit="arbitrary",
        )


def test_primary_metric_and_bounded_compute_are_required() -> None:
    current = protocol()
    with pytest.raises(ValueError, match="at least one primary metric"):
        ExperimentProtocolV1(
            experiment_id=current.experiment_id,
            hypothesis=current.hypothesis,
            implementation=current.implementation,
            splits=current.splits,
            metrics=(
                MetricContract(
                    name="descriptor",
                    role=MetricRole.DIAGNOSTIC,
                    direction=MetricDirection.DESCRIPTIVE,
                    unit="fraction",
                ),
            ),
            compute_budget=current.compute_budget,
            uncertainty=current.uncertainty,
        )

    with pytest.raises(ValueError, match="finite and positive"):
        ComputeBudget(unit="reference_steps", maximum=float("inf"))


def test_invalid_source_hash_and_uncertainty_are_rejected() -> None:
    with pytest.raises(ValueError, match="64 hexadecimal"):
        SourceIdentity(source="dataset", revision="v1", sha256="not-a-digest")
    with pytest.raises(ValueError, match="strictly between zero and one"):
        UncertaintyContract(method="bootstrap", confidence_level=1.0, paired=True)


def test_import_does_not_initialise_matplotlib() -> None:
    sys.modules.pop("itd_research.experiment_schema", None)
    importlib.import_module("itd_research.experiment_schema")
    assert "matplotlib" not in sys.modules
