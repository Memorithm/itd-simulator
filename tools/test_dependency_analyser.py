#!/usr/bin/env python3
"""
Tests déterministes et ciblés pour l'analyseur de dépendances
lexicales de `finish_v29_series.py`.

Chaque cas fournit un fragment de module autonome, demande les
dépendances calculées pour une fonction de premier niveau donnée,
et compare le résultat à l'ensemble exact attendu.

Ce script ne dépend d'aucun framework de test externe : il suit le
même style que les validateurs scientifiques du dépôt (assertions
directes, sortie non nulle en cas d'échec).
"""

from __future__ import annotations

import ast
import symtable
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import finish_v29_series as tool  # noqa: E402


def dependencies_of(
    source: str,
    function_name: str,
    target_names: frozenset[str] = frozenset(),
) -> set[str]:
    normalized = textwrap.dedent(source).strip("\n") + "\n"

    tree = ast.parse(normalized)

    module_table = symtable.symtable(
        normalized,
        "<test-fragment>",
        "exec",
    )

    node = next(
        candidate
        for candidate in tree.body
        if (
            isinstance(
                candidate,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
            and candidate.name == function_name
        )
    )

    return tool.unresolved_names(
        module_table,
        node,
        set(target_names),
    )


CASES: list[tuple[str, object]] = []


def case(name: str):
    def register(function):
        CASES.append((name, function))
        return function

    return register


@case("regression : fermeture spatial_mean (bug historique V29.15)")
def _regression_mean_field() -> None:
    deps = dependencies_of(
        """
        def outer():
            def mean_field(field):
                return spatial_mean(field)
        """,
        "outer",
    )

    assert deps == {"spatial_mean"}, deps
    assert "field" not in deps, deps


@case("regression : capture d'un local du parent (ni field ni scale)")
def _regression_closure_local() -> None:
    deps = dependencies_of(
        """
        def outer(scale):
            def inner(field):
                return field * scale
        """,
        "outer",
    )

    assert deps == set(), deps


@case("1. noms liés par except ... as ...")
def _except_as() -> None:
    deps = dependencies_of(
        """
        def f():
            try:
                risky()
            except ValueError as error:
                return str(error)
        """,
        "f",
    )

    assert deps == {"risky"}, deps
    assert "error" not in deps, deps


@case("2. paramètres de fonction imbriquée")
def _nested_function_parameters() -> None:
    deps = dependencies_of(
        """
        def outer():
            def helper(field, weight):
                return combine(field, weight)
            return helper
        """,
        "outer",
    )

    assert deps == {"combine"}, deps
    assert "field" not in deps
    assert "weight" not in deps
    assert "helper" not in deps


@case("3. variables libres capturées par fermeture")
def _closure_free_variables() -> None:
    deps = dependencies_of(
        """
        def outer():
            base = compute_base()
            def inner():
                return base + external_offset
            return inner
        """,
        "outer",
    )

    assert deps == {"compute_base", "external_offset"}, deps
    assert "base" not in deps


@case("4. valeurs par défaut imbriquées")
def _nested_default_values() -> None:
    deps = dependencies_of(
        """
        def outer():
            def inner(value=[i * FACTOR for i in range(3)]):
                return value
            return inner
        """,
        "outer",
    )

    assert deps == {"FACTOR"}, deps
    assert "i" not in deps
    assert "value" not in deps


@case("5. annotations imbriquées")
def _nested_annotations() -> None:
    deps = dependencies_of(
        """
        def outer():
            def inner(value: CustomType) -> None:
                return value
            return inner
        """,
        "outer",
    )

    assert deps == {"CustomType"}, deps


@case("6. annotation de retour")
def _return_annotation() -> None:
    deps = dependencies_of(
        """
        def f() -> ReturnType:
            return None
        """,
        "f",
    )

    assert deps == {"ReturnType"}, deps


@case("7. compréhension de liste")
def _list_comprehension() -> None:
    deps = dependencies_of(
        """
        def f(values):
            return [item * FACTOR for item in values]
        """,
        "f",
    )

    assert deps == {"FACTOR"}, deps
    assert "item" not in deps
    assert "values" not in deps


@case("8. compréhension d'ensemble")
def _set_comprehension() -> None:
    deps = dependencies_of(
        """
        def f(values):
            return {item for item in values if item > THRESHOLD}
        """,
        "f",
    )

    assert deps == {"THRESHOLD"}, deps
    assert "item" not in deps


@case("9. compréhension de dictionnaire")
def _dict_comprehension() -> None:
    deps = dependencies_of(
        """
        def f(values):
            return {key: TRANSFORM(key) for key in values}
        """,
        "f",
    )

    assert deps == {"TRANSFORM"}, deps
    assert "key" not in deps


@case("10. expression génératrice")
def _generator_expression() -> None:
    deps = dependencies_of(
        """
        def f(values):
            return sum(item * WEIGHT for item in values)
        """,
        "f",
    )

    assert deps == {"WEIGHT"}, deps
    assert "item" not in deps


@case("11. with ... as ...")
def _with_as() -> None:
    deps = dependencies_of(
        """
        def f():
            with resource_manager() as handle:
                return handle.read()
        """,
        "f",
    )

    assert deps == {"resource_manager"}, deps
    assert "handle" not in deps


@case("12. destructuration tuple / liste")
def _destructuring() -> None:
    deps = dependencies_of(
        """
        def f(pair):
            first, second = pair
            (a, (b, c)) = OTHER_PAIR
            return first + second + a + b + c
        """,
        "f",
    )

    assert deps == {"OTHER_PAIR"}, deps
    for excluded in ("first", "second", "a", "b", "c", "pair"):
        assert excluded not in deps


@case("13. affectation walrus")
def _walrus() -> None:
    deps = dependencies_of(
        """
        def f(source):
            if (n := len(source)) > THRESHOLD:
                return n
            return 0
        """,
        "f",
    )

    assert deps == {"THRESHOLD"}, deps
    assert "n" not in deps


@case("14. lambda imbriqué")
def _nested_lambda() -> None:
    deps = dependencies_of(
        """
        def outer():
            return lambda value: value * SCALE_FACTOR
        """,
        "outer",
    )

    assert deps == {"SCALE_FACTOR"}, deps
    assert "value" not in deps


@case("15. fonction async imbriquée")
def _nested_async_function() -> None:
    deps = dependencies_of(
        """
        def outer():
            async def inner():
                return await fetch_data()
            return inner
        """,
        "outer",
    )

    assert deps == {"fetch_data"}, deps
    assert "inner" not in deps


@case("16. classe imbriquée")
def _nested_class() -> None:
    deps = dependencies_of(
        """
        def outer(Base):
            class Impl(Base):
                def method(self):
                    return HELPER_CONSTANT
            return Impl
        """,
        "outer",
    )

    assert deps == {"HELPER_CONSTANT"}, deps
    for excluded in ("Base", "Impl", "method", "self"):
        assert excluded not in deps


@case("17. déclaration global")
def _global_declaration() -> None:
    deps = dependencies_of(
        """
        def bump():
            global COUNTER
            COUNTER = COUNTER + STEP
            return COUNTER
        """,
        "bump",
    )

    assert deps == {"COUNTER", "STEP"}, deps


@case("18. déclaration nonlocal")
def _nonlocal_declaration() -> None:
    deps = dependencies_of(
        """
        def outer():
            total = 0
            def inner(value):
                nonlocal total
                total += value * FACTOR
                return total
            return inner
        """,
        "outer",
    )

    assert deps == {"FACTOR"}, deps
    assert "total" not in deps


@case("19. import local à la fonction")
def _function_local_import() -> None:
    deps = dependencies_of(
        """
        def f():
            import math
            return math.sqrt(EXTERNAL_VALUE)
        """,
        "f",
    )

    assert deps == {"EXTERNAL_VALUE"}, deps
    assert "math" not in deps


@case("20. fonction locale récursive")
def _recursive_function() -> None:
    deps = dependencies_of(
        """
        def factorial(n):
            if n <= 1:
                return BASE_CASE
            return n * factorial(n - 1)
        """,
        "factorial",
        target_names=frozenset({"factorial"}),
    )

    assert deps == {"BASE_CASE"}, deps
    assert "factorial" not in deps


def main() -> int:
    failures: list[str] = []

    for name, function in CASES:
        try:
            function()

        except AssertionError as error:
            failures.append(f"{name} : ÉCHEC — {error}")
            print(f"{name} : ÉCHEC")

        except Exception as error:  # noqa: BLE001
            failures.append(
                f"{name} : ERREUR — {error!r}"
            )
            print(f"{name} : ERREUR — {error!r}")

        else:
            print(f"{name} : RÉUSSI")

    print()
    print(f"Total : {len(CASES)}  Échecs : {len(failures)}")

    if failures:
        print()
        print("Détail des échecs :")

        for failure in failures:
            print(f"- {failure}")

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
