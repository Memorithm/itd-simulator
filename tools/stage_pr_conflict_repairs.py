"""Prepare a serial integration chain; publish no branch and merge no PR."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = "Memorithm/itd-simulator"
BASE = "747e32ad5992fd71256b8fbf309376a9427cb0d8"
HEADS = {
    44: "ed18b387ac24a8267ff9b8a3c88513d622ccd6dd",
    45: "2ebd2db6d9df4fcab0039703ac58509a51eff6f5",
    46: "b65e9df4c89678302af37bef56236bf6dcdefa7b",
    47: "d3b64d88e281511dcf472d8287d22d1c277a2eb4",
    48: "a9af1ffc46172171e9ceeb8168fd20b3e60895ce",
    49: "7860e37a933ec5150cf3c134a5546c65dc5336ac",
    50: "3229a839a4837ea37fac71c88dd0a1734e0a982a",
    52: "8141216f228768cae6e9ade73147aba847bd29bc",
    53: "462a3b1a94b48ab7caa71978858436f352994342",
    56: "5ffcc24e7dabffa5074370bb91ac6c81a170b539",
}
ROOT = Path(os.environ["REPAIR_ROOT"])
WORK = ROOT / "work"
OUT = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
ENV = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
ENV.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")


def api(suffix: str, data: dict | None = None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{suffix}",
        data=None if data is None else json.dumps(data).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def command(args, *, check=True, log=None):
    p = subprocess.run(args, cwd=WORK, env=ENV, capture_output=True, text=True, timeout=600)
    if log is not None:
        log.write_text(p.stdout + p.stderr)
    if check and p.returncode:
        raise RuntimeError(f"{args!r}: exit {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def git(*args, check=True):
    return command(["git", *args], check=check).stdout.strip()


def tree_map(rev):
    result = {}
    for entry in git("ls-tree", "-rz", "--full-tree", rev).split("\0"):
        if not entry:
            continue
        spec, path = entry.split("\t", 1)
        mode, kind, sha = spec.split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise RuntimeError(f"unsupported file kind: {path}")
        result[path] = (mode, sha)
    return result


def check_live():
    assert api("branches/main")["commit"]["sha"] == BASE, "main moved"
    pulls = api("pulls?state=open&per_page=100")
    assert {p["number"] for p in pulls} == set(HEADS), "open PR set changed"
    for p in pulls:
        assert p["head"]["sha"] == HEADS[p["number"]], "PR head moved"
        assert p["base"]["ref"] == "main" and p["head"]["repo"]["full_name"] == REPO
    return {p["number"]: p for p in pulls}


def main():
    assert os.environ["GITHUB_REPOSITORY"] == REPO
    assert os.environ["GITHUB_REF"] == "refs/heads/repair/itd-pr-conflicts-20260922"
    pulls = check_live()
    subprocess.run(["git", "clone", "--no-tags", "--no-checkout", f"https://github.com/{REPO}.git", str(WORK)], check=True, env=ENV, timeout=300)
    git("config", "user.name", "MEMOPERF")
    git("config", "user.email", "contact@checkupauto.fr")
    git("config", "core.hooksPath", "/dev/null")
    results = []
    current = BASE
    expected = tree_map(BASE)
    for number, head in HEADS.items():
        dest = OUT / str(number)
        dest.mkdir()
        record = {"pr": number, "old_head": head, "main": BASE, "branch": pulls[number]["head"]["ref"], "ready": False, "refs_modified": False,
                  "predecessor_pr": results[-1]["pr"] if results else None}
        results.append(record)
        git("fetch", "--no-tags", "origin", head)
        ancestor = git("merge-base", current, head)
        head_map, ancestor_map = tree_map(head), tree_map(ancestor)
        own_paths = []
        for line in git("diff", "--name-status", ancestor, head).splitlines():
            status, path = line.split("\t")
            if path == "MANIFEST.sha256":
                continue
            assert status in ("A", "M"), (status, path)
            assert path.startswith(("itd_research/", "tests/test_itd", "docs/itd3x/")), path
            assert expected.get(path) in (ancestor_map.get(path), head_map[path]), "overlapping source edit requires review"
            expected[path] = head_map[path]
            own_paths.append(path)
        git("checkout", "--force", "--detach", head)
        merged = command(["git", "merge", "--no-commit", "--no-ff", current], check=False, log=dest/"merge.log")
        conflicts = git("diff", "--name-only", "--diff-filter=U").splitlines()
        assert merged.returncode in (0, 1) and set(conflicts) <= {"MANIFEST.sha256"}, conflicts
        if conflicts:
            git("checkout", "--ours", "--", "MANIFEST.sha256")
            git("add", "--", "MANIFEST.sha256")
        command([sys.executable, "tools/check_manifest.py", "--update"], log=dest/"manifest-update.log")
        git("add", "--", "MANIFEST.sha256")
        assert not git("diff", "--name-only", "--diff-filter=U")
        git("diff", "--cached", "--check")
        local_tree = git("write-tree")
        observed = tree_map(local_tree)
        assert {k:v for k,v in observed.items() if k != "MANIFEST.sha256"} == {k:v for k,v in expected.items() if k != "MANIFEST.sha256"}, "merged sources differ from reviewed union"
        for name, args in [
            ("manifest", [sys.executable, "tools/check_manifest.py"]),
            ("ruff", ["ruff", "check", "."]),
            ("mypy", ["mypy", "tools/check_manifest.py", "tools/check_commit_messages.py", "tools/check_v29_summary.py", "tools/deterministic_smoke.py", "itd_research"]),
            ("tests", [sys.executable, "-m", "pytest", "-q", *sorted(str(p.relative_to(WORK)) for p in (WORK/"tests").glob("test_itd*.py"))]),
        ]:
            command(args, log=dest/(name+".log"))
        assert not git("diff", "--name-only"), "tests modified sources"
        (dest/"candidate.diff").write_text(git("diff", "--cached", current)+"\n")
        manifest = (WORK/"MANIFEST.sha256").read_bytes()
        (dest/"MANIFEST.sha256").write_bytes(manifest)
        blob = api("git/blobs", {"content": manifest.decode(), "encoding": "utf-8"})["sha"]
        assert blob == hashlib.sha1(b"blob "+str(len(manifest)).encode()+b"\0"+manifest).hexdigest()
        entries = [{"path": p, "mode": spec[0], "type": "blob", "sha": spec[1]} for p, spec in observed.items() if head_map.get(p) != spec]
        assert set(head_map) <= set(observed), "unexpected file deletion"
        remote_tree = api("git/trees", {"base_tree": git("rev-parse", head+"^{tree}"), "tree": entries})["sha"]
        assert remote_tree == local_tree
        previous = current
        current = git("commit-tree", local_tree, "-p", head, "-p", previous, "-m", f"Local serial integration candidate #{number}")
        record.update(ready=True, tree=remote_tree, conflicts_resolved=conflicts, own_paths=own_paths,
                      manifest_sha256=hashlib.sha256(manifest).hexdigest(), files=len(observed),
                      tests="manifest, Ruff, mypy, cumulative test_itd*.py passed")
        expected = observed
        git("merge", "--abort", check=False)
        git("reset", "--hard", head)
        (OUT/"staged.json").write_text(json.dumps(results, indent=2)+"\n")
        print(json.dumps(record), flush=True)
    check_live()
    git("checkout", "--force", "--detach", current)
    git("archive", "-o", str(OUT/"final-source.tar"), current)
    (OUT/"scope.json").write_text(json.dumps({"base": BASE, "order": list(HEADS), "refs_modified": False, "merges_performed": False,
        "method": "serial cumulative trees; only generated-manifest conflicts resolved; exact reviewed source union"},indent=2)+"\n")


if __name__ == "__main__":
    main()
