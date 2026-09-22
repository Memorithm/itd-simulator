#!/usr/bin/env python3
"""Independent environment qualification. No connectome or learner is used.

The Rust policy receives only public observations. This Python process is an
administrator/oracle and intentionally has access to the private fixture bits.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import platform
import random
import subprocess
import sys
import time
import unittest
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BINARY: Path
PROTOCOL = json.loads((HERE / "protocol.json").read_text())


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def record(condition, a, b, r, noise, policy="exact", mode="eval"):
    return f"{condition} {a} {b} {r} {noise or '-'} {policy} {mode}"


def invoke(records):
    text = "\n".join(records) + "\n"
    result = subprocess.run([str(BINARY), "--batch"], input=text, text=True,
                            capture_output=True, timeout=180, check=True)
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    if len(rows) != len(records):
        raise AssertionError("missing results: failed trials must remain in denominator")
    return rows, result.stdout


def target(condition, a, b, r):
    if condition == "memory":
        return a
    # Independent lookup instead of the Rust environment's conditional definition.
    return (0, 1, 1, 0, 1, 0, 0, 1)[4 * a + 2 * b + r]


def observations(condition, a, b, r, noise):
    def obs(phase, **fields):
        return dict(condition=condition, phase=phase, a=None, b=None,
                    rule=None, distractor=None) | fields
    first = obs("cue_a", a=a if condition != "logic" else None)
    middle = [obs("distractor", distractor=int(x)) for x in noise]
    second = obs("cue_b", b=b if condition == "combined" else None)
    if condition == "logic":
        choice = obs("choice", a=a, b=b, rule=r)
    elif condition == "combined":
        choice = obs("choice", rule=r)
    else:
        choice = obs("choice")
    return [first, *middle, second, choice]


def check_trace(row, condition, a, b, r, noise, policy, mode="eval"):
    expected_obs = observations(condition, a, b, r, noise)
    if policy == "early":
        expected_obs = expected_obs[:1]
    actual_obs = [step["observation"] for step in row["steps"]]
    assert actual_obs == expected_obs, "observation timeline differs from independent oracle"
    assert all(set(o) == set(PROTOCOL["observation_fields"]) for o in actual_obs)
    expected_actions = ["wait"] * (len(expected_obs) - 1)
    fault = {"early": "early_action", "missing": "missing_action", "invalid": "invalid_action", "timeout": "timeout"}
    answer = target(condition, a, b, r)
    if policy in fault:
        final = "door_0" if policy == "early" else policy
        success, reason = False, fault[policy]
    else:
        chosen = answer if policy == "exact" else (answer if condition == "logic" else 0)
        if policy == "left":
            chosen = 0
        if policy == "right":
            chosen = 1
        final = f"door_{chosen}"
        success = chosen == answer
        reason = "correct" if success else "wrong"
    assert [step["action"] for step in row["steps"]] == [*expected_actions, final]
    assert row["success"] is success and row["reason"] == reason
    assert row["training_feedback"] == (int(success) if mode == "train" else None)
    assert row["observation_count"] == len(expected_obs)
    assert row["choice_attempts"] == (0 if policy == "early" else 1)
    assert row["learning_performed"] is False
    assert row["schema"] == "itd-two-doors-trace-v1"


class EnvironmentTests(unittest.TestCase):
    def test_all_bits_and_diagnostic_conditions(self):
        specs = [(c, *bits, "101", p) for c in PROTOCOL["conditions"]
                 for bits in itertools.product((0, 1), repeat=3)
                 for p in ("exact", "current")]
        rows, _ = invoke([record(*s) for s in specs])
        for row, spec in zip(rows, specs, strict=True):
            check_trace(row, *spec)

    def test_no_current_observation_label_shortcut(self):
        specs = [(c, *bits, "1010", "exact") for c in ("memory", "combined")
                 for bits in itertools.product((0, 1), repeat=3)]
        rows, _ = invoke([record(*s) for s in specs])
        labels = defaultdict(Counter)
        for row, spec in zip(rows, specs, strict=True):
            labels[canonical(row["steps"][-1]["observation"])][target(*spec[:4])] += 1
        self.assertTrue(labels)
        self.assertTrue(all(v[0] == v[1] for v in labels.values()))

    def test_future_input_cannot_change_past_observations(self):
        rows, _ = invoke([record("combined", 1, b, r, "010", "exact")
                          for b, r in itertools.product((0, 1), repeat=2)])
        prefixes = [[s["observation"] for s in row["steps"][:4]] for row in rows]
        self.assertTrue(all(p == prefixes[0] for p in prefixes))

    def test_hidden_false_is_not_visible_zero(self):
        rows, _ = invoke([record("combined", 0, 0, 0, "", "exact")])
        obs = [s["observation"] for s in rows[0]["steps"]]
        self.assertEqual(obs[0]["a"], 0)
        self.assertIsNone(obs[-1]["a"])
        self.assertIsNone(obs[-1]["b"])

    def test_training_and_evaluation_feedback(self):
        specs = [("combined", 1, 0, 0, "0", p, m)
                 for p in ("exact", "left", "missing") for m in ("train", "eval")]
        rows, _ = invoke([record(*s) for s in specs])
        for row, spec in zip(rows, specs, strict=True):
            check_trace(row, *spec)
            self.assertTrue(all(set(s) == {"observation", "action"} for s in row["steps"]))

    def test_faults_and_wrong_answers_are_retained(self):
        specs = [("memory", 1, 0, 0, "00", p)
                 for p in ("early", "invalid", "timeout", "missing", "left")]
        rows, _ = invoke([record(*s) for s in specs])
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(not r["success"] for r in rows))
        for row, spec in zip(rows, specs, strict=True):
            check_trace(row, *spec)

    def test_independent_episodes_and_byte_replay(self):
        examples = [record("memory", a, 0, 0, "101", "exact") for a in (1, 0, 0, 1)]
        together, first = invoke(examples)
        _, second = invoke(examples)
        self.assertEqual(first, second)
        self.assertEqual(together, [invoke([r])[0][0] for r in examples])

    def test_maximum_delay_and_strict_rejection(self):
        row, _ = invoke([record("combined", 1, 1, 1, "0" * 64)])
        self.assertEqual(row[0]["observation_count"], 67)
        bad = [record("memory", 0, 0, 0, "0" * 65),
               record("memory", 2, 0, 0, ""),
               record("memory", 0, 0, 0, "x"),
               record("memory", 0, 0, 0, "", mode="final"),
               "memory 0 0 0 - exact eval extra", "x" * 300]
        for value in bad:
            with self.subTest(value=value[:80]):
                proc = subprocess.run([str(BINARY), "--batch"], input=value + "\n",
                                      text=True, capture_output=True, timeout=5)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")
                self.assertIn("protocol_error", proc.stderr)

    def test_first_early_failure_not_silently_retried(self):
        rows, _ = invoke([record("combined", 0, 0, 0, "0" * 32, "early")])
        self.assertEqual(len(rows[0]["steps"]), 1)
        self.assertEqual(rows[0]["reason"], "early_action")


def noise_panel(delay):
    if delay <= PROTOCOL["exhaustive_noise_through_delay"]:
        return ["".join(bits) for bits in itertools.product("01", repeat=delay)]
    result = ["0" * delay, "1" * delay, "".join(str(i % 2) for i in range(delay))]
    for seed in (17, 29, 43):
        rng = random.Random(seed + 1009 * delay)
        result.append("".join(str(rng.getrandbits(1)) for _ in range(delay)))
    return result


def pilot(output):
    output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    specs = [(c, *bits, noise, policy) for c in PROTOCOL["conditions"]
             for delay in PROTOCOL["delay_grid"] for noise in noise_panel(delay)
             for bits in itertools.product((0, 1), repeat=3)
             for policy in PROTOCOL["policies"]]
    rows, wire = invoke([record(*s) for s in specs])
    _, replay = invoke([record(*s) for s in specs])
    if wire != replay:
        raise AssertionError("full batch replay not byte-identical")
    counters = defaultdict(Counter)
    choice_labels = defaultdict(Counter)
    samples = []
    for row, spec in zip(rows, specs, strict=True):
        c, a, b, r, noise, policy = spec
        check_trace(row, *spec)
        counts = counters[c + "/" + policy]
        counts["episodes"] += 1
        counts["successes"] += row["success"]
        counts["observations"] += row["observation_count"]
        counts[row["reason"]] += 1
        if policy == "exact" and c != "logic":
            key = canonical([c, len(noise), noise, row["steps"][-1]["observation"]])
            choice_labels[key][target(c, a, b, r)] += 1
        if noise == "0101" and (a, b, r) == (1, 0, 0) and policy in ("exact", "current"):
            samples.append({"condition": c, "control": policy, "trace": row})
    if not choice_labels or any(v[0] != v[1] for v in choice_labels.values()):
        raise AssertionError("current choice observations not counterbalanced")
    scores = dict(sorted((k, dict(v)) for k, v in counters.items()))
    for c in PROTOCOL["conditions"]:
        assert scores[c + "/exact"]["successes"] == scores[c + "/exact"]["episodes"]
        cur = scores[c + "/current"]
        assert cur["successes"] * (1 if c == "logic" else 2) == cur["episodes"]
        for p in ("missing", "invalid", "timeout", "early"):
            assert scores[c + "/" + p].get("successes", 0) == 0
    raw = wire.encode()
    (output / "traces.jsonl").write_bytes(raw)
    dump(output / "replay_samples.json", samples)
    dump(output / "protocol.json", PROTOCOL)
    report = {
        "scope": PROTOCOL["scope"], "host": platform.node(), "architecture": platform.machine(),
        "python": sys.version, "source_commit": os.environ.get("ITD_SOURCE_SHA"),
        "rust_binary_sha256": sha_file(BINARY),
        "source_sha256": {p.name: sha_file(p) for p in [HERE / "game.rs", HERE / "protocol.json", Path(__file__)]},
        "protocol_canonical_sha256": hashlib.sha256(canonical(PROTOCOL).encode()).hexdigest(),
        "trace_sha256": hashlib.sha256(raw).hexdigest(), "trace_bytes": len(raw),
        "policy_episodes": len(specs), "distinct_admin_fixtures_before_policies": len(specs) // len(PROTOCOL["policies"]),
        "full_replay_identical": True, "counterbalanced_decision_groups": len(choice_labels),
        "independent_oracle_mismatches": 0, "scores": scores,
        "policy_state_bytes_observed": {p: sorted({row["policy_state_bytes"] for row, spec in zip(rows, specs, strict=True) if spec[-1] == p}) for p in PROTOCOL["policies"]},
        "elapsed_seconds_including_two_runs_and_oracles": time.monotonic() - start,
        "V888_graph_used": False, "learning_performed": False,
        "limitations": PROTOCOL["limitations"],
    }
    dump(output / "qualification.json", report)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)


def main():
    global BINARY
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    BINARY = args.binary.resolve(strict=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EnvironmentTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.output:
        pilot(args.output)


if __name__ == "__main__":
    main()
