"""ITD-31.2 deterministic representation-transition graph planning.

The graph treats representation changes as directed, measured transitions.  It
does not assume symmetry, transitivity, triangle inequalities or mathematical
metric structure.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from itd_research.representation_strata import RepresentationTransitionV2


@dataclass(frozen=True)
class ScalarizationWeights:
    """Frozen non-negative weights used by one planning experiment."""

    fidelity: float
    transition: float
    storage: float
    peak_memory: float

    def __post_init__(self) -> None:
        for name, value in (
            ("fidelity", self.fidelity),
            ("transition", self.transition),
            ("storage", self.storage),
            ("peak_memory", self.peak_memory),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if self.fidelity == self.transition == self.storage == self.peak_memory == 0.0:
            raise ValueError("at least one scalarization weight must be positive.")


@dataclass(frozen=True)
class RepresentationTransitionGraph:
    """Finite directed transition graph over named representation states."""

    node_ids: tuple[str, ...]
    transitions: tuple[RepresentationTransitionV2, ...]

    def __post_init__(self) -> None:
        if not self.node_ids:
            raise ValueError("transition graph must contain at least one node.")
        if any(not node.strip() for node in self.node_ids):
            raise ValueError("transition graph node identifiers must not be empty.")
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("transition graph node identifiers must be unique.")

        nodes = set(self.node_ids)
        cost_units = {transition.cost_unit for transition in self.transitions}
        if len(cost_units) > 1:
            raise ValueError("transition graph requires one common transition cost unit.")
        edges: set[tuple[str, str]] = set()
        for transition in self.transitions:
            if transition.source_id not in nodes or transition.target_id not in nodes:
                raise ValueError("every transition endpoint must be a declared graph node.")
            edge = (transition.source_id, transition.target_id)
            if edge in edges:
                raise ValueError("directed transition edges must be unique.")
            edges.add(edge)

    def outgoing(self, source_id: str) -> tuple[RepresentationTransitionV2, ...]:
        if source_id not in self.node_ids:
            raise KeyError(source_id)
        return tuple(
            sorted(
                (
                    transition
                    for transition in self.transitions
                    if transition.source_id == source_id
                ),
                key=lambda item: (item.target_id, item.cost_unit),
            )
        )


@dataclass(frozen=True)
class PlannedRepresentationPath:
    """One deterministic path with its measured scalarized cost."""

    node_ids: tuple[str, ...]
    total_cost: float
    edge_count: int

    def __post_init__(self) -> None:
        if not self.node_ids:
            raise ValueError("planned path must contain at least one node.")
        if self.edge_count != len(self.node_ids) - 1:
            raise ValueError("edge_count must match path length.")
        if not math.isfinite(self.total_cost) or self.total_cost < 0.0:
            raise ValueError("planned path cost must be finite and non-negative.")


def transition_cost(
    transition: RepresentationTransitionV2,
    weights: ScalarizationWeights,
) -> float:
    """Evaluate one edge under explicit frozen weights."""

    return transition.scalarized_cost(
        alpha=weights.fidelity,
        beta=weights.transition,
        gamma=weights.storage,
        delta=weights.peak_memory,
    )


def direct_path(
    graph: RepresentationTransitionGraph,
    source_id: str,
    target_id: str,
    weights: ScalarizationWeights,
) -> PlannedRepresentationPath | None:
    """Return the direct edge baseline when it exists."""

    if source_id == target_id:
        return PlannedRepresentationPath((source_id,), 0.0, 0)
    for edge in graph.outgoing(source_id):
        if edge.target_id == target_id:
            return PlannedRepresentationPath(
                (source_id, target_id),
                transition_cost(edge, weights),
                1,
            )
    return None


def shortest_path(
    graph: RepresentationTransitionGraph,
    source_id: str,
    target_id: str,
    weights: ScalarizationWeights,
) -> PlannedRepresentationPath | None:
    """Run deterministic Dijkstra planning with lexical tie-breaking.

    Edge costs are non-negative by the transition contracts.  Equal-cost paths
    are resolved by the lexicographically smaller node-id tuple.
    """

    if source_id not in graph.node_ids:
        raise KeyError(source_id)
    if target_id not in graph.node_ids:
        raise KeyError(target_id)
    if source_id == target_id:
        return PlannedRepresentationPath((source_id,), 0.0, 0)

    queue: list[tuple[float, tuple[str, ...], str]] = [
        (0.0, (source_id,), source_id)
    ]
    best: dict[str, tuple[float, tuple[str, ...]]] = {
        source_id: (0.0, (source_id,))
    }

    while queue:
        cost, path, current = heapq.heappop(queue)
        best_cost, best_path = best[current]
        if cost != best_cost or path != best_path:
            continue
        if current == target_id:
            return PlannedRepresentationPath(path, cost, len(path) - 1)

        for edge in graph.outgoing(current):
            next_cost = cost + transition_cost(edge, weights)
            next_path = (*path, edge.target_id)
            previous = best.get(edge.target_id)
            candidate = (next_cost, next_path)
            if previous is None or candidate < previous:
                best[edge.target_id] = candidate
                heapq.heappush(queue, (next_cost, next_path, edge.target_id))

    return None


def path_advantage(
    direct: PlannedRepresentationPath | None,
    planned: PlannedRepresentationPath | None,
) -> float | None:
    """Return direct minus planned cost when both paths exist."""

    if direct is None or planned is None:
        return None
    return direct.total_cost - planned.total_cost
