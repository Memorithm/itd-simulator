from __future__ import annotations

import pytest

from itd_research.representation_graph import (
    RepresentationTransitionGraph,
    ScalarizationWeights,
    direct_path,
    path_advantage,
    shortest_path,
)
from itd_research.representation_strata import RepresentationTransitionV2


def _edge(
    source: str,
    target: str,
    *,
    fidelity: float,
    transition: float,
    storage_delta_bits: int = 0,
    peak_working_bytes: int = 0,
    unit: str = "microseconds",
) -> RepresentationTransitionV2:
    return RepresentationTransitionV2(
        source_id=source,
        target_id=target,
        fidelity_loss=fidelity,
        transition_cost=transition,
        cost_unit=unit,
        peak_working_bytes=peak_working_bytes,
        storage_delta_bits=storage_delta_bits,
    )


def _weights() -> ScalarizationWeights:
    return ScalarizationWeights(
        fidelity=1.0,
        transition=1.0,
        storage=0.0,
        peak_memory=0.0,
    )


def test_planner_can_prefer_two_step_path_over_direct_transition() -> None:
    graph = RepresentationTransitionGraph(
        node_ids=("dense", "q8", "sparse"),
        transitions=(
            _edge("dense", "sparse", fidelity=4.0, transition=4.0),
            _edge("dense", "q8", fidelity=1.0, transition=1.0),
            _edge("q8", "sparse", fidelity=1.0, transition=1.0),
        ),
    )

    direct = direct_path(graph, "dense", "sparse", _weights())
    planned = shortest_path(graph, "dense", "sparse", _weights())

    assert direct is not None
    assert planned is not None
    assert direct.node_ids == ("dense", "sparse")
    assert planned.node_ids == ("dense", "q8", "sparse")
    assert path_advantage(direct, planned) == pytest.approx(4.0)


def test_shortest_path_uses_lexical_tie_breaking() -> None:
    graph = RepresentationTransitionGraph(
        node_ids=("a", "b", "c", "d"),
        transitions=(
            _edge("a", "b", fidelity=1.0, transition=0.0),
            _edge("b", "d", fidelity=1.0, transition=0.0),
            _edge("a", "c", fidelity=1.0, transition=0.0),
            _edge("c", "d", fidelity=1.0, transition=0.0),
        ),
    )

    planned = shortest_path(graph, "a", "d", _weights())

    assert planned is not None
    assert planned.node_ids == ("a", "b", "d")


def test_graph_rejects_mixed_transition_cost_units() -> None:
    with pytest.raises(ValueError, match="common transition cost unit"):
        RepresentationTransitionGraph(
            node_ids=("a", "b", "c"),
            transitions=(
                _edge("a", "b", fidelity=0.0, transition=1.0, unit="microseconds"),
                _edge("b", "c", fidelity=0.0, transition=1.0, unit="joules"),
            ),
        )


def test_planner_returns_none_when_target_is_unreachable() -> None:
    graph = RepresentationTransitionGraph(
        node_ids=("a", "b", "c"),
        transitions=(_edge("a", "b", fidelity=1.0, transition=1.0),),
    )

    assert shortest_path(graph, "a", "c", _weights()) is None
    assert direct_path(graph, "a", "c", _weights()) is None


def test_scalarization_requires_at_least_one_positive_weight() -> None:
    with pytest.raises(ValueError, match="at least one"):
        ScalarizationWeights(
            fidelity=0.0,
            transition=0.0,
            storage=0.0,
            peak_memory=0.0,
        )
