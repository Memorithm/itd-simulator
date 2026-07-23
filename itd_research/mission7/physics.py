"""Physical validation of ingested external fields (Mission 7, H50).

Predictive claims are only made on data that first passes physical consistency. For an
isotropic-turbulence DNS cutout the strongest ingestion-correctness check is that the
field is (nearly) **solenoidal** -- a small relative divergence confirms the coordinate,
unit and axis conventions were interpreted correctly. Component isotropy, ``urms`` range
and energy stationarity are reported too, but a small sub-box is not expected to be
globally isotropic or stationary; those are described honestly, not forced to pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_research.diagnostics_3d.operators import velocity_gradient_3d
from itd_research.mission7.ingestion import Frame

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class PhysicalValidation:
    """Physical-consistency summary for an external DNS sequence."""

    component_urms: tuple[float, float, float]
    isotropy_spread: float          # (max-min)/mean of per-component urms
    divergence_relative: float      # <|div u|> / (urms/dx)
    energy_mean: float
    energy_cov: float               # std/mean across frames (stationarity proxy)
    solenoidal_ok: bool
    urms_in_range: bool
    verdict: str

    def as_dict(self) -> dict[str, object]:
        return {
            "component_urms": list(self.component_urms),
            "isotropy_spread": self.isotropy_spread,
            "divergence_relative": self.divergence_relative,
            "energy_mean": self.energy_mean,
            "energy_cov": self.energy_cov,
            "solenoidal_ok": self.solenoidal_ok,
            "urms_in_range": self.urms_in_range,
            "verdict": self.verdict,
        }


def validate_isotropic_dns(
    frames: list[Frame], *, divergence_rel_tol: float = 0.30,
    urms_low: float = 0.3, urms_high: float = 1.2,
) -> PhysicalValidation:
    """Validate an isotropic-DNS cutout sequence.

    ``solenoidal_ok`` (relative divergence below tolerance) is the decisive
    ingestion-correctness check; ``urms_in_range`` is a sanity band. Isotropy spread and
    energy variability are reported descriptively (a small cutout is not globally
    isotropic/stationary). The verdict is ``supported`` only if the field is solenoidal
    and ``urms`` is in range; otherwise ``partially supported`` / ``not supported``.
    """
    urms_frames = []
    div_rels = []
    energies = []
    for fr in frames:
        urms = [float(np.sqrt(np.mean(c**2))) for c in (fr.u, fr.v, fr.w)]
        urms_frames.append(urms)
        grad = velocity_gradient_3d(fr.u, fr.v, fr.w, fr.x, fr.y, fr.z, "finite")
        div = grad[..., 0, 0] + grad[..., 1, 1] + grad[..., 2, 2]
        dx = float(fr.x[1] - fr.x[0]) if fr.x.size >= 2 else 1.0
        scale = max(float(np.mean(urms)) / dx, 1e-12)
        div_rels.append(float(np.mean(np.abs(div)) / scale))
        energies.append(0.5 * float(np.mean(fr.u**2 + fr.v**2 + fr.w**2)))
    urms_mean = np.mean(np.asarray(urms_frames), axis=0)
    isotropy_spread = float((urms_mean.max() - urms_mean.min()) / max(urms_mean.mean(), 1e-12))
    divergence_relative = float(np.mean(div_rels))
    energy = np.asarray(energies)
    energy_mean = float(energy.mean())
    energy_cov = float(energy.std() / max(energy.mean(), 1e-12))
    solenoidal_ok = divergence_relative <= divergence_rel_tol
    mean_urms = float(urms_mean.mean())
    urms_in_range = urms_low <= mean_urms <= urms_high
    if solenoidal_ok and urms_in_range:
        verdict = "supported within tested scope"
    elif solenoidal_ok or urms_in_range:
        verdict = "partially supported"
    else:
        verdict = "not supported"
    return PhysicalValidation(
        component_urms=(float(urms_mean[0]), float(urms_mean[1]), float(urms_mean[2])),
        isotropy_spread=isotropy_spread, divergence_relative=divergence_relative,
        energy_mean=energy_mean, energy_cov=energy_cov, solenoidal_ok=solenoidal_ok,
        urms_in_range=urms_in_range, verdict=verdict,
    )
