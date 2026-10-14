"""Live Talking Bulbul session: one browser WebSocket per visitor.

Browser -> server
  {"type": "speech_start"}   the browser's VAD heard speech (with ~200 ms preroll)
  <binary>                   16 kHz mono int16 PCM, only while speaking
  {"type": "speech_end"}     the browser's VAD heard ~300 ms of silence

Server -> browser
  {"type": "partial", "text"}                       live transcript
  {"type": "final", "text", "language"}
  {"type": "barge", "turn", "situation", "cut", "cover", "filler"}
                                                    uncle steps in: cut Mitthu off if `cut`,
                                                    hand over his beak if `cover`, play the
                                                    filler URL (may be null) now
  {"type": "address", "turn", "who"}               visitor opened with "mitthu" or "chacha"
  {"type": "line", "turn", "text", "audio"}         uncle's line; `audio` is a URL when
                                                    pre-recorded, else null and PCM follows
  <binary>                                          4-byte little-endian turn id + 24 kHz int16 PCM
  {"type": "line_end", "turn", "ttfa_ms"}
  {"type": "quiet", "turn"}                         uncle stays out of it
  {"type": "error", "message"}

Mitthu's repeat never touches the server: the browser replays its own recording.
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import struct
import time
import wave
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

from .budget import BudgetExceeded
from .sarvam import STT_MODEL, Sarvam, SarvamError
from .uncle import (
    ADDRESSED_NOTE,
    FALLBACK_LINES,
    GUARDRAIL_NOTE,
    GUARDRAILS,
    MOOD_VOICE,
    PARROT_NOTE,
    SYSTEM,
    Policy,
    Situation,
    UncleReply,
    addressee,
    history_prompt,
    looks_like_question,
    line_ok,
    reply_language,
    rule_situation,
    uncle_voice,
)

log = logging.getLogger("bulbul.talk")

MAX_UTTERANCE_S = 12.0
# Names and words STT should expect; Sarvam biases towards them (saaras:v4).
STT_BIAS_WORDS = ["Mitthu", "मिट्ठू", "Chacha", "चाचा", "Sharma uncle", "Bulbul", "बुलबुल"]
STT_PROMPT = "Casual Hindi, English and Hinglish talk to a pet bulbul named Mitthu and his owner Chacha."
MAX_TURNS = 80
HISTORY_TURNS = 8
FILLER_RATE = 0.4
MODE = "talking-bulbul"


class Session:
    def __init__(
        self, ws: WebSocket, sarvam: Sarvam, recorded_dir: Path,
        policy: Policy | None = None, log_path: Path | None = None, utterance_dir: Path | None = None,
    ):
        self.utterance_dir = utterance_dir
        self.ws = ws
        self.id = secrets.token_hex(4)
        self.log_path = log_path
        self.history: list[tuple[str, bool, str | None]] = []  # visitor, Mitthu parroted, Chacha
        self.sarvam = sarvam
        self.recorded_dir = recorded_dir
        self.policy = policy or Policy()
        self.frames: asyncio.Queue[bytes | None] | None = None
        self.task: asyncio.Task | None = None
        self.send_lock = asyncio.Lock()
        self.marks: dict[int, dict[str, float]] = {}  # per-turn timings, see mark()

    # ---- plumbing --------------------------------------------------------

    async def send(self, msg: dict) -> None:
        async with self.send_lock:
            await self.ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def send_pcm(self, turn: int, pcm: bytes) -> None:
        async with self.send_lock:
            await self.ws.send_bytes(struct.pack("<I", turn) + pcm)

    def recorded_url(self, clip_id: str) -> str | None:
        return f"/uncle/{clip_id}.wav" if (self.recorded_dir / f"{clip_id}.wav").exists() else None

    async def run(self) -> None:
        try:
            while True:
                msg = await self.ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if msg.get("bytes") is not None:
                    if self.frames is not None:
                        self.frames.put_nowait(msg["bytes"])
                    continue
                data = json.loads(msg.get("text") or "{}")
                kind = data.get("type")
                if kind == "speech_start":
                    await self.start_turn()
                elif kind == "speech_end" and self.frames is not None:
                    self.mark(self.policy.turn, "speech_end")
                    self.frames.put_nowait(None)
                    self.frames = None
                elif kind == "timing":
                    self.log({"kind": "client_timing", "turn": data.get("turn"), "ms": data.get("ms")})
        except WebSocketDisconnect:
            pass
        finally:
            if self.task and not self.task.done():
                self.task.cancel()

    async def start_turn(self) -> None:
        if self.policy.turn >= MAX_TURNS:
            await self.send({"type": "error", "message": "Mitthu is tired. Come back later!"})
            return
        if self.frames is not None:  # a speech_start without an end: close the old turn
            self.frames.put_nowait(None)
        self.policy.next_turn()
        self.mark(self.policy.turn, "speech_start")
        self.frames = asyncio.Queue()
        self.task = asyncio.create_task(self.turn(self.policy.turn, self.frames))

    # ---- one turn --------------------------------------------------------

    async def turn(self, turn: int, frames: asyncio.Queue) -> None:
        barged: Situation | None = None
        who: str | None = None
        text, language = "", None
        heard = bytearray()  # the utterance as sent to STT, kept for replay tests
        try:
            async with self.sarvam.stt_realtime(
                mode=MODE, max_seconds=MAX_UTTERANCE_S, bias_words=STT_BIAS_WORDS, prompt=STT_PROMPT
            ) as stt:
                await stt.start()

                async def pump():
                    while (pcm := await frames.get()) is not None:
                        heard.extend(pcm)
                        await stt.audio(pcm)
                    await stt.end()

                pumper = asyncio.create_task(pump())
                try:
                    async for ev in stt.events():
                        kind = ev.get("event") or ev.get("type")
                        if kind == "transcript.partial":
                            self.mark(turn, "first_partial")
                            partial = ev.get("text") or ""
                            await self.send({"type": "partial", "text": partial})
                            if who is None and (who := addressee(partial)):
                                await self.send({"type": "address", "turn": turn, "who": who})
                            if barged is None and (s := rule_situation(partial)):
                                barged = await self.barge(turn, s)
                        elif kind == "transcript.final":
                            self.mark(turn, "final")
                            text, language = ev.get("text") or "", ev.get("language")
                            await self.send({"type": "final", "text": text, "language": language})
                            if who is None and (who := addressee(text)):
                                await self.send({"type": "address", "turn": turn, "who": who})
                            break
                        elif kind == "error":
                            raise SarvamError(f"STT error: {ev.get('message')}")
                finally:
                    pumper.cancel()
            self.save_utterance(turn, bytes(heard), text, language)
            await self.respond(turn, text, language, barged, who)
            self.log_timing(turn)
        except BudgetExceeded:
            await self.send({"type": "error", "message": "Aaj ka quota khatam! Try tomorrow."})
        except (SarvamError, asyncio.CancelledError) as e:
            if isinstance(e, asyncio.CancelledError):
                raise
            log.error("turn %d failed: %s", turn, e)
            await self.send({"type": "error", "message": "Mitthu got confused. Say it again?"})

    async def barge(
        self, turn: int, situation: Situation, *, cut: bool = True, filler: bool = True, cover: bool | None = None
    ) -> Situation:
        self.policy.record(situation)
        self.mark(turn, "barge")
        url = self.recorded_url(self.policy.pick_filler(situation).id) if filler else None
        if cover is None:
            cover = situation in GUARDRAILS
        await self.send({"type": "barge", "turn": turn, "situation": situation.value, "cut": cut,
                         "cover": cover, "filler": url})
        return situation

    async def respond(
        self, turn: int, text: str, language: str | None, barged: Situation | None, who: str | None = None
    ) -> None:
        """Who speaks: "Chacha, ..." gets Chacha alone. Anything else, Mitthu parrots (in the
        browser) and Chacha cuts in when he likes, always for rude words and OTPs."""
        if sum(c.isalpha() for c in text) < 2:  # noise, a cough, a stray "I"
            await self.send({"type": "quiet", "turn": turn})
            return
        parroting = who != "chacha"
        if barged is None and (s := rule_situation(text, language)):
            barged = await self.barge(turn, s)
        if barged in GUARDRAILS:
            note = GUARDRAIL_NOTE[barged.value]
        elif parroting:
            note = PARROT_NOTE
            # Let Mitthu be heard: Chacha remarks on about 1 in 3 parrot turns, never twice
            # running, but always answers a real question or a visitor in another language.
            if barged is None and not looks_like_question(text) and not self.policy.gate_parrot():
                self.remember(turn, text, language, None, None, parroting)
                await self.send({"type": "quiet", "turn": turn})
                return
        else:
            note = ADDRESSED_NOTE
        self.mark(turn, "llm_start")
        reply = await self.ask_llm(text, language, note, parroting)
        self.mark(turn, "llm_done")
        if barged is None and parroting:
            # He waits for Mitthu to finish; only guardrails cut him off mid-word.
            if reply is None or reply.situation == "none":
                self.remember(turn, text, language, None, None, parroting)
                await self.send({"type": "quiet", "turn": turn})
                return
            # His hand can go over the beak while he talks, if he thinks Mitthu should shut up.
            barged = await self.barge(turn, Situation(reply.situation), cut=reply.cover, filler=reply.cover,
                                      cover=reply.cover)
        elif barged is None:
            situation = Situation(reply.situation) if reply and reply.situation != "none" else Situation.whim
            # Mitthu is not talking, so nothing to cut. A "हम्म…" now and then covers the
            # ~1 s wait; one every turn got repetitive.
            barged = await self.barge(turn, situation, cut=False, filler=self.policy.rng.random() < FILLER_RATE)

        line = reply.line.strip() if reply else ""
        mood = reply.mood if reply else "stern"
        if not line_ok(line, language if barged == Situation.language else None):
            line = self.policy.rng.choice(FALLBACK_LINES[barged])
            language = None
        self.remember(turn, text, language, barged, line, parroting)
        await self.speak(turn, line, language, mood)

    def remember(
        self, turn: int, text: str, language: str | None, situation: Situation | None,
        line: str | None, parroted: bool = False,
    ) -> None:
        self.history.append((text, parroted, line))
        del self.history[:-HISTORY_TURNS]
        self.log({"turn": turn, "visitor": text, "language": language,
                  "situation": situation.value if situation else None, "chacha": line})

    def log(self, entry: dict) -> None:
        if self.log_path:
            entry = {"ts": round(time.time(), 1), "session": self.id, **entry}
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_utterance(self, turn: int, pcm: bytes, text: str, language: str | None) -> None:
        """Keep what STT heard (16 kHz WAV + its transcript) to compare STT settings later."""
        if not self.utterance_dir or not pcm:
            return
        self.utterance_dir.mkdir(parents=True, exist_ok=True)
        stem = self.utterance_dir / f"{self.id}-{turn:03d}"
        with wave.open(str(stem.with_suffix(".wav")), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(pcm)
        stem.with_suffix(".json").write_text(
            json.dumps({"text": text, "language": language, "model": STT_MODEL}, ensure_ascii=False), encoding="utf-8"
        )

    def mark(self, turn: int, key: str) -> None:
        """Record the first time `key` happened in this turn."""
        self.marks.setdefault(turn, {}).setdefault(key, time.monotonic())

    def log_timing(self, turn: int) -> None:
        """Log this turn's marks in ms from the end of speech (negative = before it ended)."""
        marks = self.marks.pop(turn, {})
        zero = marks.get("speech_end") or marks.get("speech_start")
        if zero is not None:
            ms = {k: round((v - zero) * 1000) for k, v in sorted(marks.items(), key=lambda kv: kv[1])}
            self.log({"kind": "server_timing", "turn": turn, "ms": ms})

    async def ask_llm(
        self, text: str, language: str | None, note: str = "", parroting: bool = False
    ) -> UncleReply | None:
        system = SYSTEM.replace("{lang}", reply_language(language)) + note
        try:
            return await self.sarvam.chat_json(
                system, history_prompt(self.history, text, parroting), UncleReply,
                mode=MODE, max_tokens=160, temperature=0.9, reasoning=None,
            )
        except SarvamError as e:
            log.warning("uncle LLM failed: %s", e)
            return None

    async def speak(self, turn: int, line: str, language: str | None, mood: str = "calm") -> None:
        speaker, lang_code = uncle_voice(language)
        pace = 1.0
        if lang_code == "hi-IN":
            speaker, pace = MOOD_VOICE.get(mood, MOOD_VOICE["calm"])
        await self.send({"type": "line", "turn": turn, "text": line, "audio": None})
        t0 = time.perf_counter()
        ttfa = None
        rest = b""
        async for chunk in self.sarvam.tts_stream(line, lang_code, speaker, mode=MODE, pace=pace):
            if ttfa is None:
                ttfa = round((time.perf_counter() - t0) * 1000)
                self.mark(turn, "tts_first_audio")
            chunk = rest + chunk
            cut = len(chunk) - len(chunk) % 2  # whole int16 samples only
            rest = chunk[cut:]
            if cut:
                await self.send_pcm(turn, chunk[:cut])
        self.mark(turn, "tts_done")
        await self.send({"type": "line_end", "turn": turn, "ttfa_ms": ttfa})
