"""Bulbul commentary: one line per event, stale lines dropped. Sarvam faked."""

from __future__ import annotations

import asyncio
import json

from bulbul_build.commentary import Commentary, Line, limit_name, line_ok, name_allowed, prompt
from bulbul_build.guard import LineQuota, RateLimiter


class FakeWS:
    def __init__(self):
        self.sent: list = []

    async def send_text(self, t):
        self.sent.append(json.loads(t))

    async def send_bytes(self, b):
        self.sent.append(b)


class FakeSarvam:
    def __init__(self, line="क्या shot है! 6 runs!", delay=0.0):
        self.line, self.delay, self.calls = line, delay, 0

    async def chat_json(self, system, user, schema, **kw):
        self.calls += 1
        await asyncio.sleep(self.delay)
        return Line(line=self.line)

    async def tts_stream(self, text, language, speaker, *, mode, pace=1.0):
        yield b"\x01\x00\x02"
        yield b"\x00"


def test_event_gets_a_spoken_line():
    ws, sv = FakeWS(), FakeSarvam()
    c = Commentary(ws, sv)

    async def go():
        await c.on_event({"id": 7, "kind": "hit", "detail": {"runs": 6}, "state": {"runs": 6}})
        await c.current

    asyncio.run(go())
    kinds = [m["type"] if isinstance(m, dict) else "pcm" for m in ws.sent]
    assert kinds[0] == "line" and kinds[-1] == "line_end" and "pcm" in kinds
    pcm = b"".join(m[4:] for m in ws.sent if isinstance(m, bytes))
    assert pcm == b"\x01\x00\x02\x00"  # whole int16 samples only


def test_newer_event_drops_an_unspoken_line():
    ws, sv = FakeWS(), FakeSarvam(delay=0.05)
    c = Commentary(ws, sv)

    async def go():
        await c.on_event({"id": 1, "kind": "hit"})
        await asyncio.sleep(0.01)  # still waiting on the LLM
        await c.on_event({"id": 2, "kind": "wicket"})
        await c.current

    asyncio.run(go())
    assert {"type": "skip", "id": 1} in ws.sent
    assert [m["id"] for m in ws.sent if isinstance(m, dict) and m["type"] == "line"] == [2]


def test_romanised_line_falls_back_to_devanagari():
    assert not line_ok("Kya shot maara hai bhai")
    assert line_ok("क्या shot मारा है!")


def test_prompt_carries_score_and_habits():
    p = prompt({"kind": "over", "state": {"need": 12}, "player": {"early": 4}}, ["पहली line"])
    assert '"need": 12' in p and '"early": 4' in p and "पहली line" in p


def test_name_is_withheld_after_a_recent_use():
    event = {"kind": "hit", "state": {"batter": "Anmol", "runs": 4}}
    assert '"batter": "Anmol"' in prompt(event, ["चौका!", "बढ़िया", "छक्का!"])
    p = prompt(event, ["क्या shot, anmol!", "चौका!"])
    # Not in the score, and not in its own past lines either (it copied it from there).
    assert "anmol" not in p.lower() and '"runs": 4' in p
    assert event["state"]["batter"] == "Anmol"  # the caller's event is untouched


def test_name_at_most_once_and_never_back_to_back():
    assert limit_name("Anmol, ये क्या, Anmol bowled!", "Anmol", True) == "Anmol, ये क्या, भाई bowled!"
    assert limit_name("Anmol bowled!", "Anmol", False) == "भाई bowled!"
    assert limit_name("Anmol, early! dot", "Anmol", False) == "Early! dot"  # a call-out is dropped
    assert limit_name("भाई, stumps में, Anmol bowled!", "Anmol", False) == "भाई, stumps में, batsman bowled!"
    assert limit_name("Anmolji का shot", "Anmol", False) == "Anmolji का shot"  # whole words only
    assert not name_allowed("Anmol", ["Anmol, चौका!", "dot", "dot"])
    assert name_allowed("Anmol", ["Anmol, चौका!", "dot", "dot", "dot"])


def test_end_line_is_never_cancelled():

    ws, sv = FakeWS(), FakeSarvam(delay=0.03)
    c = Commentary(ws, sv)

    async def go():
        await c.on_event({"id": 1, "kind": "end", "detail": {"won": True}})
        await asyncio.sleep(0.005)
        await c.on_event({"id": 2, "kind": "hit"})  # late event from the last ball
        await c.current

    asyncio.run(go())
    lines = [m["id"] for m in ws.sent if isinstance(m, dict) and m["type"] == "line"]
    assert lines == [1]


def test_ball_lines_are_spaced_out_on_one_connection():
    ws, sv = FakeWS(), FakeSarvam()
    c = Commentary(ws, sv)

    async def go():
        for i in range(5):  # a script firing balls back to back
            await c.on_event({"id": i, "kind": "hit"})
            await c.current

    asyncio.run(go())
    assert sv.calls == 1  # the rest came within MIN_GAP_S


def test_hourly_quota_per_ip_is_shared_across_connections():
    quota, sv = LineQuota(per_hour=2), FakeSarvam()
    sent = []

    async def go():
        for i in range(3):  # three connections from one IP, one start line each
            ws = FakeWS()
            c = Commentary(ws, sv, quota=quota, ip="1.2.3.4")
            await c.on_event({"id": i, "kind": "start"})
            await c.current
            sent.extend(ws.sent)

    asyncio.run(go())
    assert sv.calls == 2
    assert any(isinstance(m, dict) and m.get("type") == "error" for m in sent)
    assert quota.take("5.6.7.8")  # another IP is unaffected


def test_client_ip_behind_proxy_ignores_a_made_up_first_hop():
    class Req:
        headers = {"x-forwarded-for": "6.6.6.6, 1.2.3.4"}
        client = None

    assert RateLimiter(5, trust_proxy=True).client_ip(Req()) == "1.2.3.4"
