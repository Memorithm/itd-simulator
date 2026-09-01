"""Deterministic attention research primitives and leakage-safe protocols.

This module is an isolated AI-research layer for Mission AI-Attention-1. It
provides a transparent scalar StandardSoftmax reference, basic operator
descriptors, a deterministic associative-recall fixture, and grouped
train/validation/final partitions.

It does not modify the frozen ITD V29.18 model, claim that an ITD descriptor is
useful for attention, or select a FLAT-ATTENTION execution kernel. The final
partition is treated as frozen metadata: callers may evaluate it explicitly,
but training or calibration indices are rejected when they include final rows.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int64]
BoolArray: TypeAlias = NDArray[np.bool_]

_EPS = 1.0e-12


@dataclass(frozen=True)
class AttentionForward:
    """Scalar attention output and its row-wise mixing weights."""

    output: FloatArray
    weights: FloatArray


@dataclass(frozen=True)
class AttentionDescriptor:
    """Diagnostics for a non-negative, row-normalized attention matrix.

    These are descriptive quantities only. They are not evidence that a
    mechanism is useful, and they are not substituted for task metrics.
    """

    n_rows: int
    n_keys: int
    mean_entropy: float
    mean_normalized_entropy: float
    mean_localization: float
    mean_effective_support: float
    effective_rank: float
    negative_mass_fraction: float

    def as_dict(self) -> dict[str, float | int]:
        """Return a JSON-compatible descriptor record."""
        return {
            "n_rows": self.n_rows,
            "n_keys": self.n_keys,
            "mean_entropy": self.mean_entropy,
            "mean_normalized_entropy": self.mean_normalized_entropy,
            "mean_localization": self.mean_localization,
            "mean_effective_support": self.mean_effective_support,
            "effective_rank": self.effective_rank,
            "negative_mass_fraction": self.negative_mass_fraction,
        }


def scaled_dot_product_weights(
    query: FloatArray,
    keys: FloatArray,
    *,
    mask: BoolArray | None = None,
    scale: float | None = None,
) -> FloatArray:
    """Compute deterministic scalar StandardSoftmax weights for one query.

    The implementation is intentionally small and explicit so it can serve as
    a reference for future semantic candidates. It validates all inputs,
    applies an optional visibility mask before normalization, and never
    materializes an attention matrix larger than one query row.
    """
    query_array = np.asarray(query, dtype=np.float64)
    key_array = np.asarray(keys, dtype=np.float64)
    if query_array.ndim != 1:
        raise ValueError("query must be a one-dimensional vector.")
    if key_array.ndim != 2:
        raise ValueError("keys must be a two-dimensional matrix.")
    if query_array.size == 0 or key_array.shape[0] == 0:
        raise ValueError("query and keys must be non-empty.")
    if key_array.shape[1] != query_array.size:
        raise ValueError("query width must match the key width.")
    if not np.all(np.isfinite(query_array)) or not np.all(np.isfinite(key_array)):
        raise ValueError("query and keys must contain only finite values.")

    resolved_scale = (
        1.0 / np.sqrt(float(query_array.size)) if scale is None else float(scale)
    )
    if not np.isfinite(resolved_scale) or resolved_scale <= 0.0:
        raise ValueError("scale must be finite and strictly positive.")

    if mask is None:
        visible = np.ones(key_array.shape[0], dtype=bool)
    else:
        visible = np.asarray(mask, dtype=bool)
        if visible.ndim != 1 or visible.size != key_array.shape[0]:
            raise ValueError("mask must have one boolean entry per key.")
    if not np.any(visible):
        raise ValueError("mask must leave at least one visible key.")

    scores = key_array @ query_array * resolved_scale
    visible_scores = scores[visible]
    maximum = float(np.max(visible_scores))
    weights = np.zeros(key_array.shape[0], dtype=np.float64)
    weights[visible] = np.exp(visible_scores - maximum)
    denominator = float(np.sum(weights))
    if not np.isfinite(denominator) or denominator <= 0.0:
        raise FloatingPointError("attention normalization is not finite.")
    return np.asarray(weights / denominator, dtype=np.float64)


def scaled_dot_product_attention(
    query: FloatArray,
    keys: FloatArray,
    values: FloatArray,
    *,
    mask: BoolArray | None = None,
    scale: float | None = None,
) -> AttentionForward:
    """Run the scalar StandardSoftmax reference against value rows."""
    key_array = np.asarray(keys, dtype=np.float64)
    value_array = np.asarray(values, dtype=np.float64)
    if key_array.ndim != 2 or value_array.ndim != 2:
        raise ValueError("keys and values must be two-dimensional matrices.")
    if value_array.shape[0] != key_array.shape[0]:
        raise ValueError("values must contain one row per key.")
    if value_array.shape[1] == 0:
        raise ValueError("values must have a non-zero width.")
    if not np.all(np.isfinite(value_array)):
        raise ValueError("values must contain only finite values.")

    weights = scaled_dot_product_weights(query, key_array, mask=mask, scale=scale)
    output = np.asarray(weights @ value_array, dtype=np.float64)
    return AttentionForward(output=output, weights=weights)


def summarize_attention_weights(weights: FloatArray) -> AttentionDescriptor:
    """Summarize row-normalized softmax weights without inventing semantics."""
    array = np.asarray(weights, dtype=np.float64)
    if array.ndim == 1:
        rows = array[np.newaxis, :]
    elif array.ndim == 2:
        rows = array
    else:
        raise ValueError("weights must be one- or two-dimensional.")
    if rows.shape[0] == 0 or rows.shape[1] == 0:
        raise ValueError("weights must have at least one row and one key.")
    if not np.all(np.isfinite(rows)):
        raise ValueError("weights must contain only finite values.")
    if np.any(rows < 0.0):
        raise ValueError("softmax weights must be non-negative.")
    if not np.allclose(rows.sum(axis=1), 1.0, rtol=0.0, atol=1.0e-10):
        raise ValueError("every weight row must sum to one.")

    positive = np.where(rows > 0.0, rows, 1.0)
    entropy_per_row = -np.sum(
        np.where(rows > 0.0, rows * np.log(positive), 0.0),
        axis=1,
    )
    log_key_count = np.log(float(rows.shape[1]))
    normalized_entropy = (
        entropy_per_row / log_key_count if rows.shape[1] > 1 else np.zeros(rows.shape[0])
    )
    singular_values = np.linalg.svd(rows, compute_uv=False)
    energy = singular_values * singular_values
    energy_sum = float(np.sum(energy))
    energy_square_sum = float(np.sum(energy * energy))
    effective_rank = (
        energy_sum * energy_sum / energy_square_sum
        if energy_square_sum > _EPS
        else 0.0
    )

    return AttentionDescriptor(
        n_rows=int(rows.shape[0]),
        n_keys=int(rows.shape[1]),
        mean_entropy=float(np.mean(entropy_per_row)),
        mean_normalized_entropy=float(np.mean(normalized_entropy)),
        mean_localization=float(np.mean(np.max(rows, axis=1))),
        mean_effective_support=float(np.mean(np.exp(entropy_per_row))),
        effective_rank=float(effective_rank),
        negative_mass_fraction=0.0,
    )


@dataclass(frozen=True)
class AssociativeRecallBatch:
    """Deterministic key/query fixture for a mechanistic recall task."""

    queries: FloatArray
    keys: FloatArray
    targets: IntArray
    group_ids: tuple[str, ...]

    @property
    def n_examples(self) -> int:
        """Number of examples in the fixture."""
        return int(self.targets.size)

    def validate(self) -> None:
        """Validate shapes and finiteness before a task evaluation."""
        if self.queries.ndim != 2 or self.keys.ndim != 3:
            raise ValueError("queries must be 2D and keys must be 3D.")
        if self.queries.shape[0] != self.keys.shape[0]:
            raise ValueError("queries and keys must have the same example count.")
        if self.queries.shape[1] != self.keys.shape[2]:
            raise ValueError("query width must match the key width.")
        if self.targets.ndim != 1 or self.targets.size != self.keys.shape[0]:
            raise ValueError("targets must contain one index per example.")
        if len(self.group_ids) != self.targets.size:
            raise ValueError("group_ids must contain one label per example.")
        if self.keys.shape[1] == 0 or self.keys.shape[2] == 0:
            raise ValueError("the fixture must have non-zero sequence and feature widths.")
        if np.any(self.targets < 0) or np.any(self.targets >= self.keys.shape[1]):
            raise ValueError("targets must point to an existing key row.")
        if not (
            np.all(np.isfinite(self.queries)) and np.all(np.isfinite(self.keys))
        ):
            raise ValueError("queries and keys must contain only finite values.")
        if any(not group for group in self.group_ids):
            raise ValueError("group identifiers must not be empty.")


def make_associative_recall(
    *,
    group_count: int = 6,
    examples_per_group: int = 8,
    sequence_length: int = 16,
    dimension: int = 32,
    query_noise: float = 0.02,
    seed: int = 12345,
) -> AssociativeRecallBatch:
    """Create a deterministic grouped associative-recall fixture.

    Each query is derived from exactly one target key. Group identifiers are
    intended to represent independent runs or task instances, so a split may
    hold out complete groups rather than leaking adjacent examples.
    """
    integer_parameters = (
        ("group_count", group_count),
        ("examples_per_group", examples_per_group),
        ("sequence_length", sequence_length),
        ("dimension", dimension),
    )
    for name, value in integer_parameters:
        if int(value) != value or value < 1:
            raise ValueError(f"{name} must be a positive integer.")
    if group_count < 3:
        raise ValueError("group_count must be at least three for train/validation/test.")
    if not np.isfinite(query_noise) or query_noise < 0.0:
        raise ValueError("query_noise must be finite and non-negative.")

    rng = np.random.default_rng(seed)
    n_examples = group_count * examples_per_group
    keys = rng.normal(
        size=(n_examples, sequence_length, dimension)
    ).astype(np.float64)
    norms = np.linalg.norm(keys, axis=2, keepdims=True)
    keys /= np.maximum(norms, _EPS)
    targets = rng.integers(
        0,
        sequence_length,
        size=n_examples,
        dtype=np.int64,
    )
    rows = np.arange(n_examples)
    queries = np.sqrt(float(dimension)) * keys[rows, targets]
    if query_noise > 0.0:
        queries = queries + query_noise * rng.normal(size=queries.shape)
    queries = np.asarray(queries, dtype=np.float64)
    group_ids = tuple(
        f"group-{index // examples_per_group:03d}" for index in range(n_examples)
    )
    batch = AssociativeRecallBatch(queries, keys, targets, group_ids)
    batch.validate()
    return batch


@dataclass(frozen=True)
class RecallMetrics:
    """Bounded associative-recall metrics plus operator diagnostics."""

    partition: str
    n_examples: int
    accuracy: float
    mean_target_weight: float
    descriptor: AttentionDescriptor

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible metrics record."""
        return {
            "partition": self.partition,
            "n_examples": self.n_examples,
            "accuracy": self.accuracy,
            "mean_target_weight": self.mean_target_weight,
            "descriptor": self.descriptor.as_dict(),
        }


