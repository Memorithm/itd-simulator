from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

import itd_v29

ROOT = Path(__file__).resolve().parents[1]


def test_facade_has_no_function_definitions() -> None:
    tree = ast.parse((ROOT / "itd_v29.py").read_text(encoding="utf-8"))
    definitions = [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    assert definitions == []


def test_facade_reexports_are_direct_object_identities() -> None:
    tree = ast.parse((ROOT / "itd_v29.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module == "__future__":
            continue
        implementation = importlib.import_module(node.module)
        for alias in node.names:
            public_name = alias.asname or alias.name
            assert getattr(itd_v29, public_name) is getattr(implementation, alias.name)


def test_explicit_public_api_categories_are_complete_and_unique() -> None:
    combined = (
        *itd_v29.STABLE_PUBLIC_API,
        *itd_v29.ADVANCED_PUBLIC_API,
        *itd_v29.LEGACY_COMPATIBILITY_API,
    )
    assert itd_v29.__all__ == combined
    assert len(combined) == len(set(combined))
    assert all(hasattr(itd_v29, name) for name in combined)


def test_no_core_module_imports_facade() -> None:
    for path in sorted((ROOT / "itd_v29_core").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != "itd_v29" for alias in node.names), path
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "itd_v29", path


def test_importing_numerical_facade_does_not_initialize_matplotlib() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import itd_v29; print('matplotlib' in sys.modules)",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "False"
