"""Deterministic synthetic field sequence for OFFLINE ci (Mission 7).

This writes a tiny, fully synthetic 3D velocity sequence so the external-evidence pipeline
can be exercised without any network access. It is a CODE-VERIFICATION fixture ONLY and is
NEVER external empirical evidence -- the preregistration forbids presenting it as such. The
field is a decaying Taylor-Green-like flow with a controlled enstrophy bump so the
event/prediction path has both classes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def write_synthetic_sequence(directory: str | Path, *, nodes: int = 12, n_frames: int = 12) -> Path:
    """Write ``n_frames`` synthetic ``frame_*.npz`` files; return the directory."""
    base = Path(directory)
    base.mkdir(parents=True, exist_ok=True)
    length = 2.0 * np.pi
    coords = np.linspace(0.0, length, nodes, endpoint=False)
    x = coords[None, None, :]
    y = coords[None, :, None]
    z = coords[:, None, None]
    for i in range(n_frames):
        t = 0.1 * i
        # Decaying Taylor-Green with a late-sequence amplitude bump (controlled enstrophy)
        # so the locked temporal holdout contains both event and non-event frames.
        center = int(round(n_frames * 0.72))
        bump = 1.0 + 0.8 * np.exp(-((i - center) ** 2) / 4.0)
        decay = np.exp(-0.05 * t)
        amp = bump * decay
        u = amp * np.sin(x) * np.cos(y) * np.cos(z)
        v = -0.5 * amp * np.cos(x) * np.sin(y) * np.cos(z)
        w = -0.5 * amp * np.cos(x) * np.cos(y) * np.sin(z)
        u = np.broadcast_to(u, (nodes, nodes, nodes)).astype(np.float64)
        v = np.broadcast_to(v, (nodes, nodes, nodes)).astype(np.float64)
        w = np.broadcast_to(w, (nodes, nodes, nodes)).astype(np.float64)
        path = base / f"frame_{i:02d}.npz"
        np.savez(
            path, x=coords.astype(np.float64), y=coords.astype(np.float64),
            z=coords.astype(np.float64), u=u, v=v, w=w, time=np.array([t], dtype=np.float64),
        )
    return base
