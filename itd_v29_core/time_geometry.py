"""Géométrie temporelle discrète du simulateur ITD V29."""

from __future__ import annotations

import numpy as np


class TemporalGeometry:
    """
    Géométrie temporelle discrète strictement croissante.

    Les instants peuvent être uniformes ou irréguliers.
    Toutes les intégrations utilisent la durée réellement
    observée et les intervalles effectivement fournis.
    """

    __slots__ = (
        "times",
        "interval_dt",
        "sample_count",
        "interval_count",
        "start_time",
        "end_time",
        "duration",
        "minimum_dt",
        "maximum_dt",
        "mean_dt",
        "uniform",
    )

    def __init__(
        self,
        times: object,
    ) -> None:
        if isinstance(
            times,
            (str, bytes),
        ):
            raise ValueError(
                "Les instants doivent former une "
                "séquence numérique."
            )

        try:
            array = np.asarray(
                times,
                dtype=np.float64,
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Les instants doivent former une "
                "séquence numérique réelle."
            ) from error

        if array.ndim != 1:
            raise ValueError(
                "Les instants doivent former un "
                "tableau unidimensionnel."
            )

        if array.size < 2:
            raise ValueError(
                "La simulation exige au moins "
                "deux instants."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(
                "Les instants doivent être finis."
            )

        copied_times = np.array(
            array,
            dtype=np.float64,
            copy=True,
        )

        interval_dt = np.diff(
            copied_times
        )

        if np.any(interval_dt <= 0.0):
            raise ValueError(
                "Les instants doivent être "
                "strictement croissants."
            )

        self.sample_count = int(
            copied_times.size
        )

        self.interval_count = (
            self.sample_count - 1
        )

        self.start_time = float(
            copied_times[0]
        )

        self.end_time = float(
            copied_times[-1]
        )

        self.duration = float(
            self.end_time
            - self.start_time
        )

        if (
            not np.isfinite(self.duration)
            or self.duration <= 0.0
        ):
            raise ValueError(
                "La durée observée doit être finie "
                "et strictement positive."
            )

        self.minimum_dt = float(
            np.min(interval_dt)
        )

        self.maximum_dt = float(
            np.max(interval_dt)
        )

        self.mean_dt = float(
            self.duration
            / self.interval_count
        )

        tolerance = (
            64.0
            * np.finfo(np.float64).eps
            * max(
                1.0,
                abs(self.mean_dt),
            )
        )

        self.uniform = bool(
            np.allclose(
                interval_dt,
                self.mean_dt,
                rtol=1.0e-12,
                atol=tolerance,
            )
        )

        copied_times.setflags(
            write=False
        )

        interval_dt.setflags(
            write=False
        )

        self.times = copied_times
        self.interval_dt = interval_dt

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "interval_count": self.interval_count,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "minimum_dt": self.minimum_dt,
            "maximum_dt": self.maximum_dt,
            "mean_dt": self.mean_dt,
            "uniform": self.uniform,
        }

    def __repr__(self) -> str:
        return (
            "TemporalGeometry("
            f"sample_count={self.sample_count}, "
            f"start_time={self.start_time!r}, "
            f"end_time={self.end_time!r}, "
            f"uniform={self.uniform!r}"
            ")"
        )


def normalize_time_grid(
    times: object,
) -> TemporalGeometry:
    if isinstance(
        times,
        TemporalGeometry,
    ):
        return times

    return TemporalGeometry(times)


