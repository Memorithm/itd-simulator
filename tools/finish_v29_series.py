#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import builtins
import dataclasses
import datetime as dt
import hashlib
import os
import shutil
import stat
import subprocess
import symtable
import sys
import textwrap
from pathlib import Path
from typing import Sequence


@dataclasses.dataclass(frozen=True)
class Plan:
    version: str
    slug: str
    module: str
    functions: tuple[str, ...]
    description: str

    @property
    def archive_name(self) -> str:
        return f"v{self.version.replace('.', '_')}_{self.slug}_modularized"

    @property
    def report_name(self) -> str:
        return f"v{self.version.replace('.', '_')}_{self.slug}_certification.md"


PLANS = (
    Plan(
        "29.14",
        "material_interval",
        "itd_v29_core/material_interval.py",
        (
            "validate_positive_time_interval",
            "validate_material_interval_fields",
            "normalized_field_rate",
            "material_vorticity_interval",
        ),
        "Extraction des diagnostics d'intervalle matériel.",
    ),
    Plan(
        "29.15",
        "structural_metrics",
        "itd_v29_core/structural_metrics.py",
        (
            "normalize_structural_weights",
            "structural_metrics",
        ),
        "Extraction de la signature structurelle et de ses poids.",
    ),
    Plan(
        "29.16",
        "simulation_engine",
        "itd_v29_core/simulation_engine.py",
        (
            "validate_temporal_deformation_mode",
            "simulate",
            "simulate_multiscale",
        ),
        "Extraction du moteur principal de simulation.",
    ),
    Plan(
        "29.17",
        "material_deformation",
        "itd_v29_core/material_deformation.py",
        (
            "interpolate_interval_series_to_nodes",
            "simulate_material_deformation",
        ),
        "Extraction de l'orchestration de déformation matérielle.",
    ),
    Plan(
        "29.18",
        "entrypoint",
        "itd_v29_core/entrypoint.py",
        ("main",),
        "Extraction du point d'entrée final.",
    ),
)

EXCLUDED_VALIDATORS = {
    "validate_bounded_cubic_v27.py":
        "validateur historique du mode cubic_bounded_periodic",
}


class PipelineError(RuntimeError):
    pass


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(
    args: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    capture: bool = False,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)

    result = subprocess.run(
        list(args),
        cwd=cwd,
        env=merged,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        timeout=timeout,
        check=False,
    )

    if check and result.returncode != 0:
        raise PipelineError(
            f"Commande échouée ({result.returncode}) : {' '.join(args)}\n"
            f"{result.stdout or ''}"
        )

    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def previous_version(version: str) -> str:
    major, minor = version.split(".")
    return f"{major}.{int(minor) - 1}"


def find_reference_archive(project: Path, version: str) -> Path:
    prefix = f"v{version.replace('.', '_')}_"

    matches = sorted(
        path
        for path in (project / "archives").iterdir()
        if path.is_dir() and path.name.startswith(prefix)
    )

    if len(matches) != 1:
        raise PipelineError(
            f"Archive de référence V{version} absente ou ambiguë : {matches}"
        )

    return matches[0]


def compile_file(path: Path) -> None:
    compile(
        path.read_text(encoding="utf-8"),
        str(path),
        "exec",
    )


@dataclasses.dataclass(frozen=True)
class ImportSpec:
    kind: str
    module: str
    name: str = ""
    alias: str = ""


def import_map(tree: ast.Module) -> dict[str, ImportSpec]:
    result: dict[str, ImportSpec] = {}

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                visible = alias.asname or alias.name.split(".", 1)[0]

                result[visible] = ImportSpec(
                    kind="import",
                    module=alias.name,
                    alias=alias.asname or "",
                )

        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                visible = alias.asname or alias.name

                result[visible] = ImportSpec(
                    kind="from",
                    module=node.module,
                    name=alias.name,
                    alias=alias.asname or "",
                )

    return result


