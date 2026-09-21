from __future__ import annotations

import pytest

from itd_research.uq import selective_risk_point


def test_selective_risk_point_accounts_for_coverage_and_false_confidence() -> None:
    point = selective_risk_point(
        scores=(0.1, 0.2, 1.0, 2.0),
        errors=(0.0, 0.2, 1.0, 2.0),
        is_ood=(False, False, True, True),
        threshold=0.5,
    )

    assert point.coverage == pytest.approx(0.5)
    assert point.selective_risk == pytest.approx(0.1)
    assert point.false_confidence == 0.0


def test_selective_risk_rejects_negative_error() -> None:
    with pytest.raises(ValueError, match="errors"):
        selective_risk_point(
            scores=(0.1,),
            errors=(-1.0,),
            is_ood=(False,),
            threshold=0.5,
        )
