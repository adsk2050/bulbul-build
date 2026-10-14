"""Railway announcement mode. Sarvam is mocked with respx; nothing is billed."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from bulbul_build.budget import Caps, Ledger
from bulbul_build.modes import railway_announcement as ra
from bulbul_build.sarvam import BASE, Sarvam
from test_core import tts_response

GOOD = {"friend": "Rahul", "origin": "Bed", "destination": "Office", "late_minutes": 200,
        "late_for": "Garba night", "platform": 4, "train_number": "12951", "regional": "mr"}


def chat(content: str) -> httpx.Response:
    return httpx.Response(200, json={
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10},
    })


def marathi(n: int = 6, number: str = "1 2 9 5 1") -> str:
    lines = [f"{i+1}. प्रवाशांनी कृपया लक्ष द्यावे {i}" for i in range(n)]
    lines[1] = f"2. गाडी क्रमांक {number}, Rahul Express, Bed पासून Office पर्यंत, उशिरा धावत आहे."
    return json.dumps({"lines": lines}, ensure_ascii=False)


@pytest.fixture
def sarvam(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=10.0, total_inr=10.0, per_call_inr=5.0))
    return Sarvam("k", ledger, tmp_path / "cache")


def test_digits_read_one_by_one():
    assert ra.say_digits("12951", "hi", "words") == "एक दो नौ पाँच एक"
    assert ra.say_digits("10203", "en", "words") == "one zero two zero three"
    assert ra.say_digits("12951", "en", "spaced") == "1 2 9 5 1"


def test_delay_wording():
    assert ra.delay(200, "en") == "3 hours 20 minutes"
    assert ra.delay(60, "en") == "1 hour"
    assert ra.delay(45, "hi") == "45 मिनट"
    assert ra.delay(125, "hi") == "2 घंटे 5 मिनट"


def test_train_number_is_stable_and_five_digits():
    f = ra.Form(**{**GOOD, "train_number": ""})
    a, b = ra.train_number(f), ra.train_number(ra.Form(**{**GOOD, "train_number": "", "friend": "rahul "}))
    assert a == b and len(a) == 5 and a.isdigit()


@pytest.mark.parametrize("bad", [
    {"train_number": "1295"}, {"train_number": "12a51"}, {"platform": 0}, {"late_minutes": 0},
    {"friend": "x" * 26}, {"friend": "Ra\nhul"}, {"regional": "xx"}, {"late_for": "y" * 41},
])
def test_form_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        ra.Form(**{**GOOD, **bad})


@respx.mock
async def test_three_languages(sarvam, monkeypatch):
    monkeypatch.setattr(ra.random, "randrange", lambda n: 0)
    route = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=chat(marathi()))
    s = await ra.build(ra.Form(**GOOD), sarvam)
    assert [ln.language for ln in s.lines] == ["hi-IN"] * 6 + ["en-IN"] * 6 + ["mr-IN"] * 6
    assert s.lines[1].text.startswith("गाड़ी संख्या एक दो नौ पाँच एक")
    assert s.lines[1].caption.startswith("गाड़ी संख्या 12951")
    assert "one two nine five one" in s.lines[7].text and "3 hours 20 minutes" in s.lines[7].text
    assert "Garba night" in s.lines[8].text
    assert s.lines[13].text.startswith("गाडी क्रमांक")  # numbering stripped
    assert s.phone_line is False and "DOST RAILWAYS" in s.card["kicker"]
    assert "Rahul" in s.title and "Rahul" in s.share_text
    sent = json.loads(route.calls[0].request.content)
    assert "Marathi" in sent["messages"][1]["content"] and "1 2 9 5 1" in sent["messages"][1]["content"]
    await sarvam.aclose()


@pytest.mark.parametrize("content", [
    "not json",
    marathi(n=4),  # wrong line count
    marathi(number="12951"),  # train number not kept digit by digit
])
@respx.mock
async def test_bad_llm_output_drops_regional(sarvam, content):
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=chat(content))
    s = await ra.build(ra.Form(**GOOD), sarvam)
    assert {ln.language for ln in s.lines} == {"hi-IN", "en-IN"}
    assert len(s.lines) == 12
    await sarvam.aclose()


@respx.mock
async def test_without_late_for(sarvam):
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=chat(marathi(n=5)))
    s = await ra.build(ra.Form(**{**GOOD, "late_for": ""}), sarvam)
    assert len(s.lines) == 15
    await sarvam.aclose()


def test_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "ledger.sqlite"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("PER_IP_PER_MIN", "100")
    import importlib

    import bulbul_build.app as appmod

    appmod = importlib.reload(appmod)
    with respx.mock(assert_all_called=False) as mock:
        tts = mock.post("https://api.sarvam.ai/text-to-speech").mock(side_effect=tts_response)
        mock.post("https://api.sarvam.ai/v1/chat/completions").mock(return_value=chat(marathi()))
        mock.route(host="testserver").pass_through()
        with TestClient(appmod.app) as c:
            assert "railway-announcement" in [m["slug"] for m in c.get("/api/modes").json()]
            r = c.post("/api/railway-announcement", json=GOOD)
            assert r.status_code == 200, r.text
            data = r.json()
            assert len(data["captions"]) == 18 and "phone_audio_url" not in data
            assert "12951" in data["captions"][1]["text"]
            assert tts.call_count == 18
            sent = [json.loads(call.request.content) for call in tts.calls]
            assert {b["speaker"] for b in sent} == {"shreya_hi_news", "shubh_en_narration", "mrunal_mr_narration"}
            assert c.post("/api/railway-announcement", json={**GOOD, "train_number": "999"}).status_code == 422