FunctionLike = (ast.FunctionDef, ast.AsyncFunctionDef)


def _collect_global_symbol_names(
    table: symtable.SymbolTable,
    into: set[str],
) -> None:
    """
    Parcourt récursivement une table de symboles et toutes ses
    tables filles (fonctions, classes, lambdas, comprehensions,
    générateurs, à toute profondeur) et collecte les noms qui,
    à ce niveau précis, se résolvent vers la portée globale du
    module.

    C'est exactement la distinction que fait le compilateur CPython
    lui-même entre :

    - une variable liée localement à une portée (paramètre,
      cible d'affectation, cible de destructuration, cible de
      compréhension, cible ``for``/``with``/``except``, nom de
      fonction ou de classe imbriquée, import local) ;
    - une variable libre capturée par fermeture depuis une portée
      de fonction englobante (``is_free``), qui ne doit jamais
      être promue en dépendance de module puisqu'elle est déjà
      fournie par la portée englobante extraite avec elle ;
    - une variable qui ne se résout dans aucune portée de fonction
      englobante et qui référence donc réellement la portée
      globale du module (``is_global``), qu'elle soit lue,
      assignée, ou déclarée ``global`` explicitement.

    Utiliser ``symtable`` évite de ré-implémenter cette analyse
    lexicale à la main : la portée de chaque nom (y compris à
    travers une imbrication arbitraire de fonctions, classes,
    lambdas et compréhensions) est déterminée par le compilateur
    CPython lui-même, pas par une heuristique locale.
    """
    for symbol in table.get_symbols():
        if symbol.is_global():
            into.add(symbol.get_name())

    for child in table.get_children():
        _collect_global_symbol_names(child, into)


def _free_names_in_fragment_source(source: str) -> set[str]:
    """
    Analyse un fragment de code source autonome (une expression
    isolée, réinjectée dans une affectation synthétique) et
    retourne les noms qui s'y résolvent vers la portée globale.

    Ceci est utilisé pour les éléments de signature (décorateurs,
    annotations, valeurs par défaut, annotation de retour), qui
    sont évalués dans la portée englobante au moment de l'exécution
    de l'instruction ``def``, et non dans la portée propre de la
    fonction. Réinjecter le fragment dans un mini-module synthétique
    permet de réutiliser exactement la même analyse récursive,
    y compris lorsque le fragment contient lui-même un ``lambda``
    ou une compréhension imbriquée.
    """
    table = symtable.symtable(
        source,
        "<signature-fragment>",
        "exec",
    )

    names: set[str] = set()
    _collect_global_symbol_names(table, names)

    names.discard("__signature_fragment__")

    return names


def _signature_fragments(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.expr]:
    fragments: list[ast.expr] = list(node.decorator_list)

    arguments = node.args

    all_arguments = (
        list(arguments.posonlyargs)
        + list(arguments.args)
        + list(arguments.kwonlyargs)
    )

    if arguments.vararg is not None:
        all_arguments.append(arguments.vararg)

    if arguments.kwarg is not None:
        all_arguments.append(arguments.kwarg)

    for argument in all_arguments:
        if argument.annotation is not None:
            fragments.append(argument.annotation)

    fragments.extend(arguments.defaults)

    fragments.extend(
        default
        for default in arguments.kw_defaults
        if default is not None
    )

    if node.returns is not None:
        fragments.append(node.returns)

    return fragments


