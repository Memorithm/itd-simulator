"""Stage reviewed merge resolutions; never move a remote ref or create a PR merge."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = "Memorithm/itd-simulator"
BASE = "21e03405aa19fbeae6d0c083635b7e6fdb306c24"
HEADS = {
    42: "25656914e2f5305d5bbfd6fc4302ada0e3d994ff",
    44: "08d5650e61defc4016d6df5f2249908eaf31af0e",
    45: "0db034dff37b7ecade82fe849e8568d7f7975a6d",
    46: "aaefd8d213b38dedbe18c27c3bd17f2122dc2be4",
    47: "353a58cb80ffc4622a1d91d70b55225945d94858",
    48: "55494836cf2c2b2405920994693a4bbfec80e56c",
    49: "b9916fe61a01cd0a722d2b2e2c9ed0ed2dc5822b",
    50: "6877c414ec926dbdbdc12a823dd6747bbbb3de1f",
    52: "c2ffd080d80aa81025641c649335bcfe49bc58c5",
    53: "c17bcbcb62fe9d9095c46f6cf68d2a01d64d4d6b",
    55: "7ea3ab8cc230f4bf4843855de3ca5db863169c78",
    56: "364c6f4e9889d79c940402ccb90c24b21640ad64",
}
REVIEWED = {
    44: "itd_research/representation_strata.py",
    47: "itd_research/uq.py",
    49: "itd_research/adaptive_shadow.py",
}
ROOT = Path(os.environ["REPAIR_ROOT"])
WORK = ROOT / "work"
OUT = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
ENV = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
ENV.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")


def api(suffix: str, data: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{suffix}",
        data=None if data is None else json.dumps(data).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def command(args: list[str], *, check: bool = True, log: Path | None = None) -> subprocess.CompletedProcess:
    p = subprocess.run(args, cwd=WORK, env=ENV, capture_output=True, text=True, timeout=600)
    if log is not None:
        log.write_text(p.stdout + p.stderr)
    if check and p.returncode:
        raise RuntimeError(f"{args!r}: exit {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def git(*args: str, check: bool = True) -> str:
    return command(["git", *args], check=check).stdout.strip()


def contents(rev: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=WORK, env=ENV)


def main() -> None:
    if os.environ["GITHUB_REPOSITORY"] != REPO:
        raise RuntimeError("wrong repository")
    if os.environ["GITHUB_REF"] != "refs/heads/repair/itd-pr-conflicts-20260922":
        raise RuntimeError("wrong staging branch")
    if api("branches/main")["commit"]["sha"] != BASE:
        raise RuntimeError("main moved; review a fresh base before staging")
    subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", f"https://github.com/{REPO}.git", str(WORK)], check=True, env=ENV, timeout=300)
    git("config", "user.name", "MEMOPERF")
    git("config", "user.email", "contact@checkupauto.fr")
    results = []
    for number, head in HEADS.items():
        dest = OUT / str(number)
        dest.mkdir()
        record = {"pr": number, "old_head": head, "main": BASE, "refs_modified": False, "ready": False}
        results.append(record)
        try:
            pr = api(f"pulls/{number}")
            assert pr["state"] == "open" and not pr["merged"]
            assert pr["head"]["sha"] == head and pr["head"]["repo"]["full_name"] == REPO
            assert pr["base"]["ref"] == "research/itd-3x-bootstrap"
            record.update(branch=pr["head"]["ref"], previous_base=pr["base"]["ref"])
            git("fetch", "--no-tags", "origin", head, BASE)
            git("checkout", "--force", "--detach", head)
            merge = command(["git", "merge", "--no-commit", "--no-ff", BASE], check=False, log=dest/"merge.log")
            conflicts = git("diff", "--name-only", "--diff-filter=U").splitlines()
            expected = ["MANIFEST.sha256"] + ([REVIEWED[number]] if number in REVIEWED else [])
            assert merge.returncode == 1 and sorted(conflicts) == sorted(expected), conflicts
            record["resolved_conflicts"] = conflicts
            if number in REVIEWED:
                path = REVIEWED[number]
                main_content = contents(BASE, path)
                head_content = contents(head, path)
                assert head_content.startswith(main_content), "resolution is no longer an append-only extension"
                (WORK/path).write_bytes(head_content)
                git("add", "--", path)
            git("checkout", "--ours", "--", "MANIFEST.sha256")
            git("add", "--", "MANIFEST.sha256")
            command([sys.executable, "tools/check_manifest.py", "--update"], log=dest/"manifest-update.log")
            git("add", "--", "MANIFEST.sha256")
            assert not git("diff", "--name-only", "--diff-filter=U")
            assert not git("diff", "--cached", "--name-only", "--diff-filter=D", BASE)
            paths = git("diff", "--cached", "--name-only", BASE).splitlines()
            for path in paths:
                if path == "MANIFEST.sha256":
                    continue
                assert (WORK/path).read_bytes() == contents(head, path), f"lost or mixed PR code: {path}"
                assert path.startswith(("itd_research/", "tests/test_itd", "docs/itd3x/")), path
            git("diff", "--cached", "--check")
            for name, args in [
                ("manifest", [sys.executable, "tools/check_manifest.py"]),
                ("ruff", ["ruff", "check", "."]),
                ("mypy", ["mypy", "tools/check_manifest.py", "tools/check_commit_messages.py", "tools/check_v29_summary.py", "tools/deterministic_smoke.py", "itd_research"]),
                ("tests", [sys.executable, "-m", "pytest", "-q", *sorted(str(p.relative_to(WORK)) for p in (WORK/"tests").glob("test_itd*.py"))]),
            ]:
                command(args, log=dest/(name+".log"))
            assert not git("diff", "--name-only"), "tests changed tracked contents"
            local_tree = git("write-tree")
            (dest/"candidate.diff").write_text(git("diff", "--cached", BASE)+"\n")
            manifest = (WORK/"MANIFEST.sha256").read_bytes()
            blob = api("git/blobs", {"content": manifest.decode(), "encoding": "utf-8"})["sha"]
            assert blob == hashlib.sha1(b"blob "+str(len(manifest)).encode()+b"\0"+manifest).hexdigest()
            entries = []
            for path in git("diff", "--cached", "--name-only", head).splitlines():
                stage = git("ls-files", "--stage", "--", path).split(maxsplit=3)
                mode, sha, level = stage[:3]
                assert level == "0"
                if path != "MANIFEST.sha256":
                    candidates = []
                    for rev in (head, BASE):
                        candidates.append(git("rev-parse", f"{rev}:{path}", check=False))
                    assert sha in candidates, f"unreviewed merge blob: {path}"
                entries.append({"path": path, "mode": mode, "type": "blob", "sha": sha})
            tree = api("git/trees", {"base_tree":git("rev-parse", head+"^{tree}"), "tree":entries})["sha"]
            assert tree == local_tree
            record.update(ready=True, tree=tree, paths_vs_main=paths, tests="manifest, Ruff, mypy and test_itd*.py passed", source_changes="only reviewed append-only extensions; main files and original PR additions preserved")
        except Exception as exc:
            record["error"] = str(exc)
        finally:
            git("merge", "--abort", check=False)
            git("reset", "--hard", head, check=False)
            (OUT/"staged.json").write_text(json.dumps(results,indent=2)+"\n")
            print(json.dumps(record),flush=True)
    if not all(r["ready"] for r in results):
        raise SystemExit("some candidates need manual correction; no remote refs changed")


if __name__ == "__main__":
    main()
