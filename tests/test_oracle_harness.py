from __future__ import annotations

from pathlib import Path

import pytest

import oracle_harness

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests" / "fixtures" / "oracle_data.rs"


def test_committed_oracle_fixture_matches_generator() -> None:
    expected = REFERENCE.read_text(encoding="utf-8")
    actual = oracle_harness.render_oracle_fixture()
    matches, detail = oracle_harness.fixtures_equivalent(expected, actual)
    assert matches, detail


def test_fixture_comparison_rejects_structural_and_large_numeric_changes() -> None:
    assert not oracle_harness.fixtures_equivalent("value 1.0\n", "other 1.0\n")[0]
    assert not oracle_harness.fixtures_equivalent("value 1.0\n", "value 1.1\n")[0]


def test_normal_generation_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "fixture.rs"
    output.write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        oracle_harness.write_fixture(output, "replacement", force=False)
    assert output.read_text(encoding="utf-8") == "existing"
