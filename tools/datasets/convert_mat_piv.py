#!/usr/bin/env python3
"""Convert a MATLAB v5 PIV/CFD velocity file to the native ``.npz`` field format.

This is a **user-run preparation tool**, not part of the ``itd_research`` package
and never executed in CI. It exists so that an external ``.mat`` velocity field
(e.g. a downloaded PIV dataset) can be turned once into the NumPy-only ``.npz``
layout that :func:`itd_research.io.read_npz_field_2d` reads. The package itself
stays NumPy-only; only this optional converter uses SciPy, and only for reading
the legacy MAT-5 container (which is a plain binary format, not Python pickle).

It reads named 2D ``U`` / ``V`` arrays and 1D ``x`` / ``y`` coordinate arrays,
optionally crops and/or strides them, rescales coordinates to a target length
unit, builds a validity mask from finite values, and writes ``x, y, u, v`` (and
``mask`` when any vector is invalid) into an ``.npz``. The SHA-256 of the output
is printed so it can be recorded in ``datasets/registry.json``.

Example
-------
    python tools/datasets/convert_mat_piv.py \
        --input velocity_fields.mat --output piv.npz \
        --u-var u_means_msec --v-var v_means_msec \
        --x-var x_mm --y-var y_mm --length-scale 1e-3 \
        --length-unit m --velocity-unit m/s

SciPy is imported lazily; if it is absent the script explains how to install it
without making it a dependency of the package.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np


def _load_mat(path: Path) -> dict[str, np.ndarray]:
    try:
        from scipy.io import loadmat
    except ModuleNotFoundError:  # pragma: no cover - user-run tool
        print(
            "This converter needs SciPy to read MATLAB v5 files. Install it in a\n"
            "throwaway environment (it is not a dependency of itd_research):\n"
            "    python -m pip install scipy\n",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    if path.is_symlink():
        raise SystemExit(f"refusing to read a symlink: {path}")
    # squeeze_me collapses singleton dims; struct_as_record avoids object arrays.
    return loadmat(str(path), squeeze_me=True, struct_as_record=True)


def _get_2d(mat: dict[str, np.ndarray], name: str) -> np.ndarray:
    if name not in mat:
        raise SystemExit(f"variable {name!r} not found; have {sorted(mat)}")
    array = np.asarray(mat[name], dtype=np.float64)
    if array.ndim != 2:
        raise SystemExit(f"{name!r} must be 2D, got shape {array.shape}")
    return array


def _get_1d(mat: dict[str, np.ndarray], name: str) -> np.ndarray:
    if name not in mat:
        raise SystemExit(f"variable {name!r} not found; have {sorted(mat)}")
    return np.asarray(mat[name], dtype=np.float64).ravel()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--u-var", required=True)
    parser.add_argument("--v-var", required=True)
    parser.add_argument("--x-var", required=True)
    parser.add_argument("--y-var", required=True)
    parser.add_argument("--length-scale", type=float, default=1.0,
                        help="multiply coordinates by this to reach the target unit")
    parser.add_argument("--length-unit", default="m")
    parser.add_argument("--velocity-unit", default="m/s")
    parser.add_argument("--source", default="")
    parser.add_argument("--crop", nargs=4, type=int, metavar=("R0", "R1", "C0", "C1"),
                        help="row/col half-open crop [R0:R1, C0:C1] before striding")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true")
    arguments = parser.parse_args(argv)

    output = Path(arguments.output)
    if output.exists() and not arguments.overwrite:
        raise SystemExit(f"refusing to overwrite {output} (use --overwrite)")

    mat = _load_mat(Path(arguments.input))
    u = _get_2d(mat, arguments.u_var)
    v = _get_2d(mat, arguments.v_var)
    x = _get_1d(mat, arguments.x_var) * arguments.length_scale
    y = _get_1d(mat, arguments.y_var) * arguments.length_scale
    if u.shape != v.shape:
        raise SystemExit(f"U {u.shape} and V {v.shape} shapes differ")
    if u.shape != (y.size, x.size):
        raise SystemExit(f"U shape {u.shape} does not match (y={y.size}, x={x.size})")

    if arguments.crop is not None:
        r0, r1, c0, c1 = arguments.crop
        u, v = u[r0:r1, c0:c1], v[r0:r1, c0:c1]
        y, x = y[r0:r1], x[c0:c1]
    stride = max(1, arguments.stride)
    u, v = u[::stride, ::stride], v[::stride, ::stride]
    y, x = y[::stride], x[::stride]

    if x.size < 3 or y.size < 3:
        raise SystemExit("after crop/stride fewer than three points remain on an axis")
    if not (np.all(np.diff(x) > 0) and np.all(np.diff(y) > 0)):
        raise SystemExit("coordinates must be strictly increasing after processing")

    valid = np.isfinite(u) & np.isfinite(v)
    arrays: dict[str, np.ndarray] = {
        "x": x.astype(np.float64),
        "y": y.astype(np.float64),
        "u": np.where(valid, u, np.nan).astype(np.float64),
        "v": np.where(valid, v, np.nan).astype(np.float64),
    }
    if not bool(np.all(valid)):
        arrays["mask"] = valid
    np.savez(output, **arrays)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"wrote {output}  shape=(ny={y.size}, nx={x.size})  "
          f"valid={int(valid.sum())}/{valid.size}")
    print(f"length_unit={arguments.length_unit} velocity_unit={arguments.velocity_unit}"
          f" source={arguments.source!r}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
