from __future__ import annotations

import pytest

from itd_research.experiment_schema import SourceIdentity
from itd_research.flat_reference_adapter import (
    FlatReferenceCase,
    FlatReferenceResult,
)


def _case() -> FlatReferenceCase:
    return FlatReferenceCase(
        case_id="flat-ref-1",
        source=SourceIdentity("Memorithm/FLAT-ATTENTION", "flat-test"),
        batch=2,
        heads=4,
        seq_len=8,
        head_dim=16,
        causal=True,
        softmax_scale=None,
        q_sha256="a" * 64,
        k_sha256="b" * 64,
        v_sha256="c" * 64,
    )


def test_flat_reference_case_counts_tensor_and_lse_elements() -> None:
    case = _case()

    assert case.tensor_elements == 2 * 4 * 8 * 16
    assert case.lse_elements == 2 * 4 * 8


def test_flat_reference_result_cannot_authorize_performance_or_routing() -> None:
    case = _case()
    result = FlatReferenceResult(
        case_id=case.case_id,
        output_sha256="d" * 64,
        lse_sha256="e" * 64,
    )

    result.assert_matches_case(case)
    assert result.authorizes_performance_claim is False
    assert result.authorizes_runtime_routing is False


def test_flat_reference_rejects_wrong_source_repository() -> None:
    with pytest.raises(ValueError, match="FLAT reference source"):
        FlatReferenceCase(
            case_id="flat-ref-1",
            source=SourceIdentity("other/repo", "test"),
            batch=1,
            heads=1,
            seq_len=1,
            head_dim=1,
            causal=False,
            softmax_scale=None,
            q_sha256="a" * 64,
            k_sha256="b" * 64,
            v_sha256="c" * 64,
        )


def test_flat_reference_rejects_invalid_scale() -> None:
    with pytest.raises(ValueError, match="softmax_scale"):
        FlatReferenceCase(
            case_id="flat-ref-1",
            source=SourceIdentity("Memorithm/FLAT-ATTENTION", "test"),
            batch=1,
            heads=1,
            seq_len=1,
            head_dim=1,
            causal=False,
            softmax_scale=0.0,
            q_sha256="a" * 64,
            k_sha256="b" * 64,
            v_sha256="c" * 64,
        )
