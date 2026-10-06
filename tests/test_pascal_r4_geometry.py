from __future__ import annotations

import pytest

from itd_research.experiment_schema import SplitRole
from itd_research.pascal_resume_integrity import (
    PASCAL_R4_CASES_PER_SPLIT,
    PASCAL_R4_PREFIXES,
    pascal_r4_case_ids,
    pascal_r4_shape,
    pascal_r4_source_payload,
)


def test_r4_geometry_is_nonfinal() -> None:
    assert PASCAL_R4_PREFIXES == (1, 4, 7)
    assert PASCAL_R4_CASES_PER_SPLIT == 8
    assert pascal_r4_shape(SplitRole.DEVELOPMENT) == (7, 128)
    assert pascal_r4_shape(SplitRole.VALIDATION) == (9, 512)
    assert len(set(pascal_r4_case_ids(SplitRole.DEVELOPMENT))) == 8
    assert len(set(pascal_r4_case_ids(SplitRole.VALIDATION))) == 8
    with pytest.raises(ValueError, match="protected"):
        pascal_r4_source_payload(SplitRole.FINAL)