def _find_function_symbol_table(
    module_table: symtable.SymbolTable,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> symtable.SymbolTable:
    for child in module_table.get_children():
        if (
            child.get_type() == "function"
            and child.get_name() == node.name
            and child.get_lineno() == node.lineno
        ):
            return child

    raise PipelineError(
        "Table des symboles introuvable pour la fonction "
        f"de premier niveau : {node.name}"
    )


def unresolved_names(
    module_table: symtable.SymbolTable,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    target_names: set[str],
) -> set[str]:
    """
    Calcule l'ensemble des noms dont dépend réellement une
    fonction de premier niveau, en distinguant correctement :

    1. les noms liés localement à une portée (y compris dans
       les portées imbriquées) ;
    2. les noms référencés par une portée ;
    3. les variables libres capturées par fermeture depuis une
       portée englobante (jamais promues en dépendance) ;
    4. les dépendances réelles de module (``is_global`` à
       n'importe quelle profondeur d'imbrication) ;
    5. les fonctions natives (retirées via ``builtins``) ;
    6. les fonctions extraites dans le même module généré
       (retirées via ``target_names``).

    Le corps de la fonction (et de toute portée imbriquée :
    fonctions, fonctions asynchrones, lambdas, classes,
    compréhensions, générateurs) est analysé via la table de
    symboles construite par ``symtable`` pour le module entier.
    Les éléments de signature (décorateurs, annotations de
    paramètres, valeurs par défaut, valeurs par défaut
    nommées, annotation de retour) sont évalués dans la portée
    englobante au moment du ``def`` et sont donc analysés
    séparément à partir des fragments de source correspondants.
    """
    function_table = _find_function_symbol_table(
        module_table,
        node,
    )

    names: set[str] = set()
    _collect_global_symbol_names(function_table, names)

    for fragment in _signature_fragments(node):
        fragment_source = (
            "__signature_fragment__ = (\n"
            + ast.unparse(fragment)
            + "\n)\n"
        )

        names |= _free_names_in_fragment_source(
            fragment_source
        )

    return (
        names
        - set(dir(builtins))
        - target_names
    )


def render_imports(specs: list[ImportSpec]) -> str:
    plain = [
        spec
        for spec in specs
        if spec.kind == "import"
    ]

    grouped: dict[str, list[ImportSpec]] = {}

    for spec in specs:
        if spec.kind == "from":
            grouped.setdefault(
                spec.module,
                [],
            ).append(spec)

    lines = [
        "from __future__ import annotations",
        "",
    ]

    for spec in sorted(
        plain,
        key=lambda item: (
            item.module,
            item.alias,
        ),
    ):
        line = f"import {spec.module}"

        if spec.alias:
            line += f" as {spec.alias}"

        lines.append(line)

    if plain:
        lines.append("")

    for module in sorted(grouped):
        entries = sorted(
            grouped[module],
            key=lambda item: (
                item.name,
                item.alias,
            ),
        )

        if len(entries) == 1:
            entry = entries[0]
            line = f"from {module} import {entry.name}"

            if entry.alias:
                line += f" as {entry.alias}"

            lines.append(line)
            lines.append("")
            continue

        lines.append(f"from {module} import (")

        for entry in entries:
            line = f"    {entry.name}"

            if entry.alias:
                line += f" as {entry.alias}"

            lines.append(line + ",")

        lines.append(")")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n\n"


def build_module(
    project: Path,
    plan: Plan,
) -> dict[str, object]:
    main = project / "itd_v29.py"
    target = project / plan.module

    if target.exists():
        raise PipelineError(
            f"Le module cible existe déjà : {target}"
        )

    source = main.read_text(encoding="utf-8")
    source_lines = source.splitlines(keepends=True)

    tree = ast.parse(
        source,
        filename=str(main),
    )

    module_table = symtable.symtable(
        source,
        str(main),
        "exec",
    )

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    missing = [
        name
        for name in plan.functions
        if name not in functions
    ]

    if missing:
        raise PipelineError(
            f"Fonctions absentes : {missing}"
        )

    target_names = set(plan.functions)
    symbols = import_map(tree)
    unresolved: set[str] = set()

    for name in plan.functions:
        unresolved.update(
            unresolved_names(
                module_table,
                functions[name],
                target_names,
            )
        )

    remaining_functions = (
        set(functions)
        - target_names
    )

    circular = sorted(
        unresolved
        & remaining_functions
    )

    if circular:
        raise PipelineError(
            "Dépendances circulaires potentielles vers "
            f"des fonctions restant dans itd_v29.py : {circular}"
        )

    unknown = sorted(
        unresolved
        - set(symbols)
    )

    if unknown:
        raise PipelineError(
            f"Symboles globaux non résolus : {unknown}"
        )

    specs = {
        dataclasses.astuple(symbols[name]):
            symbols[name]
        for name in unresolved
    }

    header = textwrap.dedent(
        f"""
        \"\"\"
        {plan.description}

        Module généré automatiquement pour ITD V{plan.version}.
        L'API historique reste réexportée par itd_v29.py.
        \"\"\"

        """
    ).lstrip()

    blocks = []

    for name in plan.functions:
        node = functions[name]

        block = "".join(
            source_lines[
                node.lineno - 1:
                node.end_lineno
            ]
        ).rstrip() + "\n"

        blocks.append(block)

    module_source = (
        header
        + render_imports(
            list(specs.values())
        )
        + "\n\n".join(blocks)
    )

    module_source = (
        module_source.rstrip("\n")
        + "\n"
    )

    compile(
        module_source,
        str(target),
        "exec",
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        module_source,
        encoding="utf-8",
    )

    extracted_tree = ast.parse(
        module_source,
        filename=str(target),
    )

    extracted = {
        node.name: node
        for node in extracted_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    if tuple(extracted) != plan.functions:
        raise PipelineError(
            "Ordre ou liste des fonctions incorrecte : "
            f"{tuple(extracted)}"
        )

    for name in plan.functions:
        original = ast.dump(
            functions[name],
            include_attributes=False,
        )

        copied = ast.dump(
            extracted[name],
            include_attributes=False,
        )

        if original != copied:
            raise PipelineError(
                f"Identité AST perdue : {name}"
            )

    return {
        "module_sha256": sha256(target),
        "imports": sorted(
            dataclasses.astuple(spec)
            for spec in specs.values()
        ),
    }


def integrate_module(
    project: Path,
    plan: Plan,
) -> dict[str, object]:
    main = project / "itd_v29.py"
    source = main.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    tree = ast.parse(
        source,
        filename=str(main),
    )

    targets = set(plan.functions)

    nodes = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in targets
        )
    ]

    if {
        node.name
        for node in nodes
    } != targets:
        raise PipelineError(
            "Groupe incomplet pendant l'intégration."
        )

    module_name = (
        plan.module[:-3]
        .replace("/", ".")
    )

    if any(
        isinstance(node, ast.ImportFrom)
        and node.module == module_name
        for node in tree.body
    ):
        raise PipelineError(
            "Import du module déjà présent."
        )

    ranges = sorted(
        (
            node.lineno - 1,
            node.end_lineno,
        )
        for node in nodes
    )

    import_block = (
        f"from {module_name} import (\n"
        + "".join(
            f"    {name},\n"
            for name in plan.functions
        )
        + ")\n\n"
    )

    for start, end in reversed(ranges):
        del lines[start:end]

    lines.insert(
        ranges[0][0],
        import_block,
    )

    updated = "".join(lines)

    compile(
        updated,
        str(main),
        "exec",
    )

    main.write_text(
        updated,
        encoding="utf-8",
    )

    return {
        "main_sha256": sha256(main),
        "main_lines": len(
            updated.splitlines()
        ),
    }


