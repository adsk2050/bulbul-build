"""Yaatri Kripya Dhyan Dein: a station announcement about your late friend.

Read three times, like a real Indian station: Hindi, then English, then one
regional language. Hindi and English come from hand-written templates (free,
exact). The regional version is written by sarvam-105b from the English
template, with structured output, and is dropped if it comes back wrong.

Train numbers are read digit by digit, as announcers do ("एक दो नौ पाँच एक").
How the digits are written for TTS is set in one place: `NUMBER_STYLE`.
"""

from __future__ import annotations

import hashlib
import logging
import random
import re
from typing import Literal

from pydantic import BaseModel, Field

from ..sarvam import Sarvam, SarvamError
from .base import Line, Mode, Script

log = logging.getLogger(__name__)

# How train numbers are written in the Hindi and English templates.
#   "words":  "एक दो नौ पाँच एक" / "one two nine five one"  (no guessing by the TTS)
#   "spaced": "1 2 9 5 1"  (leaves digit reading to Bulbul's normaliser)
# The regional prompt always uses the spaced form, so the check below can find it.
NUMBER_STYLE: Literal["words", "spaced"] = "words"

DIGIT_WORDS = {
    "hi": ["शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ"],
    "en": ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"],
}

HI = ("hi-IN", "shreya_hi_news")
EN = ("en-IN", "shubh_en_narration")
PACE = 0.95  # announcers speak a touch slower than conversation

Regional = Literal["mr", "bn", "gu", "pa", "ta", "te", "kn"]
REGIONAL: dict[str, tuple[str, str]] = {
    # key: (language_code, voice)
    "mr": ("mr-IN", "mrunal_mr_narration"),
    "bn": ("bn-IN", "roopa_bn_conversational"),
    "gu": ("gu-IN", "pooja_gu_customer"),
    "pa": ("pa-IN", "harpreet_pa_narration"),
    "ta": ("ta-IN", "vijay_ta_narration"),
    "te": ("te-IN", "kavitha_te_narration"),
    "kn": ("kn-IN", "chaitra_kn_narration"),
}
LANG_NAMES = {
    "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi",
    "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
}

ONE_LINE = r"^[^\r\n]+$"  # user text goes into a numbered LLM prompt


class Form(BaseModel):
    friend: str = Field(title="Friend's name", min_length=1, max_length=25, pattern=ONE_LINE, examples=["Rahul"])
    origin: str = Field(title="From", min_length=1, max_length=25, pattern=ONE_LINE, examples=["Bed"])
    destination: str = Field(title="To", min_length=1, max_length=25, pattern=ONE_LINE, examples=["Office"])
    late_minutes: int = Field(default=180, title="How late (minutes)", ge=1, le=2880, examples=[180])
    late_for: str = Field(
        default="", title="Late for what?", max_length=40, pattern=r"^[^\r\n]*$",
        description="Optional, e.g. your birthday party", examples=["Garba night"],
    )
    platform: int = Field(default=4, title="Platform number", ge=1, le=20)
    train_number: str = Field(
        default="", title="Train number", pattern=r"^$|^\d{5}$",
        description="Optional, 5 digits. Left blank, one is made from the name.",
    )
    regional: Regional = Field(default="mr", title="Third language", json_schema_extra={"x-labels": LANG_NAMES})


def train_number(f: Form) -> str:
    """The form's number, or a stable one from the name (so repeat requests hit the TTS cache)."""
    if f.train_number:
        return f.train_number
    h = int(hashlib.sha256(f.friend.strip().lower().encode()).hexdigest(), 16)
    return f"1{h % 10000:04d}"


def say_digits(num: str, lang: str, style: str | None = None) -> str:
    style = style or NUMBER_STYLE
    if style == "words" and lang in DIGIT_WORDS:
        return " ".join(DIGIT_WORDS[lang][int(d)] for d in num)
    return " ".join(num)


def delay(minutes: int, lang: str) -> str:
    h, m = divmod(minutes, 60)
    if lang == "hi":
        parts = ([f"{h} घंटे"] if h else []) + ([f"{m} मिनट"] if m else [])
        return " ".join(parts)
    parts = ([f"{h} hour" + ("s" if h != 1 else "")] if h else []) + (
        [f"{m} minute" + ("s" if m != 1 else "")] if m else []
    )
    return " ".join(parts)


PUNCHLINES = {
    "hi": [
        "यात्रियों को हुई असुविधा के लिए {friend} को बिल्कुल भी खेद नहीं है।",
        "{friend} एक्सप्रेस की ओर से संदेश आया है: बस पाँच मिनट।",
        "यात्रियों से अनुरोध है कि {friend} एक्सप्रेस के समय पर आने की उम्मीद न रखें।",
    ],
    "en": [
        "{friend} regrets nothing about the inconvenience caused to passengers.",
        "A message from {friend} Express reads: just five more minutes.",
        "Passengers are requested not to expect {friend} Express on time, today or ever.",
    ],
}


