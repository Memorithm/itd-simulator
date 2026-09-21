from __future__ import annotations

import pytest

from itd_research.itd3x import (
    FROZEN_SCIENTIFIC_BASELINE,
    RESEARCH_ENGINE_REVISION,
    ResearchTrack,
    SeriesSpec,
    SeriesStatus,
    default_itd3x_registry,
)


def test_v29_remains_frozen_and_v30_has_separate_identity() -> None:
    assert FROZEN_SCIENTIFIC_BASELINE == "ITD V29.18"
    assert RESEARCH_ENGINE_REVISION == "ITD Research Lab V30.0-alpha"
    assert FROZEN_SCIENTIFIC_BASELINE not in RESEARCH_ENGINE_REVISION


def test_registry_is_unique_and_covers_required_tracks() -> None:
    registry = default_itd3x_registry()
    ids = [item.series_id for item in registry.series]

    assert len(ids) == len(set(ids))
    assert ids[0] == "ITD-30.0"
    assert ids[-1] == "ITD-39.3"
    assert all(series_id.startswith("ITD-3") for series_id in ids)

    covered = {item.track for item in registry.series}
    assert set(ResearchTrack) <= covered


def test_registry_fingerprint_is_deterministic() -> None:
    left = default_itd3x_registry()
    right = default_itd3x_registry()

    assert left.canonical_json() == right.canonical_json()
    assert left.fingerprint() == right.fingerprint()
    assert len(left.fingerprint()) == 64


def test_lookup_exposes_adaptive_and_trajectory_contracts() -> None:
    registry = default_itd3x_registry()

    assert registry.get("ITD-33.3").track is ResearchTrack.TRAJECTORY
    assert registry.get("ITD-36.0").track is ResearchTrack.ADAPTIVE
    assert "TDI" in registry.get("ITD-33.3").ecosystem
    assert "ElasticXxx" in registry.get("ITD-36.0").ecosystem


def test_series_validation_fails_closed() -> None:
    with pytest.raises(ValueError, match="ITD-3X"):
        SeriesSpec(
            "ITD-40.0",
            "invalid",
            ResearchTrack.CORE,
            SeriesStatus.PLANNED,
            "must fail",
        )
