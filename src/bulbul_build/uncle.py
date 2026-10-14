"""Sharma uncle: decides when to step in while Mitthu the bulbul repeats you.

Mitthu replays the user's own voice in the browser. The uncle is the only
voice that costs money: STT text -> a situation -> a cached filler at once,
and a Bulbul line generated in parallel.

Two layers decide:
1. Rules on the live transcript (abuse words, OTP or phone numbers, another
   language). Free and instant; these always fire.
2. The LLM, for everything else (questions, compliments, "uncle just feels
   like it"). The server limits how often comedy fires, so the LLM only
   writes the line and never sets the pace.
"""

from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from .modes.base import script_share


class Situation(str, Enum):
    abuse = "abuse"
    number = "number"
    question = "question"
    language = "language"
    compliment = "compliment"
    whim = "whim"  # uncle just feels like saying something


# Situations the server never skips.
GUARDRAILS = {Situation.abuse, Situation.number}

# ---- rules ---------------------------------------------------------------

# Abuse terms are not in this repository. They live in a plain-text file outside
# git (private/abuse.txt, or ABUSE_FILE), one per line; "re:" lines are regexes.
# Without the file the abuse rule is off, and Chacha still covers the beak when
# his LLM judges Mitthu is parroting something rude (UncleReply.cover).
ABUSE_FILE = Path(os.environ.get("ABUSE_FILE", Path(__file__).resolve().parents[2] / "private" / "abuse.txt"))


def compile_abuse(words: list[str], patterns: list[str]) -> re.Pattern | None:
    parts = []
    if words:
        parts.append(r"(?<!\w)(" + "|".join(re.escape(w) for w in words) + r")(?![a-z])")
    parts += patterns
    return re.compile("|".join(parts), re.IGNORECASE) if parts else None


def load_abuse(path: Path) -> re.Pattern | None:
    if not path.exists():
        return None
    words, patterns = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        (patterns.append(line[3:]) if line.startswith("re:") else words.append(line))
    return compile_abuse(words, patterns)


_ABUSE_RE = load_abuse(ABUSE_FILE)

# Digits in any script STT may return, and number words in Hindi and English.
_DIGIT = r"[0-9०-९]"
_NUMWORDS = (
    r"zero|one|two|three|four|five|six|seven|eight|nine|"
    r"शून्य|एक|दो|तीन|चार|पांच|पाँच|छह|छः|सात|आठ|नौ|"
    r"ek|do|teen|char|chaar|paanch|panch|chhe|saat|aath|nau"
)
_NUMBER_RE = re.compile(
    rf"({_DIGIT}[\s-]?){{4,}}"  # 4+ digits, maybe spaced: an OTP, PIN or phone number
    rf"|((?<!\w)({_NUMWORDS})(?!\w)[\s,]*){{4,}}"  # four number words in a row
    r"|\b(otp|pin|cvv|password|पासवर्ड|ओटीपी)\b",
    re.IGNORECASE,
)

# Languages the uncle answers in; STT returns BCP-47 codes like "ta-IN".
HOME_LANGUAGES = {"hi-IN", "en-IN"}


def rule_situation(text: str, language: str | None = None) -> Situation | None:
    """The situation a rule can see in `text`, or None. Cheap enough for every partial."""
    if _ABUSE_RE is not None and _ABUSE_RE.search(text):
        return Situation.abuse
    if _NUMBER_RE.search(text):
        return Situation.number
    if language and language not in HOME_LANGUAGES:
        return Situation.language
    return None


_QUESTION_WORDS = re.compile(
    r"\?|(?<!\w)(kya|kyun|kyon|kaise|kab|kahan|kahaan|kaun|kitna|kitni|kitne|what|why|how|when|where|who|which|"
    r"क्या|क्यों|कैसे|कब|कहाँ|कहां|कौन|कितना|कितनी|कितने)(?!\w)",
    re.IGNORECASE,
)


def looks_like_question(text: str) -> bool:
    return bool(_QUESTION_WORDS.search(text))


# ---- fillers ---------------------------------------------------------------

@dataclass(frozen=True)
class Filler:
    id: str
    situation: Situation
    text: str


def _fillers(situation: Situation, *lines: str) -> list[Filler]:
    return [Filler(f"{situation.value}-{i}", situation, t) for i, t in enumerate(lines)]