def evaluate_associative_recall(
    batch: AssociativeRecallBatch,
    indices: Iterable[int],
    *,
    partition: str = "unspecified",
    scale: float | None = None,
) -> RecallMetrics:
    """Evaluate a fixed-index partition with the scalar reference."""
    batch.validate()
    selected = tuple(int(index) for index in indices)
    if not selected:
        raise ValueError("at least one example is required.")
    if len(set(selected)) != len(selected):
        raise ValueError("evaluation indices must be unique.")
    if any(index < 0 or index >= batch.n_examples for index in selected):
        raise IndexError("evaluation index is outside the batch.")
    if not partition:
        raise ValueError("partition must not be empty.")

    weights: list[FloatArray] = []
    predictions: list[int] = []
    target_weights: list[float] = []
    for index in selected:
        forward = scaled_dot_product_weights(
            batch.queries[index],
            batch.keys[index],
            scale=scale,
        )
        weights.append(forward)
        predictions.append(int(np.argmax(forward)))
        target_weights.append(float(forward[batch.targets[index]]))
    matrix = np.vstack(weights)
    descriptor = summarize_attention_weights(matrix)
    return RecallMetrics(
        partition=partition,
        n_examples=len(selected),
        accuracy=float(
            np.mean(
                np.asarray(predictions, dtype=np.int64)
                == batch.targets[np.asarray(selected, dtype=np.int64)]
            )
        ),
        mean_target_weight=float(np.mean(target_weights)),
        descriptor=descriptor,
    )


