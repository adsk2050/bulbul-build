"""Bulbul Lab: Bulbul V4 Flash teaches text-to-speech by demonstrating it on itself.

Each lesson is a short spoken explanation followed by labelled example clips
(A, B, C, ...) that differ in one thing: the script, the voice, the punctuation,
the pace, the sampling rate. Every word is hand-written here, so a lesson costs
nothing after its first run (the TTS cache keys on the exact request).

Each lesson names the CS224S lecture and slides that teach the idea, taken
from `D:/learn/speech/cs224s/notes/`. Keep every lesson under MAX_CHARS of
spoken text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from ..sarvam import Sarvam
from .base import Line, Mode, Script

MAX_CHARS = 900  # spoken characters per lesson: ~Rs 1.8 at list price, then cached

# Narration voices: Indian English, and Hinglish for the code-mixing lesson.
NARRATOR = ("en-IN", "shubh_en_narration")
NARRATOR_ENHI = ("hi-IN", "ishita_enhi_companion")

LessonKey = Literal[
    "numbers", "script", "codemix", "punctuation", "pace", "styles", "languages", "phone", "limits",
]


@dataclass(frozen=True)
class Clip:
    label: str  # "Devanagari", shown as "A · Devanagari"
    text: str
    language: str
    speaker: str
    pace: float = 1.0


@dataclass(frozen=True)
class Lesson:
    title: str
    intro: str  # spoken before the clips
    clips: tuple[Clip, ...]
    course_ref: str
    outro: str = ""  # optional, spoken after the clips
    narrator: tuple[str, str] = NARRATOR
    phone_line: bool = False

    def spoken_chars(self) -> int:
        return len(self.intro) + len(self.outro) + sum(len(c.text) for c in self.clips)


LESSONS: dict[str, Lesson] = {
    "numbers": Lesson(
        title="Numbers, dates and acronyms",
        intro=(
            "Lesson one: text normalisation. Before I can speak, I must decide how to say what is written. "
            "Rupees, dates, times, a PNR, a phone number, and acronyms: some are read as words, some letter by letter. "
            "Listen."
        ),
        clips=(
            Clip("Money", "Your loan of ₹5,00,000 is approved.", "en-IN", "simran_en_customer"),
            Clip("Date and time", "Your train leaves on 12/10/2026 at 9:47 am.", "en-IN", "simran_en_customer"),
            Clip("PNR and phone", "PNR 4521876390. For help, call 98765 43210.", "en-IN", "simran_en_customer"),
            Clip("Acronyms", "ISRO launched it, but the EMI is still due.", "en-IN", "simran_en_customer"),
        ),
        outro="ISRO is a word. EMI is three letters. Nobody wrote that down for me; context decided.",
        course_ref="CS224S Lecture 3, slides 35 and 39–40: text normalisation of non-standard words",
    ),
    "script": Lesson(
        title="Devanagari vs romanised Hindi",
        intro=(
            "Lesson two: grapheme to phoneme. I turn letters into sounds. "
            "Devanagari spells Hindi sounds almost one to one. Romanised Hindi makes me guess: "
            "is this a short a or a long a? Same sentence, same voice, two scripts."
        ),
        clips=(
            Clip("Devanagari", "आज मौसम बहुत अच्छा है, चलो बाहर चाय पीते हैं।", "hi-IN", "simran_hi_conversation"),
            Clip("Romanised", "Aaj mausam bahut accha hai, chalo bahar chai peete hain.", "hi-IN",
                 "simran_hi_conversation"),
        ),
        outro="Sarvam's own guide says it plainly: write Hindi in Devanagari. Romanised text sounds worse.",
        course_ref="CS224S Lecture 3, slides 41 and 45: letter-to-sound rules and G2P accuracy across languages",
    ),
    "codemix": Lesson(
        title="Hinglish: Hindi voice vs Hinglish voice",
        intro=(
            "Lesson three: code-mixing. India बोलता है Hinglish. Hindi words Devanagari में, English words Latin में. "
            "पहले एक pure Hindi voice, फिर एक Hinglish voice. English words पर ध्यान दीजिए।"
        ),
        clips=(
            Clip("Hindi voice", "Kal की meeting cancel हो गई, तो weekend पर movie plan करते हैं।", "hi-IN",
                 "simran_hi_conversation"),
            Clip("Hinglish voice", "Kal की meeting cancel हो गई, तो weekend पर movie plan करते हैं।", "hi-IN",
                 "simran_enhi_companion"),
        ),
        outro="Hinglish voice तभी चुनिए जब sentence सच में mixed हो, सिर्फ़ एक-दो English शब्द हों तो नहीं।",
        narrator=NARRATOR_ENHI,
        course_ref="CS224S Lecture 3, slides 23 and 45: the front end chooses the phones, and G2P depends on the language",
    ),
    "punctuation": Lesson(
        title="Punctuation is my prosody control",
        intro=(
            "Lesson four: prosody. I have no SSML and no pause tags. Punctuation is how you steer my pauses "
            "and my pitch. Same words, four marks: comma, full stop, exclamation, and ellipsis."
        ),
        clips=(
            Clip("Comma", "Okay, I am coming, give me five minutes.", "en-IN", "simran_en_narration"),
            Clip("Full stop", "Okay. I am coming. Give me five minutes.", "en-IN", "simran_en_narration"),
            Clip("Exclamation", "Okay! I am coming! Give me five minutes!", "en-IN", "simran_en_narration"),
            Clip("Ellipsis", "Okay… I am coming… give me five minutes…", "en-IN", "simran_en_narration"),
        ),
        outro="Prosody belongs to the phrase. Move the boundary and the melody moves with it.",
        course_ref="CS224S Lecture 2, slide 49: prosodic boundaries; Lecture 3, slide 9: what prosody TTS must specify",
    ),
    "pace": Lesson(
        title="Speaking rate",
        intro=(
            "Lesson five: speaking rate. Inside the model, every sound gets a predicted duration. "
            "The pace setting stretches or squeezes those durations. "
            "Slow for teaching, normal for talking, fast for announcements."
        ),
        clips=(
            Clip("Pace 0.8", "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 0.8),
            Clip("Pace 1.0", "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 1.0),
            Clip("Pace 1.25", "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration",
                 1.25),
        ),
        course_ref="CS224S Lecture 5, slides 105–106: FastSpeech's length regulator and duration predictor",
    ),
    "styles": Lesson(
        title="One speaker, four styles",
        intro=(
            "Lesson six: voice and style. My voice IDs read name, language, style. "
            "Here is one speaker, Simran, in four styles: recovery desk, news, late night radio, "
            "and excited social. The words stay the same. The delivery changes."
        ),
        clips=(
            Clip("Recovery", "आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_recovery"),
            Clip("News", "आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_news"),
            Clip("Late night", "आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_latenight"),
            Clip("Social, excited", "आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_social_excited"),
        ),
        course_ref="CS224S Lecture 5, slides 59 and 96: speaker embeddings and Global Style Tokens",
    ),
    "languages": Lesson(
        title="Ten voices, one hello",
        intro=(
            "Lesson seven: languages. Each language has its own sounds and its own script, "
            "and a model is only as good as its data in each. Here is one greeting in all ten "
            "languages that have Bulbul V4 voices."
        ),
        clips=(
            Clip("Hindi", "नमस्ते! आप कैसे हैं?", "hi-IN", "simran_hi_conversation"),
            Clip("English", "Hello! How are you?", "en-IN", "simran_en_conversation"),
            Clip("Hinglish", "Hello! आप कैसे हो?", "hi-IN", "ishita_enhi_companion"),
            Clip("Marathi", "नमस्कार! तुम्ही कसे आहात?", "mr-IN", "ishita_mr_conversational"),
            Clip("Bengali", "নমস্কার! আপনি কেমন আছেন?", "bn-IN", "arnab_bn_conversation"),
            Clip("Gujarati", "નમસ્તે! તમે કેમ છો?", "gu-IN", "bhavik_gu_conversation"),
            Clip("Punjabi", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?", "pa-IN", "anand_pa_conversation"),
            Clip("Tamil", "வணக்கம்! எப்படி இருக்கீங்க?", "ta-IN", "gokul_ta_narration"),
            Clip("Telugu", "నమస్కారం! మీరు ఎలా ఉన్నారు?", "te-IN", "kavitha_te_conversation"),
            Clip("Kannada", "ನಮಸ್ಕಾರ! ಹೇಗಿದ್ದೀರಾ?", "kn-IN", "chaitra_kn_conversation"),
        ),
        outro="Hindi and English have over a hundred voices. Tamil, Telugu and Kannada have four each.",
        course_ref="CS224S Lecture 3, slide 45: G2P error 0.535% for English and Czech vs 37.85% across 507 languages",
    ),
    "phone": Lesson(
        title="How I sound on a phone call",
        intro=(
            "Lesson eight: telephony. A phone line samples at 8 kilohertz and passes only about "
            "300 to 3400 hertz. The high frequencies that make s and sh crisp are cut off. "
            "Listen to this sentence, then press the phone-line button to hear it narrowband."
        ),
        clips=(
            Clip("Full band", "नमस्ते, मैं आपके बैंक से बोल रहा हूँ। आपकी अगली EMI 15 तारीख़ को है।", "hi-IN",
                 "shubh_hi_customer"),
        ),
        outro="Most Indian voice bots live on this narrow channel, so a voice must stay clear on it.",
        phone_line=True,
        course_ref=(
            "CS224S Lecture 4, slide 14: 16 kHz speech vs the 8 kHz telephone rate; "
            "Lecture 1, slide 29: telephone speech roughly doubles ASR error"
        ),
    ),
    "limits": Lesson(
        title="What I cannot do (yet)",
        intro=(
            "Lesson nine: honest limits. I am Bulbul V4 Flash, the fast model. I have no laughter, "
            "whisper or emotion tags; those are promised for V4 Pro, which is not out. I do not sing. "
            "I cannot clone your voice. I have no SSML. Malayalam and Odia have no V4 voices yet. "
            "Here is what happens when you type a laugh."
        ),
        clips=(
            Clip("Typed laughter", "Haha! That was so funny.", "en-IN", "simran_en_conversation"),
        ),
        outro="I read the laugh as a word. Emotion in speech is still the open problem.",
        course_ref="CS224S Lecture 1, slide 38: modern TTS is 'not yet fully emotive'; voice cloning",
    ),
}

LESSON_NAMES = {k: f"{i}. {lesson.title}" for i, (k, lesson) in enumerate(LESSONS.items(), start=1)}


class Form(BaseModel):
    lesson: LessonKey = Field(default="numbers", title="Lesson", json_schema_extra={"x-labels": LESSON_NAMES})


def caption_label(i: int, label: str) -> str:
    return f"{chr(ord('A') + i)} · {label}"


def lesson_lines(lesson: Lesson) -> list[Line]:
    code, voice = lesson.narrator
    lines = [Line(text=lesson.intro, language=code, speaker=voice, caption=f"Bulbul: {lesson.intro}")]
    for i, c in enumerate(lesson.clips):
        lines.append(Line(
            text=c.text, language=c.language, speaker=c.speaker, pace=c.pace,
            caption=f"{caption_label(i, c.label)}: {c.text}",
        ))
    if lesson.outro:
        lines.append(Line(text=lesson.outro, language=code, speaker=voice, caption=f"Bulbul: {lesson.outro}"))
    return lines


async def build(f: Form, sarvam: Sarvam) -> Script:
    lesson = LESSONS[f.lesson]
    n = list(LESSONS).index(f.lesson) + 1
    return Script(
        lines=lesson_lines(lesson),
        title=lesson.title,
        share_text=f"Bulbul Lab, lesson {n}: {lesson.title}. A voice AI explains text-to-speech using its own voice 🧪",
        card={
            "kicker": f"BULBUL LAB · LESSON {n}",
            "emoji": "🧪",
            "bg": ["#0f2f3a", "#2f6f73"],
            "course_ref": lesson.course_ref,
            "clips": [caption_label(i, c.label) for i, c in enumerate(lesson.clips)],
        },
        phone_line=lesson.phone_line,
    )


MODE = Mode(
    slug="bulbul-lab",
    name="Bulbul Lab 🧪",
    tagline="Bulbul V4 Flash teaches you how text-to-speech works, by demonstrating it on itself.",
    form=Form,
    build=build,
    uses_llm=False,
)