def template(f: Form, lang: str, punch: int, num: str) -> list[str]:
    """One announcement, kept short so all three languages fit in ~30 s.

    `num` is the train number already written for speech or display.
    Hindi: attention, the train line, punchline. English: train line, punchline.
    """
    name, src, dst, why = f.friend.strip(), f.origin.strip(), f.destination.strip(), f.late_for.strip()
    if lang == "en":
        reason = f" for {why}" if why else ""
        return [
            f"Attention please. Train number {num}, {name} Express from {src} to {dst}, "
            f"is running {delay(f.late_minutes, 'en')} late{reason}.",
            PUNCHLINES["en"][punch].format(friend=name),
        ]
    reason = f"{why} के लिए " if why else ""
    return [
        "यात्रीगण कृपया ध्यान दें।",
        f"गाड़ी संख्या {num}, {src} से {dst} जाने वाली {name} एक्सप्रेस, "
        f"{reason}{delay(f.late_minutes, 'hi')} की देरी से प्लेटफ़ॉर्म {f.platform} पर आएगी।",
        PUNCHLINES["hi"][punch].format(friend=name),
    ]


def restore_names(text: str, names: list[str]) -> str:
    """Put user-typed names back with their exact spelling (the model sometimes lowercases them)."""
    for n in sorted({n for n in names if n}, key=len, reverse=True):
        text = re.sub(re.escape(n), lambda _m, n=n: n, text, flags=re.IGNORECASE)
    return text


class Translated(BaseModel):
    lines: list[str] = Field(description="One translated line per input line, same order")


SYSTEM = (
    "You translate a funny Indian railway station announcement into an Indian language, for a "
    "text-to-speech voice. Write it the way that language's station announcements sound, formal and "
    "official, so the joke lands. Use the target language's own script. Keep people's names and place "
    "names in Latin script, copied exactly as given, with the same capital letters. "
    "The train number is written as digits separated by "
    "spaces (like 1 2 9 5 1): copy it exactly, with the spaces. Keep other numbers as digits. "
    "Return exactly one output line per input line."
)

MAX_REGIONAL_CHARS = 600  # the English source is ~200 chars; anything far longer is the model rambling


async def regional_lines(f: Form, punch: int, num: str, sarvam: Sarvam) -> list[str] | None:
    """The regional announcement, or None if the model's output cannot be trusted."""
    spaced = say_digits(num, "en", "spaced")
    src = template(f, "en", punch, spaced)
    user = f"Target language: {LANG_NAMES[f.regional]}\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(src))
    try:
        out = await sarvam.chat_json(SYSTEM, user, Translated, mode="railway_announcement", max_tokens=900)
    except SarvamError as e:  # bad JSON or a failed call: two languages still make a good clip
        log.warning("regional translation failed: %s", e)
        return None
    texts = [t.split(". ", 1)[1] if t[:3].rstrip(". ").isdigit() and ". " in t else t for t in out.lines]
    names = [f.friend.strip(), f.origin.strip(), f.destination.strip(), f.late_for.strip()]
    texts = [restore_names(t.strip(), names) for t in texts]
    if (
        len(texts) != len(src)
        or not all(texts)
        or sum(len(t) for t in texts) > MAX_REGIONAL_CHARS
        or spaced not in texts[0]
    ):
        log.warning("regional translation rejected (%d lines for %d)", len(texts), len(src))
        return None
    return texts


async def build(f: Form, sarvam: Sarvam) -> Script:
    punch = random.randrange(len(PUNCHLINES["en"]))
    num = train_number(f)
    lines: list[Line] = []
    for lang, (code, voice) in (("hi", HI), ("en", EN)):
        spoken = template(f, lang, punch, say_digits(num, lang))
        shown = template(f, lang, punch, num)
        lines += [Line(text=s, language=code, speaker=voice, pace=PACE, caption=c) for s, c in zip(spoken, shown)]
    regional = await regional_lines(f, punch, num, sarvam)
    if regional:
        code, voice = REGIONAL[f.regional]
        lines += [Line(text=t, language=code, speaker=voice, pace=PACE) for t in regional]
    name = f.friend.strip()
    late = delay(f.late_minutes, "en")
    return Script(
        lines=lines,
        title=f"{name} Express ({num}) is running {late} late",
        share_text=f"Yaatri kripya dhyan dein! 🚆 {name} Express phir se late hai. Suniye announcement 📢",
        card={
            "kicker": "DOST RAILWAYS · यात्रीगण कृपया ध्यान दें",
            "emoji": "🚆",
            "bg": ["#111827", "#b45309"],
            "platform": f.platform,
            "train_number": num,
        },
        phone_line=False,
    )


MODE = Mode(
    slug="railway-announcement",
    name="Yaatri Kripya Dhyan Dein 🚆",
    tagline="A station announcement about your always-late friend, in Hindi, English and one more language.",
    form=Form,
    build=build,
    uses_llm=True,
)
