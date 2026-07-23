"""Tests for the industrial-readiness maturity assessment (H16)."""

from __future__ import annotations

from itd_research.industrial.readiness import (
    IRL_SCALE,
    assess_readiness,
    standard_gaps,
)


def test_irl_scale_is_ordered_zero_to_nine() -> None:
    levels = [level for level, _ in IRL_SCALE]
    assert levels == list(range(10))


def test_assessment_is_honest_not_certified() -> None:
    assessment = assess_readiness()
    # A research prototype must not self-report the qualification/certification band.
    assert 2 <= assessment.achieved_level <= 6
    # The level is capped by the first non-met criterion (monotone frontier).
    met_levels = [c.level for c in assessment.criteria if c.status == "met"]
    assert assessment.achieved_level == max(met_levels)
    assert all(c.level > assessment.achieved_level or c.status != "met" for c in assessment.next_gaps)


def test_standard_gaps_all_unsatisfied() -> None:
    gaps = standard_gaps()
    assert len(gaps) >= 6
    assert all(gap.status == "not satisfied" for gap in gaps)
    assert all(gap.missing for gap in gaps)
    names = {gap.standard for gap in gaps}
    assert {"ISO 9001", "DO-178C", "IEC 61508"} <= names
