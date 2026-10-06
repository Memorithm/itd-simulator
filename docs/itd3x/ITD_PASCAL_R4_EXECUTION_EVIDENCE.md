# ITD Pascal R4 — interruption/resume execution evidence

Status: completed Development/Validation-only secondary integrity campaign.

No protected/final source was generated, opened, inspected, or executed. R4 is
independent of the TDI Pascal cost/utility programme and does not import TDI
effect directions or promotion criteria. This evidence authorizes no model-side
promotion.

## Qualified implementation identity

- R4 implementation branch head:
  `a2d65893c13c9e827f028884941eaa4e12be3915`
- full GitHub CI run #482: success
- CI URL:
  `https://github.com/Memorithm/itd-simulator/actions/runs/37544498235`
- R4 implementation SHA-256:
  `9e73c38e3de55804ff2617c36f792bbd4283159297fca35db1375ab5483d9139`
- R4 preregistration SHA-256:
  `0a66f81560f66bb1ac75476db497d8a1feb38aa7046411d1789a3bb4c6f11c60`

The exact R4 implementation bytes were materialized from the qualified branch
head and their SHA-256 was verified before execution. The local base checkout
was the preregistration commit
`69eb5153be770f409b91f3e60e4e43baf82fe853`. The Git comparison from that
commit to the qualified implementation head changes only
`MANIFEST.sha256`, `itd_research/pascal_resume_integrity.py`, and
`tests/test_pascal_r4_geometry.py`; the exact implementation module from the
qualified head was loaded under its package identity for the campaign.

## Frozen campaign identities

- protocol fingerprint:
  `5377029042f56a06a3b7fee1c9de67be7007218235013e9b29f2c42ab3dbf58a`
- Development plan fingerprint:
  `1a7b3e296e1b0d25e024cfd8a84d749127aef5780d87626afae789ae1be1f6bd`
- Validation plan fingerprint:
  `8cd351d79dca902e019881025a60f0dc978600a9c9abc39245304d898708fc6a`
- Development source SHA-256:
  `5d3711b28552e0e76fed14d419c9a0eeed61163c8a06c09e213c5bcebdb97648`
- Validation source SHA-256:
  `568ce63f982442f2e9739c093ab1e1a0336217fb9150854fcef73c8739fdf73f`

The persistent evidence directory is
`/home/tarek/research/pascal_dual_bench/itd-r4-evidence-a2d6589`.
It contains 102 pre-manifest evidence files. Their canonical SHA-256 manifest is
`evidence.sha256`, whose SHA-256 is
`088a5be27cd16eae3b3cad60b2f6f345c93c12a17a2d293ffb70bbdc7b2465f3`.
All 102 entries were reverified after execution.

## Matched interruption/resume result

Development and Validation each executed one uninterrupted matched control and
three interrupted/resumed arms with the preregistered durable prefix lengths
1, 4, and 7. Every campaign completed exactly 8 planned cases with 8 persisted
artifacts. Every comparison retained the same plan/protocol identity, case
order, output digests, source identity, and persisted prefix bytes, with zero
duplicate or skipped case execution.

Development comparison SHA-256 values:

- prefix 1:
  `e375bd9514c3c3de010c02905ad437958210c2dc3e30b8bb2cef4a72efd132de`
- prefix 4:
  `4e9a71837472f28f0e7b4f5839ffe21bae2529c2145163ea7d83d61edbc83048`
- prefix 7:
  `5a9301bd9213730babe0e1d9731d1378bd52bc2e9b3468e7fa6486c5258a47d5`

Validation comparison SHA-256 values:

- prefix 1:
  `b2df296d85e57b21b96c917d489de434e2fef34dd6ed04e54428f3baea94571d`
- prefix 4:
  `b2089f9523a9965a98c408cb7c1c8bedbfd71dd048d0ad6278b762b3eac4f4f9`
- prefix 7:
  `40272cc0633bbc74d93d397426a0a103ce5e10e6e7e4f139c1cc48c186f49359`

All six matched comparisons have outcome `pass` and every preregistered exact
comparison check is true. The complete canonical R4 summary has SHA-256
`7cb339cb9dbdd8ca2a712126a0de6aaaf6769efc3440c9c86ea0207943670eba`.

## Fail-closed provenance probes

The three preregistered Development provenance probes were executed as
integrity checks, not as scientific replications. Each stopped at the persisted
interrupted prefix with zero additional case executions after the injected
integrity fault and retained an explicit `integrity_error` record:

- source drift:
  `9fc5878b8636a4e2422aea626633244c6832faaed12bb48c3674944b24216605`
- persisted-artifact drift:
  `d44effa3be587eb172b43eee0182ac870350e5fa646c691182d109d4618fd203`
- persisted-plan drift:
  `ede004cd26b7e41cbaea92db055b5dfc2b6c1bc57f4bb68174462960a0ac109f`

These fail-closed records are retained rather than rewritten as successful
campaign evidence.

## Interpretation boundary

R4 establishes only interruption/resume ledger integrity for the frozen
synthetic non-final Pascal campaigns. It does not establish Pascal model
utility, latency, throughput, memory efficiency, or operation-cost advantage.
It is not a rerun of R2 or R3 and is not counted as a new R3 replication.

SML-GENIUS remains the owner of model-side Pascal primitives. Nothing in R4
authorizes promotion into SBG, MOR, Delta-KV, context memory, or model
architecture.