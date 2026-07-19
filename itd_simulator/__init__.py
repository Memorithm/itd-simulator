"""Public package namespace for software release 0.2.0."""

from __future__ import annotations

import itd_v29 as _facade
from itd_v29 import *  # noqa: F403 - deliberate compatibility re-export

__version__ = "0.2.0"
SCIENTIFIC_MODEL_REVISION = "ITD V29.18"

__all__ = (
    *_facade.__all__,
    "__version__",
    "SCIENTIFIC_MODEL_REVISION",
)
