from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity
from itd_research.scirust_itd_parity import (
    NumericParityObservation,
    OracleEvidenceClass,
    OracleFixtureRef,
    ScirustItdImplementationRef,
    ScirustItdParityContract,
    ScirustItdParityReport,
)


def _implementation() -> ScirustItdImplementationRef:
    return ScirustItdImplementationRef(
        source=SourceIdentity(
            "Memorithm/scirust",
            "c6df0c6fd306c1e9456d5ce9f1ba649644639c38",
        )
    )


def _contract() -> ScirustItdParityContract:
    source = SourceIdentity("Memorithm/itd-simulator", "itd-test")
    return ScirustItdParityContract(
        implementation=_implementation(),
        model_baseline="ITD V29.18",
        fixtures=(
            OracleFixtureRef(
                fixture_id="analytical",
                evidence_class=OracleEvidenceClass.HAND_DERIVED_ANALYTICAL,
                source=source,
                path="tests/fixtures/analytical_oracles.json",
                sha256="a" * 64,
            ),
            OracleFixtureRef(
                fixture_id="python-regression",
                evidence_class=OracleEvidenceClass.PYTHON_REGRESSION_SNAPSHOT,
                source=source,
                path="tests/fixtures/oracle_data.rs",
                sha256="b" * 64,
            ),
        ),
    )


def test_parity_contract_requires_two_distinct_evidence_classes() -> None:
    contract = _contract()

    assert len(contract.fingerprint()) == 64
    assert contract.implementation.crate_name == "scirust-itd"


def test_parity_contract_rejects_regression_only_evidence() -> None:
    source = SourceIdentity("Memorithm/itd-simulator", "itd-test")

    with pytest.raises(ValueError, match="both analytical and regression"):
        ScirustItdParityContract(
            implementation=_implementation(),
            model_baseline="ITD V29.18",
            fixtures=(
                OracleFixtureRef(
                    fixture_id="python-regression",
                    evidence_class=OracleEvidenceClass.PYTHON_REGRESSION_SNAPSHOT,
                    source=source,
                    path="tests/fixtures/oracle_data.rs",
                    sha256="b" * 64,
                ),
            ),
        )


def test_numeric_parity_uses_scale_aware_tolerance() -> None:
    observation = NumericParityObservation(
        observation_id="solid-rotation-intensity",
        evidence_class=OracleEvidenceClass.HAND_DERIVED_ANALYTICAL,
        expected=4.0,
        observed=4.0 + 1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-9,
    )

    assert observation.within_tolerance is True
    assert observation.absolute_error == pytest.approx(1.0e-10)


def test_parity_report_preserves_nonclaim_boundary() -> None:
    contract = _contract()
    report = ScirustItdParityReport(
        contract_fingerprint=contract.fingerprint(),
        observations=(
            NumericParityObservation(
                observation_id="zero-field",
                evidence_class=OracleEvidenceClass.HAND_DERIVED_ANALYTICAL,
                expected=0.0,
                observed=0.0,
                absolute_tolerance=1.0e-12,
                relative_tolerance=0.0,
            ),
            NumericParityObservation(
                observation_id="python-regression",
                evidence_class=OracleEvidenceClass.PYTHON_REGRESSION_SNAPSHOT,
                expected=1.0,
                observed=1.0,
                absolute_tolerance=1.0e-11,
                relative_tolerance=1.0e-9,
            ),
        ),
    )

    report.assert_matches_contract(contract)
    assert report.all_within_tolerance is True
    assert report.failed_observation_ids == ()
    assert report.authorizes_physical_validity_claim is False
    assert report.authorizes_v30_promotion is False


def test_parity_report_exposes_failures() -> None:
    contract = _contract()
    report = ScirustItdParityReport(
        contract_fingerprint=contract.fingerprint(),
        observations=(
            NumericParityObservation(
                observation_id="bad",
                evidence_class=OracleEvidenceClass.PYTHON_REGRESSION_SNAPSHOT,
                expected=1.0,
                observed=1.1,
                absolute_tolerance=1.0e-12,
                relative_tolerance=1.0e-9,
            ),
        ),
    )

    assert report.failed_observation_ids == ("bad",)
    assert report.all_within_tolerance is False
