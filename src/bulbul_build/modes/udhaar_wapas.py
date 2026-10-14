"""Udhaar Wapas: a polite "recovery desk" voice note for a friend who owes you money.

Hindi, Hinglish and English come from hand-written templates (free, exact).
The other languages are written by sarvam-105b from the English template,
with structured output, so the line count and the numbers stay fixed.
"""

from __future__ import annotations

import random
from typing import Literal

from pydantic import BaseModel, Field

from ..sarvam import Sarvam
from .base import Line, Mode, Script

Language = Literal["enhi", "hi", "en", "mr", "bn", "gu", "pa", "ta", "te", "kn"]

LANGS: dict[str, tuple[str, str]] = {
    # key: (language_code, voice)
    "enhi": ("hi-IN", "simran_enhi_banking_expressive"),
    "hi": ("hi-IN", "simran_hi_recovery"),
    "en": ("en-IN", "simran_en_recovery"),
    "mr": ("mr-IN", "ritu_mr_insurance"),
    "bn": ("bn-IN", "roopa_bn_conversational"),
    "gu": ("gu-IN", "pooja_gu_customer"),
    "pa": ("pa-IN", "jaspal_pa_banking"),
    "ta": ("ta-IN", "aravind_ta_ads"),
    "te": ("te-IN", "kavitha_te_conversation"),
    "kn": ("kn-IN", "chaitra_kn_conversation"),
}
LANG_NAMES = {
    "enhi": "Hinglish", "hi": "Hindi", "en": "English", "mr": "Marathi", "bn": "Bengali",
    "gu": "Gujarati", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
}


class Form(BaseModel):
    friend: str = Field(title="Friend's name", min_length=1, max_length=30, examples=["Rahul"])
    amount: int = Field(title="Amount owed (₹)", ge=1, le=1_000_000, examples=[850])
    reason: str = Field(title="For what?", min_length=1, max_length=50, examples=["Garba pass"])
    since: str = Field(title="Since when?", min_length=1, max_length=30, examples=["Navratri"])
    you: str = Field(default="", title="Your name", max_length=30, description="Optional")
    upi: str = Field(
        default="", title="Your UPI ID", max_length=50, pattern=r"^$|^[\w.\-]{2,40}@[A-Za-z]{2,20}$",
        description="Optional. Read out at the end.",
    )
    language: Language = Field(default="enhi", title="Language", json_schema_extra={"x-labels": LANG_NAMES})
    paid: bool = Field(default=False, title="Already paid? Send a thank-you note instead")


