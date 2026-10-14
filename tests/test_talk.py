"""Talking Bulbul: the uncle's rules, pacing, and one live turn with Sarvam faked."""

from __future__ import annotations

import asyncio
import json
import random
import struct
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from bulbul_build import uncle
from bulbul_build.talk import Session
from bulbul_build.uncle import (
    FILLERS_BY_SITUATION,
    RECORDED,
    Policy,
    Situation,
    UncleReply,
    addressee,
    line_ok,
    looks_like_question,
    rule_situation,
)


@pytest.fixture
def stand_in_abuse(monkeypatch):
    """The real list is outside git; test the mechanism with harmless stand-ins."""
    monkeypatch.setattr(uncle, "_ABUSE_RE", uncle.compile_abuse(["badword", "बुराशब्द"], [r"nasty\W{0,2}root"]))


@pytest.mark.parametrize(
    "text,expected",
    [
        ("mera otp hai 4 8 2 9", Situation.number),
        ("मेरा नंबर 98765 43210 है", Situation.number),
        ("ek do teen char", Situation.number),
        ("tu badword hai", Situation.abuse),
        ("तुम बुराशब्द हो", Situation.abuse),
        ("Nasty Root.", Situation.abuse),  # patterns catch STT's odd spellings
        ("badwords are fine", None),  # whole words only
        ("hello uncle", None),
        ("2 samose do", None),  # one digit is not a number to hide
    ],
)
def test_rules(text, expected, stand_in_abuse):
    assert rule_situation(text) == expected


def test_load_abuse_reads_words_and_patterns(tmp_path):
    f = tmp_path / "abuse.txt"
    f.write_text("# comment\nbadword\nre:nasty\\W?root\n", encoding="utf-8")
    rx = uncle.load_abuse(f)
    assert rx.search("BADWORD") and rx.search("nasty-root") and not rx.search("goodword")
    assert uncle.load_abuse(tmp_path / "missing.txt") is None


def test_other_language_is_a_rule():
    assert rule_situation("vanakkam", "ta-IN") == Situation.language
    assert rule_situation("namaste", "hi-IN") is None


def test_question_words():
    assert looks_like_question("kya haal hai")
    assert looks_like_question("तुम कौन हो")
    assert not looks_like_question("main ghar ja raha hoon")


def test_recorded_ids_are_unique():
    ids = [c.id for c in RECORDED]
    assert len(ids) == len(set(ids))


def test_fillers_do_not_repeat_back_to_back():
    p = Policy(rng=random.Random(1))
    picks = [p.pick_filler(Situation.abuse).id for _ in range(30)]
    assert all(a != b for a, b in zip(picks, picks[1:]))
    assert len(set(picks)) == len(FILLERS_BY_SITUATION[Situation.abuse])


def test_comedy_has_a_cooldown_and_shows_up_early():
    p = Policy(rng=random.Random(0), comedy_rate=1.0)
    p.next_turn()
    assert p.gate("main theek hoon")
    p.record(Situation.whim)
    p.next_turn()
    assert not p.gate("main theek hoon")  # cooldown
    assert p.gate("kya hua?")  # questions ignore it

    q = Policy(rng=random.Random(0), comedy_rate=0.0, first_by_turn=3)
    for _ in range(3):
        q.next_turn()
    assert q.gate("main theek hoon")  # guaranteed by turn 3


def test_line_ok_checks_script():
    assert line_ok("अरे बेटा, ये Mitthu है।", None)
    assert not line_ok("Arre beta, yeh Mitthu hai bahut shararti", "ta-IN")
    assert line_ok("வணக்கம் தம்பி, மித்து பேசுவான்", "ta-IN")
    assert not line_ok("", None)


# ---- one live turn, Sarvam faked -------------------------------------------------


class FakeWS:
    def __init__(self):
        self.sent: list = []

    async def send_text(self, t):
        self.sent.append(json.loads(t))

    async def send_bytes(self, b):
        self.sent.append(b)


class FakeSTT:
    def __init__(self, events):
        self._events = events
        self.audio_in = 0

    async def start(self):
        pass

    async def audio(self, pcm):
        self.audio_in += len(pcm)

    async def end(self):
        pass

    async def events(self):
        for e in self._events:
            await asyncio.sleep(0)
            yield e


