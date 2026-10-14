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
    "numbers", "script", "codemix", "punctuation", "pace", "styles", "languages", "phone", "limits", "heteronyms",
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
        title="Same digits, four readings",
        intro="Text normalisation. Before I speak, I rewrite symbols as words. Numbers are the hardest: the same four digits can be a phone number, a year, a price or a time. Only the words around them tell me which. Listen.",
        clips=(
            Clip("Phone", "Call 1800 now.", "en-IN", "simran_en_customer"),
            Clip("Year", "He was born in 1800.", "en-IN", "simran_en_customer"),
            Clip("Price", "Pay ₹1800 today.", "en-IN", "simran_en_customer"),
            Clip("Time", "The train leaves at 18:00.", "en-IN", "simran_en_customer"),
        ),
        outro="Same digits, four readings. Context decides, and a reader trained on other rules gets it wrong.",
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
        title="Move a comma, change the meaning",
        intro="Pauses and melody. I do not have pause tags. Punctuation is how you steer my pauses and my pitch. Move one comma and the meaning flips. Change a full stop to a question mark and the end of the sentence should rise.",
        clips=(
            Clip("Stop, don't go", "रुको, मत जाओ।", "hi-IN", "simran_hi_conversation"),
            Clip("Don't stop, go", "रुको मत, जाओ।", "hi-IN", "simran_hi_conversation"),
            Clip("Statement", "आप कल आ रहे हैं।", "hi-IN", "simran_hi_conversation"),
            Clip("Question", "आप कल आ रहे हैं?", "hi-IN", "simran_hi_conversation"),
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
            Clip("Pace 0.5", "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 0.5),
            Clip("Pace 1.0", "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 1.0),
            Clip("Pace 2.0", "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 2.0),
        ),
        course_ref="CS224S Lecture 5, slides 105–106: FastSpeech's length regulator and duration predictor",
    ),
    "styles": Lesson(
        title="One speaker, four styles",
        intro="Speaker and style. A voice has two parts: who is speaking, and how. One speaker, Ratan, in four styles: sports, late-night radio, devotional and documentary. The words stay the same. Only the delivery changes.",
        clips=(
            Clip("Sports", "आज रात आठ बजे भारत का मैच है, देर मत करना!", "hi-IN", "ratan_hi_sports"),
            Clip("Late night", "आज रात आठ बजे भारत का मैच है, देर मत करना!", "hi-IN", "ratan_hi_latenight"),
            Clip("Devotional", "आज रात आठ बजे भारत का मैच है, देर मत करना!", "hi-IN", "ratan_hi_devotional"),
            Clip("Documentary", "आज रात आठ बजे भारत का मैच है, देर मत करना!", "hi-IN", "ratan_hi_documentary"),
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
        intro="Now, my limits. Laughs, sighs and whispers are not words. A model needs a separate way to make them: a tag or an instruction. I am Bulbul V4 Flash, and I have neither. Listen to what happens when you type them.",
        clips=(
            Clip("Typed laughter", "Haha! That was so funny.", "en-IN", "simran_en_conversation"),
            Clip("Stage direction", "(whispers) Come closer, I have a secret.", "en-IN", "simran_en_conversation"),
            Clip("Tag", "[sighs] I am so tired today.", "en-IN", "simran_en_conversation"),
        ),
        outro="Expression comes from choosing a voice, not from the text. Emotion in speech is still an open problem.",
        course_ref="CS224S Lecture 1, slide 38: modern TTS is 'not yet fully emotive'",
    ),
    "heteronyms": Lesson(
        title="Same spelling, two sounds",
        intro="Same spelling, two sounds. The word read can sound like reed, or like red. Record can be a noun or a verb. Spelling alone cannot decide; I have to work out the grammar of the whole sentence. Each clip says one spelling two ways.",
        clips=(
            Clip("read", "I read it yesterday, and I will read it again tomorrow.", "en-IN", "simran_en_conversation", 0.85),
            Clip("record", "Please record the record before the shop closes.", "en-IN", "simran_en_conversation", 0.85),
            Clip("wind", "The wind was so strong that I had to wind the window shut.", "en-IN", "simran_en_conversation", 0.85),
        ),
        outro="Hindi in Devanagari almost never has this problem. English has hundreds of these words.",
        course_ref="CS224S Lecture 3, slide 41: homograph disambiguation",
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