def inr(n: int) -> str:
    """Indian digit grouping: 500000 -> 5,00,000."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    parts.insert(0, head)
    return ",".join(parts) + "," + tail


PUNCHLINES = {
    "hi": [
        "भुगतान न होने पर, अगली चाय और समोसे का bill आपके नाम पर होगा।",
        "कृपया ध्यान दें, यह reminder आपकी मम्मी को भी भेजा जा सकता है।",
        "भुगतान न होने पर, आपको group photo से crop कर दिया जाएगा।",
    ],
    "enhi": [
        "Payment नहीं हुआ, तो next चाय-समोसा आपकी तरफ़ से।",
        "Please note, यह reminder आपकी मम्मी को भी forward हो सकता है।",
        "Payment नहीं हुआ, तो आपको group photo से crop कर दिया जाएगा।",
    ],
    "en": [
        "Failing payment, the next round of chai and samosa will be billed to you.",
        "Please note, a copy of this reminder may be shared with your mother.",
        "Failing payment, you will be cropped out of the next group photo.",
    ],
}


def template(f: Form, lang: str, punch: int) -> list[str]:
    amt, name = inr(f.amount), f.friend
    you = f.you or ("आपके दोस्त" if lang != "en" else "Your friend")
    if lang == "en":
        if f.paid:
            return [
                f"Hello {name}. This is the Udhaar Wapas recovery desk.",
                f"We confirm receipt of ₹{amt}, for {f.reason}. Your account is now clear.",
                f"{you} thanks you for your honesty. The friendship continues as normal. Have a great day!",
            ]
        lines = [
            f"Hello {name}. This is a courtesy call from the Udhaar Wapas recovery desk.",
            f"Our records show an outstanding amount of ₹{amt}, for {f.reason}, pending since {f.since}.",
            f"{you} has been waiting very patiently.",
        ]
        if f.upi:
            lines.append(f"Kindly pay today to the UPI ID {f.upi}.")
        lines += [PUNCHLINES["en"][punch], "Thank you, and have a lovely day."]
        return lines
    if lang == "enhi":
        if f.paid:
            return [
                f"Hello {name}! Udhaar Wapas recovery desk से बोल रही हूँ।",
                f"आपका ₹{amt} का payment, {f.reason} वाला, receive हो गया है। Account clear है।",
                f"{you} की तरफ़ से thank you! दोस्ती continue रहेगी। Have a nice day!",
            ]
        lines = [
            f"Hello {name}! मैं Udhaar Wapas recovery desk से बोल रही हूँ।",
            f"आपके नाम पर ₹{amt} का payment pending है, {f.reason} के लिए, {f.since} से।",
            f"{you} बहुत patiently wait कर रहे हैं।",
        ]
        if f.upi:
            lines.append(f"Please आज ही UPI ID {f.upi} पर payment कर दीजिए।")
        lines += [PUNCHLINES["enhi"][punch], "Thank you, आपका दिन शुभ हो!"]
        return lines
    # Hindi
    if f.paid:
        return [
            f"नमस्ते {name} जी। मैं उधार वापस रिकवरी डेस्क से बोल रही हूँ।",
            f"आपका ₹{amt} का भुगतान, {f.reason} के लिए, हमें मिल गया है। आपका खाता साफ़ है।",
            f"{you} आपका धन्यवाद करते हैं। दोस्ती पहले की तरह जारी रहेगी।",
        ]
    lines = [
        f"नमस्ते {name} जी। मैं उधार वापस रिकवरी डेस्क से बोल रही हूँ।",
        f"हमारे रिकॉर्ड के अनुसार, आपके ऊपर ₹{amt} बकाया है, {f.reason} के लिए, {f.since} से।",
        f"{you} बहुत धैर्य से इंतज़ार कर रहे हैं।",
    ]
    if f.upi:
        lines.append(f"कृपया आज ही UPI ID {f.upi} पर भुगतान करें।")
    lines += [PUNCHLINES["hi"][punch], "धन्यवाद। आपका दिन शुभ हो।"]
    return lines


class Translated(BaseModel):
    lines: list[str] = Field(description="One translated line per input line, same order")


SYSTEM = (
    "You translate short, funny 'polite debt-recovery call' scripts between friends into Indian languages "
    "for a text-to-speech voice. Write the target language in its own script. Keep people's names, UPI IDs "
    "and English brand words in Latin script. Keep every amount exactly as written, including the ₹ sign and "
    "commas. Keep the tone polite and formal, like a bank call centre, so the joke lands. "
    "Return exactly one output line per input line."
)


async def build(f: Form, sarvam: Sarvam) -> Script:
    punch = random.randrange(3)
    code, voice = LANGS[f.language]
    if f.language in ("hi", "enhi", "en"):
        texts = template(f, f.language, punch)
    else:
        src = template(f, "en", punch)
        user = f"Target language: {LANG_NAMES[f.language]}\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(src))
        out = await sarvam.chat_json(SYSTEM, user, Translated, mode="udhaar_wapas", max_tokens=900)
        texts = [t.split(". ", 1)[1] if t[:3].rstrip(". ").isdigit() else t for t in out.lines][: len(src)]
        if len(texts) != len(src):
            texts = src  # fall back to English rather than read half a script
            code, voice = LANGS["en"]
    amt = inr(f.amount)
    if f.paid:
        title = f"{f.friend} ne ₹{amt} lauta diye! ✅"
        share = f"{f.friend}, aapke liye ek thank-you voice note 🙏"
        emoji, bg = "✅", ["#0b6e4f", "#14a06f"]
    else:
        title = f"{f.friend}: ₹{amt} pending since {f.since}"
        share = f"{f.friend}, aapke liye ek important voice message hai 📞💸"
        emoji, bg = "💸", ["#1e1b4b", "#be123c"]
    return Script(
        lines=[Line(text=t, language=code, speaker=voice) for t in texts],
        title=title,
        share_text=share,
        card={"kicker": "UDHAAR WAPAS · RECOVERY DESK", "emoji": emoji, "bg": bg},
        phone_line=True,
    )


MODE = Mode(
    slug="udhaar-wapas",
    name="Udhaar Wapas 💸",
    tagline="A very polite recovery-desk call for the friend who still owes you money.",
    form=Form,
    build=build,
    uses_llm=True,
)
