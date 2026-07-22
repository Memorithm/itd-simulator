"""Optional plotting boundary for the post-V29 research package.

This module is the only place that imports Matplotlib, and it does so lazily
inside :func:`render_plots` so that importing ``itd_research`` never initialises a
plotting backend. Plotting is strictly separated from computation: it consumes
already-computed result dictionaries and writes PNG files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def render_plots(
    convergence: dict[str, Any],
    sensitivity: dict[str, Any],
    directory: Path,
) -> list[Path]:
    """Render research figures to ``directory`` and return the written paths.

    Matplotlib is imported here (not at module import time) and forced onto the
    non-interactive ``Agg`` backend.
    """
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    written: list[Path] = []
    columns = list(convergence["columns"])
    rows = list(convergence["rows"])
    study_index = columns.index("study")
    spacing_index = columns.index("spacing")
    error_index = columns.index("absolute_error")

    studies: dict[str, list[tuple[float, float]]] = {}
    for row in rows:
        study = str(row[study_index])
        spacing = float(row[spacing_index])
        error = float(row[error_index])
        if error > 0.0:
            studies.setdefault(study, []).append((spacing, error))

    if studies:
        figure, axis = plt.subplots(figsize=(8, 6))
        for study, points in sorted(studies.items()):
            points.sort()
            spacings = [item[0] for item in points]
            errors = [item[1] for item in points]
            axis.loglog(spacings, errors, marker="o", label=study)
        axis.set_xlabel("grid spacing h")
        axis.set_ylabel("absolute error")
        axis.set_title("Grid convergence (post-V29 research)")
        axis.grid(True, which="both", linewidth=0.3)
        axis.legend()
        figure.tight_layout()
        convergence_path = directory / "convergence_errors.png"
        figure.savefig(convergence_path, dpi=150)
        plt.close(figure)
        written.append(convergence_path)

    sensitivity_rows = list(sensitivity["rows"])
    structural = [
        (float(row[3]), float(row[5]))
        for row in sensitivity_rows
        if row[0] == "structural_length" and row[4] == "raw_roughness"
    ]
    if structural:
        structural.sort()
        figure, axis = plt.subplots(figsize=(8, 6))
        lengths = [item[0] for item in structural]
        values = [item[1] for item in structural]
        axis.plot(lengths, values, marker="s")
        axis.set_xlabel("structural length ell_s")
        axis.set_ylabel("raw roughness")
        axis.set_title("Raw roughness is linear in ell_s")
        axis.grid(True, linewidth=0.3)
        figure.tight_layout()
        structural_path = directory / "structural_length_linearity.png"
        figure.savefig(structural_path, dpi=150)
        plt.close(figure)
        written.append(structural_path)

    return written
