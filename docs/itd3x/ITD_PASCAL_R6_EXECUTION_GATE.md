# ITD Pascal R6 execution gate

R6 remains Development/Validation-only. No R6 scientific case has been executed and no final source is constructible.

Frozen identities before Development: protocol `8c03410b28ad71f26f6736983948b5cf2241c59874a650ff577e222ff19523e5`; implementation bundle `99612bfb85a4070859edd54c5f789991de0854af0401e02da2ff172ab742a6fe`; Development source `8463a2e683260d300c27ca96437ea065a600a5c6541988873ea4b6e6cc985d45`; Validation source `3da7077f10e7ae22db666af7827810c9544777ff3a9634b65f516132eabd64ba`; pre-execution freeze `faef608bd928e8d7847806a3091a159921a1936f067ddd77efe0d8236e52ddd2`.

Local qualification on the rebased main tree: 17 targeted tests pass; Ruff passes; Mypy passes for the R6 plan, ledger integrity and runner; `MANIFEST.sha256` verifies. R5 negative evidence is unchanged.

Development must not execute until the exact runner, plans, source bytes, tests and freeze are committed and CI is green. Validation additionally requires a frozen Development gate artifact.
