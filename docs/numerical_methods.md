# Numerical methods — ITD V29.18

## Arrays and axes

All core calculations convert numeric inputs to NumPy `float64`. Scalar and
vector component fields are two-dimensional arrays with shape `(ny, nx)`:
axis 0 is y, axis 1 is x. Cartesian mesh arrays use `meshgrid(...,
indexing="xy")`. Integer inputs are accepted only through an explicit conversion
to `float64`; outputs are floating point.

## Spatial geometry and boundaries

Uniform geometry may be given as one positive spacing or `(dx, dy)`.
Rectilinear finite geometry uses strictly increasing one-dimensional x and y
coordinate arrays with at least three points. Mesh coordinates must match the
declared geometry.

`finite` mode uses NumPy second-order edge gradients (`edge_order=2`) and
trapezoidal quadrature divided by domain area. A uniform finite grid includes
both endpoints. A rectilinear grid may be nonuniform.

`periodic` mode requires uniform endpoint-excluded axes. Gradients are centered
circular differences implemented with `numpy.roll`; the spatial mean is the
arithmetic mean. Repeating the terminal endpoint would double-count a periodic
node and is not supported by the convention.

At least three nodes per direction are required by vorticity, gradients, and
structural metrics. Cubic periodic interpolation requires at least four.

## Time discretization

Times are finite, one-dimensional, contain at least two samples, and are
strictly increasing. Uniform and nonuniform time grids are accepted. Intensity
uses trapezoidal time integration divided by the observed duration.

Temporal deformation belongs to intervals rather than nodes. Four spatial
components are trapezoidally averaged from adjacent nodes; deformation is used
directly on its interval. All final component and structural indices are
weighted by the actual interval durations. Interpolated nodal deformation and
score series are for CSV/plot presentation and are not used to calculate the
reported indices.

## Periodic transport

Semi-Lagrangian transport computes departure points from current nodes. The
available trajectory rules are midpoint-time velocity and RK4 backtrace. Each
stage wraps coordinates into the periodic domain.

Interpolation choices are:

- periodic bilinear interpolation;
- tensor-product four-point cubic Lagrange interpolation;
- cubic interpolation blended back into local bilinear bounds;
- that locally bounded result with a bounded redistribution restoring the
  cubic result's discrete sum.

Interpolation at an exact node agrees with the node value to the declared
floating-point tolerance. A translation by an integer number of full periods is
recognized as an exact index permutation in backtrace paths. The bounded
variant is constrained by the four surrounding bilinear node extrema. The
sum-preserving variant preserves its declared target within floating-point
roundoff; it is not a general conservation law for arbitrary dynamics.

Finite-boundary transport compensation is intentionally unavailable because no
scientifically neutral outside-domain fill convention has been selected.

## Geometric interpolation

`BilinearTransformPlan` validates a real orthogonal 2×2 matrix and uniform
coordinate axes. Node-aligned symmetries use an exact index map. Other
transformations use bilinear interpolation and an explicit finite-domain fill
value (zero by default). Results near a finite boundary depend on that fill
choice.

## Material derivative

On an interval, temporal tendency is `(current - previous) / dt`. The gradient
is taken from the midpoint vorticity, and midpoint velocity supplies
`u · grad(omega)`. Each term's RMS is normalized by the arithmetic mean of the
endpoint vorticity RMS values. If that reference is below `1e-12`, the
normalized rate is defined as zero.

## Floating-point contract and limitations

The declared type is IEEE-754 binary64 (`numpy.float64`). Operation ordering,
library versions, BLAS configuration, platform math functions, and CPU may
change last bits. Bitwise determinism is claimed only for repeated independent
processes in the same locked environment. Cross-version certification uses
explicit tolerances.

The exponential curvature weight is rejected if it becomes non-finite. Inputs
with NaN or infinity, inconsistent shapes, nonpositive spacing, nonmonotonic
coordinates, or nonpositive time intervals are rejected by applicable public
contracts. The mathematical core has no arbitrary grid-size cap; callers must
apply resource policy appropriate to their environment.
