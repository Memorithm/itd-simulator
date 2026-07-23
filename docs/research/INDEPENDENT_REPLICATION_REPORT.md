# Independent replication report (H60)

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Does not modify
`ITD V29.18`.

## Replication on a second, independent Python environment

The offline Mission 7 fixture campaign was re-run in a **freshly created virtual
environment on a different interpreter and a different NumPy build**, then compared to the
original.

| | original | replication |
|---|---|---|
| Python | 3.11.15 | **3.13.12** |
| NumPy | 2.3.5 | **2.5.1** |
| environment | project venv | clean `python3.13 -m venv` + `pip install numpy` |

### Result

- **Every verdict is identical**: physical-validation verdict, prediction verdict, and the
  set of complementarity-distinct ITD channels all match.
- **Maximum relative numerical difference: 1.6 × 10⁻¹⁶** (one unit in the last place, in a
  single `swirl_mean` value) — i.e. machine epsilon. The campaign JSON hashes differ only
  because of that last-bit float representation.

**Verdict: H60 supported within tested scope.** The Mission 7 external-evidence pipeline
reproduces on a genuinely independent interpreter and library build to machine precision,
with identical scientific conclusions.

## Honest scope limit

This is a **second interpreter / clean environment on the same machine and OS**. A truly
independent *second machine*, *different OS/architecture*, or *external person* was not
available within this session. The result therefore establishes cross-interpreter /
cross-library reproducibility (strong), but not cross-hardware or third-party replication
(not attempted). The reproduction bundle (`repro/mission7/`) makes the latter possible for
anyone with the public data and the documented commands.