def verify_reexports(
    project: Path,
    plan: Plan,
) -> None:
    module_name = (
        plan.module[:-3]
        .replace("/", ".")
    )

    code = textwrap.dedent(
        f"""
        import inspect
        import itd_v29
        import {module_name} as extracted

        names = {plan.functions!r}

        for name in names:
            public = getattr(itd_v29, name)
            modular = getattr(extracted, name)

            if public is not modular:
                raise SystemExit(
                    f"Réexportation incorrecte : {{name}}"
                )

            source = inspect.getsourcefile(public)

            if (
                not source
                or not source.endswith({plan.module!r})
            ):
                raise SystemExit(
                    f"Origine incorrecte : {{name}} -> {{source}}"
                )

        print(
            f"Réexportations modulaires : "
            f"{{len(names)}}/{{len(names)}}"
        )
        """
    )

    run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=project,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture=True,
    )


def run_validations(
    project: Path,
    log_dir: Path,
    timeout_seconds: int,
) -> list[dict[str, object]]:
    log_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    validators = [
        path
        for path in sorted(
            project.glob("validate_*.py")
        )
        if path.name not in EXCLUDED_VALIDATORS
    ]

    commands = [
        (
            path.stem.upper(),
            [
                sys.executable,
                path.name,
            ],
        )
        for path in validators
    ]

    commands.append(
        (
            "MAIN",
            [
                sys.executable,
                "itd_v29.py",
            ],
        )
    )

    records = []
    failures = []

    base_env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }

    for name, command in commands:
        environment = dict(base_env)

        environment[
            "MPLCONFIGDIR"
        ] = str(
            log_dir
            / f"matplotlib_{name}"
        )

        Path(
            environment["MPLCONFIGDIR"]
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            result = run(
                command,
                cwd=project,
                env=environment,
                capture=True,
                check=False,
                timeout=timeout_seconds,
            )

            code = result.returncode
            output = result.stdout or ""

        except subprocess.TimeoutExpired as error:
            code = 124
            output = (
                error.stdout or ""
            ) + "\nTIMEOUT\n"

        log_file = (
            log_dir
            / f"{name}.log"
        )

        log_file.write_text(
            output,
            encoding="utf-8",
        )

        (
            log_dir
            / f"{name}.code"
        ).write_text(
            f"{code}\n",
            encoding="utf-8",
        )

        records.append(
            {
                "name": name,
                "code": code,
                "log": str(log_file),
            }
        )

        print(
            f"{name} : "
            + (
                "RÉUSSI"
                if code == 0
                else f"ÉCHEC ({code})"
            )
        )

        if code != 0:
            failures.append(
                (
                    name,
                    log_file,
                )
            )

    if failures:
        details = []

        for name, log_file in failures:
            tail = "\n".join(
                log_file.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()[-50:]
            )

            details.append(
                f"\n### {name}\n{tail}"
            )

        raise PipelineError(
            "Validations en échec :"
            + "".join(details)
        )

    return records


def compare_summary(
    project: Path,
    reference_archive: Path,
) -> str:
    current = (
        project
        / "itd_v29_results"
        / "summary.csv"
    )

    reference = (
        reference_archive
        / "itd_v29_results"
        / "summary.csv"
    )

    if not current.is_file():
        raise PipelineError(
            "Résumé courant absent."
        )

    if not reference.is_file():
        raise PipelineError(
            "Résumé de référence absent."
        )

    if (
        current.read_bytes()
        != reference.read_bytes()
    ):
        raise PipelineError(
            "summary.csv n'est pas bit à bit "
            "identique à l'archive précédente."
        )

    return sha256(current)


def write_report(
    project: Path,
    plan: Plan,
    *,
    main_sha: str,
    module_sha: str,
    summary_sha: str,
    validations: list[dict[str, object]],
    imports: list[tuple[str, str, str, str]],
    log_dir: Path,
) -> Path:
    report = (
        project
        / "itd_v29_results"
        / plan.report_name
    )

    report.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        f"# ITD V{plan.version} — Certification",
        "",
        f"- Date UTC : `{now_utc()}`",
        f"- Module : `{plan.module}`",
        f"- Référence : `V{previous_version(plan.version)}`",
        "- Résumé principal bit à bit identique : **oui**",
        "",
        "## Portée",
        "",
        plan.description,
        "",
        "## Fonctions extraites",
        "",
    ]

    lines.extend(
        f"- `{name}`"
        for name in plan.functions
    )

    lines.extend(
        [
            "",
            "## Imports directs",
            "",
        ]
    )

    for kind, module, name, alias in imports:
        if kind == "import":
            rendered = f"import {module}"

            if alias:
                rendered += f" as {alias}"

        else:
            rendered = (
                f"from {module} import {name}"
            )

            if alias:
                rendered += f" as {alias}"

        lines.append(
            f"- `{rendered}`"
        )

    lines.extend(
        [
            "",
            "## Validations",
            "",
        ]
    )

    lines.extend(
        f"- `{record['name']}` : **PASSED**"
        for record in validations
    )

    lines.extend(
        [
            "",
            "## Exclusions historiques",
            "",
        ]
    )

    for filename, reason in (
        EXCLUDED_VALIDATORS.items()
    ):
        lines.append(
            f"- `{filename}` : {reason}"
        )

    lines.extend(
        [
            "",
            "## Architecture",
            "",
            "- Définitions extraites restant dans `itd_v29.py` : **0**",
            (
                "- Réexportations directes : "
                f"**{len(plan.functions)}/{len(plan.functions)}**"
            ),
            "",
            "## Empreintes SHA-256",
            "",
            f"- `itd_v29.py` : `{main_sha}`",
            f"- `{plan.module}` : `{module_sha}`",
            (
                "- `itd_v29_results/summary.csv` : "
                f"`{summary_sha}`"
            ),
            "",
            "## Journaux",
            "",
            f"- `{log_dir}`",
            "",
            "## Portée scientifique",
            "",
            (
                "Cette certification est relative aux suites "
                "de tests, oracles et configurations numériques "
                "déclarés. Elle ne constitue pas une preuve "
                "universelle de correction."
            ),
            "",
            "**FINAL STATUS: PASSED**",
            "",
        ]
    )

    report.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return report


