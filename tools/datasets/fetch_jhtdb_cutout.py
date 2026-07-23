#!/usr/bin/env python3
"""Fetch a small 3D velocity cutout from the JHU Turbulence Database (JHTDB).

This is a **user-run preparation tool**, not part of the ``itd_research`` package
and never executed in CI. It queries the public JHTDB ``GetVelocity`` SOAP web
service on a regular block of native grid nodes and writes the result as the
NumPy-only ``.npz`` field format that :func:`itd_research.io.read_npz_field_3d`
reads. It uses only the Python standard library (``urllib``), so no SOAP/HDF5
dependency is added to the project.

JHTDB is an external DNS database (not ITD); a cutout obtained with this tool is
genuine independent 3D CFD data. Respect the JHTDB terms of use and citation
policy (https://turbulence.pha.jhu.edu). The public testing token
``edu.jhu.pha.turbulence.testing-201406`` permits small queries; use your own
token for anything larger.

Example
-------
    python tools/datasets/fetch_jhtdb_cutout.py \
        --dataset isotropic1024coarse --origin 200 300 400 --size 24 \
        --output jhtdb_iso_24.npz
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np

_ENDPOINT = "https://turbulence.pha.jhu.edu/service/turbulence.asmx"
_NS = "http://turbulence.pha.jhu.edu/"
_TEST_TOKEN = "edu.jhu.pha.turbulence.testing-201406"
_DEFAULT_SPACING = 2.0 * np.pi / 1024.0  # native spacing of isotropic1024coarse
_VECTOR = re.compile(r"<Vector3><x>([^<]+)</x><y>([^<]+)</y><z>([^<]+)</z></Vector3>")


def _soap_envelope(token: str, dataset: str, time: float, spatial: str,
                   points: list[tuple[float, float, float]]) -> bytes:
    body = "".join(
        f"<Point3><x>{px:.9f}</x><y>{py:.9f}</y><z>{pz:.9f}</z></Point3>"
        for px, py, pz in points
    )
    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        f'<soap:Body><GetVelocity xmlns="{_NS}">'
        f"<authToken>{token}</authToken><dataset>{dataset}</dataset>"
        f"<time>{time}</time>"
        f"<spatialInterpolation>{spatial}</spatialInterpolation>"
        "<temporalInterpolation>None</temporalInterpolation>"
        f"<points>{body}</points><addr></addr>"
        "</GetVelocity></soap:Body></soap:Envelope>"
    )
    return envelope.encode("utf-8")


def _post(payload: bytes) -> str:
    request = urllib.request.Request(
        _ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{_NS}GetVelocity"',
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - explicit
        text = response.read().decode("utf-8")
    if "<soap:Fault>" in text or "<faultstring>" in text:
        fault = re.search(r"<faultstring>(.*?)</faultstring>", text, re.S)
        raise SystemExit(f"JHTDB fault: {fault.group(1)[:300] if fault else text[:300]}")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="isotropic1024coarse")
    parser.add_argument("--token", default=_TEST_TOKEN)
    parser.add_argument("--time", type=float, default=0.0)
    parser.add_argument("--origin", nargs=3, type=int, default=[200, 300, 400],
                        metavar=("IX", "IY", "IZ"), help="node mode: start node indices")
    parser.add_argument("--size", type=int, default=24, help="node mode: cube edge in nodes")
    parser.add_argument("--spacing", type=float, default=_DEFAULT_SPACING)
    parser.add_argument("--coords", nargs=3, type=float, default=None,
                        metavar=("X0", "Y0", "Z0"),
                        help="physical mode: box origin in dataset coordinates")
    parser.add_argument("--extent", nargs=3, type=float, default=None,
                        metavar=("LX", "LY", "LZ"), help="physical mode: box extents")
    parser.add_argument("--shape", nargs=3, type=int, default=None,
                        metavar=("NX", "NY", "NZ"), help="physical mode: points per axis")
    parser.add_argument("--spatial", default=None,
                        help="spatial interpolation (default: None for node mode, Lag6 for physical)")
    parser.add_argument("--chunk", type=int, default=4096, help="max points per request")
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true")
    arguments = parser.parse_args(argv)

    output = Path(arguments.output)
    if output.exists() and not arguments.overwrite:
        raise SystemExit(f"refusing to overwrite {output} (use --overwrite)")

    physical = arguments.coords is not None
    spatial = arguments.spatial or ("Lag6" if physical else "None")
    if physical:
        if arguments.extent is None or arguments.shape is None:
            raise SystemExit("physical mode needs --coords, --extent, and --shape")
        nx, ny, nz = arguments.shape
        x = np.linspace(arguments.coords[0], arguments.coords[0] + arguments.extent[0], nx)
        y = np.linspace(arguments.coords[1], arguments.coords[1] + arguments.extent[1], ny)
        z = np.linspace(arguments.coords[2], arguments.coords[2] + arguments.extent[2], nz)
        spacing = float("nan")
    else:
        nx = ny = nz = int(arguments.size)
        ix, iy, iz = arguments.origin
        spacing = float(arguments.spacing)
        x = (ix + np.arange(nx)) * spacing
        y = (iy + np.arange(ny)) * spacing
        z = (iz + np.arange(nz)) * spacing

    # points ordered z-outer, y, x-inner to match (nz, ny, nx) reshape
    points = [(float(px), float(py), float(pz)) for pz in z for py in y for px in x]
    values: list[tuple[str, str, str]] = []
    for start in range(0, len(points), arguments.chunk):
        batch = points[start:start + arguments.chunk]
        text = _post(_soap_envelope(arguments.token, arguments.dataset,
                                    arguments.time, spatial, batch))
        found = _VECTOR.findall(text)
        if len(found) != len(batch):
            raise SystemExit(f"expected {len(batch)} vectors, parsed {len(found)}")
        values.extend(found)
        print(f"  fetched {start + len(batch)}/{len(points)} points", file=sys.stderr)

    array = np.array(values, dtype=np.float64).reshape(nz, ny, nx, 3)
    if not np.all(np.isfinite(array)):
        raise SystemExit("received a non-finite velocity value")
    u, v, w = array[..., 0], array[..., 1], array[..., 2]
    np.savez(output, x=x.astype(np.float64), y=y.astype(np.float64),
             z=z.astype(np.float64), u=u, v=v, w=w)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    rms = float(np.sqrt(np.mean(u**2 + v**2 + w**2) / 3.0))
    print(f"wrote {output}  shape=({nz},{ny},{nx})  spatial={spatial}  component_rms={rms:.4f}")
    print(f"dataset={arguments.dataset} time={arguments.time}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
