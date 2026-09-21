from __future__ import annotations

from itd_research.adaptive_shadow import AdaptiveAction, ShadowDecision


def test_shadow_decision_never_actuates() -> None:
    decision = ShadowDecision(
        decision_id="d1",
        action=AdaptiveAction.CHANGE_PRECISION,
        predicted_quality_delta=-0.01,
        predicted_cost_delta=-10.0,
        invariant_risk=0.0,
        evidence_fingerprint="a" * 64,
    )
    assert decision.actuates is False