def copy_snapshot(
    project: Path,
    destination: Path,
) -> int:
    excluded_parts = {
        ".git",
        ".venv",
        "archives",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".v29_pipeline_backups",
    }

    destination.mkdir(
        parents=True,
        exist_ok=False,
    )

    count = 0

    for source in sorted(
        project.rglob("*")
    ):
        relative = source.relative_to(
            project
        )

        if any(
            part in excluded_parts
            for part in relative.parts
        ):
            continue

        if (
            source.is_dir()
            or source.is_symlink()
        ):
            continue

        if source.suffix == ".pyc":
            continue

        if ".before_" in source.name:
            continue

        if source.name.endswith(".tmp"):
            continue

        if source.name == "MANIFEST.sha256":
            continue

        target = (
            destination
            / relative
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            target,
        )

        count += 1

    return count


def write_manifest(
    root: Path,
) -> tuple[int, str]:
    files = sorted(
        path
        for path in root.rglob("*")
        if (
            path.is_file()
            and path.name != "MANIFEST.sha256"
        )
    )

    manifest = (
        root
        / "MANIFEST.sha256"
    )

    lines = [
        (
            f"{sha256(path)}  "
            f"{path.relative_to(root).as_posix()}"
        )
        for path in files
    ]

    manifest.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    for line in lines:
        digest, filename = line.split(
            "  ",
            1,
        )

        if sha256(
            root / filename
        ) != digest:
            raise PipelineError(
                f"Manifeste invalide : {filename}"
            )

    return (
        len(files),
        sha256(manifest),
    )


