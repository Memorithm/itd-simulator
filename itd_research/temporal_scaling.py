"""Explicit, dimensionally honest temporal-deformation scaling (post-V29 research).

This module is an isolated *research* API. It is a "post-V29 research candidate"
and must not be read as a new certified scientific revision.

Scope and guarantees
---------------------
* It does **not** modify V29.18 numerical behaviour and is never imported by
  ``itd_v29_core`` (the dependency direction is one-way:
  ``itd_research`` -> ``itd_v29_core``).
* :func:`raw_temporal_deformation` reproduces the V29.18 raw Eulerian temporal
  deformation rate *exactly* (proved in ``tests/test_temporal_scaling.py`` by
  comparison with :func:`itd_v29_core.structural_metrics.structural_metrics`).
  The raw rate is preserved and never silently replaced.
* On top of the preserved raw rate, an **explicit** characteristic time
  ``tau_ref`` is applied to obtain a dimensionless candidate

      ``D_star = tau_ref * D_raw``.

  There is no implicit default characteristic time: it must be supplied
  explicitly or derived by an explicitly selected policy.

Dimensions
----------
The V29.18 raw temporal deformation ``D_raw`` has dimension ``T**-1`` (inverse
time). ``tau_ref`` has dimension ``T``. Therefore ``D_star`` is dimensionless
and is invariant when every time quantity is converted consistently between unit
systems (for example seconds and milliseconds). This module does not claim that
``D_star`` is a universal physical observable; it is a research candidate.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from itd_v29_core.constants import ZERO_THRESHOLD
from itd_v29_core.spatial_operators import spatial_mean, validate_boundary_mode

FloatArray: TypeAlias = NDArray[np.float64]


class TemporalScalePolicy(Enum):
    """Selectable, explicit characteristic-time policies.

    Every policy yields a characteristic time ``tau_ref`` with dimension ``T``.
    None of them is treated as a universal default; the caller must choose one.
    """

    EXTERNAL = "external"
    OBSERVATION_DURATION = "observation_duration"
    TURNOVER = "turnover"
    VORTICITY_TIMESCALE = "vorticity_timescale"


def _require_positive_finite(value: float | None, name: str) -> float:
    """Return ``value`` as a strictly positive finite ``float`` or raise."""
    if value is None:
        raise ValueError(f"{name} must be provided for this policy.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a real number.") from error
    if not np.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive.")
    return result


@dataclass(frozen=True)
class TemporalScaleDefinition:
    """Explicit description of how the characteristic time is obtained.

    Only the fields relevant to ``policy`` are used; the required fields are
    validated by :meth:`resolve`. ``time_unit`` is metadata that records the
    declared time-unit convention (for example ``"s"`` or ``"ms"``); it is never
    used to transform values automatically.

    ``self_referential`` marks a definition whose reference quantity was derived
    from the same field it will scale (for example a vorticity timescale built
    from the field's own RMS vorticity). Such a definition is *not* rejected, but
    the resulting :class:`TemporalDeformationResult` carries an explicit warning
    because the timescale then depends circularly on the field under study.
    """

    policy: TemporalScalePolicy
    characteristic_time: float | None = None
    observation_duration: float | None = None
    reference_length: float | None = None
    reference_velocity: float | None = None
    reference_vorticity: float | None = None
    time_unit: str = "unspecified"
    self_referential: bool = False

    @classmethod
    def from_external(
        cls,
        characteristic_time: float,
        *,
        time_unit: str = "unspecified",
    ) -> TemporalScaleDefinition:
        """Characteristic time supplied directly by the caller."""
        return cls(
            policy=TemporalScalePolicy.EXTERNAL,
            characteristic_time=characteristic_time,
            time_unit=time_unit,
        )

    @classmethod
    def from_observation_duration(
        cls,
        t_initial: float,
        t_final: float,
        *,
        time_unit: str = "unspecified",
    ) -> TemporalScaleDefinition:
        """``tau_ref = t_final - t_initial`` (the observed record length)."""
        try:
            duration = float(t_final) - float(t_initial)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                "t_initial and t_final must be real numbers."
            ) from error
        return cls(
            policy=TemporalScalePolicy.OBSERVATION_DURATION,
            observation_duration=duration,
            time_unit=time_unit,
        )

    @classmethod
    def from_turnover(
        cls,
        reference_length: float,
        reference_velocity: float,
        *,
        time_unit: str = "unspecified",
    ) -> TemporalScaleDefinition:
        """``tau_ref = reference_length / reference_velocity`` (turnover time)."""
        return cls(
            policy=TemporalScalePolicy.TURNOVER,
            reference_length=reference_length,
            reference_velocity=reference_velocity,
            time_unit=time_unit,
        )

    @classmethod
    def from_vorticity_timescale(
        cls,
        reference_vorticity: float,
        *,
        time_unit: str = "unspecified",
        self_referential: bool = False,
    ) -> TemporalScaleDefinition:
        """``tau_ref = 1 / reference_vorticity`` (a declared vorticity timescale).

        Set ``self_referential=True`` when ``reference_vorticity`` was computed
        from the same field that will be scaled.
        """
        return cls(
            policy=TemporalScalePolicy.VORTICITY_TIMESCALE,
            reference_vorticity=reference_vorticity,
            time_unit=time_unit,
            self_referential=self_referential,
        )

    def resolve(self) -> tuple[float, dict[str, float]]:
        """Return ``(tau_ref, reference_values)`` for the selected policy.

        ``reference_values`` records every quantity that entered ``tau_ref`` so
        that the result is fully auditable. Raises :class:`ValueError` when a
        required input is missing, non-finite, or non-positive.
        """
        if self.policy is TemporalScalePolicy.EXTERNAL:
            tau = _require_positive_finite(
                self.characteristic_time, "characteristic_time"
            )
            return tau, {"characteristic_time": tau}

        if self.policy is TemporalScalePolicy.OBSERVATION_DURATION:
            tau = _require_positive_finite(
                self.observation_duration, "observation_duration"
            )
            return tau, {"observation_duration": tau}

        if self.policy is TemporalScalePolicy.TURNOVER:
            length = _require_positive_finite(
                self.reference_length, "reference_length"
            )
            velocity = _require_positive_finite(
                self.reference_velocity, "reference_velocity"
            )
            tau = length / velocity
            return tau, {
                "reference_length": length,
                "reference_velocity": velocity,
                "characteristic_time": tau,
            }

        if self.policy is TemporalScalePolicy.VORTICITY_TIMESCALE:
            vorticity = _require_positive_finite(
                self.reference_vorticity, "reference_vorticity"
            )
            tau = 1.0 / vorticity
            return tau, {
                "reference_vorticity": vorticity,
                "characteristic_time": tau,
            }

        raise ValueError(f"Unknown temporal-scale policy: {self.policy!r}.")


@dataclass(frozen=True)
class TemporalDeformationResult:
    """Fully separated raw and dimensionless temporal-deformation values.

    The raw rate is preserved verbatim alongside the dimensionless candidate so
    that no interpretation silently overrides the underlying V29.18 quantity.
    """

    raw_rate: float
    characteristic_time: float
    dimensionless_deformation: float
    policy: TemporalScalePolicy
    reference_values: Mapping[str, float]
    time_unit: str
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable, deterministically ordered mapping."""
        return {
            "raw_rate": self.raw_rate,
            "characteristic_time": self.characteristic_time,
            "dimensionless_deformation": self.dimensionless_deformation,
            "policy": self.policy.value,
            "reference_values": {
                key: float(self.reference_values[key])
                for key in sorted(self.reference_values)
            },
            "time_unit": self.time_unit,
            "warnings": list(self.warnings),
        }


def raw_temporal_deformation(
    previous_omega: FloatArray,
    current_omega: FloatArray,
    spacing: object,
    delta_time: float,
    boundary_mode: str = "finite",
) -> float:
    """Reproduce the V29.18 raw Eulerian temporal-deformation rate exactly.

    ``D_raw = RMS(current - previous) / (delta_time * mean_endpoint_RMS)`` with
    ``mean_endpoint_RMS = 0.5 * (RMS(current) + RMS(previous))``. When the mean
    endpoint RMS is below the V29.18 zero threshold the rate is defined as zero,
    exactly as in :func:`itd_v29_core.structural_metrics.structural_metrics`.

    The dimension of the returned rate is inverse time.
    """
    boundary_mode = validate_boundary_mode(boundary_mode)

    previous = np.asarray(previous_omega, dtype=np.float64)
    current = np.asarray(current_omega, dtype=np.float64)

    for name, array in (("previous_omega", previous), ("current_omega", current)):
        if array.ndim != 2:
            raise ValueError(f"{name} must be a 2D array.")
        if min(array.shape) < 3:
            raise ValueError(
                f"{name} must contain at least three points per direction."
            )
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} contains a non-finite value.")

    if previous.shape != current.shape:
        raise ValueError("previous_omega and current_omega must share a shape.")

    try:
        dt = float(delta_time)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("delta_time must be a real number.") from error
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("delta_time must be finite and strictly positive.")

    current_rms = np.sqrt(max(spatial_mean(current**2, spacing, boundary_mode), 0.0))
    previous_rms = np.sqrt(
        max(spatial_mean(previous**2, spacing, boundary_mode), 0.0)
    )
    reference_rms = 0.5 * (current_rms + previous_rms)

    if reference_rms < ZERO_THRESHOLD:
        return 0.0

    difference_rms = np.sqrt(
        max(spatial_mean((current - previous) ** 2, spacing, boundary_mode), 0.0)
    )
    return float(difference_rms / (dt * reference_rms))