@dataclass(frozen=True)
class GroupedSplit:
    """A deterministic split whose partitions contain whole groups."""

    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    train_groups: tuple[str, ...]
    validation_groups: tuple[str, ...]
    test_groups: tuple[str, ...]

    def assert_disjoint(self) -> None:
        """Reject any overlap between train, validation, or final groups."""
        partitions = (
            ("train", self.train_groups),
            ("validation", self.validation_groups),
            ("test", self.test_groups),
        )
        for left_index, (left_name, left_groups) in enumerate(partitions):
            for right_name, right_groups in partitions[left_index + 1 :]:
                overlap = set(left_groups).intersection(right_groups)
                if overlap:
                    raise ValueError(
                        f"{left_name} and {right_name} groups overlap: {sorted(overlap)}"
                    )

    def assert_training_only(self, indices: Iterable[int]) -> None:
        """Reject calibration/training rows drawn from the frozen final set."""
        selected = tuple(int(index) for index in indices)
        if len(set(selected)) != len(selected):
            raise ValueError("training or calibration indices must be unique.")
        if any(index < 0 for index in selected):
            raise IndexError("training or calibration indices must be non-negative.")
        overlap = set(selected).intersection(self.test_indices)
        if overlap:
            raise ValueError(
                "training or calibration cannot use frozen final indices: "
                f"{sorted(overlap)}"
            )

    def as_dict(self) -> dict[str, object]:
        """Return split assignments without exposing any mutable arrays."""
        return {
            "train_indices": list(self.train_indices),
            "validation_indices": list(self.validation_indices),
            "test_indices": list(self.test_indices),
            "train_groups": list(self.train_groups),
            "validation_groups": list(self.validation_groups),
            "test_groups": list(self.test_groups),
        }


