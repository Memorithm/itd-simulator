#!/usr/bin/env python3
"""Qualify the process bridge; no connectome, learning, or financial execution."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import platform
import subprocess
import tempfile
import time
import unittest
from collections import Counter, defaultdict
from pathlib import Path

import qualify as env_oracle

HERE = Path(__file__).resolve().parent
BINARY: Path
PROTOCOL = json.loads((HERE / "protocol_io.json").read_text())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic(row):
    return {k: v for k, v in row.items() if k not in ("child_pid", "elapsed_us")}


def record(c, a, b, r, noise, mode="eval"):
    return f"{c} {a} {b} {r} {noise or '-'} {mode}"


def invoke(records, kind="exact", deadline=1000, external=None):
    with tempfile.TemporaryDirectory(prefix="itd-empty-worker-") as cwd:
        command = [str(BINARY), "--external" if external else "--batch",
                   str(external) if external else kind, str(deadline), cwd]
        env = dict(os.environ, ITD_HIDDEN_CANARY="administrative-value-must-not-cross")
        proc = subprocess.run(command, input="\n".join(records) + "\n", text=True,
                              capture_output=True, timeout=120, check=True, env=env)
    rows = [json.loads(line) for line in proc.stdout.splitlines()]
    assert len(rows) == len(records), "worker failure dropped an episode"
    for row in rows:
        assert row["child_reaped"] and row["io_thread_joined"], "unreported lifecycle failure"
        if row.get("spawned") and platform.system() == "Linux":
            assert not Path(f'/proc/{row["child_pid"]}').exists(), "direct child still exists"
    return rows


def expected_requests(spec):
    c, a, b, r, noise = spec
    out = ["RESET 0 v1"]
    for seq, obs in enumerate(env_oracle.observations(*spec), 1):
        values = ["-" if obs[k] is None else str(obs[k]) for k in ("a", "b", "rule", "distractor")]
        out.append(f'OBS {seq} {c} {obs["phase"]} ' + " ".join(values))
    return out


def check(row, spec, kind):
    expected = expected_requests(spec)
    assert row["requests"] == expected, "candidate received unexpected observation information"
    answer = env_oracle.target(*spec[:4])
    chosen = answer if kind == "exact" or spec[0] == "logic" else 0
    expected_actions = ["wait"] * (len(expected) - 2) + [str(chosen)]
    assert row["actions"] == expected_actions
    assert row["success"] == (chosen == answer)
    assert row["reason"] == ("correct" if chosen == answer else "wrong")
    assert row["fault"] is None and row["feedback_fault"] is None
    assert row["feedback_delivered"] is False
    assert row["requests_enqueued"] == len(expected)
    assert row["request_bytes_enqueued"] == sum(len(s.encode()) + 1 for s in expected)
    assert row["response_bytes_received"] == sum(len(s.encode()) + 1 for s in row["responses"])
    assert row["responses"] == ["ACK 0 v1"] + [f"ACT {i} {a}" for i, a in enumerate(expected_actions, 1)]
    assert row["learning_performed"] is False


class ProcessTests(unittest.TestCase):
    def test_complete_bits_and_conditions(self):
        specs = [(c, *bits, "010") for c in PROTOCOL["conditions"]
                 for bits in itertools.product((0, 1), repeat=3)]
        for kind in ("exact", "current"):
            for row, spec in zip(invoke([record(*s) for s in specs], kind), specs, strict=True):
                check(row, spec, kind)

    def test_real_deadline_not_a_synthetic_timeout_action(self):
        start = time.monotonic()
        row = invoke([record("combined", 1, 0, 0, "01")], "hang", 80)[0]
        elapsed = time.monotonic() - start
        self.assertEqual((row["fault"], row["reason"], row["success"]), ("timeout", "timeout", False))
        self.assertGreaterEqual(row["elapsed_us"], 70_000)
        self.assertLess(elapsed, 5, "hung candidate did not stop under external watchdog")

    def test_reset_deadline_and_reaping(self):
        row = invoke([record("memory", 1, 0, 0, "")], "hang_reset", 80)[0]
        self.assertEqual(row["fault"], "timeout")
        self.assertEqual(row["requests"], ["RESET 0 v1"])
        self.assertFalse(row["success"])

    def test_malformed_and_aborted_workers_keep_failure_denominator(self):
        for kind, fault in (("exit", "eof"), ("truncated", "truncated"),
                            ("oversize", "oversize"), ("stale", "protocol"), ("invalid", "protocol")):
            with self.subTest(kind=kind):
                rows = invoke([record("memory", a, 0, 0, "01") for a in (0, 1)], kind)
                self.assertEqual(len(rows), 2)
                self.assertTrue(all(r["fault"] == fault and not r["success"] for r in rows))

    def test_early_action_has_no_second_chance(self):
        row = invoke([record("memory", 0, 0, 0, "0" * 64)], "early")[0]
        self.assertEqual(row["reason"], "early_action")
        self.assertEqual(len(row["requests"]), 2)
        self.assertEqual(row["actions"], ["0"])

    def test_feedback_only_after_action_and_never_during_evaluation(self):
        for kind in ("exact", "current"):
            rows = invoke([record("combined", 1, 0, 0, "01", mode) for mode in ("train", "eval")], kind)
            train, evaluation = rows
            self.assertTrue(train["feedback_delivered"])
            self.assertEqual(train["requests"][:-1], evaluation["requests"])
            self.assertTrue(train["requests"][-1].startswith("FEEDBACK "))
            self.assertEqual(train["requests"][-1].split()[-1], str(int(train["success"])))
            self.assertFalse(evaluation["feedback_delivered"])
            self.assertFalse(any(s.startswith("FEEDBACK") for s in evaluation["requests"]))

    def test_future_hidden_operands_do_not_change_wire_prefix(self):
        rows = invoke([record("combined", 1, b, r, "010") for b, r in itertools.product((0, 1), repeat=2)])
        prefixes = [row["requests"][:5] for row in rows]
        self.assertTrue(all(p == prefixes[0] for p in prefixes))
        self.assertTrue(all(row["requests"][-1].split()[4:6] == ["-", "-"] for row in rows))

    def test_fresh_process_and_semantic_replay(self):
        fixtures = [record("memory", a, 0, 0, "101") for a in (1, 0, 0, 1)]
        a, b = invoke(fixtures), invoke(fixtures)
        self.assertEqual([semantic(r) for r in a], [semantic(r) for r in b])
        self.assertEqual(len({r["child_pid"] for r in a}), len(a))
        self.assertEqual([semantic(r) for r in a], [semantic(invoke([f])[0]) for f in fixtures])

    def test_ambient_environment_is_not_inherited(self):
        row = invoke([record("combined", 1, 1, 0, "01")], "env_probe")[0]
        self.assertTrue(row["success"])
        self.assertIsNone(row["fault"])

    def test_spawn_failure_is_explicit(self):
        row = invoke([record("memory", 1, 0, 0, "")], external="/nonexistent/itd-worker")[0]
        self.assertFalse(row["success"])
        self.assertEqual(row["fault"], "spawn")
        self.assertFalse(row["spawned"])

    def test_maximum_delay_and_invalid_admin_are_bounded(self):
        spec = ("combined", 1, 0, 1, "1" * 64)
        check(invoke([record(*spec)])[0], spec, "exact")
        with tempfile.TemporaryDirectory() as cwd:
            for fixture in ("x" * 10000, record("memory", 2, 0, 0, ""),
                            record("memory", 1, 0, 0, "0" * 65)):
                proc = subprocess.run([str(BINARY), "--batch", "exact", "1000", cwd],
                                      input=fixture + "\n", text=True, capture_output=True, timeout=5)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")


def pilot(output):
    specs = [(c, *bits, noise) for c in PROTOCOL["conditions"]
             for delay in PROTOCOL["delay_grid"]
             for noise in ([""] if delay == 0 else ["0" * delay, "".join(str(i % 2) for i in range(delay))])
             for bits in itertools.product((0, 1), repeat=3)]
    records = [record(*s) for s in specs]
    scores = defaultdict(Counter)
    traces, request_hashes = [], {}
    start = time.monotonic()
    for kind in ("exact", "current"):
        rows, replay = invoke(records, kind), invoke(records, kind)
        if [semantic(r) for r in rows] != [semantic(r) for r in replay]:
            raise AssertionError("semantic replay mismatch (PID and timings explicitly excluded)")
        for row, spec in zip(rows, specs, strict=True):
            check(row, spec, kind)
            counter = scores[spec[0] + "/" + kind]
            counter["episodes"] += 1
            counter["successes"] += row["success"]
            counter["failures"] += not row["success"]
            traces.append({"condition": spec[0], "control": kind, "trace": row})
        request_hashes[kind] = hashlib.sha256(canonical([r["requests"] for r in rows]).encode()).hexdigest()
    assert request_hashes["exact"] == request_hashes["current"]
    for c in PROTOCOL["conditions"]:
        assert scores[c + "/exact"]["successes"] == scores[c + "/exact"]["episodes"]
        assert scores[c + "/current"]["successes"] * (1 if c == "logic" else 2) == scores[c + "/current"]["episodes"]
    raw = "".join(canonical(r) + "\n" for r in traces)
    (output / "traces_io.jsonl").write_text(raw)
    report = {
        "scope": "GAME-IO1 protocol/lifecycle correctness; no V888 model or learning",
        "host": platform.node(), "architecture": platform.machine(),
        "itd_source": os.environ.get("ITD_SOURCE_SHA"), "workflow_source": os.environ.get("GITHUB_SHA"),
        "binary_sha256": digest(BINARY), "protocol_sha256": hashlib.sha256(canonical(PROTOCOL).encode()).hexdigest(),
        "source_sha256": {name: digest(HERE / name) for name in PROTOCOL["source_files"]},
        "fixtures": len(specs), "episodes": len(traces), "replay_episodes": len(traces),
        "scores": {k: dict(v) for k, v in sorted(scores.items())},
        "candidate_request_hashes": request_hashes,
        "semantic_replay_identical": True, "oracle_mismatches": 0,
        "all_direct_children_reaped": True, "all_io_threads_joined": True,
        "trace_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "elapsed_seconds": time.monotonic() - start,
        "neural_dynamics_executed": False, "learning_performed": False,
        "hostile_process_sandbox": False,
        "limitations": ["trusted workers only; filesystem/network/descendant isolation not provided",
                        "response deadline excludes OS process spawn and termination overhead",
                        "fresh process per episode; persistent learned checkpoint transfer is not implemented",
                        "stdout payload bounded; not an OS CPU/RAM sandbox",
                        "task and topology gates unchanged; no BANC files accessed"],
    }
    (output / "qualification_io.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (output / "protocol_io.json").write_text(json.dumps(PROTOCOL, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)


def main():
    global BINARY
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    BINARY = args.binary.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProcessTests))
    if not result.wasSuccessful():
        raise SystemExit(1)
    pilot(args.output)


if __name__ == "__main__":
    main()