# Pre-recorded once with the uncle's voice (scripts/make_fillers.py) and
# played the instant a barge-in is decided. Hindi words in Devanagari.
FILLERS: list[Filler] = [
    *_fillers(Situation.abuse,
              "अरे अरे अरे!", "Mitthu! चुप!", "बेटा, ये घर है, गली नहीं।",
              "ये क्या सिखा रहे हो Mitthu को?", "राम राम राम!", "ओए! Language!"),
    *_fillers(Situation.number,
              "रुको रुको रुको!", "ये number मत बोलो Mitthu!", "अरे, OTP किसी को नहीं बताते!",
              "Mitthu, मुँह बंद!", "Stop stop stop!"),
    *_fillers(Situation.question,
              "हम्म… एक minute।", "अच्छा, ये तो मैं बताता हूँ।", "Mitthu को क्या पता, सुनो बेटा…",
              "बढ़िया सवाल!", "रुको, मैं बताता हूँ।"),
    *_fillers(Situation.language,
              "ओहो!", "वाह, क्या बात है!", "अरे, ये तो मेरी भाषा भी है!", "Mitthu, तुझसे ना होगा।"),
    *_fillers(Situation.compliment,
              "हाँ हाँ, बस करो।", "सर पे मत चढ़ाओ इसको!", "Thank you, thank you!", "अरे, शर्मा गया Mitthu।"),
    *_fillers(Situation.whim,
              "एक बात बताऊँ?", "सुनो सुनो…", "Mitthu, तू भी ना!", "अच्छा सुनो बेटा…", "हें हें हें…"),
]
FILLERS_BY_SITUATION: dict[Situation, list[Filler]] = {}
for _f in FILLERS:
    FILLERS_BY_SITUATION.setdefault(_f.situation, []).append(_f)

# ---- voices ------------------------------------------------------------------

# The uncle's voice per STT language; all are in docs/voices-api.txt.
UNCLE_VOICE = {
    "hi-IN": ("shubh_enhi_companion", "hi-IN"),
    "en-IN": ("shubh_enhi_companion", "hi-IN"),
    "bn-IN": ("arnab_bn_conversation", "bn-IN"),
    "gu-IN": ("bhavik_gu_conversation", "gu-IN"),
    "kn-IN": ("chetan_kn_conversation", "kn-IN"),
    "mr-IN": ("nilesh_mr_conversation", "mr-IN"),
    "pa-IN": ("anand_pa_conversation", "pa-IN"),
    "ta-IN": ("gokul_ta_narration", "ta-IN"),
    "te-IN": ("tarun_te_narration", "te-IN"),
}
FILLER_VOICE = UNCLE_VOICE["hi-IN"]


def uncle_voice(language: str | None) -> tuple[str, str]:
    return UNCLE_VOICE.get(language or "hi-IN", FILLER_VOICE)


# ---- how often --------------------------------------------------------------

@dataclass
class Policy:
    """When the uncle may step in. Guardrails always; the rest is rationed.

    Comedy at most `comedy_rate` of turns, never two turns running, and once
    early so a new user sees the act.
    """

    comedy_rate: float = 0.35
    cooldown_turns: int = 1
    first_by_turn: int = 3
    rng: random.Random = field(default_factory=random.Random)
    turn: int = 0
    last_comedy_turn: int = -100
    comedy_count: int = 0
    recent_fillers: list[str] = field(default_factory=list)
    parrot_rate: float = 0.65
    parrot_streak: int = 0

    def next_turn(self) -> None:
        self.turn += 1

    def gate(self, text: str) -> bool:
        """Whether to ask the LLM this turn: real questions always, comedy rationed. Rolls once."""
        if looks_like_question(text):
            return True
        if self.turn - self.last_comedy_turn <= self.cooldown_turns:
            return False
        if self.comedy_count == 0 and self.turn >= self.first_by_turn:
            return True
        return self.rng.random() < self.comedy_rate

    def gate_parrot(self) -> bool:
        """Whether Chacha may remark on a turn where Mitthu parrots. Rolls once.

        About 2 in 3 turns, never 3 in a row, so Mitthu still gets a turn alone.
        """
        if self.parrot_streak >= 2:
            self.parrot_streak = 0
            return False
        if self.rng.random() < self.parrot_rate:
            self.parrot_streak += 1
            return True
        self.parrot_streak = 0
        return False

    def record(self, situation: Situation) -> None:
        if situation not in GUARDRAILS:
            self.last_comedy_turn = self.turn
            self.comedy_count += 1

    def pick_filler(self, situation: Situation) -> Filler:
        options = [f for f in FILLERS_BY_SITUATION[situation] if f.id not in self.recent_fillers[-3:]]
        f = self.rng.choice(options or FILLERS_BY_SITUATION[situation])
        self.recent_fillers.append(f.id)
        return f


