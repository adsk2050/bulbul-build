"""Registry of modes. Each idea lives in its own module and registers here."""

from __future__ import annotations

import importlib
import logging

from .base import Line, Mode, Script

__all__ = ["Line", "Mode", "Script", "REGISTRY", "load_all"]

REGISTRY: dict[str, Mode] = {}

# One module per idea, in report rank order. A module that is not written yet
# is skipped, so ideas can land one at a time.
MODULES = [
    "udhaar_wapas",
    "say_my_name",
    "railway_announcement",
    "shop_diwali_ad",
    "dashanan_roast",
    "family_ivr",
    "cricket_commentary",
    "hinglish_test",
    "bulbul_lab",
]


def load_all() -> dict[str, Mode]:
    for name in MODULES:
        try:
            mod = importlib.import_module(f"{__name__}.{name}")
        except ModuleNotFoundError as e:
            if e.name == f"{__name__}.{name}":
                continue
            raise
        m: Mode = mod.MODE
        REGISTRY[m.slug] = m
    logging.getLogger(__name__).info("modes loaded: %s", list(REGISTRY))
    return REGISTRY