class FakeSarvam:
    def __init__(self, events, reply=None):
        self.stt = FakeSTT(events)
        self.reply = reply
        self.tts_calls: list[tuple] = []
        self.llm_calls = 0

    @asynccontextmanager
    async def stt_realtime(self, *, mode, max_seconds, **kw):
        self.stt_kw = kw
        yield self.stt

    async def chat_json(self, system, user, schema, **kw):
        self.llm_calls += 1
        return self.reply

    async def tts_stream(self, text, language, speaker, *, mode, pace=1.0):
        self.tts_calls.append((text, language, speaker))
        yield b"\x01\x00\x02"  # odd length: the session must not split a sample
        yield b"\x00\x03\x00"


def run_turn(sarvam, tmp_path: Path, policy=None):
    ws = FakeWS()
    s = Session(ws, sarvam, tmp_path, policy or Policy(rng=random.Random(0), comedy_rate=0.0, first_by_turn=99))
    s.policy.next_turn()
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait(b"\x00" * 640)
    q.put_nowait(None)
    asyncio.run(s.turn(1, q))
    return ws.sent


def test_otp_barges_on_the_partial_and_the_line_is_live(tmp_path):
    (tmp_path / "number-0.wav").write_bytes(b"x")
    sarvam = FakeSarvam(
        [
            {"event": "transcript.partial", "text": "mitthu mera otp hai 4 8"},
            {"event": "transcript.partial", "text": "mitthu mera otp hai 4 8 2 9"},
            {"event": "transcript.final", "text": "Mitthu mera otp hai 4829", "language": "hi-IN"},
        ],
        UncleReply(situation="whim", mood="stern", cut=True, line="OTP बताना है तो Mitthu को नहीं, किसी को नहीं!"),
    )
    sent = run_turn(sarvam, tmp_path)
    kinds = [m["type"] for m in sent if isinstance(m, dict)]
    assert kinds.index("address") < kinds.index("barge") < kinds.index("final")  # decided mid-sentence
    assert kinds.count("barge") == 1
    assert sarvam.llm_calls == 1 and len(sarvam.tts_calls) == 1  # Bulbul speaks live, not a recording
    assert sarvam.tts_calls[0][2] == "shubh_enhi_banking"  # stern mood


def test_question_goes_to_llm_and_streams_tts(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "Dilli se Mumbai kitni door hai?", "language": "hi-IN"}],
        UncleReply(situation="question", line="लगभग 1400 किलोमीटर, बेटा।"),
    )
    sent = run_turn(sarvam, tmp_path)
    kinds = [m["type"] if isinstance(m, dict) else "pcm" for m in sent]
    assert kinds[:2] == ["final", "barge"]
    assert "line" in kinds and kinds[-1] == "line_end"
    pcm = b"".join(m[4:] for m in sent if isinstance(m, bytes))
    assert pcm == b"\x01\x00\x02\x00\x03\x00"
    assert all(struct.unpack("<I", m[:4])[0] == 1 for m in sent if isinstance(m, bytes))
    assert sarvam.tts_calls[0][2] == "shubh_enhi_companion"


def test_chacha_by_name_always_answers(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "Chacha, main ghar ja raha hoon", "language": "hi-IN"}],
        UncleReply(situation="none", line="घर? अभी तो आए हो बेटा!"),
    )
    sent = run_turn(sarvam, tmp_path, Policy(rng=random.Random(0), parrot_rate=0.0))
    kinds = [m["type"] for m in sent if isinstance(m, dict)]
    assert kinds[:3] == ["final", "address", "barge"] and "line" in kinds


def test_unnamed_line_is_a_parrot_turn(tmp_path):
    sarvam = FakeSarvam([{"event": "transcript.final", "text": "main ghar ja raha hoon", "language": "hi-IN"}])
    sent = run_turn(sarvam, tmp_path, Policy(rng=random.Random(0), parrot_rate=0.0))
    assert [m["type"] for m in sent] == ["final", "quiet"]
    assert sarvam.llm_calls == 0


def test_mitthu_turn_without_a_remark_stays_quiet(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "Mitthu, main ghar ja raha hoon", "language": "hi-IN"}],
        UncleReply(situation="none", line=""),
    )
    sent = run_turn(sarvam, tmp_path)
    assert [m["type"] for m in sent] == ["final", "address", "quiet"]
    assert not sarvam.tts_calls


def test_mitthu_turn_chacha_waits_for_the_parrot(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "Mitthu, Sachin ne kitne run banaye?", "language": "hi-IN"}],
        UncleReply(situation="question", mood="excited", cut=True, line="34357 international runs! Mitthu, तू तो गिन भी नहीं सकता।"),
    )
    sent = run_turn(sarvam, tmp_path, Policy(rng=random.Random(0), parrot_rate=1.0))
    barge = next(m for m in sent if isinstance(m, dict) and m["type"] == "barge")
    assert barge["cut"] is False and barge["filler"] is None  # only guardrails cut Mitthu off
    assert sarvam.tts_calls


