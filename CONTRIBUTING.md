# Contributing

Thank you for reviewing ITD Simulator. The repository is currently maintained
as a single-author research project by Tarek Zekriti.

## Before proposing code

No software licence or external-contribution agreement has been selected.
Until those legal terms are explicit, use issues for reproducible bug reports,
scientific questions, test cases, and review observations; do not submit code
for incorporation. See `docs/license_decision.md`.

Do not include confidential data, credentials, third-party code, or material
whose redistribution rights are unclear. Security reports follow `SECURITY.md`.

## Reproducible reports

Include:

- software version, scientific model revision, commit SHA, and operating system;
- Python, NumPy, SciPy, and Matplotlib versions;
- deterministic environment variables and exact command;
- the smallest input that reproduces the behavior;
- actual output, expected output, and whether the expectation is analytical or
  implementation-generated;
- tolerances and units.

Do not propose changing expected scientific values solely to make a test pass.

## Maintainer workflow

Changes are made on a dedicated branch and validated with:

```bash
python -m compileall -q .
pytest -q
ruff check .
./run_validation.sh
python tools/check_manifest.py
```

Scientific calculation changes require analytical justification, regression
comparison, documented tolerances, and an explicit scientific revision
decision. Oracle fixtures and the manifest are never regenerated silently.

Commits and annotated tags in this repository use only:

```text
Tarek Zekriti <194770978+CHECKUPAUTO@users.noreply.github.com>
```

Automated-authorship trailers are prohibited by CI. Already published history
is not rewritten merely to alter old metadata.

## Style

Ruff checks syntax, undefined names, import ordering, unused imports, common
correctness issues, and safe modernization. Avoid broad formatting or
autofixes that obscure mathematical expressions or change operation order.
Type checking is incremental and currently applies to new repository tooling,
not the complete historical scientific code.

No separate code of conduct is included at present because this is not yet an
open contribution project. If the collaboration model changes, contribution
terms and a conduct policy should be selected together.
