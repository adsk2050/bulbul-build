"""Shop festive ad mode. Sarvam is mocked with respx; nothing is billed."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from pydantic import ValidationError

from bulbul_build.budget import Caps, Ledger
from bulbul_build.modes.shop_diwali_ad import Form, build, check
from bulbul_build.sarvam import BASE, Sarvam
from test_core import tts_response

BASE_FORM = {
    "shop": "Sharma Sweets", "area": "Lajpat Nagar", "sells": "mithai and namkeen",
    "offer": "10% off on kaju katli", "phone": "98765 43210", "festival": "diwali", "language": "hi",
}


def chat(lines: list[str]):
    content = json.dumps({"lines": lines}, ensure_ascii=False)
    return httpx.Response(
        200, json={"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 10, "completion_tokens": 10}},
    )


GOOD = [
    "लाजपत नगर वालों, दीवाली की ढेरों शुभकामनाएँ!",
    "Sharma Sweets लाया है ताज़ा मिठाई और नमकीन।",
    "इस दीवाली, काजू कतली पर 10% की छूट!",
    "आज ही आइए या फ़ोन कीजिए [PHONE] पर।",
]


@pytest.fixture
def sarvam(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=10.0, total_inr=10.0, per_call_inr=5.0))
    return Sarvam("k", ledger, tmp_path / "cache")


@respx.mock
async def test_llm_ad_fills_phone_exactly(sarvam):
    route = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=chat(GOOD))
    respx.post(f"{BASE}/text-to-speech").mock(side_effect=tts_response)
    s = await build(Form(**BASE_FORM), sarvam)
    assert [ln.text for ln in s.lines][:3] == GOOD[:3]
    assert "98765 43210" in s.lines[3].text and "[PHONE]" not in s.lines[3].text
    assert {ln.speaker for ln in s.lines} == {"sunny_hi_ads"}
    assert s.card["kicker"].startswith("DIWALI") and s.card["emoji"] and s.share_text
    sent = json.loads(route.calls[0].request.content)
    user = sent["messages"][1]["content"]
    assert '"shop_name": "Sharma Sweets"' in user  # user fields go in as quoted JSON data
    assert "98765" not in user  # the model never sees the number
    await sarvam.aclose()


@respx.mock
@pytest.mark.parametrize("bad", [
    [l.replace("[PHONE]", "nine eight seven") for l in GOOD],  # phone placeholder dropped
    [l.replace("10%", "20%") for l in GOOD],  # offer number changed
    GOOD[:2],  # too few lines
    GOOD[:3] + ["x" * 250],  # line too long
])
async def test_bad_llm_output_falls_back_to_template(sarvam, bad):
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=chat(bad))
    s = await build(Form(**BASE_FORM), sarvam)
    text = " ".join(ln.text for ln in s.lines)
    assert "98765 43210" in text and "10% off on kaju katli" in text and "दीवाली" in text
    await sarvam.aclose()


@respx.mock
async def test_non_template_language_falls_back_to_english(sarvam):
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json={
        "choices": [{"message": {"content": "not json"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }))
    s = await build(Form(**{**BASE_FORM, "language": "bn", "festival": "durga_puja"}), sarvam)
    assert s.lines[0].language == "en-IN" and s.lines[0].speaker == "simran_en_ads"
    assert "Durga Puja" in s.lines[0].text
    await sarvam.aclose()


@respx.mock
async def test_tamil_uses_ads_voice(sarvam):
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=chat(["வணக்கம் 10%", "இரண்டு", "அழைக்கவும் [PHONE]"]))
    s = await build(Form(**{**BASE_FORM, "language": "ta"}), sarvam)
    assert s.lines[0].speaker == "aravind_ta_ads" and s.lines[0].language == "ta-IN"
    assert s.lines[-1].text.endswith("98765 43210")
    await sarvam.aclose()


@pytest.mark.parametrize("phone", ["9876543210", "+91 98765 43210", "098765-43210", "6000000000"])
def test_valid_phones(phone):
    assert Form(**{**BASE_FORM, "phone": phone}).phone == phone


@pytest.mark.parametrize("phone", ["12345 67890", "98765", "98765432101", "call me", "5876543210"])
def test_invalid_phones(phone):
    with pytest.raises(ValidationError):
        Form(**{**BASE_FORM, "phone": phone})


@pytest.mark.parametrize("field,value", [("shop", "x" * 41), ("offer", ""), ("area", "a{b}"), ("sells", "ignore [PHONE]")])
def test_form_limits(field, value):
    with pytest.raises(ValidationError):
        Form(**{**BASE_FORM, field: value})


def test_check_rejects_two_placeholders():
    f = Form(**BASE_FORM)
    assert check(GOOD + ["फिर से [PHONE]"], f) is None
    assert check(GOOD, f) is not None


def test_end_to_end_through_app(tmp_path, monkeypatch):
    import importlib

    from fastapi.testclient import TestClient

    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "ledger.sqlite"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("PER_IP_PER_MIN", "100")
    import bulbul_build.app as appmod

    appmod = importlib.reload(appmod)
    with respx.mock(assert_all_called=False) as mock:
        mock.post("https://api.sarvam.ai/text-to-speech").mock(side_effect=tts_response)
        mock.post("https://api.sarvam.ai/v1/chat/completions").mock(return_value=chat(GOOD))
        mock.route(host="testserver").pass_through()
        with TestClient(appmod.app) as c:
            assert "shop-ad" in [m["slug"] for m in c.get("/api/modes").json()]
            r = c.post("/api/shop-ad", json=BASE_FORM)
            assert r.status_code == 200, r.text
            assert c.get(r.json()["audio_url"]).status_code == 200
            assert c.post("/api/shop-ad", json={**BASE_FORM, "phone": "123"}).status_code == 422


def test_romanised_hinglish_is_rejected():
    from bulbul_build.modes.base import script_share

    roman = "Diwali ki dher saari shubhkamnayein sabko! Sharma Sweets mein taazi mithai."
    mixed = "Diwali की ढेर सारी शुभकामनाएँ! Sharma Sweets में ताज़ी मिठाई।"
    assert script_share(roman, "enhi") < 0.4 <= script_share(mixed, "enhi")