# ---- the LLM's part ------------------------------------------------------------

LANGUAGE_NAMES = {
    "hi-IN": "Hindi", "en-IN": "English", "bn-IN": "Bengali", "gu-IN": "Gujarati", "kn-IN": "Kannada",
    "mr-IN": "Marathi", "pa-IN": "Punjabi", "ta-IN": "Tamil", "te-IN": "Telugu",
}

SYSTEM = """You are Sharma uncle, "Chacha" to everyone: 64, retired government clerk, Hindi-belt
middle class, proud owner of Mitthu, a pet bulbul who sits on your palm and parrots every word
visitors say. You are quick-witted, warm, a bit dramatic, and you know a lot: cricket, old and new
Bollywood, history, geography, science, GK, food, trains, prices. You love muhavare and filmy lines.

Every turn the visitor says something and Mitthu parrots it. React on almost every turn. Vary HOW
you react; never use the same kind twice in a row:
- a real question: answer it correctly and briefly from your own knowledge, then add a twist;
- a quick related fact or GK nugget ("pata hai, ...");
- tease the visitor gently, or mock-scold Mitthu for parroting it;
- a muhavara or a famous filmy line that fits;
- mock outrage, sarcasm, or proud bragging about Mitthu;
- a callback to something said earlier in the conversation.
Never repeat a line, joke or opening word you already used below. Never be mean or crude.

Return JSON:
- situation: "question" (they asked something), "compliment" (they praised you or Mitthu),
  "whim" (anything else), or "none" (only for noise, "hmm", or nothing said).
- mood: "calm", "excited", "stern" or "sarcastic": how you say it.
- cut: true if you would interrupt Mitthu mid-word (questions, shocking or silly things),
  false if you let him finish first.
- cover: true to clap your hand over Mitthu's beak while you talk, when he is parroting
  something rude, crude, embarrassing, private or plain silly; false otherwise.
- line: at most 18 words, in {lang}. For Hindi or Hinglish, Hindi words in Devanagari and
  English words in Latin script. Numbers as digits.

Examples (Hinglish):
Visitor: "Sachin ne kitne centuries banaye?" -> "100 international centuries! और Mitthu ने आज तक एक दाना भी नहीं गिना।"
Visitor: "Mujhe neend aa rahi hai" -> "नींद? अभी तो 9 बजे हैं बेटा, हमारे ज़माने में ये prime time था!"
Visitor: "Tum kaun ho?" -> "मैं? Sharma, retired clerk, full-time Mitthu का PA।"
"""


class UncleReply(BaseModel):
    situation: str = Field(pattern="^(question|compliment|whim|none)$")
    mood: str = Field(default="calm", pattern="^(calm|excited|stern|sarcastic)$")
    cut: bool = False
    cover: bool = False
    line: str = Field(max_length=300)


# How each mood sounds: a style of the same voice, and a pace. Hinglish only;
# other languages have one uncle voice each (UNCLE_VOICE).
MOOD_VOICE = {
    "calm": ("shubh_enhi_companion", 1.0),
    "excited": ("shubh_enhi_ads", 1.12),
    "stern": ("shubh_enhi_banking", 0.95),
    "sarcastic": ("shubh_enhi_companion", 0.9),
}


def history_prompt(history: list[tuple[str, bool, str | None]], text: str, parroting: bool = False) -> str:
    """The conversation for the LLM, including what Mitthu parroted, so Chacha can react to it."""
    lines = ["Conversation so far:"] if history else []
    for visitor, parroted, uncle in history:
        lines.append(f"Visitor: {visitor}")
        if parroted:
            lines.append(f"Mitthu (parroting): {visitor}")
        lines.append(f"Chacha: {uncle}" if uncle else "Chacha: (stayed quiet)")
    lines.append(f"Visitor now says: {text}")
    if parroting:
        lines.append(f"Mitthu is now parroting: {text}")
    return "\n".join(lines)