def grouped_holdout_split(
    group_ids: Sequence[str],
    *,
    seed: int = 12345,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> GroupedSplit:
    """Build a deterministic whole-group train/validation/final partition."""
    labels = tuple(str(group) for group in group_ids)
    if not labels or any(not group for group in labels):
        raise ValueError("group_ids must contain non-empty identifiers.")
    if not (
        np.isfinite(train_fraction)
        and np.isfinite(validation_fraction)
        and train_fraction > 0.0
        and validation_fraction > 0.0
        and train_fraction + validation_fraction < 1.0
    ):
        raise ValueError(
            "train_fraction and validation_fraction must be positive and sum below one."
        )

    unique_groups = tuple(sorted(set(labels)))
    if len(unique_groups) < 3:
        raise ValueError("at least three distinct groups are required.")
    permutation = np.random.default_rng(seed).permutation(len(unique_groups))
    ordered_groups = tuple(unique_groups[int(index)] for index in permutation)
    n_groups = len(ordered_groups)
    n_train = max(1, min(n_groups - 2, int(np.floor(n_groups * train_fraction))))
    remaining = n_groups - n_train
    n_validation = max(
        1,
        min(remaining - 1, int(np.floor(n_groups * validation_fraction))),
    )
    train_groups = ordered_groups[:n_train]
    validation_groups = ordered_groups[n_train : n_train + n_validation]
    test_groups = ordered_groups[n_train + n_validation :]

    def indices_for(groups: tuple[str, ...]) -> tuple[int, ...]:
        allowed = set(groups)
        return tuple(index for index, group in enumerate(labels) if group in allowed)

    split = GroupedSplit(
        train_indices=indices_for(train_groups),
        validation_indices=indices_for(validation_groups),
        test_indices=indices_for(test_groups),
        train_groups=train_groups,
        validation_groups=validation_groups,
        test_groups=test_groups,
    )
    split.assert_disjoint()
    return split


@dataclass(frozen=True)
class AttentionResearchProtocol:
    """Preregistered task metadata with a frozen final-evaluation partition."""

    task_name: str
    seed: int
    split: GroupedSplit

    def __post_init__(self) -> None:
        if not self.task_name:
            raise ValueError("task_name must not be empty.")
        self.split.assert_disjoint()

    @property
    def training_indices(self) -> tuple[int, ...]:
        """Rows allowed for fitting or calibration."""
        return self.split.train_indices

    @property
    def validation_indices(self) -> tuple[int, ...]:
        """Rows allowed for model/threshold selection."""
        return self.split.validation_indices

    @property
    def final_indices(self) -> tuple[int, ...]:
        """Rows reserved for one final evaluation."""
        return self.split.test_indices

    def assert_training_indices(self, indices: Iterable[int]) -> None:
        """Guard fitting/calibration from final-evaluation rows."""
        self.split.assert_training_only(indices)

    def assert_final_indices(self, indices: Iterable[int]) -> None:
        """Require final reporting to use exactly the frozen final rows."""
        selected = tuple(int(index) for index in indices)
        if selected != self.final_indices:
            raise ValueError("final evaluation must use the frozen final indices exactly.")

    def as_dict(self) -> dict[str, object]:
        """Return the complete preregistered protocol record."""
        return {
            "task_name": self.task_name,
            "seed": self.seed,
            "split": self.split.as_dict(),
        }


def build_attention_protocol(
    group_ids: Sequence[str],
    *,
    task_name: str = "associative-recall",
    seed: int = 12345,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> AttentionResearchProtocol:
    """Construct a grouped, leakage-safe protocol for a research task."""
    split = grouped_holdout_split(
        group_ids,
        seed=seed,
        train_fraction=train_fraction,
        validation_fraction=validation_fraction,
    )
    return AttentionResearchProtocol(task_name=task_name, seed=seed, split=split)
