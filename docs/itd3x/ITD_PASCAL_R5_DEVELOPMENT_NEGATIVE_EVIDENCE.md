# ITD Pascal R5 — frozen Development negative evidence

Status: Development-only, negative under the preregistered byte-exact ledger criterion. No Validation execution and no confirmatory/final access.

## Frozen identities

- R5 implementation commit: `d3331b8293b664b62593f3545d7ceee3d03742b4`
- protocol document SHA-256: `e8929c13146fad71b6844adac42dd55d95650bc27401edf46c330332d649cbd0`
- protocol fingerprint: `cc29a27dac2724ae3167f7ec634f0df693f41f7ba92dde61702aa1980bdc7840`
- Development plan fingerprint: `a3e2fb9db5a376f746c8a64d0f3c2152ce8dcef844a0a84ebc4669213d3ff561`
- Development source SHA-256: `cbc6b7f2c13e6e73e0f810f6e7a0ad0352fa94db127e62342850e5ac6310ca56`
- R5 source implementation SHA-256: `b1375a2e951f3165d46134a8d411715714108ffef98712dd70d90f33afc6d4f0`
- R5 test source SHA-256: `a9b744102597b6142ff94f69881df38e13f329b0f56f88cd100b2d1af9207999`

The original evidence resides at `/home/tarek/research/pascal_dual_bench/itd-r5-evidence-d3331b8`, including `freeze.json`, plan/source bytes, control ledger, relocated ledger, original artifacts and `development/prefix-02/comparison.json`. These files are not overwritten or relabelled here.

## Preregistered matched test

- Development: six cases `dev-n6-relocation-case-00` through `-05`.
- Matched continuous control and relocated/resumed experimental arm.
- Relocation at frozen completed-case prefix 2, followed by a fresh-process resume.
- Both arms completed six cases with zero duplicated or skipped cases.
- Source bytes, plan fingerprint, case order and six artifact digests agree exactly.
- Before/after relocation tree fingerprints agree:
  `28ebacf3c79fe84b38c53db3a322d7cab5038d80ceb217bf8e82c1ced450110a`.

## Negative primary result

Preregistered byte-exact full ledger equality **failed**:

- control ledger SHA-256:
  `0ad9b16681e0fcafba35df2a57beb82564034c4f95d45a4ceb8365045c26f7c9`
- relocated ledger SHA-256:
  `6b2c979ed32ffcc6cda0fe238b7f060f29452e594c95fb53f197262db369bb79`

The differing field is the operational ledger `reason`:
`all planned cases executed` versus `resumed interrupted campaign completed`.
This is a genuine negative result against **R5's frozen bytewise-ledger gate**,
not a scientific payload mismatch and not a reason to rewrite the gate.

A **post-hoc diagnostic only** (not a new experiment and not a reclassified R5 result)
shows that canonically serialized ledgers with exactly the `reason` field
excluded are identical, SHA-256
`2d6347ea5f00712489b0f181c767ac303821446a473029af35b0592ff02f2b9f`.
This diagnostic motivates a separately preregistered R6; it does not repair R5.

The campaign was stopped after the prefix-2 failure. No prefix-5 replay or
Validation campaign was executed after this failure. No completed evidence is
to be rerun as fresh replication.

## Packaging and interpretation

At this frozen R5 head, `MANIFEST.sha256` contains stale entries for
`itd_research/pascal_relocation_integrity.py` and
`tests/test_pascal_r5_geometry.py`. Their exact file hashes are recorded
above; manifest repair and full CI qualification remain required before merge.

R5 establishes neither Pascal model utility nor an improvement in TDI or
another architecture. SML-GENIUS owns model-side Pascal primitives. This
negative result authorizes no promotion into SBG, MOR, Delta-KV, context, or
model architecture. Protected/final populations were not opened.
