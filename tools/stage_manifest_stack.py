"""Stage cumulative, source-preserving PR repairs. Never update remote refs."""
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
MANIFEST = "MANIFEST.sha256"
ROOT = Path(os.environ["REPAIR_ROOT"])
WORK = ROOT / "work"
OUT = ROOT / "evidence"
ENV = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
ENV.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def api(suffix, data=None):
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
    p = subprocess.run(args, cwd=WORK, env=ENV, capture_output=True, text=True, timeout=900)
    if log is not None:
        log.write_text(p.stdout + p.stderr)
    if check and p.returncode:
        raise RuntimeError(f"{args!r}: exit {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def git(*args, check=True):
    return command(["git", *args], check=check).stdout.strip()


def tree(ref):
    raw = subprocess.check_output(["git", "ls-tree", "-rz", ref], cwd=WORK, env=ENV)
    result = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, sha = meta.decode().split()
        require(kind == "blob" and mode in ("100644", "100755"), "non-regular tree entry")
        result[path.decode()] = (mode, sha)
    return result


def nonmanifest(entries):
    return {p: v for p, v in entries.items() if p != MANIFEST}


def check_live():
    require(api("branches/main")["commit"]["sha"] == BASE, "main moved; stop and review new base")
    snapshots = {}
    for number, head in HEADS.items():
        p = api(f"pulls/{number}")
        require(p["state"] == "open" and not p["merged"], f"PR {number} is no longer open")
        require(p["base"]["ref"] == "main", f"PR {number} changed base")
        require(p["head"]["sha"] == head and p["head"]["repo"]["full_name"] == REPO,
                f"PR {number} changed head or repository")
        snapshots[number] = {"branch": p["head"]["ref"], "title": p["title"], "body": p["body"]}
    return snapshots


def main():
    require(os.environ["GITHUB_REPOSITORY"] == REPO, "wrong repository")
    require(os.environ["GITHUB_REF"] == "refs/heads/repair/itd-pr-conflicts-20260922", "wrong staging branch")
    OUT.mkdir(parents=True)
    snapshots = check_live()
    subprocess.run(["git", "clone", "--no-checkout", f"https://github.com/{REPO}.git", str(WORK)],
                   check=True, env=ENV, timeout=300)
    git("config", "user.name", "MEMOPERF")
    git("config", "user.email", "contact@checkupauto.fr")
    expected = nonmanifest(tree(BASE))
    parent = BASE
    records = []
    for number, head in HEADS.items():
        dest = OUT / str(number)
        dest.mkdir()
        git("fetch", "--no-tags", "origin", head)
        common = git("merge-base", BASE, head)
        old_tree, ancestor_tree = tree(head), tree(common)
        delta = {p: v for p, v in old_tree.items() if p != MANIFEST and ancestor_tree.get(p) != v}
        require(not (set(ancestor_tree) - set(old_tree)), f"unexpected deletion in PR {number}")
        for path, value in delta.items():
            require(path.startswith(("itd_research/", "tests/test_itd", "docs/itd3x/")), f"unreviewed path {path}")
            require(expected.get(path) in (None, ancestor_tree.get(path), value), f"source overlap {path}")
            expected[path] = value
        git("checkout", "--force", "--detach", head)
        merge = command(["git", "merge", "--no-commit", "--no-ff", parent], check=False, log=dest/"merge.log")
        conflicts = git("diff", "--name-only", "--diff-filter=U").splitlines()
        require(merge.returncode in (0, 1) and set(conflicts) <= {MANIFEST}, f"non-manifest conflict {conflicts}")
        if conflicts:
            git("checkout", "--ours", "--", MANIFEST)
            git("add", "--", MANIFEST)
        require(tree(BASE)["tools/check_manifest.py"] == tree(head)["tools/check_manifest.py"], "manifest checker changed")
        command([sys.executable, "tools/check_manifest.py", "--update"], log=dest/"manifest-update.log")
        git("add", "--", MANIFEST)
        require(not git("diff", "--name-only", "--diff-filter=U"), "unresolved index")
        candidate_tree = git("write-tree")
        require(nonmanifest(tree(candidate_tree)) == expected, "source union differs; no staged commit published")
        git("diff", "--cached", "--check")
        for label, args in (
            ("manifest", [sys.executable, "tools/check_manifest.py"]),
            ("ruff", ["ruff", "check", "."]),
            ("mypy", ["mypy", "tools/check_manifest.py", "tools/check_commit_messages.py", "tools/check_v29_summary.py", "tools/deterministic_smoke.py", "itd_research"]),
            ("tests", [sys.executable, "-m", "pytest", "-q", *sorted(str(p.relative_to(WORK)) for p in (WORK/"tests").glob("test_itd*.py"))]),
        ):
            command(args, log=dest/(label+".log"))
        require(not git("diff", "--name-only"), "tests modified tracked files")
        (dest/"increment.diff").write_text(git("diff", "--cached", parent)+"\n")
        (dest/"cumulative.diff").write_text(git("diff", "--cached", BASE)+"\n")
        manifest = (WORK/MANIFEST).read_bytes()
        (dest/MANIFEST).write_bytes(manifest)
        blob = api("git/blobs", {"content": manifest.decode(), "encoding": "utf-8"})["sha"]
        require(blob == hashlib.sha1(b"blob "+str(len(manifest)).encode()+b"\0"+manifest).hexdigest(), "blob hash differs")
        local = tree(candidate_tree)
        entries = [{"path": p, "mode": mode, "type": "blob", "sha": sha}
                   for p, (mode, sha) in local.items() if old_tree.get(p) != (mode, sha)]
        remote_tree = api("git/trees", {"base_tree": git("rev-parse", head+"^{tree}"), "tree": entries})["sha"]
        require(remote_tree == candidate_tree, "tree hash differs")
        parents = [head, parent]
        commit = api("git/commits", {"tree": remote_tree, "parents": parents,
            "message": f"fix(integration): preserve cumulative manifest stack through PR #{number}",
            "author": {"name": "MEMOPERF", "email": "contact@checkupauto.fr"},
            "committer": {"name": "MEMOPERF", "email": "contact@checkupauto.fr"}})
        require([p["sha"] for p in commit["parents"]] == parents, "commit parent mismatch")
        row = {"pr": number, "old_head": head, "new_head": commit["sha"], "tree": remote_tree,
               "parent_stack": parent, "main": BASE, "conflicts_resolved": conflicts,
               "feature_paths": sorted(delta), "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
               "manifest_entries": len(manifest.splitlines()), "source_union_verified": True,
               "refs_modified": False, "tests_passed": True, **snapshots[number]}
        records.append(row)
        (OUT/"staged.json").write_text(json.dumps(records, indent=2)+"\n")
        print(json.dumps({k: v for k, v in row.items() if k not in ("body", "title")}), flush=True)
        git("merge", "--abort", check=False)
        git("reset", "--hard", head)
        git("fetch", "--no-tags", "origin", commit["sha"])
        parent = commit["sha"]
    # Rehearse real merge commits, not just individually mergeable branch states.
    git("checkout", "--force", "--detach", BASE)
    rehearsals = []
    for row in records:
        command(["git", "merge", "--no-ff", "--no-commit", row["new_head"]], log=OUT/f"sequential-{row['pr']}.log")
        require(not git("diff", "--name-only", "--diff-filter=U"), "sequential merge conflict")
        require(git("write-tree") == row["tree"], "sequential merged tree differs")
        command([sys.executable, "tools/check_manifest.py"], log=OUT/f"sequential-manifest-{row['pr']}.log")
        git("commit", "--no-verify", "-m", f"local-only rehearsal #{row['pr']}")
        rehearsals.append({"pr": row["pr"], "tree": row["tree"], "conflicts": 0, "manifest_valid": True})
    check_live()
    (OUT/"summary.json").write_text(json.dumps({"main": BASE, "staged_count": len(records),
        "sequential_merge_rehearsals": rehearsals, "source_union_verified": True,
        "remote_refs_modified": False, "default_branch_merged": False,
        "protocol": "cumulative existing-PR heads; use normal merge commits to preserve ancestry"}, indent=2)+"\n")


if __name__ == "__main__":
    main()