def make_readonly(root: Path) -> None:
    for path in sorted(
        root.rglob("*"),
        reverse=True,
    ):
        path.chmod(
            path.stat().st_mode
            & ~stat.S_IWUSR
            & ~stat.S_IWGRP
            & ~stat.S_IWOTH
        )

    root.chmod(
        root.stat().st_mode
        & ~stat.S_IWUSR
        & ~stat.S_IWGRP
        & ~stat.S_IWOTH
    )


def archive_release(
    project: Path,
    plan: Plan,
) -> dict[str, object]:
    archive = (
        project
        / "archives"
        / plan.archive_name
    )

    if archive.exists():
        raise PipelineError(
            f"Archive déjà existante : {archive}"
        )

    build = archive.with_name(
        f"{archive.name}.building.{os.getpid()}"
    )

    if build.exists():
        shutil.rmtree(build)

    copied = copy_snapshot(
        project,
        build,
    )

    manifest_count, manifest_sha = (
        write_manifest(build)
    )

    if copied != manifest_count:
        shutil.rmtree(build)

        raise PipelineError(
            "Incohérence entre fichiers copiés "
            "et entrées du manifeste."
        )

    build.rename(archive)
    make_readonly(archive)

    return {
        "archive": str(archive),
        "file_count": manifest_count,
        "manifest_sha256": manifest_sha,
    }