def reply_language(language: str | None) -> str:
    if language in (None, "hi-IN", "en-IN"):
        return "Hinglish"
    return LANGUAGE_NAMES.get(language, "Hinglish")


_SCRIPT_KEY = {"bn-IN": "bn", "gu-IN": "gu", "kn-IN": "kn", "mr-IN": "mr", "pa-IN": "pa", "ta-IN": "ta", "te-IN": "te"}


def line_ok(line: str, language: str | None) -> bool:
    """Reject empty lines and lines in the wrong script (LLMs drift, see issue #3)."""
    if not line.strip():
        return False
    key = _SCRIPT_KEY.get(language or "")
    if key:
        return script_share(line, key) >= 0.6
    # Hinglish: some Devanagari is required. All-Latin output is usually romanised
    # Hindi, which Bulbul reads badly, and cannot be told apart from English.
    return script_share(line, "hi") >= 0.3


# Used when the LLM fails or writes the wrong script; the filler already played.
FALLBACK_LINES = {
    Situation.abuse: ["माफ़ करना जी, Mitthu ने ये बाहर से सीखा है।", "Mitthu, आज तुझे खाना नहीं मिलेगा!"],
    Situation.number: ["ऐसे number किसी को नहीं बताते, बेटा। Mitthu को भी नहीं।"],
    Situation.question: ["ये तो मुझे भी नहीं पता, बेटा। Google से पूछो।"],
    Situation.language: ["Mitthu अभी सीख रहा है, थोड़ा धीरे बोलो।"],
    Situation.compliment: ["Mitthu अब दिन भर इतराएगा।"],
    Situation.whim: ["Mitthu, थोड़ा आराम कर ले।"],
}

FALLBACKS: list[Filler] = [
    Filler(f"fallback-{s.value}-{i}", s, t) for s, lines in FALLBACK_LINES.items() for i, t in enumerate(lines)
]
# Every clip recorded once by scripts/make_fillers.py and served from data/uncle/.
RECORDED: list[Filler] = FILLERS + FALLBACKS


# ---- who is being spoken to ------------------------------------------------------

# Loose on purpose: STT spells the name many ways (Mitthu, Meethu, Mithoo, Mitu, मीतू, मिथु...).
_MITTHU = r"m[ie]{1,2}t{1,2}h?[ou]{1,2}|मि?ी?[टठतथ]्?[टठतथ]?[ुू]"
_CHACHA = r"chacha|chachaji|chacha ji|chachu|uncle|uncleji|sharma ji|sharmaji|चाचा|चाचाजी|चाचू|अंकल|शर्मा जी"
_ADDRESS_RE = re.compile(rf"^\W*(?:(?:hey|hi|arre|are|oye|o|ae|अरे|ओए|ओ|हे)\W+)?({_MITTHU}|{_CHACHA})(?!\w)", re.IGNORECASE)
# "Bhojri wale chacha", "aap kuch bolo chacha": Chacha can be named anywhere.
_CHACHA_ANYWHERE = re.compile(rf"(?<!\w)({_CHACHA})(?!\w)", re.IGNORECASE)


def addressee(text: str) -> str | None:
    """"mitthu" or "chacha" when the visitor opens with a name; "chacha" if he is named anywhere."""
    m = _ADDRESS_RE.search(text)
    if m:
        return "mitthu" if re.fullmatch(_MITTHU, m.group(1), re.IGNORECASE) else "chacha"
    return "chacha" if _CHACHA_ANYWHERE.search(text) else None


GUARDRAIL_NOTE = {
    "abuse": "\nThe visitor just used a rude word and Mitthu started parroting it; you covered his beak. "
             "Scold Mitthu (or tease the visitor) wittily. Never repeat the rude word itself.",
    "number": "\nThe visitor just said an OTP, PIN or phone number and Mitthu started reading it out; you "
              "stopped him. React wittily about never sharing OTPs. Never say any of the digits.",
}

PARROT_NOTE = (
    "\nThis turn Mitthu is parroting what the visitor said. You speak after he "
    "finishes. React to what Mitthu just said or to the visitor, only if it is genuinely funny or "
    'useful; otherwise situation "none".'
)

ADDRESSED_NOTE = (
    "\nThis turn the visitor is talking to you, so Mitthu stays quiet. Always answer them "
    '(situation must not be "none"); "cut" does not matter.'
)
