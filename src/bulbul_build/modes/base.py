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
