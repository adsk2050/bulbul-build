"""What every idea ("mode") provides.

A mode turns a validated form into a script: a list of lines, each with its
own text, language and voice. The server synthesises the lines, joins them and
returns the audio plus card text. Modes never call HTTP themselves; they get
the shared `Sarvam` client, so every paid call is in the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from pydantic import BaseModel

from ..sarvam import Sarvam


# Unicode block per language, for checking that LLM output is in the right script.
SCRIPT_BLOCKS = {
    "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F), "enhi": (0x0900, 0x097F),
    "bn": (0x0980, 0x09FF), "pa": (0x0A00, 0x0A7F), "gu": (0x0A80, 0x0AFF),
    "ta": (0x0B80, 0x0BFF), "te": (0x0C00, 0x0C7F), "kn": (0x0C80, 0x0CFF),
}


def script_share(text: str, lang: str) -> float:
    """Fraction of letters in `text` that are in `lang`'s own script (Latin for "en")."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    if lang == "en":
        return sum(c.isascii() for c in letters) / len(letters)
    lo, hi = SCRIPT_BLOCKS[lang]
    return sum(lo <= ord(c) <= hi for c in letters) / len(letters)


@dataclass
class Line:
    text: str
    language: str  # e.g. "hi-IN"
    speaker: str  # a bulbul:v4-flash voice ID
    pace: float = 1.0
    caption: str | None = None  # shown on the card; defaults to text


@dataclass
class Script:
    lines: list[Line]
    title: str
    share_text: str  # pre-filled message for WhatsApp / X
    card: dict[str, Any] = field(default_factory=dict)  # mode-specific card fields
    phone_line: bool = False  # also render the 8 kHz phone version


@dataclass
class Mode:
    slug: str
    name: str
    tagline: str
    form: type[BaseModel]
    build: Callable[[BaseModel, Sarvam], Awaitable[Script]]
    uses_llm: bool = False
