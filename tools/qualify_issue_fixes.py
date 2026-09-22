"""Apply reviewed contract corrections in an isolated checkout; never move refs."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = "7ba33919d47232a093c882a8ee4b531ecc0f1aeb"
REPO = "Memorithm/itd-simulator"
EXPECTED = "96ff0686039ce71deb9968a8ecf0af414e96926c"
ROOT = Path(os.environ["RUNNER_TEMP"]) / ("issue-contracts-" + os.environ["GITHUB_RUN_ID"])
WORK = ROOT / "work"
OUT = ROOT / "evidence"
SOURCE = Path(os.environ["GITHUB_WORKSPACE"])
ENV = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}


def run(args: list[str], log: str | None = None) -> str:
    result = subprocess.run(args, cwd=WORK, env=ENV, capture_output=True, text=True, timeout=900)
    if log:
        (OUT / log).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"{args!r}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def api(path: str, data: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        data=json.dumps(data).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main() -> None:
    if os.environ["GITHUB_REPOSITORY"] != REPO or os.environ["GITHUB_REF"] != "refs/heads/repair/itd-issue-contracts-20260922":
        raise RuntimeError("wrong staging scope")
    OUT.mkdir(parents=True)
    subprocess.run(["git", "worktree", "add", "--detach", str(WORK), BASE], cwd=SOURCE, env=ENV, check=True)
    for name in ("apply_issue_fixes.py", "apply_uq_fixes.py"):
        run([sys.executable, str(SOURCE / "tools" / name)])
    campaign_path = WORK / "itd_research/campaign_runner.py"
    campaign_text = campaign_path.read_text()
    old_import = "from itd_research.experiment_schema import ExperimentProtocolV1, SourceIdentity, SplitRole"
    if campaign_text.count(old_import) != 1:
        raise RuntimeError("unexpected campaign import")
    campaign_path.write_text(campaign_text.replace(old_import, "from itd_research.experiment_schema import (\n    ExperimentProtocolV1,\n    SourceIdentity,\n    SplitRole,\n)"))
    for name in ("test_itd30_evidence_integrity.py", "test_itd34_undefined_risk.py"):
        (WORK / "tests" / name).write_bytes((SOURCE / "tools" / "issue-fixtures" / name).read_bytes())
    for name, expression in {
        "test_itd38_forge_search_adapter.py": "_contract(role)",
        "test_itd33_tdi_trajectory_adapter.py": "_step(0, role=role)",
        "test_itd37_noiselab_adapter.py": "_intervention(role)",
        "test_itd32_neural_operator_adapter.py": "_sample(role).assert_selection_allowed()",
        "test_itd32_auxiliary_supervision.py": 'replace(_arm("baseline", None), role=role)',
    }.items():
        path = WORK / "tests" / name
        text = path.read_text()
        if "replace(" in expression:
            text = text.replace("import pytest", "from dataclasses import replace\n\nimport pytest")
        text += '\n\n@pytest.mark.parametrize("role", ["final", "unknown", None])\ndef test_serialized_role_cannot_bypass_final_boundary(role: object) -> None:\n    with pytest.raises((ValueError, TypeError)):\n        ' + expression + '\n'
        path.write_text(text)
    (WORK / "docs/itd3x/ITD_30_6_EVIDENCE_INTEGRITY.md").write_bytes((SOURCE / "tools/issue-fixtures/ITD_30_6_EVIDENCE_INTEGRITY.md").read_bytes())
    run(["git", "add", "itd_research", "tests", "docs/itd3x"])
    run([sys.executable, "tools/check_manifest.py", "--update"], "manifest-update.log")
    run(["git", "add", "MANIFEST.sha256"])
    run(["git", "diff", "--cached", "--check"])
    tree = run(["git", "write-tree"])
    if tree != EXPECTED:
        raise RuntimeError(f"candidate differs from locally reviewed tree: {tree}")
    for name, args in [
        ("manifest.log", [sys.executable, "tools/check_manifest.py"]),
        ("ruff.log", ["ruff", "check", "."]),
        ("mypy.log", ["mypy", "tools/check_manifest.py", "tools/check_commit_messages.py", "tools/check_v29_summary.py", "tools/deterministic_smoke.py", "itd_research"]),
        ("tests.log", [sys.executable, "-m", "pytest", "-q", *sorted(str(p.relative_to(WORK)) for p in (WORK / "tests").glob("test_itd*.py")), "tests/test_ai_experiment_schema.py"]),
    ]:
        run(args, name)
    if run(["git", "diff", "--name-only"]):
        raise RuntimeError("validation changed tracked files")
    paths = run(["git", "diff", "--cached", "--name-only", BASE]).splitlines()
    entries = []
    for path in paths:
        if path != "MANIFEST.sha256" and not path.startswith(("itd_research/", "tests/test_itd", "docs/itd3x/")):
            raise RuntimeError("unreviewed path")
        content = (WORK / path).read_bytes()
        blob = api("git/blobs", {"content": content.decode(), "encoding": "utf-8"})["sha"]
        digest = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if blob != digest:
            raise RuntimeError("remote blob mismatch")
        mode = run(["git", "ls-files", "--stage", "--", path]).split()[0]
        entries.append({"path": path, "mode": mode, "type": "blob", "sha": blob})
    remote = api("git/trees", {"base_tree": run(["git", "rev-parse", BASE + "^{tree}"]), "tree": entries})["sha"]
    if tree != remote:
        raise RuntimeError("remote tree mismatch")
    (OUT / "candidate.diff").write_text(run(["git", "diff", "--cached", "--binary"]) + "\n")
    (OUT / "MANIFEST.sha256").write_bytes((WORK / "MANIFEST.sha256").read_bytes())
    summary = {"base": BASE, "tree": tree, "paths": paths, "remote_refs_modified": False,
               "tests": "manifest, Ruff, mypy, test_itd*.py and protocol suite passed"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