def create_backup(
    project: Path,
    plan: Plan,
) -> Path:
    backup = (
        project
        / ".v29_pipeline_backups"
        / (
            f"v{plan.version}_"
            + dt.datetime.now().strftime(
                "%Y%m%dT%H%M%S"
            )
        )
    )

    backup.mkdir(
        parents=True,
        exist_ok=False,
    )

    for relative in (
        "itd_v29.py",
        "itd_v29_results/summary.csv",
    ):
        source = project / relative

        if not source.exists():
            continue

        target = backup / relative

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            target,
        )

    return backup


def restore_backup(
    project: Path,
    backup: Path,
) -> None:
    for relative in (
        "itd_v29.py",
        "itd_v29_results/summary.csv",
    ):
        source = backup / relative

        if not source.exists():
            continue

        target = project / relative

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            target,
        )


def verify_start(
    project: Path,
    plan: Plan,
) -> Path:
    main = project / "itd_v29.py"

    compile_file(main)

    target = project / plan.module

    if target.exists():
        raise PipelineError(
            f"Module cible déjà présent : {target}"
        )

    reference_version = previous_version(
        plan.version
    )

    reference = find_reference_archive(
        project,
        reference_version,
    )

    current_summary = (
        project
        / "itd_v29_results"
        / "summary.csv"
    )

    reference_summary = (
        reference
        / "itd_v29_results"
        / "summary.csv"
    )

    if (
        current_summary.read_bytes()
        != reference_summary.read_bytes()
    ):
        raise PipelineError(
            "Le résumé courant ne correspond pas "
            f"à V{reference_version}."
        )

    return reference


def execute_release(
    project: Path,
    plan: Plan,
    *,
    timeout_seconds: int,
) -> dict[str, object]:
    print()
    print("=" * 78)
    print(
        f"ITD V{plan.version} — {plan.slug}"
    )
    print("=" * 78)

    reference = verify_start(
        project,
        plan,
    )

    backup = create_backup(
        project,
        plan,
    )

    module = project / plan.module

    record = {
        "version": plan.version,
        "started_utc": now_utc(),
        "backup": str(backup),
        "reference_archive": str(reference),
    }

    try:
        candidate = build_module(
            project,
            plan,
        )

        integrated = integrate_module(
            project,
            plan,
        )

        compile_file(
            project / "itd_v29.py"
        )

        compile_file(module)

        verify_reexports(
            project,
            plan,
        )

        log_dir = (
            Path("/tmp")
            / (
                f"itd_v{plan.version.replace('.', '_')}_"
                "certification_"
                + dt.datetime.now(
                    dt.timezone.utc
                ).strftime(
                    "%Y%m%dT%H%M%SZ"
                )
            )
        )

        validations = run_validations(
            project,
            log_dir,
            timeout_seconds,
        )

        summary_sha = compare_summary(
            project,
            reference,
        )

        report = write_report(
            project,
            plan,
            main_sha=integrated[
                "main_sha256"
            ],
            module_sha=candidate[
                "module_sha256"
            ],
            summary_sha=summary_sha,
            validations=validations,
            imports=candidate["imports"],
            log_dir=log_dir,
        )

        archive = archive_release(
            project,
            plan,
        )

        record.update(
            {
                "candidate": candidate,
                "integrated": integrated,
                "validations": validations,
                "summary_sha256": summary_sha,
                "report": str(report),
                "archive": archive,
                "status": "PASSED",
                "finished_utc": now_utc(),
            }
        )

        return record

    except Exception:
        restore_backup(
            project,
            backup,
        )

        if module.exists():
            module.unlink()

        raise


