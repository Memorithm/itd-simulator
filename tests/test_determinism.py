from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETERMINISTIC_ENVIRONMENT = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def run_smoke() -> bytes:
    environment = os.environ.copy()
    environment.update(DETERMINISTIC_ENVIRONMENT)
    return subprocess.run(
        [sys.executable, "tools/deterministic_smoke.py"],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
    ).stdout


def test_reduced_scenario_is_bitwise_deterministic_between_processes() -> None:
    first = run_smoke()
    second = run_smoke()
    assert first == second
