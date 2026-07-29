"""Tests for ``tools/check_commit_messages.py``.

The identity requirement is exempt for MERGE commits and only for them: a merge produced
by GitHub's merge button is authored by whoever clicked it and committed by
``GitHub <noreply@github.com>``, an identity no human can set, so enforcing it there made
every merge into the default branch fail while saying nothing about who wrote the code.

These tests pin BOTH halves of that statement, so the exemption can never quietly widen
into "the policy is off": an ordinary commit with the wrong identity must still fail, and
a merge carrying a forbidden trailer must still fail.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_CHECKER = _ROOT / "tools" / "check_commit_messages.py"
_IDENTITY = ("Tarek Zekriti", "194770978+CHECKUPAUTO@users.noreply.github.com")


def _git(repo: Path, *args: str, name: str | None = None, email: str | None = None) -> str:
    command = ["git"]
    if name is not None:
        command += ["-c", f"user.name={name}"]
    if email is not None:
        command += ["-c", f"user.email={email}"]
    result = subprocess.run(
        [*command, *args], cwd=repo, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _run_checker(repo: Path, revision_range: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(_CHECKER), "--require-identity", revision_range],
        cwd=repo, capture_output=True, text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A tiny repository with a side branch ready to merge."""
    _git(tmp_path, "init", "-q", ".")
    _git(tmp_path, "config", "user.name", _IDENTITY[0])
    _git(tmp_path, "config", "user.email", _IDENTITY[1])
    (tmp_path / "a.txt").write_text("a\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "checkout", "-qb", "side")
    (tmp_path / "b.txt").write_text("b\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "side commit")
    _git(tmp_path, "checkout", "-q", "-")
    return tmp_path


def test_merge_commit_with_github_identity_is_accepted(repo: Path) -> None:
    """The fix: GitHub's merge-button identity no longer fails the default branch."""
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "merge", "--no-ff", "-q", "side", "-m", "Merge pull request #1 from x/y",
         name="GitHub", email="noreply@github.com")
    result = _run_checker(repo, f"{base}..HEAD")
    assert result.returncode == 0, result.stdout + result.stderr


def test_ordinary_commit_with_wrong_identity_still_fails(repo: Path) -> None:
    """The guardrail is intact: the exemption covers merges only."""
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "ordinary commit",
         name="Someone Else", email="else@example.com")
    result = _run_checker(repo, f"{base}..HEAD")
    assert result.returncode != 0
    assert "author is" in (result.stdout + result.stderr)


def test_merge_commit_carrying_a_forbidden_trailer_still_fails(repo: Path) -> None:
    """Merges are exempt from the IDENTITY rule only -- never from the trailer rule."""
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "merge", "--no-ff", "-q", "side",
         "-m", "Merge pull request #1\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
         name="GitHub", email="noreply@github.com")
    result = _run_checker(repo, f"{base}..HEAD")
    assert result.returncode != 0
    assert "forbidden trailer" in (result.stdout + result.stderr)
