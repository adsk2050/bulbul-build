"""Every voice ID a mode names must exist on the live API.

`docs/voices-api.txt` is the list the API itself returned (2026-10-14). Sarvam's
docs page was stale: it named `vetri_ta_*` and `bappa_bn_*`, which the API rejects.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOICE = re.compile(r"\b[a-z]+_(?:hi|en|enhi|mr|bn|gu|pa|ta|te|kn)_[a-z_]+[a-z]\b")


def test_all_mode_voices_exist_on_api():
    api = set((ROOT / "docs" / "voices-api.txt").read_text().split())
    bad = {}
    src = ROOT / "src" / "bulbul_build"
    for path in [*(src / "modes").glob("*.py"), src / "uncle.py"]:
        unknown = {v for v in VOICE.findall(path.read_text(encoding="utf-8")) if v not in api}
        if unknown:
            bad[path.name] = sorted(unknown)
    assert not bad, f"voice IDs the API does not know: {bad}"
