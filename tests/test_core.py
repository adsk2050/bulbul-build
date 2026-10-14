"""Core tests. No test reaches Sarvam: every HTTP call is mocked with respx."""

from __future__ import annotations

import base64
import io
import json
import threading
import wave

import httpx
import pytest
import respx

from bulbul_build.budget import BudgetExceeded, Caps, Ledger, cost_of
from bulbul_build.sarvam import BASE, Sarvam


def fake_wav(seconds: float = 0.5, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    return buf.getvalue()


def tts_response(request):
    return httpx.Response(200, json={"request_id": "x", "audios": [base64.b64encode(fake_wav()).decode()]})


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "l.sqlite", Caps(daily_inr=1.0, total_inr=2.0, per_call_inr=0.5))


def test_reserve_refuses_past_daily_cap(ledger):
    ledger.reserve("tts", "t", 0.4, 200)
    ledger.reserve("tts", "t", 0.4, 200)
    with pytest.raises(BudgetExceeded):
        ledger.reserve("tts", "t", 0.4, 200)
    assert ledger.spent() == pytest.approx(0.8)


def test_per_call_cap(ledger):
    with pytest.raises(BudgetExceeded):
        ledger.reserve("tts", "t", 0.6, 300)


def test_concurrent_reservations_never_pass_cap(ledger):
    ok, refused = [], []

    def worker():
        try:
            ledger.reserve("tts", "t", 0.1, 50)
            ok.append(1)
        except BudgetExceeded:
            refused.append(1)

    threads = [threading.Thread(target=worker) for _ in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(ok) == 10  # daily cap 1.0 / 0.1
    assert ledger.spent() <= 1.0 + 1e-9


@respx.mock
async def test_tts_charges_once_then_caches(ledger, tmp_path):
    route = respx.post(f"{BASE}/text-to-speech").mock(side_effect=tts_response)
    s = Sarvam("k", ledger, tmp_path / "cache")
    a = await s.tts("नमस्ते Rahul", "hi-IN", "simran_hi_recovery", mode="t")
    b = await s.tts("नमस्ते Rahul", "hi-IN", "simran_hi_recovery", mode="t")
    assert a == b and route.call_count == 1
    assert ledger.spent() == pytest.approx(cost_of("tts", len("नमस्ते Rahul")))
    sent = json.loads(route.calls[0].request.content)
    assert sent["model"] == "bulbul:v4-flash"
    await s.aclose()


@respx.mock
async def test_client_error_is_not_charged(ledger, tmp_path):
    respx.post(f"{BASE}/text-to-speech").mock(return_value=httpx.Response(400, json={"error": "bad"}))
    s = Sarvam("k", ledger, tmp_path / "cache")
    with pytest.raises(Exception):
        await s.tts("hello", "en-IN", "simran_en_recovery", mode="t")
    assert ledger.spent() == 0
    await s.aclose()


@respx.mock
async def test_server_error_keeps_reservation(ledger, tmp_path):
    respx.post(f"{BASE}/text-to-speech").mock(return_value=httpx.Response(503))
    s = Sarvam("k", ledger, tmp_path / "cache")
    with pytest.raises(Exception):
        await s.tts("hello", "en-IN", "simran_en_recovery", mode="t")
    assert ledger.spent() == pytest.approx(cost_of("tts", 5))
    await s.aclose()


def test_inr_grouping():
    from bulbul_build.modes.udhaar_wapas import inr

    assert [inr(n) for n in (5, 850, 1000, 50000, 500000, 12345678)] == [
        "5", "850", "1,000", "50,000", "5,00,000", "1,23,45,678",
    ]