def write_series_report(
    project: Path,
    records: list[dict[str, object]],
) -> Path:
    report = (
        project
        / "itd_v29_results"
        / "V29_SERIES_AUTOMATION_REPORT.md"
    )

    report.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "# ITD V29.xx — Rapport d'automatisation",
        "",
        f"- Généré le : `{now_utc()}`",
        "",
    ]

    for record in records:
        lines.extend(
            [
                f"## V{record['version']}",
                "",
                (
                    "- Statut : "
                    f"**{record.get('status', 'FAILED')}**"
                ),
                (
                    "- Début : "
                    f"`{record.get('started_utc', '')}`"
                ),
                (
                    "- Fin : "
                    f"`{record.get('finished_utc', '')}`"
                ),
            ]
        )

        archive = record.get("archive")

        if isinstance(archive, dict):
            lines.extend(
                [
                    (
                        "- Archive : "
                        f"`{archive.get('archive')}`"
                    ),
                    (
                        "- Fichiers manifestés : "
                        f"`{archive.get('file_count')}`"
                    ),
                    (
                        "- SHA-256 du manifeste : "
                        f"`{archive.get('manifest_sha256')}`"
                    ),
                ]
            )

        error = record.get("error")

        if error:
            lines.extend(
                [
                    "",
                    "### Erreur",
                    "",
                    "```text",
                    str(error),
                    "```",
                ]
            )

        lines.append("")

    report.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return report


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Automatise l'extraction, la validation, "
            "le rapport Markdown et l'archivage des "
            "dernières versions ITD V29.xx."
        )
    )

    parser.add_argument(
        "--project",
        type=Path,
        default=(
            Path.home()
            / "itd-simulator"
        ),
    )

    parser.add_argument(
        "--version",
        choices=[
            plan.version
            for plan in PLANS
        ],
    )

    parser.add_argument(
        "--all",
        action="store_true",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1200,
    )

    parser.add_argument(
        "--list-plan",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    if arguments.list_plan:
        for plan in PLANS:
            print(
                f"V{plan.version}: "
                f"{plan.module} <- "
                + ", ".join(plan.functions)
            )

        return 0

    if (
        not arguments.all
        and not arguments.version
    ):
        raise PipelineError(
            "Choisir --version X ou --all."
        )

    if (
        arguments.all
        and arguments.version
    ):
        raise PipelineError(
            "--all et --version sont incompatibles."
        )

    project = arguments.project.resolve()

    if not (
        project
        / "itd_v29.py"
    ).is_file():
        raise PipelineError(
            f"Projet invalide : {project}"
        )

    selected = (
        list(PLANS)
        if arguments.all
        else [
            next(
                plan
                for plan in PLANS
                if (
                    plan.version
                    == arguments.version
                )
            )
        ]
    )

    records: list[dict[str, object]] = []
    exit_code = 0

    for plan in selected:
        try:
            records.append(
                execute_release(
                    project,
                    plan,
                    timeout_seconds=(
                        arguments.timeout
                    ),
                )
            )

        except Exception as error:
            records.append(
                {
                    "version": plan.version,
                    "status": "FAILED",
                    "started_utc": now_utc(),
                    "finished_utc": now_utc(),
                    "error": str(error),
                }
            )

            exit_code = 1
            break

    report = write_series_report(
        project,
        records,
    )

    print()
    print(
        f"Rapport global : {report}"
    )

    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())

    except PipelineError as error:
        print(
            f"ERREUR : {error}",
            file=sys.stderr,
        )

        raise SystemExit(2)
