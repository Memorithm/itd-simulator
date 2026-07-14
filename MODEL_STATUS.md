# ITD Simulator — Model Status

Current published snapshot: ITD V29.7.

- Constants, temporal geometry and spatial geometry remain modularized.
- Orthogonal transforms, rotations and bilinear transform plans moved to `itd_v29_core/geometric_transforms.py`.
- Historical public imports remain available from `itd_v29`.
- Main numerical summary remains identical bit for bit.
- Arbitrary rotations, D4 invariance and exact permutation cases passed.
- The published snapshot is source-clean and contains no Python bytecode cache.
- Certification is relative to the declared validation suite.
