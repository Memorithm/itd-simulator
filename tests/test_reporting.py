"""Tests for the deterministic, overwrite-safe reporting layer."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_csv,
    write_json,
    write_manifest,
)


def test_write_json_is_sorted_and_round_trippable(tmp_path: Path) -> None:
    data = {"b": 2, "a": np.float64(1.5), "nested": {"z": [np.int64(3)]}}
    path = write_json(tmp_path, "out.json", data)
    text = path.read_text(encoding="utf-8")
    assert text.index('"a"') < text.index('"b"')
    loaded = json.loads(text)
    assert loaded == {"a": 1.5, "b": 2, "nested": {"z": [3]}}


def test_write_json_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    write_json(tmp_path, "out.json", {"x": 1})
    with pytest.raises(FileExistsError):
        write_json(tmp_path, "out.json", {"x": 2})
    # explicit overwrite succeeds
    path = write_json(tmp_path, "out.json", {"x": 2}, overwrite=True)
    assert json.loads(path.read_text())["x"] == 2


def test_write_csv_is_deterministic_and_rejects_bad_cells(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        "out.csv",
        ("name", "value", "flag"),
        [["a", 1.5, True], ["b", 2, False]],
    )
    assert path.read_text(encoding="utf-8") == "name,value,flag\na,1.5,true\nb,2,false\n"
    with pytest.raises(ValueError):
        write_csv(tmp_path, "bad.csv", ("a",), [["has,comma"]])
    with pytest.raises(ValueError):
        write_csv(tmp_path, "bad2.csv", ("a", "b"), [["only-one"]])


def test_reporting_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_json(tmp_path, "../escape.json", {"x": 1})
    with pytest.raises(ValueError):
        write_json(tmp_path, "sub/../../escape.json", {"x": 1})


def test_reporting_rejects_symlink_target(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    os.symlink(real, link)
    with pytest.raises(ValueError):
        write_json(tmp_path, "link.json", {"x": 1}, overwrite=True)


def test_write_json_rejects_unserialisable(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        write_json(tmp_path, "bad.json", {"x": object()})


def test_prepare_output_directory_rejects_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real_dir"
    real.mkdir()
    link = tmp_path / "link_dir"
    os.symlink(real, link)
    with pytest.raises(ValueError):
        prepare_output_directory(link)


def test_manifest_records_digests_and_environment(tmp_path: Path) -> None:
    a = write_json(tmp_path, "a.json", {"x": 1})
    b = write_csv(tmp_path, "b.csv", ("h",), [["1"]])
    manifest = write_manifest(tmp_path, [a, b], environment_metadata())
    loaded = json.loads(manifest.read_text(encoding="utf-8"))
    assert {entry["path"] for entry in loaded["artifacts"]} == {"a.json", "b.csv"}
    for entry in loaded["artifacts"]:
        assert len(entry["sha256"]) == 64
    assert loaded["environment"]["model_baseline"] == "ITD V29.18 (preserved)"
    assert "numpy_version" in loaded["environment"]


def test_environment_metadata_has_expected_keys() -> None:
    metadata = environment_metadata()
    for key in ("python_version", "numpy_version", "git_commit", "thread_environment"):
        assert key in metadata
