"""Tests for the deterministic AI-attention research protocol."""

from __future__ import annotations

import numpy as np
import pytest

from itd_research.attention_lab import (
    build_attention_protocol,
    evaluate_associative_recall,
    grouped_holdout_split,
    make_associative_recall,
    scaled_dot_product_attention,
    summarize_attention_weights,
)


def test_scalar_attention_is_normalized_and_respects_visibility() -> None:
    query = np.array([1.0, 0.0])
    keys = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    values = np.array([[2.0], [4.0], [8.0]])
    forward = scaled_dot_product_attention(
        query,
        keys,
        values,
        mask=np.array([True, True, False]),
        scale=4.0,
    )

    assert np.sum(forward.weights) == pytest.approx(1.0)
    assert forward.weights[2] == 0.0
    assert forward.output[0] < 4.0


def test_attention_descriptor_is_bounded_and_deterministic() -> None:
    weights = np.array([[0.8, 0.2, 0.0], [0.1, 0.1, 0.8]])
    first = summarize_attention_weights(weights)
    second = summarize_attention_weights(weights)

    assert first == second
    assert 0.0 <= first.mean_normalized_entropy <= 1.0
    assert 0.0 <= first.mean_localization <= 1.0
    assert first.effective_rank >= 1.0
    assert first.negative_mass_fraction == 0.0


def test_associative_recall_fixture_and_protocol_are_reproducible() -> None:
    first = make_associative_recall(
        group_count=6,
        examples_per_group=3,
        sequence_length=8,
        dimension=8,
        seed=7,
    )
    second = make_associative_recall(
        group_count=6,
        examples_per_group=3,
        sequence_length=8,
        dimension=8,
        seed=7,
    )
    assert np.array_equal(first.queries, second.queries)
    assert np.array_equal(first.keys, second.keys)
    assert np.array_equal(first.targets, second.targets)
    assert first.group_ids == second.group_ids

    protocol = build_attention_protocol(first.group_ids, seed=19)
    protocol.assert_training_indices(protocol.training_indices + protocol.validation_indices)
    train = evaluate_associative_recall(
        first,
        protocol.training_indices,
        partition="train",
    )
    final = evaluate_associative_recall(
        first,
        protocol.final_indices,
        partition="final",
    )
    assert train.n_examples > 0
    assert final.n_examples > 0
    assert 0.0 <= train.accuracy <= 1.0
    assert 0.0 <= final.mean_target_weight <= 1.0


def test_grouped_protocol_rejects_final_set_reuse() -> None:
    groups = tuple(f"run-{index // 2}" for index in range(12))
    split = grouped_holdout_split(groups, seed=3)
    assert set(split.train_groups).isdisjoint(split.validation_groups)
    assert set(split.train_groups).isdisjoint(split.test_groups)
    assert set(split.validation_groups).isdisjoint(split.test_groups)

    with pytest.raises(ValueError, match="frozen final"):
        split.assert_training_only(split.test_indices)

    protocol = build_attention_protocol(groups, seed=3)
    with pytest.raises(ValueError, match="frozen final indices exactly"):
        protocol.assert_final_indices(protocol.final_indices[:-1])
