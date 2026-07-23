"""Import-boundary tests: no Matplotlib on import, one-way dependency direction."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]

_NUMERICAL_MODULES = (
    "itd_research",
    "itd_research.temporal_scaling",
    "itd_research.analytical_cases",
    "itd_research.established_diagnostics",
    "itd_research.signature",
    "itd_research.benchmark_runner",
    "itd_research.convergence",
    "itd_research.sensitivity",
    "itd_research.reporting",
    "itd_research.plotting",
    "itd_research.diagnostics_3d",
    "itd_research.diagnostics_3d.operators",
    "itd_research.diagnostics_3d.velocity_gradient",
    "itd_research.diagnostics_3d.analytical_fields",
    "itd_research.diagnostics_3d.itd_3d",
    "itd_research.io",
    "itd_research.io.field_data",
    "itd_research.io.metadata",
    "itd_research.io.csv_fields",
    "itd_research.io.npz",
    "itd_research.io.vtk",
    "itd_research.io.openfoam",
    "itd_research.io.piv",
    "itd_research.external_validation",
    "itd_research.external_validation.comparison",
    "itd_research.external_validation.synthetic_flows",
    "itd_research.external_validation.transport",
    "itd_research.external_validation.experiments",
    "itd_research.external_validation.experiments_3d",
    "itd_research.external_validation.hypotheses",
    "itd_research.external_validation.spectral_ns",
    "itd_research.external_validation.piv_agreement",
    "itd_research.spectral3d",
    "itd_research.spectral3d.grids",
    "itd_research.spectral3d.operators",
    "itd_research.spectral3d.initial_conditions",
    "itd_research.spectral3d.forcing",
    "itd_research.spectral3d.invariants",
    "itd_research.spectral3d.simulation",
    "itd_research.spectral3d.vorticity_budget",
    "itd_research.spectral3d.checkpoint",
    "itd_research.validation_lab",
    "itd_research.validation_lab.statistics",
    "itd_research.validation_lab.candidates",
    "itd_research.validation_lab.flows",
    "itd_research.validation_lab.sampling",
    "itd_research.validation_lab.ablation",
    "itd_research.realtime",
    "itd_research.realtime.streaming",
    "itd_research.realtime.benchmarks",
    "itd_research.prediction",
    "itd_research.prediction.events",
    "itd_research.prediction.ensemble",
    "itd_research.prediction.evaluation",
    "itd_research.generalization",
    "itd_research.generalization.baselines",
    "itd_research.generalization.transfer",
    "itd_research.industrial",
    "itd_research.industrial.readiness",
    "itd_research.hard_prediction",
    "itd_research.hard_prediction.protocol",
    "itd_research.hard_prediction.degradation",
    "itd_research.hard_prediction.models",
    "itd_research.hard_prediction.flows",
    "itd_research.hard_prediction.evaluation",
    "itd_research.ood",
    "itd_research.ood.reference",
    "itd_research.ood.abstention",
    "itd_research.product",
    "itd_research.product.result",
    "itd_research.product.pipeline",
    "itd_research.cross_code",
    "itd_research.cross_code.fd_solver",
    "itd_research.cross_code.comparison",
    "itd_research.cross_code.normalization",
    "itd_research.cross_code.transfer",
    "itd_research.ood_near",
    "itd_research.ood_near.campaign",
    "itd_research.ood_shift",
    "itd_research.ood_shift.detector",
    "itd_research.ood_shift.policy",
    "itd_research.ood_shift.campaign",
    "itd_research.full_volume",
    "itd_research.full_volume.benchmark",
    "itd_research.full_volume.optimized",
    "itd_research.profiles",
    "itd_research.profiles.schema",
    "itd_research.profiles.registry",
    "itd_research.profiles.stability",
    "itd_research.external_validation.cylinder_re3900",
    "itd_research.external_validation.cylinder_re3900.metadata",
    "itd_research.external_validation.cylinder_re3900.integration",
)


def _import_and_check_no_matplotlib(module: str) -> subprocess.CompletedProcess[str]:
    code = (
        f"import importlib, sys; importlib.import_module({module!r}); "
        "sys.exit(1 if 'matplotlib' in sys.modules else 0)"
    )
    env = {"PYTHONPATH": str(_ROOT), "PATH": "/usr/bin:/bin"}
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("module", _NUMERICAL_MODULES)
def test_importing_research_modules_does_not_initialise_matplotlib(module: str) -> None:
    result = _import_and_check_no_matplotlib(module)
    assert result.returncode == 0, (
        f"{module} imported matplotlib at import time:\n{result.stderr}"
    )


def _iter_source_files() -> list[Path]:
    files = list((_ROOT / "itd_v29_core").glob("*.py"))
    files.append(_ROOT / "compare_scenarios.py")
    files.append(_ROOT / "itd_v29.py")
    return files


def test_v29_core_does_not_import_itd_research() -> None:
    offenders: list[str] = []
    for path in _iter_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name == "itd_research" or name.startswith("itd_research.") for name in names):
                offenders.append(path.name)
    assert not offenders, f"V29 core/facade imports itd_research: {sorted(set(offenders))}"


def test_research_package_imports_v29_core_only_downstream() -> None:
    # The research package must depend on the core, never the other way around.
    text = (_ROOT / "itd_research" / "signature.py").read_text(encoding="utf-8")
    assert "itd_v29_core" in text
