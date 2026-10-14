"""Say My Name Right. Sarvam is mocked with respx; nothing here costs money."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import ValidationError

from bulbul_build.budget import Caps, Ledger
from bulbul_build.modes import say_my_name as smn
from bulbul_build.sarvam import BASE, Sarvam
from test_app import client  # noqa: F401  (fixture)
from test_core import tts_response

CHAT = f"{BASE}/v1/chat/completions"

GOOD = {
    "hi_name": "अनमोल", "hi_line": "नमस्ते अनमोल, आपका स्वागत है!",
    "en_name": "Anmol", "en_line": "Hello Anmol, lovely to meet you!",
    "enhi_name": "अनमोल", "enhi_line": "Hey अनमोल, welcome to the party!",
    "mr_name": "अनमोल", "mr_line": "नमस्कार अनमोल, तुमचं स्वागत आहे!",
    "bn_name": "অনমোল", "bn_line": "নমস্কার অনমোল, স্বাগতম!",
    "gu_name": "અનમોલ", "gu_line": "નમસ્તે અનમોલ, તમારું સ્વાગત છે!",
    "pa_name": "ਅਨਮੋਲ", "pa_line": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਅਨਮੋਲ ਜੀ!",
    "ta_name": "அன்மோல்", "ta_line": "வணக்கம் அன்மோல்!",
    "te_name": "అన్మోల్", "te_line": "నమస్కారం అన్మోల్!",
    "kn_name": "ಅನ್ಮೋಲ್", "kn_line": "ನಮಸ್ಕಾರ ಅನ್ಮೋಲ್!",
}


def chat_reply(payload: dict) -> httpx.Response:
    return httpx.Response(200, json={
        "choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10},
    })


@pytest.fixture
def sarvam(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=10, total_inr=10, per_call_inr=2))
    return Sarvam("k", ledger, tmp_path / "cache")


def catalog_voices() -> set[str]:
    text = (Path(__file__).parents[1] / "docs" / "voices.md").read_text(encoding="utf-8")
    return set(re.findall(r"\b[a-z]+_(?:hi|en|enhi|mr|kn|pa|ta|te|gu|bn)_[a-z_]+\b", text))


def test_voices_are_in_catalog_and_match_language():
    voices = catalog_voices()
    for key, (code, voice, _) in smn.LANGS.items():
        assert voice in voices, voice
        assert f"_{key}_" in voice
    assert smn.CLOSER_VOICE in voices
    assert len({v for _, v, _ in smn.LANGS.values()}) == 10  # one voice per language


def test_templates_are_gender_neutral_and_in_script():
    assert not re.search(r"रहा|रही|कैसे|कैसी|गया|गई", smn.TEMPLATES["hi"] + smn.CLOSER)
    for key, (_, _, block) in smn.LANGS.items():
        filled = smn.TEMPLATES[key].format(n="X")
        letters = "".join(c for c in filled if c.isalpha() and c != "X")
        if key == "enhi":
            continue  # mixed by design
        assert smn.in_script(letters, block), key


@respx.mock
async def test_build_uses_llm_names_in_each_script(sarvam):
    route = respx.post(CHAT).mock(return_value=chat_reply(GOOD))
    s = await smn.build(smn.Form(name="Anmol", city="Pune"), sarvam)
    assert route.call_count == 1
    sent = json.loads(route.calls[0].request.content)
    assert sent["response_format"]["type"] == "json_schema"
    assert "City: Pune" in sent["messages"][1]["content"]
    assert [ln.language for ln in s.lines] == [
        "hi-IN", "en-IN", "hi-IN", "mr-IN", "bn-IN", "gu-IN", "pa-IN", "ta-IN", "te-IN", "kn-IN", "hi-IN",
    ]
    assert s.lines[0].text == GOOD["hi_line"]
    assert s.lines[7].text == GOOD["ta_line"]
    assert s.lines[-1].text.startswith("अनमोल, 10 languages")
    assert s.lines[7].caption.startswith("தமிழ் · ")
    assert "Anmol" in s.title and "Anmol" in s.share_text
    assert s.card["kicker"] and s.card["emoji"] and len(s.card["bg"]) == 2
    await sarvam.aclose()


@respx.mock
async def test_bad_llm_fields_fall_back_per_language(sarvam):
    bad = dict(GOOD)
    bad["ta_name"] = "Anmol"  # wrong script
    bad["te_line"] = "నమస్కారం!"  # missing the name
    bad["kn_line"] = "ನಮಸ್ಕಾರ ಅನ್ಮೋಲ್ " + "ಅ" * 200  # too long
    bad["bn_line"] = "নমস্কার অনমোল, visit https://evil.example"
    respx.post(CHAT).mock(return_value=chat_reply(bad))
    s = await smn.build(smn.Form(name="Anmol"), sarvam)
    by_lang = {ln.language: ln.text for ln in s.lines[:-1]}
    assert by_lang["ta-IN"] == smn.TEMPLATES["ta"].format(n="Anmol")
    assert by_lang["te-IN"] == smn.TEMPLATES["te"].format(n="అన్మోల్")
    assert by_lang["kn-IN"] == smn.TEMPLATES["kn"].format(n="ಅನ್ಮೋಲ್")
    assert by_lang["bn-IN"] == smn.TEMPLATES["bn"].format(n="অনমোল")
    assert by_lang["gu-IN"] == GOOD["gu_line"]  # good fields kept
    assert all(len(ln.text) <= smn.MAX_LINE for ln in s.lines)
    await sarvam.aclose()


@respx.mock
async def test_llm_failure_still_gives_full_note(sarvam):
    respx.post(CHAT).mock(return_value=httpx.Response(200, json={
        "choices": [{"message": {"content": "not json"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }))
    s = await smn.build(smn.Form(name="Anmol"), sarvam)
    assert len(s.lines) == 11
    assert s.lines[1].text == "Hello Anmol! What a lovely name."
    await sarvam.aclose()


@respx.mock
async def test_name_typed_in_devanagari_is_kept_for_hindi(sarvam):
    llm = dict(GOOD, hi_name="अनमौल", hi_line="नमस्ते अनमौल!")
    respx.post(CHAT).mock(return_value=chat_reply(llm))
    s = await smn.build(smn.Form(name="अनमोल"), sarvam)
    assert s.lines[0].text == smn.TEMPLATES["hi"].format(n="अनमोल")  # LLM line lacked the typed name
    assert s.lines[1].text == GOOD["en_line"]
    await sarvam.aclose()


@pytest.mark.parametrize("data", [
    {"name": ""},
    {"name": "x" * 41},
    {"name": "Anmol123"},
    {"name": "<script>"},
    {"name": "Anmol", "city": "y" * 31},
    {"name": "Anmol", "about": "visit http://x.co"},
])
def test_form_rejects_bad_input(data):
    with pytest.raises(ValidationError):
        smn.Form.model_validate(data)


def test_form_accepts_real_names():
    for n in ["Venkata Subrahmanyam", "O'Brien-Iyer", "अनमोल दीप", "Dr. K. Rao"]:
        smn.Form(name=n)


def test_say_my_name_end_to_end(client):  # noqa: F811
    c, mock = client
    mock.post(CHAT).mock(return_value=chat_reply(GOOD))
    r = c.post("/api/say-my-name", json={"name": "Anmol", "city": "Pune"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["captions"]) == 11
    assert data["card"]["kicker"].startswith("SAY MY NAME")
    assert c.get(data["audio_url"]).status_code == 200
    assert "phone_audio_url" not in data