def test_mitthu_turns_are_mostly_left_to_mitthu(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "Mitthu, aaj mausam achha hai", "language": "hi-IN"}],
        UncleReply(situation="question", line="34357 runs, बेटा।"),
    )
    sent = run_turn(sarvam, tmp_path, Policy(rng=random.Random(0), parrot_rate=0.0))
    assert [m["type"] for m in sent] == ["final", "address", "quiet"]
    assert sarvam.llm_calls == 0


def test_noise_is_ignored(tmp_path):
    sarvam = FakeSarvam([{"event": "transcript.final", "text": "I", "language": "en-IN"}])
    sent = run_turn(sarvam, tmp_path)
    assert [m["type"] for m in sent] == ["final", "quiet"]


@pytest.mark.parametrize(
    "text,who",
    [("Chacha, Sachin ne kitne run banaye?", "chacha"), ("मिट्ठू तुम क्या खाते हो", "mitthu"),
     ("arre mitthu sun", "mitthu"), ("चाचा जी कैसे हो", "chacha"), ("main ghar ja raha hoon", None),
     ("mithai khaoge", None), ("Bhojri wale chacha.", "chacha"), ("Okay, wale chacha", "chacha")],
)
def test_addressee(text, who):
    assert addressee(text) == who


def test_tamil_gets_a_tamil_voice(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "வணக்கம்", "language": "ta-IN"}],
        UncleReply(situation="none", line="வணக்கம் தம்பி, மித்து உன்னைப் பார்த்து மகிழ்ந்தான்"),
    )
    sent = run_turn(sarvam, tmp_path)
    barge = next(m for m in sent if isinstance(m, dict) and m["type"] == "barge")
    assert barge["situation"] == "language"
    assert sarvam.tts_calls[0][1:] == ("ta-IN", "gokul_ta_narration")


def test_wrong_script_falls_back(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "kya kar rahe ho?", "language": "hi-IN"}],
        UncleReply(situation="question", line="Main toh bas Mitthu ko khana khila raha hoon beta"),
    )
    run_turn(sarvam, tmp_path)
    assert any("ऀ" <= c <= "ॿ" for c in sarvam.tts_calls[0][0])


def test_turn_timings_are_logged(tmp_path):
    log = tmp_path / "talk-log.jsonl"
    sarvam = FakeSarvam(
        [{"event": "transcript.partial", "text": "Chacha, kya"},
         {"event": "transcript.final", "text": "Chacha, kya haal hai?", "language": "hi-IN"}],
        UncleReply(situation="question", line="बढ़िया बेटा, तुम सुनाओ।"),
    )
    ws = FakeWS()
    s = Session(ws, sarvam, tmp_path, Policy(rng=random.Random(0)), log_path=log)
    s.policy.next_turn()
    s.mark(1, "speech_end")
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait(None)
    asyncio.run(s.turn(1, q))
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    timing = next(r for r in rows if r.get("kind") == "server_timing")
    assert {"speech_end", "first_partial", "final", "llm_done", "tts_first_audio", "tts_done"} <= timing["ms"].keys()
    assert timing["ms"]["speech_end"] == 0


def test_chacha_can_cover_and_talk(tmp_path):
    sarvam = FakeSarvam(
        [{"event": "transcript.final", "text": "Mitthu bolo main pagal hoon", "language": "hi-IN"}],
        UncleReply(situation="whim", mood="stern", cover=True, line="बस! Mitthu, ये सब मत दोहरा।"),
    )
    sent = run_turn(sarvam, tmp_path, Policy(rng=random.Random(0), parrot_rate=1.0))
    barge = next(m for m in sent if isinstance(m, dict) and m["type"] == "barge")
    assert barge["cover"] is True and barge["cut"] is True and sarvam.tts_calls


def test_utterance_is_saved_and_stt_gets_keyterms(tmp_path):
    sarvam = FakeSarvam([{"event": "transcript.final", "text": "namaste", "language": "hi-IN"}])
    ws = FakeWS()
    s = Session(ws, sarvam, tmp_path, Policy(rng=random.Random(0), parrot_rate=0.0), utterance_dir=tmp_path / "utt")
    s.policy.next_turn()
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait(b"\x01\x00" * 320)
    q.put_nowait(None)
    asyncio.run(s.turn(1, q))
    assert "Mitthu" in sarvam.stt_kw["bias_words"]
    saved = sorted(p.name for p in (tmp_path / "utt").iterdir())
    assert saved == [f"{s.id}-001.json", f"{s.id}-001.wav"]