def scale_temporal_deformation(
    raw_rate: float,
    definition: TemporalScaleDefinition,
) -> TemporalDeformationResult:
    """Apply an explicit characteristic time to a preserved raw rate.

    ``raw_rate`` must be a finite, non-negative inverse-time value (the V29.18
    raw temporal-deformation rate is a non-negative RMS ratio). The returned
    result exposes the raw rate, the characteristic time, the dimensionless
    candidate ``D_star = tau_ref * raw_rate``, the selected policy, all reference
    values, the declared time unit, and any warnings.
    """
    try:
        rate = float(raw_rate)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("raw_rate must be a real number.") from error
    if not np.isfinite(rate):
        raise ValueError("raw_rate must be finite.")
    if rate < 0.0:
        raise ValueError("raw_rate must be non-negative.")

    tau, reference_values = definition.resolve()
    dimensionless = tau * rate
    if not np.isfinite(dimensionless):
        raise ValueError(
            "dimensionless deformation exceeds the finite numeric range."
        )

    warnings: list[str] = []
    if rate == 0.0:
        warnings.append(
            "raw rate is zero; dimensionless deformation is zero regardless of "
            "the characteristic time."
        )
    if definition.self_referential:
        warnings.append(
            "characteristic time is derived from the field under study; the "
            "dimensionless value depends circularly on that field."
        )

    return TemporalDeformationResult(
        raw_rate=rate,
        characteristic_time=tau,
        dimensionless_deformation=dimensionless,
        policy=definition.policy,
        reference_values=reference_values,
        time_unit=definition.time_unit,
        warnings=tuple(warnings),
    )


def temporal_deformation_from_fields(
    previous_omega: FloatArray,
    current_omega: FloatArray,
    spacing: object,
    delta_time: float,
    definition: TemporalScaleDefinition,
    boundary_mode: str = "finite",
) -> TemporalDeformationResult:
    """Compute the raw rate from two fields and scale it with ``definition``.

    Convenience wrapper combining :func:`raw_temporal_deformation` and
    :func:`scale_temporal_deformation`.
    """
    rate = raw_temporal_deformation(
        previous_omega,
        current_omega,
        spacing,
        delta_time,
        boundary_mode,
    )
    return scale_temporal_deformation(rate, definition)
