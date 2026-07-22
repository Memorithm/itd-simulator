# Python-to-Rust oracle contract

## Purpose and authority

`oracle_harness.py` generates reference fixtures for the SciRust port from the
Python implementation of scientific model `ITD V29.18`. The committed fixture
is `tests/fixtures/oracle_data.rs`.

The fixture is an implementation-generated regression snapshot. Agreement
shows that another implementation reproduces specified Python behavior; it is
not an independent mathematical proof. Simple analytical cases in the pytest
suite—zero derivatives, solid rotation, identity transforms, periodic full
translations, and related invariants—are the independent oracles.

## Data representation

- Floating-point type: IEEE-754 binary64, generated from NumPy `float64`.
- Integer dimensions and sample indices: Rust `usize` constants/slices.
- Layout: contiguous row-major flattening (`numpy.ravel` default C order).
- Two-dimensional shape: `(ny, nx)`.
- Axis order: y is NumPy axis 0; x is axis 1.
- Mesh convention: `meshgrid(x, y, indexing="xy")`.
- Vector component order: `(vx, vy)`.
- Gradient return order: `(d/dy, d/dx)`.
- Vorticity sign: `d(vy)/dx - d(vx)/dy`.

Rust consumers must reconstruct the declared shape rather than infer a
transposed or column-major layout from a flat slice.

## Coordinates and boundaries

Finite grids include both endpoints and use second-order boundary derivatives
plus trapezoidal spatial means. Periodic grids are uniform and endpoint
excluded; their period is `spacing * node_count`, and wrapping maps into
`[origin, origin + period)`.

Periodic interpolation follows the conventions in `numerical_methods.md`:
bilinear, unrestricted cubic Lagrange, cubic locally bounded by the surrounding
bilinear nodes, or locally bounded with discrete-sum restoration. RK4 departure
stages wrap before evaluating the transport velocity. Geometric transforms use
source coordinates `Q^T(x-o)+o` and explicit finite-domain fill values.

## Comparison tolerance

`python oracle_harness.py --check REFERENCE` requires the same line structure,
identifiers, dimensions, array lengths, and integer values. Binary64 literals
are compared with relative and absolute tolerances of `1e-12`. Exact text is
expected in the declared reference environment, but the tolerance admits
documented last-bit library/interpreter differences.

A Rust test should use a scale-aware comparison no weaker than the tolerance
assigned to each fixture family. Values expected to be exact permutations,
zeros, dimensions, or indices should be compared exactly. NaN/infinity are
encoded as Rust `f64` constants, although current reviewed fixtures are finite.

## Deterministic environment

Generate under the pinned reference dependencies and environment variables in
`reproducibility.md`, including single-thread settings and `PYTHONHASHSEED=0`.
Record Python, NumPy, operating system, architecture, and commit SHA in the
review that proposes a fixture change.

## Safe generation and checking

Normal generation refuses to overwrite an existing path and refuses symbolic
link destinations:

```bash
python oracle_harness.py /tmp/oracle_data.rs
python oracle_harness.py --check tests/fixtures/oracle_data.rs
```

Explicit regeneration is:

```bash
python oracle_harness.py --force /tmp/oracle_data.rs
diff -u tests/fixtures/oracle_data.rs /tmp/oracle_data.rs
```

Only after review may a maintainer explicitly replace the committed fixture.
Routine validation always writes to a temporary new file and never updates the
golden fixture.

## Fixture-change review requirements

A changed fixture must include:

1. the source commit and confirmation that the model revision is still V29.18,
   or an explicit scientific-revision change;
2. a semantic diff grouped by operator/scenario, not merely a new file hash;
3. analytical justification or a documented dependency/environment cause;
4. complete Python tests, V29 summary comparison, and SciRust comparison;
5. reviewer confirmation that expected values were not edited simply to make a
   failing implementation pass;
6. an update to reproducibility and changelog records if dependencies or
   tolerances changed.

Implementation snapshots and analytical expected values must remain labelled
separately. A snapshot change cannot override a contradictory analytical
invariant without resolving the underlying scientific or implementation issue.

## Separate hand-derived analytical oracles

`tests/fixtures/analytical_oracles.json` is a distinct, hand-derived analytical
oracle set (see `docs/research/ANALYTICAL_ORACLES.md`). Unlike `oracle_data.rs`,
its values are derived by hand from the field definitions and are independent of
the Python implementation. A future pure-Rust suite can consume that JSON
without importing any Python-generated numerical output. The two categories must
never be merged: the Rust snapshot is a regression reference; the JSON oracles
are independent analytical expectations.
