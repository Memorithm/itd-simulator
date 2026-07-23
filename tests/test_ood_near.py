"""Tests for the near-OOD campaign primitives (Mission 5, H31).

The full campaign runs in the bounded CI step ``ood_near validate``; here we test the
controlled-merger primitive and the result contract cheaply.
"""

from __future__ import annotations

from itd_research.ood_near.campaign import NearOODResult, _controlled_merger


def test_controlled_merger_produces_rawrun() -> None:
    raw = _controlled_merger(10, circulation=1.2, viscosity=0.0025, separation=1.2, nodes=48)
    assert raw.family == "merger_controlled"
    assert len(raw.velocities) == len(raw.times)
    assert raw.event_frame is None or 0 <= raw.event_frame < len(raw.times)


def test_near_ood_result_serializes() -> None:
    result = NearOODResult(
        group_mean_scores={"in_domain": 1.5, "near_viscosity": 5.0, "far_taylorgreen": 400.0},
        detection_auc_near=0.9, detection_auc_far=1.0, predictable_near_auc=0.6,
        selective={"in_domain_coverage": 0.9, "selective_risk": 0.01, "full_risk": 0.3},
        unnecessary_abstention_rate=0.6, risk_coverage=[(0.9, 0.01)], h31_verdict="partially supported",
    )
    payload = result.as_dict()
    assert payload["h31_verdict"] == "partially supported"
    assert payload["risk_coverage"] == [{"coverage": 0.9, "selective_risk": 0.01}]
